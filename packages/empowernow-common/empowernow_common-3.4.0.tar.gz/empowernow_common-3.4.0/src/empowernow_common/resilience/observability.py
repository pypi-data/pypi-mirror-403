"""Observability support for resilience patterns.

Provides metrics, distributed tracing, and correlation ID support
for enterprise-grade observability.

Enterprise patterns:
- Prometheus metrics integration
- Distributed tracing support
- Correlation ID propagation
- Structured logging with context
"""

import time
import logging
from typing import Any, Dict, Optional, Callable, Coroutine, TypeVar
from contextvars import ContextVar
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Context variable for correlation ID (thread-local for async)
_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

# Optional metrics collector (can be set by application)
_metrics_collector: Optional[Any] = None


def set_correlation_id(correlation_id: Optional[str]) -> None:
    """Set correlation ID for current async context.
    
    Args:
        correlation_id: Correlation/trace ID for distributed tracing
    """
    _correlation_id.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get correlation ID from current async context.
    
    Returns:
        Correlation ID if set, None otherwise
    """
    return _correlation_id.get()


def set_metrics_collector(collector: Any) -> None:
    """Set metrics collector for resilience patterns.
    
    The collector should have methods like:
    - increment_counter(name, labels, value)
    - record_histogram(name, labels, value)
    - record_gauge(name, labels, value)
    
    Args:
        collector: Metrics collector instance (e.g., Prometheus client)
    """
    global _metrics_collector
    _metrics_collector = collector


def get_metrics_collector() -> Optional[Any]:
    """Get current metrics collector.
    
    Returns:
        Metrics collector instance or None
    """
    return _metrics_collector


class ResilienceMetrics:
    """Metrics collector for resilience patterns.
    
    Tracks:
    - Circuit breaker state transitions
    - Retry attempts and successes
    - Timeout occurrences
    - Cache hits/misses
    - Execution durations
    """
    
    def __init__(self, collector: Optional[Any] = None):
        """Initialize metrics collector.
        
        Args:
            collector: Optional external metrics collector
        """
        self._collector = collector or _metrics_collector
    
    def record_circuit_breaker_transition(
        self,
        name: str,
        from_state: str,
        to_state: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record circuit breaker state transition.
        
        Args:
            name: Circuit breaker name
            from_state: Previous state
            to_state: New state
            labels: Additional labels
        """
        if not self._collector:
            return
        
        labels = labels or {}
        labels.update({
            "circuit_breaker": name,
            "from_state": from_state,
            "to_state": to_state,
        })
        
        try:
            if hasattr(self._collector, "increment_counter"):
                self._collector.increment_counter(
                    "resilience_circuit_breaker_transitions_total",
                    labels,
                    1,
                )
        except Exception as e:
            logger.debug("Failed to record circuit breaker transition metric: %s", e)
    
    def record_retry_attempt(
        self,
        name: str,
        attempt: int,
        success: bool,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record retry attempt.
        
        Args:
            name: Retry strategy name
            attempt: Attempt number (1-based)
            success: Whether attempt succeeded
            labels: Additional labels
        """
        if not self._collector:
            return
        
        labels = labels or {}
        labels.update({
            "retry_strategy": name,
            "success": str(success).lower(),
        })
        
        try:
            if hasattr(self._collector, "increment_counter"):
                self._collector.increment_counter(
                    "resilience_retry_attempts_total",
                    labels,
                    1,
                )
        except Exception as e:
            logger.debug("Failed to record retry attempt metric: %s", e)
    
    def record_timeout(
        self,
        operation_name: str,
        timeout_seconds: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record timeout occurrence.
        
        Args:
            operation_name: Name of the operation
            timeout_seconds: Timeout value in seconds
            labels: Additional labels
        """
        if not self._collector:
            return
        
        labels = labels or {}
        labels.update({"operation": operation_name})
        
        try:
            if hasattr(self._collector, "increment_counter"):
                self._collector.increment_counter(
                    "resilience_timeouts_total",
                    labels,
                    1,
                )
            if hasattr(self._collector, "record_histogram"):
                self._collector.record_histogram(
                    "resilience_timeout_seconds",
                    labels,
                    timeout_seconds,
                )
        except Exception as e:
            logger.debug("Failed to record timeout metric: %s", e)
    
    def record_cache_operation(
        self,
        operation: str,
        hit: bool,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record cache operation.
        
        Args:
            operation: Cache operation type (get, set, delete)
            hit: Whether cache hit (for get operations)
            labels: Additional labels
        """
        if not self._collector:
            return
        
        labels = labels or {}
        labels.update({
            "operation": operation,
            "hit": str(hit).lower() if operation == "get" else "n/a",
        })
        
        try:
            if hasattr(self._collector, "increment_counter"):
                self._collector.increment_counter(
                    "resilience_cache_operations_total",
                    labels,
                    1,
                )
        except Exception as e:
            logger.debug("Failed to record cache operation metric: %s", e)
    
    def record_execution_duration(
        self,
        executor_name: str,
        duration_seconds: float,
        success: bool,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Record execution duration.
        
        Args:
            executor_name: Executor name
            duration_seconds: Execution duration in seconds
            success: Whether execution succeeded
            labels: Additional labels
        """
        if not self._collector:
            return
        
        labels = labels or {}
        labels.update({
            "executor": executor_name,
            "success": str(success).lower(),
        })
        
        try:
            if hasattr(self._collector, "record_histogram"):
                self._collector.record_histogram(
                    "resilience_execution_duration_seconds",
                    labels,
                    duration_seconds,
                )
        except Exception as e:
            logger.debug("Failed to record execution duration metric: %s", e)


# Global metrics instance
_metrics = ResilienceMetrics()


def get_metrics() -> ResilienceMetrics:
    """Get global metrics instance.
    
    Returns:
        ResilienceMetrics instance
    """
    return _metrics


def enrich_log_context(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Enrich logging context with correlation ID and other context.
    
    Args:
        extra: Additional context to add
        
    Returns:
        Enriched context dictionary
    """
    context = extra or {}
    correlation_id = get_correlation_id()
    if correlation_id:
        context["correlation_id"] = correlation_id
    return context


def trace_operation(
    operation_name: str,
    labels: Optional[Dict[str, str]] = None,
):
    """Decorator to trace an async operation.
    
    Records execution duration and success/failure metrics.
    
    Args:
        operation_name: Name of the operation
        labels: Additional labels for metrics
        
    Example:
        @trace_operation("external_api_call", {"service": "empowerid"})
        async def call_api():
            ...
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            success = False
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            finally:
                duration = time.time() - start_time
                get_metrics().record_execution_duration(
                    operation_name,
                    duration,
                    success,
                    labels,
                )
                logger.debug(
                    "Operation '%s' completed in %.3fs (success=%s)",
                    operation_name,
                    duration,
                    success,
                    extra=enrich_log_context({
                        "operation": operation_name,
                        "duration_seconds": duration,
                        "success": success,
                    }),
                )
        return wrapper
    return decorator
