"""Circuit Breaker Pattern Implementation.

The circuit breaker pattern prevents cascading failures by failing fast
when a service is known to be unavailable.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Too many failures, requests immediately rejected
- HALF_OPEN: Testing if service recovered, allowing limited requests

Usage:
    from empowernow_common.resilience import CircuitBreaker, CircuitBreakerConfig

    cb = CircuitBreaker(
        name="empowerid",
        config=CircuitBreakerConfig(threshold=5, timeout=60.0)
    )

    async def call_service():
        return await external_api()

    result = await cb.execute(call_service)
"""

import asyncio
import time
import logging
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, TypeVar

from .config import CircuitBreakerConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Rejecting requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and rejecting requests."""

    def __init__(
        self,
        message: str,
        name: str,
        state: CircuitBreakerState,
        failure_count: int,
        time_until_retry: float,
    ):
        super().__init__(message)
        self.name = name
        self.state = state
        self.failure_count = failure_count
        self.time_until_retry = time_until_retry


class CircuitBreaker:
    """Async circuit breaker with sliding window failure tracking.

    This implementation:
    - Uses a sliding time window for counting failures
    - Supports per-target isolation (each external service has its own breaker)
    - Is fully async-safe with locks
    - Provides detailed state information for monitoring
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        """Initialize circuit breaker.

        Args:
            name: Identifier for this circuit breaker (e.g., "empowerid")
            config: Configuration options (uses defaults if not provided)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()

        # State
        self._state = CircuitBreakerState.CLOSED
        self._failure_times: List[float] = []
        self._success_count = 0
        self._last_state_change = time.time()
        self._last_failure_time: Optional[float] = None

        # Async lock for thread safety
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitBreakerState:
        """Get current state (read-only)."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count within window."""
        return len(self._failure_times)

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitBreakerState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (rejecting)."""
        return self._state == CircuitBreakerState.OPEN

    async def execute(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute function through circuit breaker.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func if successful

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception from func if it fails
        """
        if not self.config.enabled:
            # SECURITY: In security mode, disabled circuit breaker is a configuration error
            # Fail-secure: raise error instead of passing through
            if self.config.security_mode:
                raise ValueError(
                    f"Circuit breaker disabled in security mode for '{self.name}'. "
                    "Security-critical operations require circuit breaker protection. "
                    "Enable circuit breaker or disable security_mode."
                )
            # Non-security mode: pass through (legacy behavior)
            return await func(*args, **kwargs)

        # Check state and potentially transition
        await self._check_state_transition()

        # If still open after transition check, reject
        if self._state == CircuitBreakerState.OPEN:
            time_in_state = time.time() - self._last_state_change
            time_until_retry = max(0, self.config.timeout - time_in_state)
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Retry in {time_until_retry:.1f}s",
                name=self.name,
                state=self._state,
                failure_count=len(self._failure_times),
                time_until_retry=time_until_retry,
            )

        # Execute the function
        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
        except Exception as e:
            await self._record_failure()
            raise

    async def _check_state_transition(self) -> None:
        """Check if state should transition (OPEN -> HALF_OPEN)."""
        async with self._lock:
            if self._state == CircuitBreakerState.OPEN:
                elapsed = time.time() - self._last_state_change
                if elapsed >= self.config.timeout:
                    self._transition_to(CircuitBreakerState.HALF_OPEN)
                    self._success_count = 0

            # Clean up old failures outside the sliding window
            if self._state == CircuitBreakerState.CLOSED:
                now = time.time()
                cutoff = now - self.config.window_seconds
                self._failure_times = [
                    ft for ft in self._failure_times if ft > cutoff
                ]

    async def _record_success(self) -> None:
        """Record a successful operation."""
        async with self._lock:
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to(CircuitBreakerState.CLOSED)
                    self._failure_times.clear()

    async def _record_failure(self) -> None:
        """Record a failed operation."""
        async with self._lock:
            now = time.time()
            self._failure_times.append(now)
            self._last_failure_time = now

            if self._state == CircuitBreakerState.HALF_OPEN:
                # Any failure in half-open immediately opens
                self._transition_to(CircuitBreakerState.OPEN)
            elif self._state == CircuitBreakerState.CLOSED:
                # Check if threshold exceeded
                # Clean old failures first
                cutoff = now - self.config.window_seconds
                self._failure_times = [
                    ft for ft in self._failure_times if ft > cutoff
                ]
                if len(self._failure_times) >= self.config.threshold:
                    self._transition_to(CircuitBreakerState.OPEN)

    def _transition_to(self, new_state: CircuitBreakerState) -> None:
        """Transition to a new state (must be called with lock held)."""
        old_state = self._state
        self._state = new_state
        self._last_state_change = time.time()
        self._success_count = 0

        # Record metrics if available
        try:
            from .observability import get_metrics
            get_metrics().record_circuit_breaker_transition(
                self.name,
                old_state.value,
                new_state.value,
            )
        except ImportError:
            pass  # Observability module not available

        logger.warning(
            "Circuit breaker [%s]: %s -> %s (failures: %d)",
            self.name,
            old_state.value.upper(),
            new_state.value.upper(),
            len(self._failure_times),
            extra={
                "component": "circuit_breaker",
                "circuit_name": self.name,
                "old_state": old_state.value,
                "new_state": new_state.value,
                "failure_count": len(self._failure_times),
            },
        )

    def get_state(self) -> Dict[str, Any]:
        """Get current state for monitoring/logging."""
        now = time.time()
        time_in_state = now - self._last_state_change

        # Calculate time until retry for OPEN state
        time_until_retry = None
        if self._state == CircuitBreakerState.OPEN:
            time_until_retry = max(0, self.config.timeout - time_in_state)

        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": len(self._failure_times),
            "threshold": self.config.threshold,
            "time_in_state_seconds": round(time_in_state, 2),
            "time_until_retry_seconds": (
                round(time_until_retry, 2) if time_until_retry is not None else None
            ),
            "last_failure_time": self._last_failure_time,
            "success_count": (
                self._success_count
                if self._state == CircuitBreakerState.HALF_OPEN
                else None
            ),
        }

    async def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        async with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._failure_times.clear()
            self._success_count = 0
            self._last_state_change = time.time()
            logger.info(
                "Circuit breaker [%s]: manually reset to CLOSED",
                self.name,
                extra={
                    "component": "circuit_breaker",
                    "circuit_name": self.name,
                },
            )


