"""OAuth client Prometheus metrics.

This module provides production-grade observability for OAuth operations.
Metrics are exported via prometheus_client and can be scraped by Prometheus.

All metrics use the `empowernow_oauth_` prefix and follow Prometheus naming conventions.

Usage:
    from empowernow_common.oauth.metrics import (
        track_token_request,
        record_cache_hit,
        record_cache_miss,
    )
    
    # Use context manager for automatic duration tracking
    with track_token_request("client_credentials", "my-app"):
        token = await oauth._do_token_request()
"""

from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Try to import prometheus_client - gracefully degrade if not available
try:
    from prometheus_client import Counter, Histogram, Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.debug("prometheus_client not installed - metrics disabled")


# Metrics definitions (only created if prometheus_client is available)
if PROMETHEUS_AVAILABLE:
    # Token acquisition metrics
    OAUTH_TOKEN_REQUESTS = Counter(
        "empowernow_oauth_token_requests_total",
        "Total OAuth token requests",
        ["grant_type", "status", "client_id"]
    )

    OAUTH_TOKEN_LATENCY = Histogram(
        "empowernow_oauth_token_latency_seconds",
        "OAuth token request latency in seconds",
        ["grant_type", "client_id"],
        buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    )

    OAUTH_TOKEN_CACHE_HITS = Counter(
        "empowernow_oauth_token_cache_hits_total",
        "OAuth token cache hits",
        ["client_id"]
    )

    OAUTH_TOKEN_CACHE_MISSES = Counter(
        "empowernow_oauth_token_cache_misses_total",
        "OAuth token cache misses",
        ["client_id"]
    )

    OAUTH_TOKEN_CACHE_OPERATIONS = Counter(
        "empowernow_oauth_token_cache_operations_total",
        "OAuth token cache operations",
        ["client_id", "operation"]  # operation: hit, miss, clear, refresh
    )

    OAUTH_TOKEN_EXPIRY = Gauge(
        "empowernow_oauth_token_expiry_seconds",
        "OAuth token expiry timestamp",
        ["client_id"]
    )

    OAUTH_DPOP_NONCE_CHALLENGES = Counter(
        "empowernow_oauth_dpop_nonce_challenges_total",
        "DPoP nonce challenges received",
        ["client_id"]
    )

    OAUTH_CIRCUIT_BREAKER_STATE = Gauge(
        "empowernow_oauth_circuit_breaker_state",
        "OAuth circuit breaker state (0=closed, 1=half-open, 2=open)",
        ["client_id"]
    )

    OAUTH_CIRCUIT_BREAKER_TRIPS = Counter(
        "empowernow_oauth_circuit_breaker_trips_total",
        "Total times OAuth circuit breaker has tripped",
        ["client_id"]
    )

    OAUTH_HTTP_REQUESTS = Counter(
        "empowernow_oauth_http_requests_total",
        "Total HTTP requests to OAuth endpoints",
        ["client_id", "endpoint_type", "status_code"]
    )

    OAUTH_RETRY_ATTEMPTS = Counter(
        "empowernow_oauth_retry_attempts_total",
        "OAuth request retry attempts",
        ["client_id", "grant_type", "reason"]
    )


def _truncate_client_id(client_id: str, max_len: int = 16) -> str:
    """Truncate client ID to prevent cardinality explosion."""
    return client_id[:max_len] if client_id else "unknown"


@contextmanager
def track_token_request(
    grant_type: str,
    client_id: str,
) -> Generator[None, None, None]:
    """Context manager to track token request metrics.
    
    Automatically records duration and status (success/error).
    
    Args:
        grant_type: OAuth grant type (client_credentials, authorization_code, etc.)
        client_id: OAuth client ID
    
    Example:
        with track_token_request("client_credentials", "my-app"):
            token = await oauth._do_token_request()
    """
    if not PROMETHEUS_AVAILABLE:
        yield
        return
    
    start = time.perf_counter()
    status = "success"
    truncated_id = _truncate_client_id(client_id)
    
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        duration = time.perf_counter() - start
        OAUTH_TOKEN_REQUESTS.labels(
            grant_type=grant_type,
            status=status,
            client_id=truncated_id,
        ).inc()
        OAUTH_TOKEN_LATENCY.labels(
            grant_type=grant_type,
            client_id=truncated_id,
        ).observe(duration)


