"""Timeout Wrapper for Async Operations.

Provides configurable timeout handling for async operations.

Usage:
    from empowernow_common.resilience import timeout_wrapper

    async def slow_operation():
        await asyncio.sleep(60)

    # Wrap with 5 second timeout
    result = await timeout_wrapper(slow_operation(), timeout=5.0)
"""

import asyncio
import logging
from typing import Any, Coroutine, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ResilienceTimeoutError(asyncio.TimeoutError):
    """Extended timeout error with additional context."""

    def __init__(
        self,
        message: str,
        timeout: float,
        operation_name: str = "operation",
    ):
        super().__init__(message)
        self.timeout = timeout
        self.operation_name = operation_name


async def timeout_wrapper(
    coro: Coroutine[Any, Any, T],
    timeout: float,
    operation_name: str = "operation",
) -> T:
    """Wrap an async operation with a timeout.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        operation_name: Name for logging/error messages

    Returns:
        Result of the coroutine

    Raises:
        ResilienceTimeoutError: If operation times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        # Record metrics if available
        try:
            from .observability import get_metrics
            get_metrics().record_timeout(operation_name, timeout)
        except ImportError:
            pass  # Observability module not available
        
        logger.warning(
            "Timeout after %.1fs for %s",
            timeout,
            operation_name,
            extra={
                "component": "timeout",
                "operation_name": operation_name,
                "timeout_seconds": timeout,
            },
        )
        raise ResilienceTimeoutError(
            f"{operation_name} timed out after {timeout}s",
            timeout=timeout,
            operation_name=operation_name,
        )

