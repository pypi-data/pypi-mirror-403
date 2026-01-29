"""Configuration loader for resilience patterns.

Loads resilience configuration from YAML files (ServiceConfigs pattern).
NO hardcoded configs - all values come from external configuration.

Usage:
    # At app startup (ONCE) - loads YAML and creates all executors
    from empowernow_common.resilience import initialize_executors
    initialize_executors("/app/config/resilience.yaml")
    
    # Later in code (no file I/O, just cache lookup)
    from empowernow_common.resilience import get_executor
    executor = get_executor("empowerid")

Example YAML (ServiceConfigs/services/idp/resilience.yaml):
    
    resilience:
      external-api:
        timeout: 30.0
        max_retries: 2
        retry_delay: 0.5
        circuit_breaker_threshold: 5
        circuit_breaker_timeout: 60.0
        cache_enabled: false
        cache_ttl: 300
      
      redis:
        timeout: 5.0
        max_retries: 3
        circuit_breaker_threshold: 10
      
      empowerid:
        timeout: 60.0
        max_retries: 2
        circuit_breaker_threshold: 5
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union, TYPE_CHECKING

import yaml

from .config import ResilienceConfig
from .resilient_client import ResilientExecutor

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)

# Default config file locations (checked in order)
DEFAULT_CONFIG_PATHS = [
    "/app/config/resilience.yaml",
    "/app/config/resilience.yml",
    "./config/resilience.yaml",
    "./config/resilience.yml",
    "./resilience.yaml",
]

# Environment variable to override config path
CONFIG_PATH_ENV_VAR = "RESILIENCE_CONFIG_PATH"


def find_config_file() -> Optional[Path]:
    """Find the resilience config file.
    
    Checks in order:
    1. RESILIENCE_CONFIG_PATH environment variable
    2. Default paths
    
    Returns:
        Path to config file if found, None otherwise
    """
    # Check environment variable first
    env_path = os.environ.get(CONFIG_PATH_ENV_VAR)
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path
        logger.warning(
            "Config path from %s does not exist: %s",
            CONFIG_PATH_ENV_VAR,
            env_path,
        )
    
    # Check default paths
    for path_str in DEFAULT_CONFIG_PATHS:
        path = Path(path_str)
        if path.exists():
            return path
    
    return None


def load_config_file(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load the resilience YAML config file.
    
    Args:
        config_path: Path to config file (auto-discovers if not provided)
        
    Returns:
        Parsed YAML config dict
        
    Raises:
        FileNotFoundError: If no config file found
        ValueError: If config file is invalid
    """
    if config_path:
        path = Path(config_path)
    else:
        path = find_config_file()
    
    if not path or not path.exists():
        raise FileNotFoundError(
            f"Resilience config file not found. "
            f"Set {CONFIG_PATH_ENV_VAR} environment variable or place config at: "
            f"{', '.join(DEFAULT_CONFIG_PATHS[:2])}"
        )
    
    logger.info("Loading resilience config from: %s", path)
    
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    
    if not data:
        raise ValueError(f"Empty config file: {path}")
    
    return data


def load_resilience_config(
    name: str,
    config_path: Optional[Union[str, Path]] = None,
    section: str = "resilience",
) -> ResilienceConfig:
    """Load resilience config for a specific service/target from YAML.
    
    Args:
        name: Name of the service/target (e.g., "external-api", "redis")
        config_path: Path to YAML config file (auto-discovers if not provided)
        section: Top-level section in YAML (default: "resilience")
        
    Returns:
        ResilienceConfig instance
        
    Raises:
        FileNotFoundError: If config file not found
        KeyError: If service name not found in config
        
    Example YAML:
        resilience:
          external-api:
            timeout: 30.0
            max_retries: 2
    """
    data = load_config_file(config_path)
    
    # Get resilience section
    resilience_config = data.get(section, {})
    if not resilience_config:
        raise KeyError(f"Section '{section}' not found in config file")
    
    # Get config for specific service
    service_config = resilience_config.get(name)
    if not service_config:
        available = list(resilience_config.keys())
        raise KeyError(
            f"Service '{name}' not found in resilience config. "
            f"Available: {available}"
        )
    
    logger.debug(
        "Loaded resilience config for '%s': %s",
        name,
        service_config,
    )
    
    return ResilienceConfig(**service_config)


def load_all_configs(
    config_path: Optional[Union[str, Path]] = None,
    section: str = "resilience",
) -> Dict[str, ResilienceConfig]:
    """Load all resilience configs from YAML.
    
    Args:
        config_path: Path to YAML config file
        section: Top-level section in YAML
        
    Returns:
        Dict mapping service names to ResilienceConfig instances
    """
    data = load_config_file(config_path)
    resilience_config = data.get(section, {})
    
    configs = {}
    for name, config_data in resilience_config.items():
        try:
            configs[name] = ResilienceConfig(**config_data)
            logger.debug("Loaded config for '%s'", name)
        except Exception as e:
            logger.error("Failed to load config for '%s': %s", name, e)
            raise
    
    return configs


