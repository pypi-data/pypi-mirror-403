"""EmpowerNow Resilience Library.

Resilience patterns for async Python services:
- Circuit Breaker (CLOSED, OPEN, HALF_OPEN states)
- Retry with exponential backoff and jitter
- Timeout handling
- Redis caching (optional)
- Combined ResilientExecutor

Usage:
    from empowernow_common.resilience import ResilientExecutor, ResilienceConfig

    executor = ResilientExecutor(
        name="external-api",
        config=ResilienceConfig(
            timeout=30.0,
            max_retries=2,
            circuit_breaker_threshold=5,
        )
    )

    result = await executor.execute(my_async_function)

    # With caching
    executor = ResilientExecutor(
        name="api",
        config=ResilienceConfig(cache_enabled=True, cache_ttl=300),
        redis_client=redis_client,
    )

    @executor.wrap(cache_ttl=300)
    async def get_data(item_id: str):
        ...
"""

from .config import (
    ResilienceConfig,
    CircuitBreakerConfig,
    RetryConfig,
    CacheConfig,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerOpenError,
    get_circuit_breaker,
    get_all_circuit_breaker_states,
)
from .retry import (
    RetryStrategy,
    RetryExhaustedError,
    DEFAULT_RETRYABLE_EXCEPTIONS,
    DEFAULT_NON_RETRYABLE_EXCEPTIONS,
)
from .timeout import (
    timeout_wrapper,
    ResilienceTimeoutError,
)
from .cache import (
    CacheWrapper,
    RedisClientFactory,
    generate_cache_key,
    validate_cache_key,
)
from .resilient_client import ResilientExecutor
from .config_loader import (
    initialize_executors,
    get_executor,
    is_initialized,
    get_available_executors,
    get_all_executor_states,
    load_resilience_config,
    load_all_configs,
    create_executor,
    find_config_file,
    clear_executor_cache,
)
from .observability import (
    ResilienceMetrics,
    get_metrics,
    set_metrics_collector,
    set_correlation_id,
    get_correlation_id,
    enrich_log_context,
    trace_operation,
)
from .errors import (
    ResilienceError,
    ErrorCategory,
    ErrorSeverity,
    CircuitBreakerError,
    RetryExhaustedError,
    TimeoutError as ResilienceTimeoutErrorEnhanced,
    classify_error,
    enrich_error_context,
)
from .lifecycle import (
    graceful_shutdown,
    register_shutdown_handler,
    unregister_shutdown_handler,
    get_shutdown_event,
    is_shutting_down,
    lifespan_context,
    HealthCheck,
    get_health_check,
)
from .bulkhead import (
    Bulkhead,
    BulkheadConfig,
    BulkheadFullError,
    get_bulkhead,
    get_all_bulkhead_stats,
)

__all__ = [
    # Config
    "ResilienceConfig",
    "CircuitBreakerConfig",
    "RetryConfig",
    "CacheConfig",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerState",
    "CircuitBreakerOpenError",
    "get_circuit_breaker",
    "get_all_circuit_breaker_states",
    # Retry
    "RetryStrategy",
    "RetryExhaustedError",
    "DEFAULT_RETRYABLE_EXCEPTIONS",
    "DEFAULT_NON_RETRYABLE_EXCEPTIONS",
    # Timeout
    "timeout_wrapper",
    "ResilienceTimeoutError",
    # Cache
    "CacheWrapper",
    "RedisClientFactory",
    "generate_cache_key",
    "validate_cache_key",
    # Combined Executor
    "ResilientExecutor",
    "get_all_executor_states",
    # Config Loader (ServiceConfigs integration)
    "initialize_executors",
    "get_executor",
    "is_initialized",
    "get_available_executors",
    "load_resilience_config",
    "load_all_configs",
    "create_executor",
    "find_config_file",
    "clear_executor_cache",
    # Observability
    "ResilienceMetrics",
    "get_metrics",
    "set_metrics_collector",
    "set_correlation_id",
    "get_correlation_id",
    "enrich_log_context",
    "trace_operation",
    # Error Handling
    "ResilienceError",
    "ErrorCategory",
    "ErrorSeverity",
    "CircuitBreakerError",
    "RetryExhaustedError",
    "ResilienceTimeoutErrorEnhanced",
    "classify_error",
    "enrich_error_context",
    # Lifecycle Management
    "graceful_shutdown",
    "register_shutdown_handler",
    "unregister_shutdown_handler",
    "get_shutdown_event",
    "is_shutting_down",
    "lifespan_context",
    "HealthCheck",
    "get_health_check",
    # Bulkhead Pattern
    "Bulkhead",
    "BulkheadConfig",
    "BulkheadFullError",
    "get_bulkhead",
    "get_all_bulkhead_stats",
]

