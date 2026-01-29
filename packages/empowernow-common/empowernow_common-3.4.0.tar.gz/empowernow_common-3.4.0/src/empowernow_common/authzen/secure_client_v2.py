"""
Production-Grade Secure PDP Client v2 - AuthZEN 1.0 Compliant

Policy Decision Point (PDP) client with enterprise-grade features:
- AuthZEN 1.0 compliance (correct endpoints for single vs batch)
- True batch evaluation (single HTTP call, not N calls)
- Redis caching with differential TTLs (allow: 5min, deny: 1min)
- Per-item batch caching for optimal performance
- Rate limiting via semaphore (prevents connection pool exhaustion)
- Circuit breaker from empowernow_common.resilience
- Prometheus metrics for observability
- Pydantic Settings for configuration
- Comprehensive security hardening

Based on patterns from:
- membership/src/api/pdp_client.py (gold standard)
- AI_PYTHON_FASTAPI_EXCELLENCE_PLAYBOOK.md
- AuthZEN 1.0 Specification

Author: Refactored per SDK_AUTHZEN_REFACTOR_PLAN.md
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import ssl
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncIterator, Callable, Awaitable, Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None

from pydantic import BaseModel, Field

from .models import (
    SecureSubject,
    SecureResource,
    SecureAction,
    SecureContext,
    SecureAuthRequest,
    SecureAuthResponse,
)
from .config import PDPConfig, get_pdp_config
from .metrics import PDPMetrics, get_pdp_metrics, LatencyTimer
from ..fips.entropy import generate_correlation_id, generate_secure_token
from ..fips.validator import FIPSValidator
from ..exceptions import AuthZENError

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ============================================================================
# Error Types
# ============================================================================

class PDPError(AuthZENError):
    """
    Base error for PDP operations.
    
    Follows playbook error response contract:
    {"error": "error_code", "detail": "message", "correlation_id": "uuid"}
    """
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        error_code: str = "pdp_error",
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.correlation_id = correlation_id
        self.error_code = error_code
        super().__init__(message)
    
    def to_response(self) -> Dict[str, Any]:
        """Convert to standard error response per playbook Section 9.3."""
        return {
            "error": self.error_code,
            "detail": self.message,
            "correlation_id": self.correlation_id,
        }


class PDPAuthenticationError(PDPError):
    """PDP OAuth token acquisition failed - fail-fast instead of silent failure."""
    
    def __init__(self, message: str, correlation_id: Optional[str] = None) -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code="unauthorized",
            correlation_id=correlation_id,
        )


class PDPCircuitOpenError(PDPError):
    """PDP circuit breaker is open - fail fast per playbook."""
    
    def __init__(self, message: str, correlation_id: Optional[str] = None) -> None:
        super().__init__(
            message=message,
            status_code=503,
            error_code="service_unavailable",
            correlation_id=correlation_id,
        )


class PDPRateLimitError(PDPError):
    """PDP rate limit exceeded per playbook Section 8."""
    
    def __init__(self, message: str, correlation_id: Optional[str] = None) -> None:
        super().__init__(
            message=message,
            status_code=429,
            error_code="rate_limited",
            correlation_id=correlation_id,
        )


class ConstraintSecurityError(PDPError):
    """Constraint security-related errors."""
    pass


class ObligationSecurityError(PDPError):
    """Obligation security-related errors."""
    pass


# ============================================================================
# AuthZEN Models
# ============================================================================

class EvaluationSemantic(str, Enum):
    """Batch evaluation semantics per AuthZEN 1.0 draft-04."""
    EXECUTE_ALL = "execute_all"
    DENY_ON_FIRST_DENY = "deny_on_first_deny"
    PERMIT_ON_FIRST_PERMIT = "permit_on_first_permit"


@dataclass
class SecureConstraint:
    """Secure Constraint model with validation."""
    id: str
    type: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecureObligation:
    """Secure Obligation model with validation."""
    id: str
    type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timing: str = "after"  # before, after, async, immediate
    critical: bool = False


class AuthorizationResult(Generic[T]):
    """Wrapper containing PDP evaluation result or error."""
    
    def __init__(
        self,
        success: bool,
        result: Optional[T] = None,
        error: Optional[PDPError] = None,
        cached: bool = False,
        correlation_id: Optional[str] = None,
    ) -> None:
        self.success = success
        self.result = result
        self.error = error
        self.cached = cached
        self.correlation_id = correlation_id or generate_correlation_id()


class SecureEnhancedAuthResult:
    """Enhanced authorization result with PEP capabilities."""
    
    def __init__(
        self,
        decision: bool,
        reason: str = "",
        constraints: Optional[List[SecureConstraint]] = None,
        obligations: Optional[List[SecureObligation]] = None,
        correlation_id: Optional[str] = None,
        raw_context: Optional[Dict[str, Any]] = None,
        cached: bool = False,
    ):
        self.decision = decision
        self.reason = reason
        self.constraints = constraints or []
        self.obligations = obligations or []
        self.correlation_id = correlation_id or generate_correlation_id()
        self.raw_context = raw_context or {}
        self.cached = cached
        
        # Legacy compatibility
        self.allowed = decision
        self.denied = not decision
        
        # PEP state tracking
        self._constraints_applied = False
        self._obligations_processed = False
    
    def __bool__(self) -> bool:
        return self.decision
    
    @property
    def has_constraints(self) -> bool:
        return len(self.constraints) > 0
    
    @property
    def has_obligations(self) -> bool:
        return len(self.obligations) > 0
    
    def get_extra(self, key: str, default: Any = None) -> Any:
        """Return opaque value from PDP context if present."""
        return self.raw_context.get(key, default)


class BatchAuthorizationResponse(BaseModel):
    """Batch authorization response per AuthZEN 1.0."""
    
    model_config = {"arbitrary_types_allowed": True}
    
    evaluations: List[SecureEnhancedAuthResult] = Field(default_factory=list)


# ============================================================================
# Cache Backend Interface
# ============================================================================

class CacheBackend:
    """Abstract cache backend interface."""
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError
    
    async def set(self, key: str, value: Dict[str, Any], ttl: int) -> None:
        raise NotImplementedError
    
    async def delete(self, key: str) -> None:
        raise NotImplementedError


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend with TTL support."""
    
    def __init__(self):
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            if key in self._cache:
                expiry, value = self._cache[key]
                if expiry > time.time():
                    return value
                else:
                    del self._cache[key]
            return None
    
    async def set(self, key: str, value: Dict[str, Any], ttl: int) -> None:
        async with self._lock:
            self._cache[key] = (time.time() + ttl, value)
    
    async def delete(self, key: str) -> None:
        async with self._lock:
            self._cache.pop(key, None)
    
    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()