def create_executor(
    name: str,
    config_path: Optional[Union[str, Path]] = None,
    redis_client: Optional["Redis[str]"] = None,
    section: str = "resilience",
) -> ResilientExecutor:
    """Create a ResilientExecutor from YAML config.
    
    This is the recommended way to create executors - config comes from
    ServiceConfigs YAML, not from code.
    
    Args:
        name: Name of the service/target (must exist in YAML config)
        config_path: Path to YAML config file (auto-discovers if not provided)
        redis_client: Optional Redis client for caching
        section: Top-level section in YAML
        
    Returns:
        Configured ResilientExecutor
        
    Example:
        # In ServiceConfigs/services/idp/resilience.yaml:
        # resilience:
        #   empowerid:
        #     timeout: 60.0
        #     max_retries: 2
        #     circuit_breaker_threshold: 5
        
        # In code:
        executor = create_executor("empowerid")
        
        @executor.wrap
        async def call_empowerid():
            ...
    """
    config = load_resilience_config(name, config_path, section)
    
    executor = ResilientExecutor(
        name=name,
        config=config,
        redis_client=redis_client,
    )
    
    logger.info(
        "Created executor '%s' from config (timeout=%.1fs, retries=%d, cb_threshold=%d)",
        name,
        config.timeout,
        config.max_retries,
        config.circuit_breaker_threshold,
    )
    
    return executor


class ResilienceRegistry:
    """Registry for managing resilience executors.

    This class replaces global mutable state with an instance-based approach
    that can be injected via dependency injection frameworks.
    """

    def __init__(self):
        """Initialize an empty registry."""
        self._executors: Dict[str, ResilientExecutor] = {}
        self._initialized: bool = False

    def initialize(
        self,
        executor_configs: Dict[str, ResilienceConfig],
        redis_client: Optional["Redis[str]"] = None,
    ) -> None:
        """Initialize executors from configuration.

        Args:
            executor_configs: Dictionary mapping executor names to configurations
            redis_client: Optional Redis client for caching (shared across executors)
        """
        for name, config in executor_configs.items():
            self._executors[name] = ResilientExecutor(
                name=name,
                config=config,
                redis_client=redis_client,
            )
            logger.info(
                "Initialized executor: %s",
                name,
                extra={
                    "component": "config_loader",
                    "executor_name": name,
                    "config": config.model_dump(),
                },
            )

        self._initialized = True
        logger.info(
            "Resilience registry initialized with %d executors",
            len(self._executors),
            extra={
                "component": "config_loader",
                "executor_count": len(self._executors),
            },
        )

    def get_executor(self, name: str) -> ResilientExecutor:
        """Get executor by name (synchronous).

        Args:
            name: Executor name

        Returns:
            ResilientExecutor instance

        Raises:
            ValueError: If registry not initialized or executor not found
        """
        if not self._initialized:
            raise ValueError(
                "Resilience registry not initialized. "
                "Call initialize_executors() at startup."
            )

        if name not in self._executors:
            raise ValueError(
                f"Executor '{name}' not found. "
                f"Available executors: {list(self._executors.keys())}"
            )

        return self._executors[name]

    def is_initialized(self) -> bool:
        """Check if registry has been initialized.

        Returns:
            True if initialized, False otherwise
        """
        return self._initialized

    def get_available_executors(self) -> list[str]:
        """Get list of available executor names.

        Returns:
            List of executor names
        """
        return list(self._executors.keys())

    def get_all_executor_states(self) -> Dict[str, Dict[str, Any]]:
        """Get state of all registered executors (for monitoring).

        Returns:
            Dictionary mapping executor names to their state
        """
        return {name: executor.get_state() for name, executor in self._executors.items()}

    def clear(self) -> None:
        """Clear the registry (mainly for testing)."""
        self._executors.clear()
        self._initialized = False


# Global registry instance (singleton pattern)
_registry = ResilienceRegistry()


def initialize_executors(
    config_path: Optional[Union[str, Path]] = None,
    redis_client: Optional["Redis[str]"] = None,
    section: str = "resilience",
) -> Dict[str, ResilientExecutor]:
    """Initialize all executors from YAML config at startup.
    
    Call this ONCE at application startup. Reads the YAML file once
    and creates all executors upfront. After this, get_executor() is
    just a cache lookup (no file I/O).
    
    Args:
        config_path: Path to YAML config file (auto-discovers if not provided)
        redis_client: Optional Redis client for caching
        section: Top-level section in YAML
        
    Returns:
        Dict of all created executors
        
    Example:
        # At app startup (main.py or lifespan)
        from empowernow_common.resilience import initialize_executors
        
        initialize_executors("/app/config/resilience.yaml")
        
        # Later, anywhere in code (no file I/O)
        executor = get_executor("empowerid")
    """
    configs = load_all_configs(config_path, section)
    _registry.initialize(configs, redis_client)
    logger.info("Initialized %d resilience executors", len(_registry._executors))
    return _registry._executors.copy()


def get_executor(name: str) -> ResilientExecutor:
    """Get a pre-initialized executor by name.
    
    IMPORTANT: Call initialize_executors() at app startup first!
    This function is just a cache lookup - no file I/O.
    
    Args:
        name: Name of the service/target (must exist in YAML config)
        
    Returns:
        Cached ResilientExecutor
        
    Raises:
        ValueError: If registry not initialized or executor not found
        
    Example:
        executor = get_executor("empowerid")
        
        @executor.wrap
        async def call_empowerid():
            ...
    """
    return _registry.get_executor(name)


def is_initialized() -> bool:
    """Check if resilience executors have been initialized."""
    return _registry.is_initialized()


def get_available_executors() -> list[str]:
    """Get list of available executor names."""
    return _registry.get_available_executors()


def get_all_executor_states() -> Dict[str, Dict[str, Any]]:
    """Get state of all registered executors (for monitoring).

    Returns:
        Dictionary mapping executor names to their state
    """
    return _registry.get_all_executor_states()


def clear_executor_cache() -> None:
    """Clear the executor cache (mainly for testing)."""
    _registry.clear()

