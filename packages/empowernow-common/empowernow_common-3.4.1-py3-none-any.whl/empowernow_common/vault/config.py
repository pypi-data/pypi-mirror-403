"""Vault provider configuration and async loading.

Per design Decision 5: Async Initialization
- load_vault_providers() is async with startup validation option
- Providers are initialized and validated before registration
- Fail-fast on startup if required providers aren't available

Configuration Format (vault_providers.yaml):
    vault_providers:
      openbao:
        type: openbao
        url: "${{ENV:VAULT_URL}}"
        auth:
          method: kubernetes
          role: "${{ENV:VAULT_ROLE}}"
        timeout_s: 30
        verify_ssl: true
        pool_size: 10
        circuit_breaker:
          threshold: 5
          timeout_s: 30

Per Playbook §16.2: ConfigLoader placeholder pattern (${{ENV:...}}, ${{FILE:...}})
"""
from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml

from empowernow_common.vault.registry import VaultProviderRegistry
from empowernow_common.vault.base import VaultProvider
from empowernow_common.vault.exceptions import (
    VaultConfigurationError,
    StartupValidationError,
)


logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for a vault provider instance."""
    
    name: str
    type: str
    url: Optional[str] = None
    auth: Dict[str, Any] = field(default_factory=dict)
    timeout_s: int = 30
    verify_ssl: bool = True
    pool_size: int = 10
    circuit_breaker: Dict[str, Any] = field(default_factory=dict)
    capabilities: Dict[str, bool] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)


# Provider factory registry
_PROVIDER_FACTORIES: Dict[str, Type[VaultProvider]] = {}


def register_provider_factory(
    provider_type: str,
    factory: Type[VaultProvider],
) -> None:
    """Register a provider factory for a type.
    
    This is called during module initialization to register
    available provider implementations.
    
    Args:
        provider_type: The type name (e.g., "openbao", "azure")
        factory: The provider class to instantiate
    """
    _PROVIDER_FACTORIES[provider_type.lower()] = factory
    logger.debug("Registered provider factory: %s", provider_type)


def _resolve_placeholder(value: str) -> str:
    """Resolve configuration placeholders.
    
    Supports:
        ${{ENV:VAR_NAME}}          - Environment variable
        ${{ENV:VAR_NAME:default}}  - Environment variable with default
        ${{FILE:/path/to/file}}    - File contents
    
    Args:
        value: String that may contain placeholders
    
    Returns:
        Resolved string value
    """
    if not isinstance(value, str):
        return value
    
    if not (value.startswith("${{") and value.endswith("}}")):
        return value
    
    placeholder = value[3:-2]  # Remove ${{ and }}
    
    if placeholder.startswith("ENV:"):
        # Environment variable
        env_part = placeholder[4:]
        if ":" in env_part:
            var_name, default = env_part.split(":", 1)
            return os.getenv(var_name, default)
        return os.getenv(env_part, "")
    
    elif placeholder.startswith("FILE:"):
        # File contents
        file_path = placeholder[5:]
        try:
            return Path(file_path).read_text().strip()
        except Exception as e:
            logger.warning("Failed to read file '%s': %s", file_path, e)
            return ""
    
    # Unknown placeholder type
    logger.warning("Unknown placeholder type: %s", placeholder)
    return value


def _resolve_config_values(config: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively resolve all placeholders in config.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Configuration with all placeholders resolved
    """
    result = {}
    for key, value in config.items():
        if isinstance(value, str):
            result[key] = _resolve_placeholder(value)
        elif isinstance(value, dict):
            result[key] = _resolve_config_values(value)
        elif isinstance(value, list):
            result[key] = [
                _resolve_config_values(v) if isinstance(v, dict)
                else _resolve_placeholder(v) if isinstance(v, str)
                else v
                for v in value
            ]
        else:
            result[key] = value
    return result


