"""Configuration models for the resilience library.

These Pydantic models define the configuration schema for resilience patterns.
They can be loaded from YAML files or instantiated directly.
"""

from typing import Optional
from pydantic import BaseModel, Field


class CacheConfig(BaseModel):
    """Configuration for Redis caching."""

    enabled: bool = Field(
        default=False,
        description="Whether caching is enabled",
    )
    ttl: int = Field(
        default=300,
        description="Default cache TTL in seconds",
        ge=1,
    )
    key_prefix: str = Field(
        default="resilience:",
        description="Prefix for all cache keys",
    )

    model_config = {"extra": "allow"}


class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker pattern."""

    enabled: bool = Field(
        default=True,
        description="Whether circuit breaker is enabled",
    )
    threshold: int = Field(
        default=5,
        description="Number of failures before opening the circuit",
        ge=1,
    )
    timeout: float = Field(
        default=60.0,
        description="Seconds before attempting recovery (OPEN -> HALF_OPEN)",
        ge=1.0,
    )
    success_threshold: int = Field(
        default=1,
        description="Successes needed in HALF_OPEN to close circuit",
        ge=1,
    )
    window_seconds: float = Field(
        default=60.0,
        description="Time window for counting failures (sliding window)",
        ge=1.0,
    )
    security_mode: bool = Field(
        default=False,
        description=(
            "Enable security mode (fail-secure). "
            "When True and enabled=False, raises error instead of passing through."
        ),
    )

    model_config = {"extra": "allow"}


class RetryConfig(BaseModel):
    """Configuration for retry with exponential backoff."""

    max_retries: int = Field(
        default=2,
        description="Maximum number of retry attempts (0 = no retries)",
        ge=0,
    )
    initial_delay: float = Field(
        default=0.5,
        description="Initial delay between retries in seconds",
        ge=0.0,
    )
    max_delay: float = Field(
        default=30.0,
        description="Maximum delay between retries in seconds",
        ge=0.0,
    )
    backoff_factor: float = Field(
        default=2.0,
        description="Multiplier for exponential backoff",
        ge=1.0,
    )
    jitter: float = Field(
        default=0.1,
        description="Random jitter factor (0-1) to add to delays",
        ge=0.0,
        le=1.0,
    )

    model_config = {"extra": "allow"}


class ResilienceConfig(BaseModel):
    """Combined resilience configuration.

    This model combines all resilience patterns into a single configuration
    that can be loaded from YAML or constructed programmatically.

    Example YAML:
        resilience:
          timeout: 30.0
          max_retries: 2
          retry_delay: 0.5
          circuit_breaker:
            enabled: true
            threshold: 5
            timeout: 60.0

    Security Mode:
        When security_mode=True, enforces fail-secure behavior:
        - Circuit breaker disabled raises error (does not pass through)
        - Cache errors raise exceptions (do not return None)
        - Prevents fail-open patterns in security-critical operations
    """

    # Security Mode (fail-secure for security-critical operations)
    security_mode: bool = Field(
        default=False,
        description=(
            "Enable security mode (fail-secure). "
            "When True: circuit breaker disabled raises error, cache errors raise exceptions. "
            "Use for authentication, authorization, token validation operations."
        ),
    )

    # Timeout
    timeout: float = Field(
        default=30.0,
        description="Request timeout in seconds",
        ge=0.1,
    )

    # Retry (flat fields for simpler YAML)
    max_retries: int = Field(
        default=2,
        description="Maximum number of retry attempts",
        ge=0,
    )
    retry_delay: float = Field(
        default=0.5,
        description="Initial delay between retries in seconds",
        ge=0.0,
    )
    retry_max_delay: float = Field(
        default=30.0,
        description="Maximum delay between retries",
        ge=0.0,
    )
    retry_backoff_factor: float = Field(
        default=2.0,
        description="Exponential backoff multiplier",
        ge=1.0,
    )
    retry_jitter: float = Field(
        default=0.1,
        description="Jitter factor for retry delays",
        ge=0.0,
        le=1.0,
    )

    # Circuit Breaker (can be nested object or flat)
    circuit_breaker: Optional[CircuitBreakerConfig] = Field(
        default=None,
        description="Circuit breaker configuration (nested)",
    )

    # Flat circuit breaker fields (alternative to nested)
    circuit_breaker_enabled: bool = Field(
        default=True,
        description="Whether circuit breaker is enabled",
    )
    circuit_breaker_threshold: int = Field(
        default=5,
        description="Failures before opening circuit",
        ge=1,
    )
    circuit_breaker_timeout: float = Field(
        default=60.0,
        description="Seconds before recovery attempt",
        ge=1.0,
    )
    circuit_breaker_success_threshold: int = Field(
        default=1,
        description="Successes needed to close circuit",
        ge=1,
    )

    # Cache (can be nested object or flat)
    cache: Optional[CacheConfig] = Field(
        default=None,
        description="Cache configuration (nested)",
    )

    # Flat cache fields (alternative to nested)
    cache_enabled: bool = Field(
        default=False,
        description="Whether caching is enabled",
    )
    cache_ttl: int = Field(
        default=300,
        description="Default cache TTL in seconds",
        ge=1,
    )
    cache_key_prefix: str = Field(
        default="resilience:",
        description="Prefix for cache keys",
    )

    model_config = {"extra": "allow"}

    def get_circuit_breaker_config(self) -> CircuitBreakerConfig:
        """Get circuit breaker config, preferring nested over flat fields."""
        if self.circuit_breaker is not None:
            # Inherit security_mode from parent if not explicitly set in nested config
            cb_dict = self.circuit_breaker.model_dump()
            # If security_mode not set in nested config, inherit from parent
            if 'security_mode' not in cb_dict or cb_dict.get('security_mode') is None:
                cb_dict['security_mode'] = self.security_mode
            return CircuitBreakerConfig(**cb_dict)
        return CircuitBreakerConfig(
            enabled=self.circuit_breaker_enabled,
            threshold=self.circuit_breaker_threshold,
            timeout=self.circuit_breaker_timeout,
            success_threshold=self.circuit_breaker_success_threshold,
            security_mode=self.security_mode,
        )

    def get_retry_config(self) -> RetryConfig:
        """Get retry config from flat fields."""
        return RetryConfig(
            max_retries=self.max_retries,
            initial_delay=self.retry_delay,
            max_delay=self.retry_max_delay,
            backoff_factor=self.retry_backoff_factor,
            jitter=self.retry_jitter,
        )

    def get_cache_config(self) -> CacheConfig:
        """Get cache config, preferring nested over flat fields."""
        if self.cache is not None:
            return self.cache
        return CacheConfig(
            enabled=self.cache_enabled,
            ttl=self.cache_ttl,
            key_prefix=self.cache_key_prefix,
        )

    @classmethod
    def from_flat(
        cls,
        timeout: float = 30.0,
        max_retries: int = 2,
        retry_delay: float = 0.5,
        circuit_breaker_enabled: bool = True,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 60.0,
    ) -> "ResilienceConfig":
        """Create config from flat parameters (convenience method)."""
        return cls(
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            circuit_breaker_enabled=circuit_breaker_enabled,
            circuit_breaker_threshold=circuit_breaker_threshold,
            circuit_breaker_timeout=circuit_breaker_timeout,
        )

