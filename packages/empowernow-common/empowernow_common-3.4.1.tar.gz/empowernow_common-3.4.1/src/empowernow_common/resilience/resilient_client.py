"""Resilient Executor - Combines all resilience patterns.

The ResilientExecutor combines circuit breaker, retry, timeout,
and optional caching into a single, easy-to-use wrapper.

Usage:
    from empowernow_common.resilience import ResilientExecutor, ResilienceConfig

    executor = ResilientExecutor(
        name="empowerid",
        config=ResilienceConfig(
            timeout=30.0,
            max_retries=2,
            retry_delay=0.5,
            circuit_breaker_enabled=True,
            circuit_breaker_threshold=5,
            circuit_breaker_timeout=60.0,
        )
    )

    # Execute with all resilience patterns
    result = await executor.execute(call_external_service)

    # Or use as decorator
    @executor.wrap
    async def call_external_service():
        ...

    # With caching (requires redis_client)
    executor = ResilientExecutor(
        name="api",
        config=ResilienceConfig(cache_enabled=True),
        redis_client=redis_client,
    )

    @executor.wrap(cache_ttl=300)
    async def get_user(user_id: str):
        ...
"""

import asyncio
import functools
import time
import logging
from typing import Any, Callable, Coroutine, Dict, Optional, TypeVar, Union, TYPE_CHECKING

from .config import ResilienceConfig