class CircuitBreakerRegistry:
    """Registry for circuit breakers (replaces global state).
    
    Provides per-target isolation - each external service gets its own
    circuit breaker instance.
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
    
    async def get(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ) -> CircuitBreaker:
        """Get or create a circuit breaker by name.
        
        Args:
            name: Unique identifier for this circuit breaker
            config: Configuration (only used if creating new breaker)
            
        Returns:
            CircuitBreaker instance
        """
        async with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
                logger.info(
                    "Created circuit breaker: %s (threshold=%d, timeout=%.1fs)",
                    name,
                    (config or CircuitBreakerConfig()).threshold,
                    (config or CircuitBreakerConfig()).timeout,
                )
            return self._breakers[name]
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get state of all registered circuit breakers (for monitoring).
        
        Returns:
            Dictionary mapping breaker names to their state
        """
        return {name: cb.get_state() for name, cb in self._breakers.items()}
    
    def clear(self) -> None:
        """Clear all circuit breakers (mainly for testing)."""
        self._breakers.clear()


# Global registry instance (singleton pattern)
_registry = CircuitBreakerRegistry()


async def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
) -> CircuitBreaker:
    """Get or create a circuit breaker by name.

    This provides per-target isolation - each external service gets its own
    circuit breaker instance.

    Args:
        name: Unique identifier for this circuit breaker
        config: Configuration (only used if creating new breaker)

    Returns:
        CircuitBreaker instance
    """
    return await _registry.get(name, config)


def get_all_circuit_breaker_states() -> Dict[str, Dict[str, Any]]:
    """Get state of all registered circuit breakers (for monitoring)."""
    return _registry.get_all_states()

