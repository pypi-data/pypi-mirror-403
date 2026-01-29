"""Lifecycle management for resilience components.

Provides graceful shutdown, resource cleanup, and health checks
for enterprise-grade reliability.
"""

import asyncio
import logging
import signal
import atexit
from typing import List, Callable, Awaitable, Optional, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Global shutdown handlers
_shutdown_handlers: List[Callable[[], Awaitable[None]]] = []
_shutdown_event: Optional[asyncio.Event] = None
_shutdown_timeout: float = 30.0  # Default shutdown timeout


def set_shutdown_timeout(timeout: float) -> None:
    """Set shutdown timeout in seconds.
    
    Args:
        timeout: Shutdown timeout in seconds
    """
    global _shutdown_timeout
    _shutdown_timeout = timeout


def register_shutdown_handler(handler: Callable[[], Awaitable[None]]) -> None:
    """Register a shutdown handler.
    
    Handlers are called in reverse order of registration during shutdown.
    
    Args:
        handler: Async function to call during shutdown
    """
    _shutdown_handlers.append(handler)
    logger.debug("Registered shutdown handler: %s", handler.__name__)


def unregister_shutdown_handler(handler: Callable[[], Awaitable[None]]) -> None:
    """Unregister a shutdown handler.
    
    Args:
        handler: Handler to remove
    """
    if handler in _shutdown_handlers:
        _shutdown_handlers.remove(handler)
        logger.debug("Unregistered shutdown handler: %s", handler.__name__)


async def graceful_shutdown(timeout: Optional[float] = None) -> None:
    """Perform graceful shutdown of all registered handlers.
    
    Args:
        timeout: Shutdown timeout (uses default if not provided)
    """
    global _shutdown_event
    
    timeout = timeout or _shutdown_timeout
    
    logger.info("Starting graceful shutdown...")
    
    # Set shutdown event
    if _shutdown_event:
        _shutdown_event.set()
    
    # Call handlers in reverse order
    for handler in reversed(_shutdown_handlers):
        try:
            logger.debug("Calling shutdown handler: %s", handler.__name__)
            await asyncio.wait_for(handler(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(
                "Shutdown handler %s timed out after %.1fs",
                handler.__name__,
                timeout,
            )
        except Exception as e:
            logger.error(
                "Error in shutdown handler %s: %s",
                handler.__name__,
                e,
                exc_info=True,
            )
    
    logger.info("Graceful shutdown completed")


def get_shutdown_event() -> asyncio.Event:
    """Get or create shutdown event.
    
    Returns:
        Shutdown event that can be checked for shutdown signal
    """
    global _shutdown_event
    if _shutdown_event is None:
        _shutdown_event = asyncio.Event()
    return _shutdown_event


def is_shutting_down() -> bool:
    """Check if shutdown has been initiated.
    
    Returns:
        True if shutdown initiated, False otherwise
    """
    if _shutdown_event is None:
        return False
    return _shutdown_event.is_set()


@asynccontextmanager
async def lifespan_context():
    """Async context manager for application lifespan.
    
    Sets up signal handlers and ensures graceful shutdown.
    
    Example:
        async with lifespan_context():
            # Application code
            await run_application()
    """
    shutdown_event = get_shutdown_event()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info("Received signal %d, initiating shutdown...", signum)
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register atexit handler for sync cleanup
    atexit.register(lambda: asyncio.run(graceful_shutdown()))
    
    try:
        yield
    finally:
        await graceful_shutdown()


class HealthCheck:
    """Health check for resilience components."""
    
    def __init__(self, name: str):
        """Initialize health check.
        
        Args:
            name: Name of the health check
        """
        self.name = name
        self._checks: List[Callable[[], Awaitable[Dict[str, Any]]]] = []
    
    def register_check(
        self,
        check: Callable[[], Awaitable[Dict[str, Any]]],
    ) -> None:
        """Register a health check function.
        
        Args:
            check: Async function returning health status dict
        """
        self._checks.append(check)
    
    async def check(self) -> Dict[str, Any]:
        """Run all health checks.
        
        Returns:
            Health status dictionary
        """
        results = {}
        overall_healthy = True
        
        for check in self._checks:
            try:
                result = await check()
                results[check.__name__] = result
                if not result.get("healthy", False):
                    overall_healthy = False
            except Exception as e:
                logger.error("Health check %s failed: %s", check.__name__, e)
                results[check.__name__] = {
                    "healthy": False,
                    "error": str(e),
                }
                overall_healthy = False
        
        return {
            "healthy": overall_healthy,
            "checks": results,
        }


# Global health check instance
_health_check = HealthCheck("resilience")


def get_health_check() -> HealthCheck:
    """Get global health check instance.
    
    Returns:
        HealthCheck instance
    """
    return _health_check