if TYPE_CHECKING:
    from redis.asyncio import Redis
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    get_circuit_breaker,
)
from .retry import RetryStrategy, RetryExhaustedError
from .timeout import timeout_wrapper, ResilienceTimeoutError
from .cache import CacheWrapper, generate_cache_key

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ResilientExecutor:
    """Combined resilience executor with circuit breaker, retry, timeout, and caching.

    Execution order:
    1. Cache check (if caching enabled)
    2. Circuit Breaker check (fail fast if open)
    3. Retry wrapper (with exponential backoff)
    4. Timeout wrapper (per-attempt timeout)
    5. Cache store (if caching enabled and successful)

    The retry wrapper will NOT retry circuit breaker errors, ensuring
    fast-fail behavior is preserved.
    """

    def __init__(
        self,
        name: str,
        config: Optional[ResilienceConfig] = None,
        redis_client: Optional["Redis[str]"] = None,
    ):
        """Initialize resilient executor.

        Args:
            name: Identifier for this executor (used for circuit breaker isolation)
            config: Resilience configuration
            redis_client: Optional async Redis client for caching
        """
        self.name = name
        self.config = config or ResilienceConfig()
        self._redis_client = redis_client

        # Initialize components
        self._circuit_breaker: Optional[CircuitBreaker] = None
        self._retry_strategy = RetryStrategy(
            config=self.config.get_retry_config(),
            name=name,
        )

        # Initialize cache if redis provided
        self._cache: Optional[CacheWrapper] = None
        if redis_client is not None:
            cache_config = self.config.get_cache_config()
            self._cache = CacheWrapper(
                redis_client=redis_client,
                key_prefix=f"{cache_config.key_prefix}{name}:",
                default_ttl=cache_config.ttl,
                security_mode=self.config.security_mode,
            )

    async def _get_circuit_breaker(self) -> CircuitBreaker:
        """Get or create circuit breaker (lazy initialization)."""
        if self._circuit_breaker is None:
            cb_config = self.config.get_circuit_breaker_config()
            self._circuit_breaker = await get_circuit_breaker(self.name, cb_config)
        return self._circuit_breaker

    async def execute(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute function with all resilience patterns.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func if successful

        Raises:
            CircuitBreakerOpenError: If circuit is open
            RetryExhaustedError: If all retries exhausted
            TimeoutError: If operation times out
            Exception: Original exception if non-retryable
        """
        start_time = time.time()
        cb = await self._get_circuit_breaker()

        async def _with_timeout():
            """Inner function that applies timeout."""
            return await timeout_wrapper(
                func(*args, **kwargs),
                timeout=self.config.timeout,
                operation_name=self.name,
            )

        async def _with_retry():
            """Inner function that applies retry and timeout."""
            return await self._retry_strategy.execute(_with_timeout)

        try:
            # Circuit breaker wraps everything
            result = await cb.execute(_with_retry)

            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.debug(
                "Resilient execution succeeded for %s in %.2fms",
                self.name,
                duration_ms,
                extra={
                    "component": "resilient_executor",
                    "executor_name": self.name,
                    "duration_ms": duration_ms,
                },
            )
            return result

        except CircuitBreakerOpenError:
            # Re-raise circuit breaker errors directly
            raise
        except RetryExhaustedError as e:
            # Log and re-raise retry exhaustion
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                "Resilient execution failed for %s after %.2fms: retries exhausted",
                self.name,
                duration_ms,
                extra={
                    "component": "resilient_executor",
                    "executor_name": self.name,
                    "duration_ms": duration_ms,
                    "error": "retry_exhausted",
                },
            )
            raise
        except Exception as e:
            # Log other errors
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                "Resilient execution failed for %s after %.2fms: %s",
                self.name,
                duration_ms,
                str(e)[:100],
                extra={
                    "component": "resilient_executor",
                    "executor_name": self.name,
                    "duration_ms": duration_ms,
                    "error_type": type(e).__name__,
                },
            )
            raise

    def wrap(
        self,
        func: Optional[Callable[..., Coroutine[Any, Any, T]]] = None,
        *,
        cache_ttl: Optional[int] = None,
        cache_key: Optional[Union[str, Callable[..., str]]] = None,
    ) -> Callable[..., Coroutine[Any, Any, T]]:
        """Decorator to wrap a function with resilience and optional caching.

        Usage:
            # Without caching
            @executor.wrap
            async def my_function():
                ...

            # With caching (auto-generated key)
            @executor.wrap(cache_ttl=300)
            async def get_user(user_id: str):
                ...

            # With custom cache key
            @executor.wrap(cache_ttl=300, cache_key=lambda uid: f"user:{uid}")
            async def get_user(uid: str):
                ...

        Args:
            func: The async function to wrap
            cache_ttl: Cache TTL in seconds (enables caching if set)
            cache_key: Static key string or callable(*args, **kwargs) -> str
        """

        def decorator(fn: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
            @functools.wraps(fn)
            async def wrapper(*args: Any, **kwargs: Any) -> T:
                # Check cache first if caching enabled
                if cache_ttl is not None and self._cache is not None:
                    key = self._resolve_cache_key(cache_key, fn.__name__, args, kwargs)
                    cached_value = await self._cache.get(key)
                    if cached_value is not None:
                        logger.debug(
                            "Cache hit for %s",
                            key,
                            extra={"cache_key": key, "executor_name": self.name},
                        )
                        return cached_value

                # Execute with resilience patterns
                result = await self.execute(fn, *args, **kwargs)

                # Cache result if caching enabled
                if cache_ttl is not None and self._cache is not None:
                    key = self._resolve_cache_key(cache_key, fn.__name__, args, kwargs)
                    await self._cache.set(key, result, ttl=cache_ttl)

                return result

            return wrapper

        # Support both @wrap and @wrap() syntax
        if func is not None:
            return decorator(func)
        return decorator

    def _resolve_cache_key(
        self,
        cache_key: Optional[Union[str, Callable[..., str]]],
        func_name: str,
        args: tuple,
        kwargs: dict,
    ) -> str:
        """Resolve cache key from string, callable, or auto-generate.

        Args:
            cache_key: Static key, callable, or None for auto-generation
            func_name: Name of the cached function
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Resolved cache key string
        """
        cache_config = self.config.get_cache_config()
        prefix = f"{cache_config.key_prefix}{self.name}:"

        if cache_key is None:
            # Auto-generate from args
            return generate_cache_key(prefix, func_name, args, kwargs)
        elif callable(cache_key):
            # Call function with args/kwargs
            return f"{prefix}{cache_key(*args, **kwargs)}"
        else:
            # Static string
            return f"{prefix}{cache_key}"

    def get_state(self) -> Dict[str, Any]:
        """Get current state for monitoring."""
        cb_state = (
            self._circuit_breaker.get_state()
            if self._circuit_breaker
            else {"state": "uninitialized"}
        )
        cache_config = self.config.get_cache_config()
        cache_state = (
            self._cache.get_stats()
            if self._cache
            else {"enabled": False}
        )
        return {
            "name": self.name,
            "config": {
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries,
                "retry_delay": self.config.retry_delay,
                "circuit_breaker_enabled": self.config.circuit_breaker_enabled,
                "circuit_breaker_threshold": self.config.circuit_breaker_threshold,
                "circuit_breaker_timeout": self.config.circuit_breaker_timeout,
                "cache_enabled": cache_config.enabled,
                "cache_ttl": cache_config.ttl,
            },
            "circuit_breaker": cb_state,
            "cache": cache_state,
        }


# Note: get_executor() and get_all_executor_states() are now provided by
# config_loader module. The async get_executor has been removed in favor
# of the synchronous version that requires pre-initialization via
# initialize_executors() at startup.