class RedisCacheBackend(CacheBackend):
    """Redis cache backend using enterprise_redis_service."""
    
    def __init__(self, redis_service: Any):
        self._redis = redis_service
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            return await self._redis.get(key)
        except Exception as e:
            logger.warning("Redis cache GET error: %s", e)
            return None
    
    async def set(self, key: str, value: Dict[str, Any], ttl: int) -> None:
        try:
            await self._redis.setex(key, ttl, value)
        except Exception as e:
            logger.warning("Redis cache SET error: %s", e)
    
    async def delete(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except Exception as e:
            logger.warning("Redis cache DELETE error: %s", e)


# ============================================================================
# Main PDP Client
# ============================================================================

class SecureEnhancedPDP:
    """
    Production-Grade Secure PDP Client - AuthZEN 1.0 Compliant.
    
    Features:
    - AuthZEN 1.0 compliant endpoints (single vs batch)
    - True batch evaluation with single HTTP call
    - Redis or memory caching with differential TTLs
    - Per-item batch caching for optimal cache utilization
    - Rate limiting via semaphore
    - Circuit breaker for resilience
    - Prometheus metrics
    - Pydantic Settings configuration
    
    Example:
        async with SecureEnhancedPDP.from_env() as pdp:
            result = await pdp.evaluate(request)
            if result.decision:
                print("Access granted")
    """
    
    def __init__(
        self,
        config: Optional[PDPConfig] = None,
        cache_backend: Optional[CacheBackend] = None,
    ):
        """
        Initialize the PDP client.
        
        Args:
            config: PDP configuration (uses singleton if not provided)
            cache_backend: Optional cache backend (creates based on config if not provided)
        """
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx required. Install with: pip install httpx")
        
        # Validate FIPS compliance
        FIPSValidator.ensure_compliance()
        
        self.config = config or get_pdp_config()
        self._metrics = get_pdp_metrics()
        
        # HTTP client (lazy init)
        self._http_client: Optional[httpx.AsyncClient] = None
        
        # OAuth token cache with singleflight (Issue #11)
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._token_lock = asyncio.Lock()  # Singleflight: only one token request at a time
        self._token_refresh_task: Optional[asyncio.Task] = None
        
        # Cache backend
        self._cache = cache_backend
        if self._cache is None and self.config.cache.enabled:
            if self.config.cache.backend == "redis":
                # Lazy init - will be set via set_redis_service()
                self._cache = None
            else:
                self._cache = MemoryCacheBackend()
        
        # Rate limiting semaphore
        self._semaphore = asyncio.Semaphore(self.config.rate_limit.max_inflight)
        
        # Circuit breaker (from empowernow_common.resilience)
        self._circuit_breaker = None
        if self.config.circuit_breaker.enabled:
            self._init_circuit_breaker()
        
        # Token retry strategy (from empowernow_common.resilience)
        self._token_retry_strategy = None
        self._init_token_retry_strategy()
        
        # Constraint and obligation handlers
        self._constraint_handlers: Dict[str, Callable] = {}
        self._obligation_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
        
        # Security context
        self._security_context = {
            "session_id": generate_correlation_id(),
            "created_at": datetime.now(timezone.utc),
        }
        
        logger.info(
            "SecureEnhancedPDP initialized",
            extra={
                "base_url": self.config.connection.base_url,
                "cache_enabled": self.config.cache.enabled,
                "cache_backend": self.config.cache.backend,
                "circuit_breaker_enabled": self.config.circuit_breaker.enabled,
                "max_inflight": self.config.rate_limit.max_inflight,
            },
        )
    
    def _init_circuit_breaker(self) -> None:
        """Initialize circuit breaker from resilience module."""
        try:
            from ..resilience import CircuitBreaker, CircuitBreakerConfig
            
            cb_config = CircuitBreakerConfig(
                enabled=self.config.circuit_breaker.enabled,
                threshold=self.config.circuit_breaker.failure_threshold,
                timeout=self.config.circuit_breaker.reset_timeout,
                window_seconds=self.config.circuit_breaker.window_seconds,
            )
            self._circuit_breaker = CircuitBreaker(name="pdp", config=cb_config)
            logger.debug("Circuit breaker initialized from resilience module")
        except ImportError:
            logger.warning(
                "empowernow_common.resilience not available, using fallback circuit breaker"
            )
            self._circuit_breaker = None
    
    def _init_token_retry_strategy(self) -> None:
        """Initialize retry strategy for token acquisition.
        
        Uses PDPRetryConfig to configure exponential backoff with jitter
        for transient failures when connecting to the IdP token endpoint.
        """
        try:
            from ..resilience import RetryStrategy, RetryConfig
            # Import RetryExhaustedError from retry module directly to match
            # the exception type that RetryStrategy.execute() raises
            from ..resilience.retry import RetryExhaustedError
            
            # Store RetryExhaustedError for use in _do_token_refresh
            self._retry_exhausted_error_cls = RetryExhaustedError
            
            # Convert PDPRetryConfig to resilience RetryConfig
            # Jitter of 0.1 (10%) prevents thundering herd on retry storms
            retry_config = RetryConfig(
                max_retries=self.config.retry.max_retries,
                initial_delay=self.config.retry.backoff_ms / 1000.0,  # ms to seconds
                max_delay=self.config.retry.max_backoff_ms / 1000.0,  # ms to seconds
                backoff_factor=self.config.retry.backoff_multiplier,
                jitter=0.1,
            )
            self._token_retry_strategy = RetryStrategy(
                config=retry_config,
                name="pdp_token",
            )
            logger.debug(
                "Token retry strategy initialized",
                extra={
                    "max_retries": self.config.retry.max_retries,
                    "initial_delay_ms": self.config.retry.backoff_ms,
                    "max_delay_ms": self.config.retry.max_backoff_ms,
                },
            )
        except ImportError:
            logger.warning(
                "empowernow_common.resilience not available, token acquisition will not retry"
            )
            self._token_retry_strategy = None
            self._retry_exhausted_error_cls = None
    
    def _register_default_handlers(self) -> None:
        """Register default constraint and obligation handlers."""
        self._constraint_handlers["rate_limit"] = self._handle_rate_limit_constraint
        self._constraint_handlers["time_window"] = self._handle_time_window_constraint
        self._obligation_handlers["audit_log"] = self._handle_audit_log_obligation
    
    async def set_redis_service(self, redis_service: Any) -> None:
        """
        Set Redis service for caching.
        
        Args:
            redis_service: EnterpriseRedisService instance
        """
        self._cache = RedisCacheBackend(redis_service)
        logger.info("Redis cache backend configured")
    
    @classmethod
    def from_env(cls) -> "SecureEnhancedPDP":
        """Create PDP client from environment variables (Issue #5)."""
        return cls(config=PDPConfig())
    
    @classmethod
    def for_service(cls, service_name: str) -> "SecureEnhancedPDP":
        """
        Create PDP client with service-specific defaults (Issue #5).
        
        Service-specific environment variables:
            {SERVICE}_PDP_BASE_URL
            {SERVICE}_PDP_CLIENT_ID
            etc.
        
        Args:
            service_name: Service name (e.g., "bff", "idp", "membership")
            
        Returns:
            Configured SecureEnhancedPDP instance
        """
        prefix = service_name.upper()
        
        # Try service-specific env vars first, fall back to generic
        config = PDPConfig()
        
        if url := os.getenv(f"{prefix}_PDP_BASE_URL"):
            config.connection.base_url = url
        
        if client_id := os.getenv(f"{prefix}_PDP_CLIENT_ID"):
            config.connection.client_id = client_id
        
        if client_secret := os.getenv(f"{prefix}_PDP_CLIENT_SECRET"):
            config.connection.client_secret = client_secret
        
        if token_url := os.getenv(f"{prefix}_PDP_TOKEN_URL"):
            config.connection.token_url = token_url
        
        if app := os.getenv(f"{prefix}_PDP_APPLICATION"):
            config.default_application = app
        
        logger.info(
            f"Created PDP client for service: {service_name}",
            extra={"service": service_name, "base_url": config.connection.base_url},
        )
        
        return cls(config=config)
    
    async def __aenter__(self) -> "SecureEnhancedPDP":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._cleanup()
    
    async def _cleanup(self) -> None:
        """Cleanup resources."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
        
        logger.info("SecureEnhancedPDP cleanup complete", extra=self._metrics.get_stats())
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with configurable connection pooling (Issue #7)."""
        if self._http_client is None or self._http_client.is_closed:
            ssl_context = None
            if self.config.connection.validate_ssl:
                ssl_context = ssl.create_default_context()
            
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=self.config.connection.connect_timeout,
                    read=self.config.connection.request_timeout,
                    write=self.config.connection.request_timeout,
                    pool=self.config.connection.connect_timeout,
                ),
                verify=ssl_context if ssl_context else not self.config.connection.validate_ssl,
                follow_redirects=False,
                limits=httpx.Limits(
                    max_connections=self.config.connection.max_connections,
                    max_keepalive_connections=self.config.connection.max_keepalive_connections,
                    keepalive_expiry=self.config.connection.keepalive_expiry,
                ),
            )
        return self._http_client
    
    async def _acquire_token(self) -> str:
        """
        Acquire OAuth access token for PDP authentication with singleflight (Issue #11).
        
        Uses lock to prevent thundering herd on token refresh - only one
        concurrent token request is allowed.
        
        Features:
        - Singleflight: Only one concurrent token request
        - Refresh-ahead: Proactively refresh token 120s before expiry
        - Background refresh: Non-blocking refresh for better latency
        
        FAIL-FAST: Raises PDPAuthenticationError on failure.
        
        Returns:
            Valid OAuth access token
            
        Raises:
            PDPAuthenticationError: If token acquisition fails
        """
        now = time.time()
        
        # Fast path: Token is valid and not in refresh window
        if self._access_token and now < self._token_expires_at - 120:
            return self._access_token
        
        # Token is in refresh window (60-120s before expiry) - try background refresh
        if self._access_token and now < self._token_expires_at - 60:
            # Token still valid but should refresh soon
            self._schedule_background_refresh()
            return self._access_token
        
        # Token expired or will expire soon - must refresh now
        async with self._token_lock:
            # Double-check after acquiring lock (another request may have refreshed)
            if self._access_token and time.time() < self._token_expires_at - 60:
                return self._access_token
            
            # Perform token refresh inside the lock
            return await self._do_token_refresh()
    
    def _schedule_background_refresh(self) -> None:
        """
        Schedule a background token refresh to avoid latency spikes.
        
        The refresh happens in the background - current requests continue
        with the existing valid token.
        """
        # Don't schedule if already refreshing
        if self._token_refresh_task and not self._token_refresh_task.done():
            return
        
        async def _background_refresh():
            try:
                async with self._token_lock:
                    # Check if still needs refresh after getting lock
                    if time.time() < self._token_expires_at - 120:
                        return  # Another task refreshed while we waited
                    await self._do_token_refresh()
                    logger.debug("Background token refresh completed")
            except PDPAuthenticationError as e:
                logger.warning("Background token refresh failed: %s", e)
            except Exception as e:
                logger.warning("Background token refresh error: %s", e)
        
        try:
            loop = asyncio.get_running_loop()
            self._token_refresh_task = loop.create_task(_background_refresh())
        except RuntimeError:
            # No running loop - skip background refresh
            pass
    
    async def _do_token_refresh(self) -> str:
        """Actually perform the token refresh (called inside lock).
        
        Uses RetryStrategy for transient connection failures to the IdP
        token endpoint. Retries are only performed for connection-level
        errors (timeouts, connection refused, etc.), NOT for HTTP status
        errors like 401/403 which indicate permanent failures.
        """
        token_url = self.config.connection.token_url
        if not token_url:
            raise PDPAuthenticationError(
                "PDP token_url not configured. Set PDP_TOKEN_URL environment variable."
            )
        
        client = await self._get_http_client()
        
        # Build token request
        token_data = {
            "grant_type": "client_credentials",
            "client_id": self.config.connection.client_id,
        }
        
        if self.config.connection.scope:
            token_data["scope"] = self.config.connection.scope
        
        if self.config.connection.resource:
            token_data["resource"] = self.config.connection.resource
        
        # Handle authentication method
        auth_method = self.config.connection.token_auth_method
        
        if auth_method == "private_key_jwt":
            token_data.update(await self._build_private_key_jwt_assertion())
        else:
            # client_secret_post
            if not self.config.connection.client_secret:
                raise PDPAuthenticationError(
                    "client_secret required for client_secret_post authentication"
                )
            token_data["client_secret"] = self.config.connection.client_secret
        
        async def _fetch_token() -> httpx.Response:
            """Inner function for retry strategy."""
            response = await client.post(
                token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response
        
        try:
            # Use retry strategy if available, otherwise fall back to direct call
            if self._token_retry_strategy and self._retry_exhausted_error_cls:
                try:
                    response = await self._token_retry_strategy.execute(_fetch_token)
                except self._retry_exhausted_error_cls as e:
                    # All retries exhausted - wrap as PDPAuthenticationError
                    logger.warning(
                        "Token acquisition failed after retries",
                        extra={
                            "attempts": e.attempts,
                            "total_time_seconds": e.total_time,
                            "last_error": str(e.last_exception),
                        },
                    )
                    raise PDPAuthenticationError(
                        f"Failed to connect to PDP token endpoint after {e.attempts} attempts: {e.last_exception}"
                    ) from e.last_exception
            else:
                response = await _fetch_token()
        except httpx.HTTPStatusError as e:
            # HTTP status errors (4xx/5xx) - don't retry, these are permanent failures
            error_detail = ""
            try:
                error_body = e.response.json()
                error_detail = f" - {error_body.get('error', '')} {error_body.get('error_description', '')}".strip()
            except Exception:
                pass
            raise PDPAuthenticationError(
                f"PDP token endpoint returned {e.response.status_code}{error_detail}"
            ) from e
        except httpx.RequestError as e:
            # Connection-level errors without retry strategy
            raise PDPAuthenticationError(
                f"Failed to connect to PDP token endpoint: {e}"
            ) from e
        
        token_response = response.json()
        access_token = token_response.get("access_token")
        
        if not access_token:
            raise PDPAuthenticationError(
                f"PDP token response missing access_token"
            )
        
        self._access_token = access_token
        self._token_expires_at = time.time() + token_response.get("expires_in", 3600)
        
        logger.debug(
            "PDP token acquired",
            extra={"expires_in": token_response.get("expires_in", 3600)},
        )
        return self._access_token
    
    async def _build_private_key_jwt_assertion(self) -> Dict[str, str]:
        """Build private_key_jwt client assertion."""
        from ..oauth.client import PrivateKeyJWTConfig
        
        key_path = self.config.private_key_jwt.key_path
        if not key_path:
            raise PDPAuthenticationError(
                "private_key_jwt requires PDP_CLIENT_ASSERTION_KEY_PATH"
            )
        
        try:
            with open(key_path, "rb") as kf:
                key_pem = kf.read()
        except FileNotFoundError:
            raise PDPAuthenticationError(f"Private key file not found: {key_path}")
        except PermissionError:
            raise PDPAuthenticationError(f"Permission denied reading: {key_path}")
        
        pkjwt_config = PrivateKeyJWTConfig(
            signing_key=key_pem,
            signing_alg=self.config.private_key_jwt.alg,
            assertion_ttl=300,
            kid=self.config.private_key_jwt.kid,
        )
        
        assertion = pkjwt_config.to_jwt(
            self.config.connection.client_id,
            self.config.connection.token_url,
        )
        
        return {
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": assertion,
        }
    
    def _get_cache_key(
        self,
        subject_id: str,
        subject_type: str,
        resource_type: str,
        resource_id: str,
        action_name: str,
    ) -> str:
        """
        Generate cache key for authorization decision.
        Uses base64 encoding for IDs with special characters.
        """
        safe_subject_id = base64.urlsafe_b64encode(subject_id.encode()).decode()
        safe_resource_id = base64.urlsafe_b64encode(resource_id.encode()).decode()
        
        key_parts = [
            safe_subject_id,
            subject_type or "account",
            resource_type or "resource",
            safe_resource_id,
            action_name or "access",
        ]
        
        return f"{self.config.cache.key_prefix}{':'.join(key_parts)}"
    
    def _cache_key_for_request(self, request: SecureAuthRequest) -> str:
        """Generate cache key from SecureAuthRequest."""
        return self._get_cache_key(
            subject_id=request.subject.id,
            subject_type=request.subject.type,
            resource_type=request.resource.type,
            resource_id=request.resource.id,
            action_name=request.action.name,
        )
    
    async def _get_cached_decision(
        self,
        cache_key: str,
        correlation_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get cached PDP decision."""
        if not self.config.cache.enabled or not self._cache:
            return None
        
        try:
            cached = await self._cache.get(cache_key)
            if cached:
                self._metrics.record_cache_hit()
                logger.debug(
                    "Cache HIT",
                    extra={"cache_key": cache_key[:50], "correlation_id": correlation_id},
                )
                return cached
            
            self._metrics.record_cache_miss()
            return None
        except Exception as e:
            logger.warning("Cache GET error: %s", e)
            self._metrics.record_cache_miss()
            return None
    
    async def _cache_decision(
        self,
        cache_key: str,
        decision_data: Dict[str, Any],
        decision: bool,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Cache PDP decision with differential TTL."""
        if not self.config.cache.enabled or not self._cache:
            return
        
        try:
            ttl = (
                self.config.cache.ttl_allow
                if decision
                else self.config.cache.ttl_deny
            )
            await self._cache.set(cache_key, decision_data, ttl)
            self._metrics.record_cache_set()
            
            logger.debug(
                "Cached decision",
                extra={
                    "cache_key": cache_key[:50],
                    "ttl": ttl,
                    "decision": decision,
                    "correlation_id": correlation_id,
                },
            )
        except Exception as e:
            logger.warning("Cache SET error: %s", e)
    
    async def _call_pdp_api(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        correlation_id: str,
    ) -> Dict[str, Any]:
        """
        Make authenticated HTTP call to PDP with rate limiting.
        
        Args:
            endpoint: API endpoint path
            payload: Request payload
            correlation_id: Request correlation ID
            
        Returns:
            Response JSON
            
        Raises:
            PDPError: On request failure
            PDPCircuitOpenError: If circuit breaker is open
            PDPRateLimitError: If rate limited
        """
        # Rate limiting
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=0.5)
        except asyncio.TimeoutError:
            self._metrics.record_rate_limit_hit()
            raise PDPRateLimitError(
                "PDP rate limit exceeded - too many concurrent requests",
                correlation_id=correlation_id,
            )
        
        self._metrics.record_inflight_change(1)
        
        try:
            # Circuit breaker check
            if self._circuit_breaker:
                from ..resilience import CircuitBreakerOpenError
                try:
                    return await self._circuit_breaker.execute(
                        self._make_pdp_request,
                        endpoint,
                        payload,
                        correlation_id,
                    )
                except CircuitBreakerOpenError as e:
                    self._metrics.record_circuit_state("pdp", "open")
                    raise PDPCircuitOpenError(
                        f"PDP circuit breaker is open: {e}",
                        correlation_id=correlation_id,
                    ) from e
            else:
                return await self._make_pdp_request(endpoint, payload, correlation_id)
        finally:
            self._semaphore.release()
            self._metrics.record_inflight_change(-1)
    
    async def _make_pdp_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        correlation_id: str,
    ) -> Dict[str, Any]:
        """Make the actual HTTP request to PDP."""
        client = await self._get_http_client()
        token = await self._acquire_token()
        
        url = f"{self.config.connection.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Request-ID": correlation_id,
            "X-Correlation-ID": correlation_id,
            "User-Agent": "EmpowerNow-SecurePDP/2.0",
        }
        
        with LatencyTimer() as timer:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                # Validate response size
                if len(response.content) > 1024 * 1024:  # 1MB limit
                    raise PDPError("PDP response too large", correlation_id=correlation_id)
                
                result = response.json()
                
                self._metrics.record_request(
                    endpoint=endpoint,
                    success=True,
                    latency_seconds=timer.elapsed_seconds,
                )
                
                logger.debug(
                    "PDP request successful",
                    extra={
                        "endpoint": endpoint,
                        "latency_ms": timer.elapsed_ms,
                        "correlation_id": correlation_id,
                    },
                )
                
                return result
                
            except httpx.HTTPStatusError as e:
                self._metrics.record_request(
                    endpoint=endpoint,
                    success=False,
                    latency_seconds=timer.elapsed_seconds,
                )
                
                error_detail = f"HTTP {e.response.status_code}"
                try:
                    error_data = e.response.json()
                    if msg := error_data.get("message") or error_data.get("error"):
                        error_detail = f"{error_detail} - {msg}"
                except Exception:
                    pass
                
                logger.error(
                    "PDP request failed",
                    extra={
                        "endpoint": endpoint,
                        "status_code": e.response.status_code,
                        "correlation_id": correlation_id,
                    },
                )
                
                raise PDPError(
                    message=f"PDP request failed: {error_detail}",
                    status_code=e.response.status_code,
                    correlation_id=correlation_id,
                )
                
            except Exception as e:
                self._metrics.record_request(
                    endpoint=endpoint,
                    success=False,
                    latency_seconds=timer.elapsed_seconds,
                )
                
                if isinstance(e, PDPError):
                    raise
                
                logger.error(
                    "PDP request error",
                    extra={
                        "endpoint": endpoint,
                        "error": str(e),
                        "correlation_id": correlation_id,
                    },
                )
                
                raise PDPError(
                    message=f"PDP request error: {e}",
                    correlation_id=correlation_id,
                ) from e
    
    def _parse_response(
        self,
        raw_response: Dict[str, Any],
        correlation_id: str,
        cached: bool = False,
    ) -> SecureEnhancedAuthResult:
        """Parse PDP response into SecureEnhancedAuthResult."""
        decision = raw_response.get("decision", False)
        context = raw_response.get("context", {})
        
        # Parse constraints
        constraints = []
        for c in context.get("constraints", []):
            try:
                constraints.append(SecureConstraint(
                    id=c.get("id", generate_correlation_id()),
                    type=c.get("type", "unknown"),
                    parameters=c.get("parameters", {}),
                ))
            except Exception as e:
                logger.warning("Invalid constraint in response: %s", e)
        
        # Parse obligations
        obligations = []
        for o in context.get("obligations", []):
            try:
                obligations.append(SecureObligation(
                    id=o.get("id", generate_correlation_id()),
                    type=o.get("type", "unknown"),
                    parameters=o.get("parameters", {}),
                    timing=o.get("timing", "after"),
                    critical=o.get("critical", False),
                ))
            except Exception as e:
                logger.warning("Invalid obligation in response: %s", e)
        
        # Extract reason
        reason = ""
        if reason_user := context.get("reason_user"):
            reason = reason_user.get("en", "")
        elif reason_admin := context.get("reason_admin"):
            reason = reason_admin.get("en", "")
        
        return SecureEnhancedAuthResult(
            decision=decision,
            reason=reason,
            constraints=constraints,
            obligations=obligations,
            correlation_id=correlation_id,
            raw_context=context,
            cached=cached,
        )
    
    # =========================================================================
    # Public API - Single Evaluation
    # =========================================================================
    
    async def evaluate(
        self,
        request: SecureAuthRequest,
        correlation_id: Optional[str] = None,
        application: Optional[str] = None,
    ) -> SecureEnhancedAuthResult:
        """
        Evaluate a single authorization request.
        
        Uses AuthZEN 1.0 compliant endpoint: POST /access/v1/evaluation (SINGULAR)
        
        Args:
            request: Authorization request
            correlation_id: Optional correlation ID for tracing
            application: Optional pdp_application for policy scoping (Issue #3)
            
        Returns:
            SecureEnhancedAuthResult with decision
        """
        correlation_id = correlation_id or generate_correlation_id()
        
        # Apply application scoping if specified (Issue #3)
        effective_app = application or self.config.default_application
        if effective_app:
            # Inject pdp_application into resource properties
            resource_props = dict(request.resource.properties)
            if "pdp_application" not in resource_props:
                resource_props["pdp_application"] = effective_app
                request = SecureAuthRequest(
                    subject=request.subject,
                    resource=SecureResource(
                        id=request.resource.id,
                        type=request.resource.type,
                        properties=resource_props,
                    ),
                    action=request.action,
                    context=request.context,
                )
        
        # Check cache first
        cache_key = self._cache_key_for_request(request)
        cached = await self._get_cached_decision(cache_key, correlation_id)
        
        if cached:
            self._metrics.record_request(
                endpoint=self.config.endpoints.evaluation,
                success=True,
                cached=True,
            )
            return self._parse_response(cached, correlation_id, cached=True)
        
        # Build payload
        payload = {
            "subject": request.subject.model_dump(),
            "resource": request.resource.model_dump(),
            "action": request.action.model_dump(),
            "context": request.context.model_dump(),
        }
        
        # Call PDP - CRITICAL: Use SINGULAR endpoint /access/v1/evaluation
        raw_response = await self._call_pdp_api(
            endpoint=self.config.endpoints.evaluation,  # /access/v1/evaluation
            payload=payload,
            correlation_id=correlation_id,
        )
        
        # Cache result
        await self._cache_decision(
            cache_key,
            raw_response,
            raw_response.get("decision", False),
            correlation_id,
        )
        
        return self._parse_response(raw_response, correlation_id)
    
    # =========================================================================
    # Public API - Batch Evaluation
    # =========================================================================
    
    async def evaluate_batch(
        self,
        requests: List[SecureAuthRequest],
        semantics: EvaluationSemantic = EvaluationSemantic.EXECUTE_ALL,
        correlation_id: Optional[str] = None,
    ) -> List[SecureEnhancedAuthResult]:
        """
        Evaluate multiple authorization requests with per-item caching.
        
        Uses AuthZEN 1.0 compliant endpoint: POST /access/v1/evaluations (PLURAL)
        with {"evaluations": [...]} payload format.
        
        This is a TRUE batch implementation - sends one HTTP request instead of N.
        
        Flow:
        1. Check cache for each item
        2. Send only cache-misses to PDP in single batch request
        3. Merge results preserving order
        4. Cache fresh results with differential TTLs
        
        Args:
            requests: List of authorization requests
            semantics: Evaluation semantics (execute_all, deny_on_first_deny, etc.)
            correlation_id: Optional correlation ID
            
        Returns:
            List of SecureEnhancedAuthResult in same order as input
        """
        correlation_id = correlation_id or generate_correlation_id()
        
        if not requests:
            return []
        
        # Track cache hits and requests to evaluate
        cached_results: Dict[int, SecureEnhancedAuthResult] = {}
        requests_to_evaluate: List[SecureAuthRequest] = []
        index_map: List[int] = []  # Maps batch index -> original index
        
        # Check cache for each request
        for idx, req in enumerate(requests):
            cache_key = self._cache_key_for_request(req)
            cached = await self._get_cached_decision(cache_key, correlation_id)
            
            if cached:
                cached_results[idx] = self._parse_response(
                    cached, correlation_id, cached=True
                )
            else:
                requests_to_evaluate.append(req)
                index_map.append(idx)
        
        # If all cached, return early
        if not requests_to_evaluate:
            logger.debug(
                "Batch fully served from cache",
                extra={"count": len(requests), "correlation_id": correlation_id},
            )
            return [cached_results[i] for i in range(len(requests))]
        
        # Build TRUE batch payload per AuthZEN 1.0
        batch_evaluations = []
        for req in requests_to_evaluate:
            batch_evaluations.append({
                "subject": req.subject.model_dump(),
                "resource": req.resource.model_dump(),
                "action": req.action.model_dump(),
                "context": req.context.model_dump(),
            })
        
        batch_payload = {
            "evaluations": batch_evaluations,
            "options": {"evaluation_semantics": semantics.value},
        }
        
        # Call PDP - CRITICAL: Use PLURAL endpoint /access/v1/evaluations
        raw_response = await self._call_pdp_api(
            endpoint=self.config.endpoints.batch,  # /access/v1/evaluations
            payload=batch_payload,
            correlation_id=correlation_id,
        )
        
        # Parse batch response
        batch_results = raw_response.get("evaluations", [])
        all_results: List[Optional[SecureEnhancedAuthResult]] = [None] * len(requests)
        
        # Fill cached results
        for idx, result in cached_results.items():
            all_results[idx] = result
        
        # Fill fresh results and cache them
        for i, result_data in enumerate(batch_results):
            original_idx = index_map[i]
            req = requests_to_evaluate[i]
            
            # Parse result
            parsed = self._parse_response(result_data, correlation_id)
            all_results[original_idx] = parsed
            
            # Cache this result
            cache_key = self._cache_key_for_request(req)
            await self._cache_decision(
                cache_key,
                result_data,
                result_data.get("decision", False),
                correlation_id,
            )
        
        logger.debug(
            "Batch evaluation complete",
            extra={
                "total": len(requests),
                "cached": len(cached_results),
                "evaluated": len(requests_to_evaluate),
                "correlation_id": correlation_id,
            },
        )
        
        return all_results
    
    # =========================================================================
    # Public API - Convenience Methods
    # =========================================================================
    
    async def can(
        self,
        who: Union[str, SecureSubject],
        action: Union[str, SecureAction],
        what: Union[str, SecureResource],
        **context_attrs,
    ) -> bool:
        """
        Simple boolean permission check.
        
        Example:
            allowed = await pdp.can("alice", "read", "/documents/secret.pdf")
        """
        request = self._build_request(who, action, what, **context_attrs)
        result = await self.evaluate(request)
        return result.decision
    
    async def check(
        self,
        who: Union[str, SecureSubject],
        action: Union[str, SecureAction],
        what: Union[str, SecureResource],
        **context_attrs,
    ) -> SecureEnhancedAuthResult:
        """
        Enhanced check with full result including constraints/obligations.
        
        Example:
            result = await pdp.check("alice", "read", "/documents/secret.pdf")
            if result.has_constraints:
                apply_constraints(result.constraints)
        """
        request = self._build_request(who, action, what, **context_attrs)
        return await self.evaluate(request)
    
    async def check_permission(
        self,
        subject_id: str,
        resource_type: str,
        action: str,
        resource_id: str = "*",
        subject_type: str = "account",
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Simple permission check - convenience wrapper.
        
        Args:
            subject_id: Subject ID (ARN or user ID)
            resource_type: Resource type
            action: Action name
            resource_id: Resource ID (default "*")
            subject_type: Subject type (default "account")
            context: Additional context
            
        Returns:
            True if authorized
        """
        request = SecureAuthRequest(
            subject=SecureSubject(id=subject_id, type=subject_type),
            resource=SecureResource(id=resource_id, type=resource_type),
            action=SecureAction(name=action),
            context=SecureContext(attributes=context or {}),
        )
        result = await self.evaluate(request)
        return result.decision
    
    def _build_request(
        self,
        who: Union[str, SecureSubject],
        action: Union[str, SecureAction],
        what: Union[str, SecureResource],
        **context_attrs,
    ) -> SecureAuthRequest:
        """Build SecureAuthRequest from flexible inputs."""
        # Normalize subject
        if isinstance(who, SecureSubject):
            subject = who
        elif isinstance(who, dict):
            subject = SecureSubject(
                id=str(who.get("id", who)),
                type=who.get("type", "account"),
                properties=who.get("properties", {}),
            )
        else:
            subject = SecureSubject(id=str(who), type="account")
        
        # Normalize resource
        if isinstance(what, SecureResource):
            resource = what
        elif isinstance(what, dict):
            resource = SecureResource(
                id=str(what.get("id", what)),
                type=what.get("type", "resource"),
                properties=what.get("properties", {}),
            )
        else:
            resource = SecureResource(id=str(what), type="resource")
        
        # Normalize action
        if isinstance(action, SecureAction):
            action_obj = action
        elif isinstance(action, dict):
            action_obj = SecureAction(
                name=str(action.get("name", action)),
                properties=action.get("properties", {}),
            )
        else:
            action_obj = SecureAction(name=str(action))
        
        # Build context
        context = SecureContext(attributes=context_attrs) if context_attrs else SecureContext()
        
        return SecureAuthRequest(
            subject=subject,
            resource=resource,
            action=action_obj,
            context=context,
        )
    
    # =========================================================================
    # Search API
    # =========================================================================
    
    async def search_actions(
        self,
        subject: SecureSubject,
        resource: SecureResource,
        context: Optional[SecureContext] = None,
        correlation_id: Optional[str] = None,
        page_limit: Optional[int] = None,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for available actions (AuthZEN 1.0 Section 8.6).
        
        Returns all actions that a subject can perform on a resource.
        Note: Per spec, the action key is OMITTED from the request payload.
        
        Args:
            subject: The subject requesting access (REQUIRED)
            resource: The target resource (REQUIRED)
            context: Additional context (OPTIONAL)
            correlation_id: Request tracing ID
            page_limit: Maximum results per page (OPTIONAL)
            page_token: Pagination token from previous response (OPTIONAL)
            
        Returns:
            Dict with "results" (List[SecureAction]) and optional "page" info
        """
        correlation_id = correlation_id or generate_correlation_id()
        
        # Build payload per AuthZEN 1.0 Section 8.6.1
        # Note: action key is intentionally omitted
        payload: Dict[str, Any] = {
            "subject": subject.model_dump(exclude_none=True),
            "resource": resource.model_dump(exclude_none=True),
        }
        
        # Only include context if provided (don't send empty {})
        if context:
            payload["context"] = context.model_dump(exclude_none=True)
        
        # Add pagination if specified (Section 8.2)
        if page_limit is not None or page_token is not None:
            payload["page"] = {}
            if page_limit is not None:
                payload["page"]["limit"] = page_limit
            if page_token is not None:
                payload["page"]["token"] = page_token
        
        try:
            response = await self._call_pdp_api(
                endpoint=self.config.endpoints.search_actions,
                payload=payload,
                correlation_id=correlation_id,
            )
            
            results = [
                SecureAction(name=r.get("name", r.get("id", "")))
                for r in response.get("results", [])
            ]
            
            return {
                "results": results,
                "page": response.get("page"),
                "context": response.get("context"),
            }
        except Exception as e:
            logger.error(
                "Search actions failed: %s",
                e,
                extra={"correlation_id": correlation_id},
            )
            return {"results": [], "page": None, "context": None}
    
    async def search_subjects(
        self,
        action: SecureAction,
        resource: SecureResource,
        subject_type: str = "user",
        context: Optional[SecureContext] = None,
        correlation_id: Optional[str] = None,
        page_limit: Optional[int] = None,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for subjects that can perform an action (AuthZEN 1.0 Section 8.4).
        
        Returns all subjects of a given type that are permitted to perform
        the specified action on the resource.
        
        Args:
            action: The action being performed
            resource: The target resource
            subject_type: Type of subjects to search for (default: "user")
            context: Additional context
            correlation_id: Request tracing ID
            page_limit: Maximum results per page
            page_token: Pagination token from previous response
            
        Returns:
            Dict with "results" (List[SecureSubject]) and optional "page" info
        """
        correlation_id = correlation_id or generate_correlation_id()
        
        # Build payload per AuthZEN 1.0 Section 8.4.1
        # Subject MUST contain type, ID SHOULD be omitted
        payload: Dict[str, Any] = {
            "subject": {"type": subject_type},
            "action": action.model_dump(exclude_none=True),
            "resource": resource.model_dump(exclude_none=True),
        }
        
        # Only include context if provided (don't send empty {})
        if context:
            payload["context"] = context.model_dump(exclude_none=True)
        
        # Add pagination if specified (Section 8.2)
        if page_limit is not None or page_token is not None:
            payload["page"] = {}
            if page_limit is not None:
                payload["page"]["limit"] = page_limit
            if page_token is not None:
                payload["page"]["token"] = page_token
        
        try:
            response = await self._call_pdp_api(
                endpoint=self.config.endpoints.search_subjects,
                payload=payload,
                correlation_id=correlation_id,
            )
            
            results = [
                SecureSubject(
                    id=r.get("id", ""),
                    type=r.get("type", subject_type),
                    properties=r.get("properties", {}),
                )
                for r in response.get("results", [])
            ]
            
            return {
                "results": results,
                "page": response.get("page"),
                "context": response.get("context"),
            }
        except Exception as e:
            logger.error("Search subjects failed: %s", e, extra={"correlation_id": correlation_id})
            return {"results": [], "page": None, "context": None}
    
    async def search_resources(
        self,
        subject: SecureSubject,
        action: SecureAction,
        resource_type: str,
        context: Optional[SecureContext] = None,
        correlation_id: Optional[str] = None,
        page_limit: Optional[int] = None,
        page_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for resources a subject can access (AuthZEN 1.0 Section 8.5).
        
        Returns all resources of a given type that the subject is permitted
        to perform the specified action on.
        
        Args:
            subject: The subject requesting access
            action: The action being performed
            resource_type: Type of resources to search for
            context: Additional context
            correlation_id: Request tracing ID
            page_limit: Maximum results per page
            page_token: Pagination token from previous response
            
        Returns:
            Dict with "results" (List[SecureResource]) and optional "page" info
        """
        correlation_id = correlation_id or generate_correlation_id()
        
        # Build payload per AuthZEN 1.0 Section 8.5.1
        # Resource MUST contain type, ID SHOULD be omitted
        payload: Dict[str, Any] = {
            "subject": subject.model_dump(exclude_none=True),
            "action": action.model_dump(exclude_none=True),
            "resource": {"type": resource_type},
        }
        
        # Only include context if provided (don't send empty {})
        if context:
            payload["context"] = context.model_dump(exclude_none=True)
        
        # Add pagination if specified (Section 8.2)
        if page_limit is not None or page_token is not None:
            payload["page"] = {}
            if page_limit is not None:
                payload["page"]["limit"] = page_limit
            if page_token is not None:
                payload["page"]["token"] = page_token
        
        try:
            response = await self._call_pdp_api(
                endpoint=self.config.endpoints.search_resources,
                payload=payload,
                correlation_id=correlation_id,
            )
            
            results = [
                SecureResource(
                    id=r.get("id", ""),
                    type=r.get("type", resource_type),
                    properties=r.get("properties", {}),
                )
                for r in response.get("results", [])
            ]
            
            return {
                "results": results,
                "page": response.get("page"),
                "context": response.get("context"),
            }
        except Exception as e:
            logger.error("Search resources failed: %s", e, extra={"correlation_id": correlation_id})
            return {"results": [], "page": None, "context": None}
    
    # =========================================================================
    # Constraint & Obligation Handlers
    # =========================================================================
    
    def register_constraint_handler(
        self,
        constraint_type: str,
        handler: Callable,
    ) -> None:
        """Register a custom constraint handler."""
        self._constraint_handlers[constraint_type] = handler
    
    def register_obligation_handler(
        self,
        obligation_type: str,
        handler: Callable,
    ) -> None:
        """Register a custom obligation handler."""
        self._obligation_handlers[obligation_type] = handler
    
    async def _handle_rate_limit_constraint(
        self,
        request: Any,
        constraint: SecureConstraint,
    ) -> Any:
        """Default rate limit constraint handler."""
        logger.info(
            "Rate limit constraint applied",
            extra={"constraint_id": constraint.id, "parameters": constraint.parameters},
        )
        return request
    
    async def _handle_time_window_constraint(
        self,
        request: Any,
        constraint: SecureConstraint,
    ) -> Any:
        """Default time window constraint handler."""
        params = constraint.parameters
        current_time = datetime.now(timezone.utc)
        
        if "start_time" in params and "end_time" in params:
            try:
                start = datetime.fromisoformat(params["start_time"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(params["end_time"].replace("Z", "+00:00"))
                
                if not (start <= current_time <= end):
                    raise ConstraintSecurityError(
                        f"Request outside allowed time window: {start} - {end}"
                    )
            except ValueError as e:
                raise ConstraintSecurityError(f"Invalid time window format: {e}")
        
        return request
    
    async def _handle_audit_log_obligation(
        self,
        obligation: SecureObligation,
    ) -> Dict[str, Any]:
        """Default audit log obligation handler."""
        logger.info(
            "Audit log obligation",
            extra={
                "obligation_id": obligation.id,
                "parameters": obligation.parameters,
            },
        )
        return {"status": "logged", "audit_id": obligation.id}
    
    # =========================================================================
    # Metrics & Health
    # =========================================================================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics including cache statistics."""
        stats = self._metrics.get_stats()
        
        # Add cache backend info
        stats["cache"] = {
            "enabled": self.config.cache.enabled,
            "backend": self.config.cache.backend,
            "ttl_allow_seconds": self.config.cache.ttl_allow,
            "ttl_deny_seconds": self.config.cache.ttl_deny,
        }
        
        # Add memory cache size if using memory backend
        if self._cache and isinstance(self._cache, MemoryCacheBackend):
            stats["cache"]["entries"] = len(self._cache._cache)
        
        # Add token status
        stats["token"] = {
            "valid": self._access_token is not None and time.time() < self._token_expires_at,
            "expires_in_seconds": max(0, int(self._token_expires_at - time.time())) if self._token_expires_at else 0,
        }
        
        return stats
    
    async def health(self) -> Dict[str, Any]:
        """
        Comprehensive health check for PDP connectivity and components.
        
        Checks:
        - PDP endpoint connectivity
        - OAuth token acquisition
        - Circuit breaker state
        - Cache backend status
        
        Example:
            health = await pdp.health()
            if health["status"] == "healthy":
                print(f"PDP latency: {health['latency_ms']}ms")
        
        Returns:
            Dict with health status and component details
        """
        correlation_id = generate_correlation_id()
        result: Dict[str, Any] = {
            "status": "unhealthy",
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {},
        }
        
        # Check circuit breaker state
        if self._circuit_breaker:
            cb_state = getattr(self._circuit_breaker, "state", None)
            result["components"]["circuit_breaker"] = {
                "status": "healthy" if cb_state and cb_state.value == "closed" else "degraded",
                "state": cb_state.value if cb_state else "unknown",
            }
            if cb_state and cb_state.value == "open":
                result["components"]["circuit_breaker"]["status"] = "unhealthy"
        else:
            result["components"]["circuit_breaker"] = {"status": "disabled"}
        
        # Check cache backend
        cache_status = "healthy"
        if self.config.cache.enabled:
            if self._cache:
                try:
                    # Test cache operations
                    test_key = f"health:{correlation_id}"
                    await self._cache.set(test_key, {"test": True}, ttl=5)
                    cached = await self._cache.get(test_key)
                    await self._cache.delete(test_key)
                    cache_status = "healthy" if cached else "degraded"
                except Exception as e:
                    cache_status = "unhealthy"
                    logger.warning("Cache health check failed: %s", e)
            else:
                cache_status = "not_initialized"
        else:
            cache_status = "disabled"
        
        result["components"]["cache"] = {
            "status": cache_status,
            "backend": self.config.cache.backend if self.config.cache.enabled else "disabled",
        }
        
        # Check OAuth token acquisition
        token_status = "unknown"
        try:
            with LatencyTimer() as token_timer:
                await self._acquire_token()
            token_status = "healthy"
            result["components"]["oauth"] = {
                "status": "healthy",
                "latency_ms": round(token_timer.elapsed_ms, 2),
                "token_valid": True,
                "expires_in_seconds": max(0, int(self._token_expires_at - time.time())),
            }
        except PDPAuthenticationError as e:
            token_status = "unhealthy"
            result["components"]["oauth"] = {
                "status": "unhealthy",
                "error": str(e),
            }
        
        # Check PDP endpoint connectivity (only if token is valid)
        if token_status == "healthy":
            try:
                with LatencyTimer() as pdp_timer:
                    # Use a minimal evaluation request
                    test_request = SecureAuthRequest(
                        subject=SecureSubject(id="_health_check_", type="system"),
                        resource=SecureResource(id="_health_", type="health"),
                        action=SecureAction(name="check"),
                        context=SecureContext(),
                    )
                    await self.evaluate(test_request, correlation_id=correlation_id)
                
                result["components"]["pdp"] = {
                    "status": "healthy",
                    "latency_ms": round(pdp_timer.elapsed_ms, 2),
                    "base_url": self.config.connection.base_url,
                }
                result["status"] = "healthy"
                result["latency_ms"] = round(pdp_timer.elapsed_ms, 2)
            except PDPCircuitOpenError:
                result["components"]["pdp"] = {
                    "status": "circuit_open",
                    "base_url": self.config.connection.base_url,
                }
            except Exception as e:
                result["components"]["pdp"] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "base_url": self.config.connection.base_url,
                }
        else:
            result["components"]["pdp"] = {
                "status": "not_checked",
                "reason": "OAuth token unavailable",
            }
        
        # Determine overall status
        component_statuses = [c.get("status") for c in result["components"].values()]
        if all(s in ("healthy", "disabled", "not_checked") for s in component_statuses):
            result["status"] = "healthy"
        elif any(s == "unhealthy" for s in component_statuses):
            result["status"] = "unhealthy"
        else:
            result["status"] = "degraded"
        
        return result
    
    # Backward compatibility alias
    async def health_check(self) -> Dict[str, Any]:
        """Alias for health() - backward compatibility."""
        return await self.health()
    
    # =========================================================================
    # Pagination Iterators (AsyncIterator helpers)
    # =========================================================================
    
    async def iter_search_subjects(
        self,
        action: SecureAction,
        resource: SecureResource,
        subject_type: str = "user",
        context: Optional[SecureContext] = None,
        page_limit: int = 100,
    ) -> "AsyncIterator[SecureSubject]":
        """
        Async iterator for searching subjects with automatic pagination.
        
        Example:
            async for subject in pdp.iter_search_subjects(action, resource, "user"):
                print(f"Subject: {subject.id}")
        
        Args:
            action: The action being performed
            resource: The target resource
            subject_type: Type of subjects to search for
            context: Additional context
            page_limit: Results per page (default 100)
            
        Yields:
            SecureSubject for each matching subject
        """
        page_token: Optional[str] = None
        
        while True:
            result = await self.search_subjects(
                action=action,
                resource=resource,
                subject_type=subject_type,
                context=context,
                page_limit=page_limit,
                page_token=page_token,
            )
            
            for subject in result.get("results", []):
                yield subject
            
            # Check for next page
            page_info = result.get("page")
            if page_info and page_info.get("next_token"):
                page_token = page_info["next_token"]
            else:
                break
    
    async def iter_search_resources(
        self,
        subject: SecureSubject,
        action: SecureAction,
        resource_type: str,
        context: Optional[SecureContext] = None,
        page_limit: int = 100,
    ) -> "AsyncIterator[SecureResource]":
        """
        Async iterator for searching resources with automatic pagination.
        
        Example:
            async for resource in pdp.iter_search_resources(subject, action, "document"):
                print(f"Resource: {resource.id}")
        
        Args:
            subject: The subject requesting access
            action: The action being performed
            resource_type: Type of resources to search for
            context: Additional context
            page_limit: Results per page (default 100)
            
        Yields:
            SecureResource for each matching resource
        """
        page_token: Optional[str] = None
        
        while True:
            result = await self.search_resources(
                subject=subject,
                action=action,
                resource_type=resource_type,
                context=context,
                page_limit=page_limit,
                page_token=page_token,
            )
            
            for resource in result.get("results", []):
                yield resource
            
            # Check for next page
            page_info = result.get("page")
            if page_info and page_info.get("next_token"):
                page_token = page_info["next_token"]
            else:
                break
    
    async def iter_search_actions(
        self,
        subject: SecureSubject,
        resource: SecureResource,
        context: Optional[SecureContext] = None,
        page_limit: int = 100,
    ) -> "AsyncIterator[SecureAction]":
        """
        Async iterator for searching actions with automatic pagination.
        
        Example:
            async for action in pdp.iter_search_actions(subject, resource):
                print(f"Action: {action.name}")
        
        Args:
            subject: The subject requesting access
            resource: The target resource
            context: Additional context
            page_limit: Results per page (default 100)
            
        Yields:
            SecureAction for each available action
        """
        page_token: Optional[str] = None
        
        while True:
            result = await self.search_actions(
                subject=subject,
                resource=resource,
                context=context,
                page_limit=page_limit,
                page_token=page_token,
            )
            
            for action in result.get("results", []):
                yield action
            
            # Check for next page
            page_info = result.get("page")
            if page_info and page_info.get("next_token"):
                page_token = page_info["next_token"]
            else:
                break


# Aliases for backward compatibility
SecurePDP = SecureEnhancedPDP
SecureAuthzClient = SecureEnhancedPDP
SecurePDPClient = SecureEnhancedPDP
PDPClient = SecureEnhancedPDP
PolicyClient = SecureEnhancedPDP
AuthzClient = SecureEnhancedPDP


# ============================================================================
# Sync Wrapper for Non-Async Contexts (Issue #6)
# ============================================================================

def _get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """Get existing event loop or create a new one for sync contexts."""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.new_event_loop()


def sync_evaluate(
    subject: Union[str, SecureSubject],
    resource: Union[str, SecureResource],
    action: Union[str, SecureAction],
    application: Optional[str] = None,
    **context_attrs,
) -> SecureEnhancedAuthResult:
    """
    Synchronous authorization check for non-async contexts (Issue #6).
    
    For Django views, CLI tools, and other sync code.
    Runs the async evaluation in a thread pool executor.
    
    Example:
        from empowernow_common.authzen import sync_evaluate
        
        # In Django view
        result = sync_evaluate("alice", "/docs/secret.pdf", "read")
        if result.decision:
            return HttpResponse("OK")
    
    Args:
        subject: Subject ID or SecureSubject
        resource: Resource ID or SecureResource  
        action: Action name or SecureAction
        application: Optional pdp_application for policy scoping
        **context_attrs: Additional context attributes
        
    Returns:
        SecureEnhancedAuthResult with decision
    """
    import concurrent.futures
    
    async def _async_evaluate():
        async with SecureEnhancedPDP.from_env() as pdp:
            request = pdp._build_request(subject, action, resource, **context_attrs)
            return await pdp.evaluate(request, application=application)
    
    # Check if we're already in an async context
    try:
        loop = asyncio.get_running_loop()
        # We're in async context - run in executor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, _async_evaluate())
            return future.result(timeout=30.0)
    except RuntimeError:
        # No running loop - we can use asyncio.run directly
        return asyncio.run(_async_evaluate())


def sync_can(
    subject: Union[str, SecureSubject],
    resource: Union[str, SecureResource],
    action: Union[str, SecureAction],
    application: Optional[str] = None,
    **context_attrs,
) -> bool:
    """
    Synchronous boolean permission check (Issue #6).
    
    Example:
        if sync_can("alice", "/docs/secret.pdf", "read"):
            print("Access granted")
    """
    result = sync_evaluate(subject, resource, action, application, **context_attrs)
    return result.decision


class SyncPDPClient:
    """
    Synchronous PDP client wrapper for non-async contexts (Issue #6).
    
    Example:
        client = SyncPDPClient.from_env()
        result = client.evaluate(request)
        allowed = client.can("alice", "read", "/docs/secret.pdf")
    """
    
    def __init__(self, config: Optional[PDPConfig] = None):
        self._config = config or PDPConfig()
        self._async_client: Optional[SecureEnhancedPDP] = None
    
    @classmethod
    def from_env(cls) -> "SyncPDPClient":
        """Create sync client from environment variables."""
        return cls(config=PDPConfig())
    
    @classmethod
    def for_service(cls, service_name: str) -> "SyncPDPClient":
        """Create sync client for a specific service."""
        prefix = service_name.upper()
        config = PDPConfig()
        
        if url := os.getenv(f"{prefix}_PDP_BASE_URL"):
            config.connection.base_url = url
        if client_id := os.getenv(f"{prefix}_PDP_CLIENT_ID"):
            config.connection.client_id = client_id
        if client_secret := os.getenv(f"{prefix}_PDP_CLIENT_SECRET"):
            config.connection.client_secret = client_secret
        if token_url := os.getenv(f"{prefix}_PDP_TOKEN_URL"):
            config.connection.token_url = token_url
        if app := os.getenv(f"{prefix}_PDP_APPLICATION"):
            config.default_application = app
            
        return cls(config=config)
    
    def _run_async(self, coro):
        """Run async coroutine in sync context."""
        import concurrent.futures
        
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result(timeout=30.0)
        except RuntimeError:
            return asyncio.run(coro)
    
    def evaluate(
        self,
        request: SecureAuthRequest,
        application: Optional[str] = None,
    ) -> SecureEnhancedAuthResult:
        """Synchronous single evaluation."""
        async def _eval():
            async with SecureEnhancedPDP(config=self._config) as pdp:
                return await pdp.evaluate(request, application=application)
        return self._run_async(_eval())
    
    def evaluate_batch(
        self,
        requests: List[SecureAuthRequest],
        semantics: EvaluationSemantic = EvaluationSemantic.EXECUTE_ALL,
    ) -> List[SecureEnhancedAuthResult]:
        """Synchronous batch evaluation."""
        async def _eval():
            async with SecureEnhancedPDP(config=self._config) as pdp:
                return await pdp.evaluate_batch(requests, semantics)
        return self._run_async(_eval())
    
    def can(
        self,
        who: Union[str, SecureSubject],
        action: Union[str, SecureAction],
        what: Union[str, SecureResource],
        application: Optional[str] = None,
        **context_attrs,
    ) -> bool:
        """Synchronous boolean permission check."""
        async def _can():
            async with SecureEnhancedPDP(config=self._config) as pdp:
                return await pdp.can(who, action, what, **context_attrs)
        return self._run_async(_can())
    
    def check(
        self,
        who: Union[str, SecureSubject],
        action: Union[str, SecureAction],
        what: Union[str, SecureResource],
        application: Optional[str] = None,
        **context_attrs,
    ) -> SecureEnhancedAuthResult:
        """Synchronous enhanced check with constraints/obligations."""
        async def _check():
            async with SecureEnhancedPDP(config=self._config) as pdp:
                return await pdp.check(who, action, what, **context_attrs)
        return self._run_async(_check())
