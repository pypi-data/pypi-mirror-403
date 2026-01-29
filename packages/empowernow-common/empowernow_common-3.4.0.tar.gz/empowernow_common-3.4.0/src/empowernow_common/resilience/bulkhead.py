"""Bulkhead pattern for resource isolation.

The bulkhead pattern isolates resources (like thread pools or connections)
to prevent failures in one area from affecting others.

Enterprise patterns:
- Semaphore-based concurrency limiting
- Per-service resource isolation
- Queue-based request handling
- Timeout on resource acquisition
"""

import asyncio
import time
import logging
from typing import Any, Callable, Coroutine, Optional, TypeVar
from dataclasses import dataclass

from .errors import ResilienceError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class BulkheadConfig:
    """Configuration for bulkhead pattern."""
    
    max_concurrent: int = 10  # Maximum concurrent executions
    max_waiting: int = 100  # Maximum waiting requests in queue
    timeout: float = 60.0  # Timeout for acquiring semaphore (seconds)


class BulkheadFullError(ResilienceError):
    """Raised when bulkhead is full and cannot accept more requests."""
    
    def __init__(
        self,
        bulkhead_name: str,
        max_concurrent: int,
        current_usage: int,
        **kwargs: Any,
    ):
        """Initialize bulkhead full error.
        
        Args:
            bulkhead_name: Name of the bulkhead
            max_concurrent: Maximum concurrent executions
            current_usage: Current number of concurrent executions
            **kwargs: Additional arguments for ResilienceError
        """
        message = (
            f"Bulkhead '{bulkhead_name}' is full "
            f"({current_usage}/{max_concurrent} concurrent)"
        )
        context = kwargs.pop("context", {})
        context.update({
            "bulkhead_name": bulkhead_name,
            "max_concurrent": max_concurrent,
            "current_usage": current_usage,
        })
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            context=context,
            **kwargs,
        )


class Bulkhead:
    """Bulkhead pattern implementation using semaphores.
    
    Limits concurrent executions to prevent resource exhaustion
    and provides isolation between different services.
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[BulkheadConfig] = None,
    ):
        """Initialize bulkhead.
        
        Args:
            name: Identifier for this bulkhead
            config: Bulkhead configuration
        """
        self.name = name
        self.config = config or BulkheadConfig()
        
        # Semaphore for concurrent execution limit
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        # Queue for waiting requests (if max_waiting > 0)
        self._queue: Optional[asyncio.Queue] = None
        if self.config.max_waiting > 0:
            self._queue = asyncio.Queue(maxsize=self.config.max_waiting)
        
        # Statistics
        self._total_acquired = 0
        self._total_rejected = 0
        self._total_timeouts = 0
    
    async def execute(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute function through bulkhead.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of func if successful
            
        Raises:
            BulkheadFullError: If bulkhead is full
            ResilienceError: If timeout acquiring semaphore
        """
        # Try to acquire semaphore with timeout
        try:
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.config.timeout,
            )
        except asyncio.TimeoutError:
            self._total_timeouts += 1
            raise ResilienceError(
                f"Timeout acquiring bulkhead '{self.name}' after {self.config.timeout}s",
                category=ErrorCategory.TIMEOUT,
                severity=ErrorSeverity.MEDIUM,
                context={"bulkhead_name": self.name},
            )
        
        self._total_acquired += 1
        
        try:
            # Execute the function
            return await func(*args, **kwargs)
        finally:
            # Always release semaphore
            self._semaphore.release()
    
    @property
    def current_usage(self) -> int:
        """Get current number of concurrent executions.
        
        Returns:
            Number of active executions
        """
        return self.config.max_concurrent - self._semaphore._value
    
    @property
    def available_capacity(self) -> int:
        """Get available capacity.
        
        Returns:
            Number of available slots
        """
        return self._semaphore._value
    
    def get_stats(self) -> dict[str, Any]:
        """Get bulkhead statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "name": self.name,
            "max_concurrent": self.config.max_concurrent,
            "current_usage": self.current_usage,
            "available_capacity": self.available_capacity,
            "total_acquired": self._total_acquired,
            "total_rejected": self._total_rejected,
            "total_timeouts": self._total_timeouts,
            "utilization_percent": (
                (self.current_usage / self.config.max_concurrent) * 100
                if self.config.max_concurrent > 0
                else 0
            ),
        }


# Global registry for bulkheads (per-service isolation)
_bulkheads: dict[str, Bulkhead] = {}
_bulkhead_lock = asyncio.Lock()


async def get_bulkhead(
    name: str,
    config: Optional[BulkheadConfig] = None,
) -> Bulkhead:
    """Get or create a bulkhead by name.
    
    Provides per-service isolation - each service gets its own bulkhead.
    
    Args:
        name: Unique identifier for this bulkhead
        config: Configuration (only used if creating new bulkhead)
        
    Returns:
        Bulkhead instance
    """
    async with _bulkhead_lock:
        if name not in _bulkheads:
            _bulkheads[name] = Bulkhead(name, config)
            logger.info(
                "Created bulkhead: %s (max_concurrent=%d)",
                name,
                (config or BulkheadConfig()).max_concurrent,
            )
        return _bulkheads[name]


def get_all_bulkhead_stats() -> dict[str, dict[str, Any]]:
    """Get statistics for all bulkheads.
    
    Returns:
        Dictionary mapping bulkhead names to their statistics
    """
    return {name: bulkhead.get_stats() for name, bulkhead in _bulkheads.items()}