def _load_yaml_config(config_path: str) -> Dict[str, Any]:
    """Load and parse YAML configuration file.
    
    Args:
        config_path: Path to vault_providers.yaml
    
    Returns:
        Parsed configuration dictionary
    
    Raises:
        VaultConfigurationError: If file not found or invalid
    """
    path = Path(config_path)
    
    if not path.exists():
        raise VaultConfigurationError(
            f"Configuration file not found: {config_path}",
        )
    
    try:
        content = path.read_text()
        config = yaml.safe_load(content) or {}
        return config
    except yaml.YAMLError as e:
        raise VaultConfigurationError(
            f"Invalid YAML in {config_path}: {e}",
        ) from e


def _parse_provider_config(name: str, raw: Dict[str, Any]) -> ProviderConfig:
    """Parse raw config dict into ProviderConfig.
    
    Args:
        name: Provider instance name
        raw: Raw configuration dictionary
    
    Returns:
        Parsed ProviderConfig
    """
    resolved = _resolve_config_values(raw)
    
    return ProviderConfig(
        name=name,
        type=resolved.get("type", "").lower(),
        url=resolved.get("url"),
        auth=resolved.get("auth", {}),
        timeout_s=int(resolved.get("timeout_s", resolved.get("timeout", 30))),
        verify_ssl=resolved.get("verify_ssl", True),
        pool_size=int(resolved.get("pool_size", 10)),
        circuit_breaker=resolved.get("circuit_breaker", {}),
        capabilities=resolved.get("capabilities", {}),
        extra={k: v for k, v in resolved.items() 
               if k not in ("type", "url", "auth", "timeout_s", "timeout", 
                           "verify_ssl", "pool_size", "circuit_breaker", "capabilities")},
    )


async def _create_provider(config: ProviderConfig) -> VaultProvider:
    """Create a provider instance from configuration.
    
    Args:
        config: Parsed provider configuration
    
    Returns:
        Initialized provider instance
    
    Raises:
        VaultConfigurationError: If provider type unknown or creation fails
    """
    factory = _PROVIDER_FACTORIES.get(config.type)
    
    if factory is None:
        available = list(_PROVIDER_FACTORIES.keys())
        raise VaultConfigurationError(
            f"Unknown provider type '{config.type}' for '{config.name}'. "
            f"Available: {available}",
        )
    
    try:
        # Build provider-specific config dict
        provider_config = {
            "url": config.url,
            "timeout": config.timeout_s,
            "verify_ssl": config.verify_ssl,
            "pool_size": config.pool_size,
            **config.auth,
            **config.extra,
        }
        
        # Add circuit breaker config
        if config.circuit_breaker:
            provider_config["cb_failure_threshold"] = config.circuit_breaker.get("threshold", 5)
            provider_config["cb_reset_timeout_s"] = config.circuit_breaker.get("timeout_s", 30)
        
        # Create provider instance
        # Some providers may have async initialization
        provider = factory(provider_config)  # type: ignore[call-arg]
        
        return provider
        
    except Exception as e:
        raise VaultConfigurationError(
            f"Failed to create provider '{config.name}': {e}",
        ) from e


async def _validate_provider(
    provider: VaultProvider,
    name: str,
    timeout: float = 5.0,
) -> None:
    """Validate provider connectivity during startup.
    
    Args:
        provider: Provider instance to validate
        name: Provider name for logging
        timeout: Validation timeout in seconds
    
    Raises:
        StartupValidationError: If validation fails
    """
    try:
        if hasattr(provider, "health_check"):
            await asyncio.wait_for(
                provider.health_check(),  # type: ignore[attr-defined]
                timeout=timeout,
            )
        logger.info(
            "✅ Provider '%s' validated successfully",
            name,
            extra={"component": "vault_config", "provider_name": name},
        )
    except asyncio.TimeoutError:
        raise StartupValidationError(
            name,
            f"Health check timed out after {timeout}s",
        )
    except Exception as e:
        raise StartupValidationError(name, str(e))


