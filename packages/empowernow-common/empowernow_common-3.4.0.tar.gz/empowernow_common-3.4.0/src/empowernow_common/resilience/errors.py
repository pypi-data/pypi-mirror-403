"""Enhanced error handling for resilience patterns.

Provides error classification, context enrichment, and structured error information
for better observability and debugging.
"""

from typing import Any, Dict, Optional, List
from enum import Enum
import traceback


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    
    NETWORK = "network"  # Network/connection errors
    TIMEOUT = "timeout"  # Timeout errors
    CIRCUIT_BREAKER = "circuit_breaker"  # Circuit breaker open
    RETRY_EXHAUSTED = "retry_exhausted"  # All retries failed
    CONFIGURATION = "configuration"  # Configuration errors
    CACHE = "cache"  # Cache errors
    VALIDATION = "validation"  # Input validation errors
    UNKNOWN = "unknown"  # Unknown/unclassified errors


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    
    LOW = "low"  # Non-critical, recoverable
    MEDIUM = "medium"  # May impact functionality
    HIGH = "high"  # Significant impact
    CRITICAL = "critical"  # System failure


class ResilienceError(Exception):
    """Base exception for resilience patterns with enhanced context.
    
    Provides:
    - Error categorization
    - Severity classification
    - Rich context information
    - Correlation ID support
    """
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """Initialize resilience error.
        
        Args:
            message: Error message
            category: Error category
            severity: Error severity
            context: Additional context information
            cause: Underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.cause = cause
        self.timestamp = None
        
        # Capture traceback if cause provided
        if cause:
            self.context["cause_type"] = type(cause).__name__
            self.context["cause_message"] = str(cause)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization.
        
        Returns:
            Dictionary representation of error
        """
        result = {
            "error_type": type(self).__name__,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "context": self.context,
        }
        
        if self.cause:
            result["cause"] = {
                "type": type(self.cause).__name__,
                "message": str(self.cause),
            }
        
        return result
    
    def __str__(self) -> str:
        """String representation."""
        parts = [f"[{self.category.value}] {self.message}"]
        if self.context:
            parts.append(f"Context: {self.context}")
        if self.cause:
            parts.append(f"Caused by: {type(self.cause).__name__}: {self.cause}")
        return " | ".join(parts)


class CircuitBreakerError(ResilienceError):
    """Error raised when circuit breaker is open."""
    
    def __init__(
        self,
        circuit_name: str,
        state: str,
        time_until_retry: float,
        failure_count: int,
        **kwargs: Any,
    ):
        """Initialize circuit breaker error.
        
        Args:
            circuit_name: Name of the circuit breaker
            state: Current state
            time_until_retry: Seconds until retry allowed
            failure_count: Number of failures
            **kwargs: Additional arguments for ResilienceError
        """
        message = (
            f"Circuit breaker '{circuit_name}' is {state.upper()}. "
            f"Retry in {time_until_retry:.1f}s"
        )
        context = kwargs.pop("context", {})
        context.update({
            "circuit_name": circuit_name,
            "state": state,
            "time_until_retry": time_until_retry,
            "failure_count": failure_count,
        })
        super().__init__(
            message,
            category=ErrorCategory.CIRCUIT_BREAKER,
            severity=ErrorSeverity.HIGH,
            context=context,
            **kwargs,
        )


class RetryExhaustedError(ResilienceError):
    """Error raised when all retry attempts are exhausted."""
    
    def __init__(
        self,
        operation_name: str,
        attempts: int,
        total_time: float,
        last_exception: Exception,
        **kwargs: Any,
    ):
        """Initialize retry exhausted error.
        
        Args:
            operation_name: Name of the operation
            attempts: Number of attempts made
            total_time: Total time spent retrying
            last_exception: Last exception encountered
            **kwargs: Additional arguments for ResilienceError
        """
        message = (
            f"All {attempts} retry attempts exhausted for '{operation_name}' "
            f"after {total_time:.2f}s"
        )
        context = kwargs.pop("context", {})
        context.update({
            "operation_name": operation_name,
            "attempts": attempts,
            "total_time": total_time,
            "last_exception_type": type(last_exception).__name__,
        })
        super().__init__(
            message,
            category=ErrorCategory.RETRY_EXHAUSTED,
            severity=ErrorSeverity.HIGH,
            context=context,
            cause=last_exception,
            **kwargs,
        )


class TimeoutError(ResilienceError):
    """Error raised when operation times out."""
    
    def __init__(
        self,
        operation_name: str,
        timeout_seconds: float,
        **kwargs: Any,
    ):
        """Initialize timeout error.
        
        Args:
            operation_name: Name of the operation
            timeout_seconds: Timeout value in seconds
            **kwargs: Additional arguments for ResilienceError
        """
        message = f"Operation '{operation_name}' timed out after {timeout_seconds}s"
        context = kwargs.pop("context", {})
        context.update({
            "operation_name": operation_name,
            "timeout_seconds": timeout_seconds,
        })
        super().__init__(
            message,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            **kwargs,
        )


def classify_error(exception: Exception) -> ErrorCategory:
    """Classify an exception into an error category.
    
    Args:
        exception: Exception to classify
        
    Returns:
        Error category
    """
    error_type = type(exception).__name__
    error_message = str(exception).lower()
    
    # Network errors
    if any(keyword in error_message for keyword in ["connection", "network", "dns", "socket"]):
        return ErrorCategory.NETWORK
    
    # Timeout errors
    if "timeout" in error_message or "timed out" in error_message:
        return ErrorCategory.TIMEOUT
    
    # Circuit breaker errors
    if "circuit breaker" in error_message or isinstance(exception, CircuitBreakerError):
        return ErrorCategory.CIRCUIT_BREAKER
    
    # Retry exhausted
    if "retry" in error_message and "exhausted" in error_message:
        return ErrorCategory.RETRY_EXHAUSTED
    
    # Configuration errors
    if any(keyword in error_message for keyword in ["config", "configuration", "invalid"]):
        return ErrorCategory.CONFIGURATION
    
    # Validation errors
    if any(keyword in error_message for keyword in ["validation", "invalid", "malformed"]):
        return ErrorCategory.VALIDATION
    
    return ErrorCategory.UNKNOWN


def enrich_error_context(
    error: Exception,
    operation_name: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Enrich error with additional context.
    
    Args:
        error: Exception to enrich
        operation_name: Name of the operation that failed
        additional_context: Additional context to add
        
    Returns:
        Enriched context dictionary
    """
    from .observability import get_correlation_id
    
    context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "error_category": classify_error(error).value,
    }
    
    if operation_name:
        context["operation_name"] = operation_name
    
    correlation_id = get_correlation_id()
    if correlation_id:
        context["correlation_id"] = correlation_id
    
    if additional_context:
        context.update(additional_context)
    
    return context
