"""
EmpowerNow AuthZEN Package - Production-Grade PDP Client

AuthZEN 1.0 compliant authorization models and Policy Decision Point (PDP) client
with enterprise-grade features:

- AuthZEN 1.0 compliant endpoints (single vs batch)
- True batch evaluation (single HTTP call, not N calls)
- Redis caching with differential TTLs (allow: 5min, deny: 1min)
- Per-item batch caching for optimal performance
- Rate limiting via semaphore
- Circuit breaker from empowernow_common.resilience
- Prometheus metrics for observability
- Pydantic Settings configuration

Examples:
    # Simple permission check
    async with SecureEnhancedPDP.from_env() as pdp:
        allowed = await pdp.can("alice", "read", "/documents/secret.pdf")
    
    # Structured request with full result
    request = SecureAuthRequest(
        subject=SecureSubject.account("alice@example.com"),
        resource=SecureResource.for_app("*", "admin_api", "idp"),
        action=SecureAction(name="read"),
    )
    result = await pdp.evaluate(request)
    
    # Batch evaluation (TRUE batch - single HTTP call)
    results = await pdp.evaluate_batch([req1, req2, req3])

References:
    - membership/src/api/pdp_client.py (gold standard)
    - AI_PYTHON_FASTAPI_EXCELLENCE_PLAYBOOK.md
    - SDK_AUTHZEN_REFACTOR_PLAN.md
"""

from .models import (
    # Secure models (preferred)
    SecureSubject,
    SecureResource,
    SecureAction,
    SecureContext,
    SecureAuthRequest,
    SecureAuthResponse,
    # Aliases for convenience
    Subject,
    Who,
    Resource,
    What,
    Action,
    How,
    Context,
    When,
    AuthRequest,
    AuthResponse,
)

from .config import (
    PDPConfig,
    PDPConnectionConfig,
    PDPEndpointsConfig,
    PDPCacheConfig,
    PDPCircuitBreakerConfig,
    PDPRateLimitConfig,
    get_pdp_config,
    reset_pdp_config,
)

from .metrics import (
    PDPMetrics,
    get_pdp_metrics,
    reset_pdp_metrics,
    LatencyTimer,
)

from .secure_client_v2 import (
    # Main client (production-grade)
    SecureEnhancedPDP,
    SecureEnhancedAuthResult,
    EvaluationSemantic,
    # Errors
    PDPError,
    PDPAuthenticationError,
    PDPCircuitOpenError,
    PDPRateLimitError,
    ConstraintSecurityError,
    ObligationSecurityError,
    # Cache backends
    CacheBackend,
    MemoryCacheBackend,
    RedisCacheBackend,
    # Models
    SecureConstraint,
    SecureObligation,
    AuthorizationResult,
    BatchAuthorizationResponse,
    # Sync wrappers (Issue #6)
    sync_evaluate,
    sync_can,
    SyncPDPClient,
    # Aliases for backward compatibility
    SecurePDP,
    SecureAuthzClient,
    SecurePDPClient,
    PDPClient,
    PolicyClient,
    AuthzClient,
)

from .client import (
    # Legacy enhanced PDP (for backward compatibility)
    EnhancedPDP,
    EnhancedAuthResult,
    PDPConfig as LegacyPDPConfig,
    PDPError as LegacyPDPError,
    ConstraintViolationError,
    CriticalObligationFailure,
    Constraint,
    Obligation,
    PolicyMatchInfo,
    DecisionFactor,
    ConstraintsMode,
    PDP,
    AuthResult,
)

from .helpers import (
    # Pattern B helper functions
    filter_authorized,
    filter_authorized_with_details,
    can_access_any,
    get_accessible_ids,
)

__all__ = [
    # Secure Models (AuthZEN 1.0 compliant)
    "SecureSubject",
    "SecureResource",
    "SecureAction",
    "SecureContext",
    "SecureAuthRequest",
    "SecureAuthResponse",
    # Natural Language Aliases
    "Subject",
    "Who",
    "Resource",
    "What",
    "Action",
    "How",
    "Context",
    "When",
    "AuthRequest",
    "AuthResponse",
    # Configuration (Pydantic Settings)
    "PDPConfig",
    "PDPConnectionConfig",
    "PDPEndpointsConfig",
    "PDPCacheConfig",
    "PDPCircuitBreakerConfig",
    "PDPRateLimitConfig",
    "get_pdp_config",
    "reset_pdp_config",
    # Metrics (Prometheus compatible)
    "PDPMetrics",
    "get_pdp_metrics",
    "reset_pdp_metrics",
    "LatencyTimer",
    # Production PDP Client (v2)
    "SecureEnhancedPDP",
    "SecureEnhancedAuthResult",
    "EvaluationSemantic",
    # Error Types
    "PDPError",
    "PDPAuthenticationError",
    "PDPCircuitOpenError",
    "PDPRateLimitError",
    "ConstraintSecurityError",
    "ObligationSecurityError",
    # Cache Backends
    "CacheBackend",
    "MemoryCacheBackend",
    "RedisCacheBackend",
    # Advanced Models
    "SecureConstraint",
    "SecureObligation",
    "AuthorizationResult",
    "BatchAuthorizationResponse",
    # Sync Wrappers (Issue #6)
    "sync_evaluate",
    "sync_can",
    "SyncPDPClient",
    # Legacy Compatibility
    "EnhancedPDP",
    "EnhancedAuthResult",
    "LegacyPDPConfig",
    "LegacyPDPError",
    "ConstraintViolationError",
    "CriticalObligationFailure",
    "Constraint",
    "Obligation",
    "PolicyMatchInfo",
    "DecisionFactor",
    "ConstraintsMode",
    # Backward Compatibility Aliases
    "SecurePDP",
    "SecureAuthzClient",
    "SecurePDPClient",
    "PDPClient",
    "PolicyClient",
    "AuthzClient",
    "PDP",
    "AuthResult",
    # Pattern B Helper Functions
    "filter_authorized",
    "filter_authorized_with_details",
    "can_access_any",
    "get_accessible_ids",
]