async def load_vault_providers(
    config_path: str,
    *,
    validate_connectivity: bool = True,
    validation_timeout: float = 5.0,
    required_providers: Optional[List[str]] = None,
) -> VaultProviderRegistry:
    """Load and initialize vault providers from configuration.
    
    This is the main entry point for loading providers during
    application startup.
    
    Args:
        config_path: Path to vault_providers.yaml
        validate_connectivity: If True, test connectivity during startup.
                              If False, defer validation to first request.
        validation_timeout: Timeout for each provider validation (seconds)
        required_providers: List of provider names that MUST be loaded.
                          Startup fails if any are missing.
    
    Returns:
        VaultProviderRegistry with all loaded providers
    
    Raises:
        VaultConfigurationError: If configuration invalid
        StartupValidationError: If required provider validation fails
    
    Example:
        registry = await load_vault_providers(
            "/app/config/vault_providers.yaml",
            validate_connectivity=True,
            required_providers=["openbao"],
        )
    """
    registry = VaultProviderRegistry()
    
    # Load configuration
    try:
        raw_config = _load_yaml_config(config_path)
    except VaultConfigurationError:
        if required_providers:
            raise
        logger.warning(
            "Configuration file not found, returning empty registry: %s",
            config_path,
        )
        return registry
    
    providers_config = raw_config.get("vault_providers", {})
    
    if not providers_config:
        logger.warning("No providers configured in %s", config_path)
        if required_providers:
            raise VaultConfigurationError(
                f"Required providers not found: {required_providers}",
            )
        return registry
    
    # Load each provider
    loaded_providers: List[str] = []
    
    for name, raw_provider_config in providers_config.items():
        # Check if provider type is disabled
        provider_type = raw_provider_config.get("type", "").lower()
        enabled_env = f"{provider_type.upper()}_VAULT_ENABLED"
        if os.getenv(enabled_env, "true").lower() in ("false", "0", "no"):
            logger.info(
                "Skipping provider '%s' (disabled by %s)",
                name,
                enabled_env,
            )
            continue
        
        try:
            config = _parse_provider_config(name, raw_provider_config)
            provider = await _create_provider(config)
            
            if validate_connectivity:
                await _validate_provider(provider, name, validation_timeout)
            
            registry.register(name, provider)
            loaded_providers.append(name)
            
            logger.info(
                "✅ Loaded provider '%s' (type: %s)",
                name,
                config.type,
                extra={
                    "component": "vault_config",
                    "provider_name": name,
                    "provider_type": config.type,
                },
            )
            
        except StartupValidationError:
            # Re-raise validation errors if this is a required provider
            if required_providers and name in required_providers:
                raise
            logger.error(
                "❌ Failed to load provider '%s' (non-required, skipping)",
                name,
                exc_info=True,
            )
        except Exception as e:
            if required_providers and name in required_providers:
                raise VaultConfigurationError(
                    f"Required provider '{name}' failed to load: {e}",
                ) from e
            logger.error(
                "❌ Failed to load provider '%s': %s",
                name,
                e,
                exc_info=True,
            )
    
    # Check required providers
    if required_providers:
        missing = set(required_providers) - set(loaded_providers)
        if missing:
            raise VaultConfigurationError(
                f"Required providers not loaded: {sorted(missing)}. "
                f"Loaded: {sorted(loaded_providers)}",
            )
    
    logger.info(
        "Vault provider registry initialized with %d providers: %s",
        len(loaded_providers),
        loaded_providers,
        extra={
            "component": "vault_config",
            "provider_count": len(loaded_providers),
            "providers": loaded_providers,
        },
    )
    
    return registry


def load_vault_providers_sync(
    config_path: str,
    **kwargs: Any,
) -> VaultProviderRegistry:
    """Synchronous wrapper for load_vault_providers.
    
    Convenience method for non-async contexts (e.g., CLI tools).
    
    Args:
        config_path: Path to vault_providers.yaml
        **kwargs: Additional arguments passed to load_vault_providers
    
    Returns:
        VaultProviderRegistry with all loaded providers
    """
    return asyncio.run(load_vault_providers(config_path, **kwargs))
