"""Retry Strategy with Exponential Backoff.

Provides retry logic with configurable exponential backoff and jitter
for handling transient failures.

Usage:
    from empowernow_common.resilience import RetryStrategy, RetryConfig

    strategy = RetryStrategy(
        config=RetryConfig(max_retries=3, initial_delay=0.5)
    )

    async def call_service():
        return await external_api()

    result = await strategy.execute(call_service)
"""

import asyncio
import random
import time
import logging
from typing import Any, Callable, Coroutine, Optional, Set, Type, TypeVar

import httpx

from .config import RetryConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(
        self,
        message: str,
        attempts: int,
        last_exception: Exception,
        total_time: float,
    ):
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception
        self.total_time = total_time


# Default exceptions that should be retried
DEFAULT_RETRYABLE_EXCEPTIONS: Set[Type[Exception]] = {
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    ConnectionError,
    ConnectionResetError,
    asyncio.TimeoutError,
}

# Exceptions that should NOT be retried (permanent failures)
DEFAULT_NON_RETRYABLE_EXCEPTIONS: Set[Type[Exception]] = {
    httpx.HTTPStatusError,  # 4xx/5xx errors - check status code
    ValueError,
    TypeError,
    KeyError,
}


class RetryStrategy:
    """Retry strategy with exponential backoff and jitter.

    Features:
    - Configurable max retries
    - Exponential backoff with jitter
    - Configurable retryable/non-retryable exceptions
    - Detailed logging of retry attempts
    """

    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        retryable_exceptions: Optional[Set[Type[Exception]]] = None,
        non_retryable_exceptions: Optional[Set[Type[Exception]]] = None,
        name: str = "default",
    ):
        """Initialize retry strategy.

        Args:
            config: Retry configuration
            retryable_exceptions: Exceptions that should trigger retry
            non_retryable_exceptions: Exceptions that should NOT retry
            name: Identifier for logging
        """
        self.config = config or RetryConfig()
        self.name = name
        self.retryable_exceptions = (
            retryable_exceptions or DEFAULT_RETRYABLE_EXCEPTIONS
        )
        self.non_retryable_exceptions = (
            non_retryable_exceptions or DEFAULT_NON_RETRYABLE_EXCEPTIONS
        )

    def is_retryable(self, exception: Exception) -> bool:
        """Check if exception should trigger a retry.

        Args:
            exception: The exception to check

        Returns:
            True if should retry, False otherwise
        """
        # Check non-retryable first
        for exc_type in self.non_retryable_exceptions:
            if isinstance(exception, exc_type):
                # Special handling for HTTP status errors
                if isinstance(exception, httpx.HTTPStatusError):
                    # Only retry 5xx errors (server errors)
                    status = exception.response.status_code
                    return 500 <= status < 600
                return False

        # Check if explicitly retryable
        for exc_type in self.retryable_exceptions:
            if isinstance(exception, exc_type):
                return True

        # Default: don't retry unknown exceptions
        return False

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number.

        Uses exponential backoff with jitter:
        delay = min(initial_delay * (backoff_factor ** attempt), max_delay)
        delay += random_jitter

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        base_delay = min(
            self.config.initial_delay * (self.config.backoff_factor ** attempt),
            self.config.max_delay,
        )

        # Add jitter
        jitter_amount = base_delay * self.config.jitter * random.random()
        return base_delay + jitter_amount

    async def execute(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func if successful

        Raises:
            RetryExhaustedError: If all retries exhausted
            Exception: Original exception if non-retryable
        """
        if self.config.max_retries == 0:
            # No retries, just execute
            return await func(*args, **kwargs)

        start_time = time.time()
        last_exception: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                result = await func(*args, **kwargs)

                if attempt > 0:
                    # Record metrics if available
                    try:
                        from .observability import get_metrics
                        get_metrics().record_retry_attempt(
                            self.name,
                            attempt + 1,
                            True,
                        )
                    except ImportError:
                        pass  # Observability module not available
                    
                    logger.info(
                        "Retry succeeded on attempt %d/%d for %s",
                        attempt + 1,
                        self.config.max_retries + 1,
                        self.name,
                        extra={
                            "component": "retry",
                            "retry_name": self.name,
                            "attempt": attempt + 1,
                            "max_attempts": self.config.max_retries + 1,
                            "total_time_ms": round(
                                (time.time() - start_time) * 1000, 2
                            ),
                        },
                    )

                return result

            except Exception as e:
                last_exception = e

                # Check if should retry
                if not self.is_retryable(e):
                    logger.debug(
                        "Non-retryable exception for %s: %s",
                        self.name,
                        type(e).__name__,
                        extra={
                            "component": "retry",
                            "retry_name": self.name,
                            "exception_type": type(e).__name__,
                        },
                    )
                    raise

                # Check if more attempts available
                if attempt >= self.config.max_retries:
                    break

                # Calculate delay and wait
                delay = self.calculate_delay(attempt)
                
                # Record metrics if available
                try:
                    from .observability import get_metrics
                    get_metrics().record_retry_attempt(
                        self.name,
                        attempt + 1,
                        False,
                    )
                except ImportError:
                    pass  # Observability module not available
                
                logger.warning(
                    "Retry %d/%d for %s after %.2fs (error: %s)",
                    attempt + 1,
                    self.config.max_retries + 1,
                    self.name,
                    delay,
                    str(e)[:100],
                    extra={
                        "component": "retry",
                        "retry_name": self.name,
                        "attempt": attempt + 1,
                        "max_attempts": self.config.max_retries + 1,
                        "delay_seconds": delay,
                        "exception_type": type(e).__name__,
                    },
                )

                await asyncio.sleep(delay)

        # All retries exhausted
        total_time = time.time() - start_time
        logger.error(
            "All %d retries exhausted for %s after %.2fs",
            self.config.max_retries + 1,
            self.name,
            total_time,
            extra={
                "component": "retry",
                "retry_name": self.name,
                "total_attempts": self.config.max_retries + 1,
                "total_time_seconds": total_time,
                "last_exception": type(last_exception).__name__ if last_exception else None,
            },
        )

        raise RetryExhaustedError(
            f"All {self.config.max_retries + 1} retries exhausted for {self.name}",
            attempts=self.config.max_retries + 1,
            last_exception=last_exception,  # type: ignore
            total_time=total_time,
        )

