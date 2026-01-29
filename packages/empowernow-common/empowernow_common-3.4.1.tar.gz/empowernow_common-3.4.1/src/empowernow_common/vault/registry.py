"""Vault provider registry following PIPRegistry pattern.

Per Playbook §16.7: PIPRegistry pattern with @dataclass.

The registry manages provider instances by name, allowing:
- Multiple instances of the same provider type (e.g., openbao-dev, openbao-prod)
- Runtime lookup by instance name
- Health status aggregation
- Graceful shutdown of all providers
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Optional

from empowernow_common.vault.base import VaultProvider, ReadableVaultProvider
from empowernow_common.vault.exceptions import VaultConfigurationError


logger = logging.getLogger(__name__)


@dataclass
class ProviderStatus:
    """Health status of a provider instance."""
    
    name: str
    healthy: bool
    last_check_time: Optional[float] = None
    error_message: Optional[str] = None
    capabilities: Dict[str, bool] = field(default_factory=dict)


@dataclass
class VaultProviderRegistry:
    """Registry for vault provider instances.
    
    Thread-safe registry that manages provider lifecycle:
    - Register providers by name
    - Lookup providers by name
    - Aggregate health status
    - Close all providers on shutdown
    
    Usage:
        registry = VaultProviderRegistry()
        registry.register("openbao", openbao_provider)
        registry.register("openbao-prod", openbao_prod_provider)
        
        provider = registry.get_provider("openbao")
        secret = await provider.get_secret("secret/app#token")
        
        await registry.close_all()
    
    Per design Decision 1: Scheme = Instance Name
    The provider name should match the URI scheme used to access it.
    """
    
    _providers: Dict[str, VaultProvider] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    def register(self, name: str, provider: VaultProvider) -> None:
        """Register a provider instance.
        
        Args:
            name: Instance name (e.g., "openbao", "openbao-prod")
            provider: Provider instance implementing VaultProvider protocol
        
        Raises:
            VaultConfigurationError: If name is already registered
        """
        name_lower = name.lower()
        
        if name_lower in self._providers:
            raise VaultConfigurationError(
                f"Provider '{name}' is already registered. "
                f"Use unregister() first to replace.",
            )
        
        # Validate provider implements required protocol
        if not isinstance(provider, ReadableVaultProvider):
            raise VaultConfigurationError(
                f"Provider '{name}' does not implement ReadableVaultProvider protocol",
            )
        
        self._providers[name_lower] = provider
        logger.info(
            "Registered vault provider: %s (type: %s)",
            name,
            getattr(provider, "VAULT_TYPE", "unknown"),
            extra={
                "component": "vault_registry",
                "provider_name": name,
                "provider_type": getattr(provider, "VAULT_TYPE", "unknown"),
            },
        )
    
    def unregister(self, name: str) -> Optional[VaultProvider]:
        """Unregister a provider instance.
        
        Args:
            name: Instance name to unregister
        
        Returns:
            The removed provider, or None if not found
        """
        return self._providers.pop(name.lower(), None)
    
    def get_provider(self, name: str) -> VaultProvider:
        """Get a provider by instance name.
        
        Args:
            name: Instance name (e.g., "openbao", "openbao-prod")
        
        Returns:
            The provider instance
        
        Raises:
            VaultConfigurationError: If provider not found
        """
        provider = self._providers.get(name.lower())
        if provider is None:
            available = list(self._providers.keys())
            raise VaultConfigurationError(
                f"Provider '{name}' not found. Available: {available}",
            )
        return provider
    
    def get_provider_or_none(self, name: str) -> Optional[VaultProvider]:
        """Get a provider by instance name, or None if not found.
        
        Args:
            name: Instance name
        
        Returns:
            The provider instance or None
        """
        return self._providers.get(name.lower())
    
    def has_provider(self, name: str) -> bool:
        """Check if a provider is registered.
        
        Args:
            name: Instance name
        
        Returns:
            True if provider exists
        """
        return name.lower() in self._providers
    
    def list_providers(self) -> Dict[str, VaultProvider]:
        """Get a copy of all registered providers.
        
        Returns:
            Dictionary mapping names to providers
        """
        return self._providers.copy()
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over provider names."""
        return iter(self._providers)
    
    def __len__(self) -> int:
        """Return number of registered providers."""
        return len(self._providers)
    
    def __contains__(self, name: str) -> bool:
        """Check if provider is registered."""
        return name.lower() in self._providers
    
    async def health_check(self, name: str) -> ProviderStatus:
        """Check health of a specific provider.
        
        Args:
            name: Provider instance name
        
        Returns:
            ProviderStatus with health information
        """
        import time
        
        provider = self.get_provider_or_none(name)
        if provider is None:
            return ProviderStatus(
                name=name,
                healthy=False,
                error_message="Provider not found",
            )
        
        try:
            # Try health check method if available
            if hasattr(provider, "health_check"):
                await asyncio.wait_for(
                    provider.health_check(),  # type: ignore[attr-defined]
                    timeout=5.0,
                )
            
            return ProviderStatus(
                name=name,
                healthy=True,
                last_check_time=time.time(),
                capabilities=getattr(provider, "CAPABILITIES", {}),
            )
            
        except asyncio.TimeoutError:
            return ProviderStatus(
                name=name,
                healthy=False,
                last_check_time=time.time(),
                error_message="Health check timed out",
                capabilities=getattr(provider, "CAPABILITIES", {}),
            )
        except Exception as e:
            return ProviderStatus(
                name=name,
                healthy=False,
                last_check_time=time.time(),
                error_message=str(e),
                capabilities=getattr(provider, "CAPABILITIES", {}),
            )
    
    async def health_status(self) -> Dict[str, ProviderStatus]:
        """Get health status of all providers.
        
        Returns:
            Dictionary mapping provider names to their status
        """
        statuses = await asyncio.gather(
            *[self.health_check(name) for name in self._providers],
            return_exceptions=True,
        )
        
        result = {}
        for name, status in zip(self._providers, statuses):
            if isinstance(status, Exception):
                result[name] = ProviderStatus(
                    name=name,
                    healthy=False,
                    error_message=str(status),
                )
            else:
                result[name] = status
        
        return result
    
    async def close_all(self) -> None:
        """Close all registered providers.
        
        Safe to call multiple times. Logs errors but doesn't raise.
        
        Per design: Lifecycle tests require close_all() to complete
        without hanging (5 second timeout).
        """
        async with self._lock:
            close_tasks = []
            
            for name, provider in self._providers.items():
                if hasattr(provider, "close"):
                    close_tasks.append(
                        asyncio.create_task(
                            self._close_provider(name, provider),
                            name=f"close_{name}",
                        )
                    )
            
            if close_tasks:
                # Wait with timeout to prevent hanging
                done, pending = await asyncio.wait(
                    close_tasks,
                    timeout=5.0,
                )
                
                # Cancel any pending tasks
                for task in pending:
                    task.cancel()
                    logger.warning(
                        "Provider close timed out: %s",
                        task.get_name(),
                        extra={"component": "vault_registry"},
                    )
            
            self._providers.clear()
            logger.info(
                "Closed all vault providers",
                extra={"component": "vault_registry"},
            )
    
    async def _close_provider(self, name: str, provider: VaultProvider) -> None:
        """Close a single provider with error handling."""
        try:
            await provider.close()
            logger.debug(
                "Closed vault provider: %s",
                name,
                extra={"component": "vault_registry", "provider_name": name},
            )
        except Exception as e:
            logger.error(
                "Error closing vault provider %s: %s",
                name,
                e,
                extra={
                    "component": "vault_registry",
                    "provider_name": name,
                    "error_type": type(e).__name__,
                },
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert registry to dictionary for monitoring/debugging.
        
        Returns:
            Dictionary with provider names and their types
        """
        return {
            "providers": {
                name: {
                    "type": getattr(p, "VAULT_TYPE", "unknown"),
                    "capabilities": getattr(p, "CAPABILITIES", {}),
                }
                for name, p in self._providers.items()
            },
            "count": len(self._providers),
        }
