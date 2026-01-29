"""
PDP Client Metrics - Prometheus Compatible.

Production-grade metrics for the AuthZEN PDP client following the
AI_PYTHON_FASTAPI_EXCELLENCE_PLAYBOOK.md patterns.

Metrics Exported:
    - empowernow_pdp_requests_total: Counter of PDP requests by endpoint and result
    - empowernow_pdp_latency_seconds: Histogram of request latency
    - empowernow_pdp_cache_total: Counter of cache hits/misses
    - empowernow_pdp_circuit_breaker_state: Gauge of circuit breaker state
    - empowernow_pdp_inflight_requests: Gauge of concurrent requests
"""

import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import prometheus_client
try:
    from prometheus_client import Counter, Histogram, Gauge, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class PDPMetrics:
    """
    Production-grade metrics collector for PDP operations.
    
    Provides both Prometheus metrics (if available) and internal counters
    for monitoring and debugging.
    """
    
    _instance: Optional["PDPMetrics"] = None
    
    def __init__(self):
        """Initialize metrics collectors."""
        # Internal counters (always available)
        self._requests: Dict[str, int] = {}
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._latency_sum: float = 0.0
        self._latency_count: int = 0
        self._errors: int = 0
        self._circuit_trips: int = 0
        self._rate_limit_hits: int = 0
        
        # Prometheus metrics (if available)
        if PROMETHEUS_AVAILABLE:
            self._init_prometheus_metrics()
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics collectors."""
        # Check if metrics already registered (avoid duplicate registration)
        try:
            self.requests_total = Counter(
                "empowernow_pdp_requests_total",
                "Total PDP requests",
                ["endpoint", "result", "cached"]
            )
        except ValueError:
            self.requests_total = REGISTRY._names_to_collectors.get(
                "empowernow_pdp_requests_total"
            )
        
        try:
            self.latency_seconds = Histogram(
                "empowernow_pdp_latency_seconds",
                "PDP request latency in seconds",
                ["endpoint"],
                buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
            )
        except ValueError:
            self.latency_seconds = REGISTRY._names_to_collectors.get(
                "empowernow_pdp_latency_seconds"
            )
        
        try:
            self.cache_total = Counter(
                "empowernow_pdp_cache_total",
                "PDP cache operations",
                ["operation"]  # hit, miss, set
            )
        except ValueError:
            self.cache_total = REGISTRY._names_to_collectors.get(
                "empowernow_pdp_cache_total"
            )
        
        try:
            self.circuit_breaker_state = Gauge(
                "empowernow_pdp_circuit_breaker_state",
                "Circuit breaker state (0=closed, 1=open, 2=half-open)",
                ["name"]
            )
        except ValueError:
            self.circuit_breaker_state = REGISTRY._names_to_collectors.get(
                "empowernow_pdp_circuit_breaker_state"
            )
        
        try:
            self.inflight_requests = Gauge(
                "empowernow_pdp_inflight_requests",
                "Number of concurrent PDP requests"
            )
        except ValueError:
            self.inflight_requests = REGISTRY._names_to_collectors.get(
                "empowernow_pdp_inflight_requests"
            )
        
        try:
            self.circuit_trips_total = Counter(
                "empowernow_pdp_circuit_breaker_trips_total",
                "Total circuit breaker trips"
            )
        except ValueError:
            self.circuit_trips_total = REGISTRY._names_to_collectors.get(
                "empowernow_pdp_circuit_breaker_trips_total"
            )
        
        try:
            self.rate_limit_total = Counter(
                "empowernow_pdp_rate_limit_total",
                "Total rate limit rejections"
            )
        except ValueError:
            self.rate_limit_total = REGISTRY._names_to_collectors.get(
                "empowernow_pdp_rate_limit_total"
            )
        
        try:
            self.cache_size = Gauge(
                "empowernow_pdp_cache_size",
                "Current number of entries in the cache"
            )
        except ValueError:
            self.cache_size = REGISTRY._names_to_collectors.get(
                "empowernow_pdp_cache_size"
            )
        
        try:
            self.token_expiry_seconds = Gauge(
                "empowernow_pdp_token_expiry_seconds",
                "Seconds until OAuth token expires"
            )
        except ValueError:
            self.token_expiry_seconds = REGISTRY._names_to_collectors.get(
                "empowernow_pdp_token_expiry_seconds"
            )
    
    def record_request(
        self,
        endpoint: str,
        success: bool,
        cached: bool = False,
        latency_seconds: Optional[float] = None,
    ) -> None:
        """
        Record a PDP request.
        
        Args:
            endpoint: API endpoint called
            success: Whether request succeeded
            cached: Whether result was from cache
            latency_seconds: Request latency in seconds
        """
        result = "success" if success else "error"
        key = f"{endpoint}:{result}:{cached}"
        self._requests[key] = self._requests.get(key, 0) + 1
        
        if not success:
            self._errors += 1
        
        if latency_seconds is not None:
            self._latency_sum += latency_seconds
            self._latency_count += 1
        
        if PROMETHEUS_AVAILABLE and hasattr(self, 'requests_total'):
            self.requests_total.labels(
                endpoint=endpoint,
                result=result,
                cached=str(cached).lower()
            ).inc()
            
            if latency_seconds is not None and hasattr(self, 'latency_seconds'):
                self.latency_seconds.labels(endpoint=endpoint).observe(latency_seconds)
    
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self._cache_hits += 1
        if PROMETHEUS_AVAILABLE and hasattr(self, 'cache_total'):
            self.cache_total.labels(operation="hit").inc()
    
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self._cache_misses += 1
        if PROMETHEUS_AVAILABLE and hasattr(self, 'cache_total'):
            self.cache_total.labels(operation="miss").inc()
    
    def record_cache_set(self) -> None:
        """Record a cache set operation."""
        if PROMETHEUS_AVAILABLE and hasattr(self, 'cache_total'):
            self.cache_total.labels(operation="set").inc()
    
    def record_circuit_state(self, name: str, state: str) -> None:
        """
        Record circuit breaker state change.
        
        Args:
            name: Circuit breaker name
            state: State (closed, open, half_open)
        """
        state_map = {"closed": 0, "open": 1, "half_open": 2}
        state_value = state_map.get(state, 0)
        
        if state == "open":
            self._circuit_trips += 1
            if PROMETHEUS_AVAILABLE and hasattr(self, 'circuit_trips_total'):
                self.circuit_trips_total.inc()
        
        if PROMETHEUS_AVAILABLE and hasattr(self, 'circuit_breaker_state'):
            self.circuit_breaker_state.labels(name=name).set(state_value)
    
    def record_inflight_change(self, delta: int) -> None:
        """
        Record change in inflight requests.
        
        Args:
            delta: Change amount (+1 for start, -1 for end)
        """
        if PROMETHEUS_AVAILABLE and hasattr(self, 'inflight_requests'):
            if delta > 0:
                self.inflight_requests.inc(delta)
            else:
                self.inflight_requests.dec(abs(delta))
    
    def record_rate_limit_hit(self) -> None:
        """Record a rate limit rejection."""
        self._rate_limit_hits += 1
        if PROMETHEUS_AVAILABLE and hasattr(self, 'rate_limit_total'):
            self.rate_limit_total.inc()
    
    def record_cache_size(self, size: int) -> None:
        """Record the current cache size."""
        if PROMETHEUS_AVAILABLE and hasattr(self, 'cache_size'):
            self.cache_size.set(size)
    
    def record_token_expiry(self, seconds_until_expiry: float) -> None:
        """Record time until token expires."""
        if PROMETHEUS_AVAILABLE and hasattr(self, 'token_expiry_seconds'):
            self.token_expiry_seconds.set(max(0, seconds_until_expiry))
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current metrics as a dictionary.
        
        Returns:
            Dictionary of metric values
        """
        total_cache = self._cache_hits + self._cache_misses
        cache_hit_rate = (
            self._cache_hits / total_cache * 100 if total_cache > 0 else 0
        )
        avg_latency = (
            self._latency_sum / self._latency_count * 1000
            if self._latency_count > 0
            else 0
        )
        
        return {
            "requests": self._requests,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "total_latency_count": self._latency_count,
            "errors": self._errors,
            "circuit_trips": self._circuit_trips,
            "rate_limit_hits": self._rate_limit_hits,
            "prometheus_available": PROMETHEUS_AVAILABLE,
        }
    
    def reset(self) -> None:
        """Reset all internal counters (for testing)."""
        self._requests.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        self._latency_sum = 0.0
        self._latency_count = 0
        self._errors = 0
        self._circuit_trips = 0
        self._rate_limit_hits = 0


# Global metrics instance
_pdp_metrics: Optional[PDPMetrics] = None


def get_pdp_metrics() -> PDPMetrics:
    """Get the global PDP metrics collector."""
    global _pdp_metrics
    if _pdp_metrics is None:
        _pdp_metrics = PDPMetrics()
    return _pdp_metrics


def reset_pdp_metrics() -> None:
    """Reset the global PDP metrics collector (for testing)."""
    global _pdp_metrics
    if _pdp_metrics is not None:
        _pdp_metrics.reset()


class LatencyTimer:
    """
    Context manager for timing operations.
    
    Example:
        with LatencyTimer() as timer:
            await make_request()
        print(f"Took {timer.elapsed_seconds}s")
    """
    
    def __init__(self):
        self.start_time: float = 0
        self.end_time: float = 0
    
    def __enter__(self) -> "LatencyTimer":
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args) -> None:
        self.end_time = time.perf_counter()
    
    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        if self.end_time == 0:
            return time.perf_counter() - self.start_time
        return self.end_time - self.start_time
    
    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return self.elapsed_seconds * 1000