def record_token_request(
    client_id: str,
    grant_type: str,
    status: str,
    duration_seconds: float,
) -> None:
    """Record a token request metric.
    
    Args:
        client_id: OAuth client ID
        grant_type: Grant type used (client_credentials, authorization_code, etc.)
        status: Request result (success, error, timeout, circuit_open)
        duration_seconds: Request duration in seconds
    """
    if not PROMETHEUS_AVAILABLE:
        return
    
    truncated_id = _truncate_client_id(client_id)
    
    OAUTH_TOKEN_REQUESTS.labels(
        grant_type=grant_type,
        status=status,
        client_id=truncated_id,
    ).inc()
    
    OAUTH_TOKEN_LATENCY.labels(
        grant_type=grant_type,
        client_id=truncated_id,
    ).observe(duration_seconds)


def record_cache_hit(client_id: str) -> None:
    """Record a token cache hit."""
    if not PROMETHEUS_AVAILABLE:
        return
    
    truncated_id = _truncate_client_id(client_id)
    OAUTH_TOKEN_CACHE_HITS.labels(client_id=truncated_id).inc()
    OAUTH_TOKEN_CACHE_OPERATIONS.labels(
        client_id=truncated_id,
        operation="hit",
    ).inc()


def record_cache_miss(client_id: str) -> None:
    """Record a token cache miss."""
    if not PROMETHEUS_AVAILABLE:
        return
    
    truncated_id = _truncate_client_id(client_id)
    OAUTH_TOKEN_CACHE_MISSES.labels(client_id=truncated_id).inc()
    OAUTH_TOKEN_CACHE_OPERATIONS.labels(
        client_id=truncated_id,
        operation="miss",
    ).inc()


def record_cache_clear(client_id: str) -> None:
    """Record a token cache clear."""
    if not PROMETHEUS_AVAILABLE:
        return
    OAUTH_TOKEN_CACHE_OPERATIONS.labels(
        client_id=_truncate_client_id(client_id),
        operation="clear",
    ).inc()


def record_cache_refresh(client_id: str) -> None:
    """Record a proactive token cache refresh."""
    if not PROMETHEUS_AVAILABLE:
        return
    OAUTH_TOKEN_CACHE_OPERATIONS.labels(
        client_id=_truncate_client_id(client_id),
        operation="refresh",
    ).inc()


def set_token_expiry(client_id: str, expiry_timestamp: float) -> None:
    """Set token expiry timestamp gauge."""
    if not PROMETHEUS_AVAILABLE:
        return
    OAUTH_TOKEN_EXPIRY.labels(
        client_id=_truncate_client_id(client_id)
    ).set(expiry_timestamp)


def record_dpop_nonce_challenge(client_id: str) -> None:
    """Record a DPoP nonce challenge."""
    if not PROMETHEUS_AVAILABLE:
        return
    OAUTH_DPOP_NONCE_CHALLENGES.labels(
        client_id=_truncate_client_id(client_id)
    ).inc()


def set_circuit_breaker_state(client_id: str, state: int) -> None:
    """Set circuit breaker state gauge.
    
    Args:
        client_id: OAuth client ID
        state: 0=closed, 1=half-open, 2=open
    """
    if not PROMETHEUS_AVAILABLE:
        return
    OAUTH_CIRCUIT_BREAKER_STATE.labels(
        client_id=_truncate_client_id(client_id)
    ).set(state)


def record_circuit_breaker_trip(client_id: str) -> None:
    """Record a circuit breaker trip."""
    if not PROMETHEUS_AVAILABLE:
        return
    OAUTH_CIRCUIT_BREAKER_TRIPS.labels(
        client_id=_truncate_client_id(client_id)
    ).inc()


def record_http_request(
    client_id: str,
    endpoint_type: str,
    status_code: int,
) -> None:
    """Record an HTTP request to an OAuth endpoint.
    
    Args:
        client_id: OAuth client ID
        endpoint_type: Type of endpoint (token, introspect, revoke, par, ciba)
        status_code: HTTP response status code
    """
    if not PROMETHEUS_AVAILABLE:
        return
    OAUTH_HTTP_REQUESTS.labels(
        client_id=_truncate_client_id(client_id),
        endpoint_type=endpoint_type,
        status_code=str(status_code),
    ).inc()


def record_retry_attempt(
    client_id: str,
    grant_type: str,
    reason: str,
) -> None:
    """Record a retry attempt.
    
    Args:
        client_id: OAuth client ID
        grant_type: Grant type being requested
        reason: Reason for retry (rate_limit, server_error, dpop_nonce, etc.)
    """
    if not PROMETHEUS_AVAILABLE:
        return
    OAUTH_RETRY_ATTEMPTS.labels(
        client_id=_truncate_client_id(client_id),
        grant_type=grant_type,
        reason=reason,
    ).inc()


def is_metrics_available() -> bool:
    """Check if Prometheus metrics are available."""
    return PROMETHEUS_AVAILABLE
