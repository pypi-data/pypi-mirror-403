"""Delegation Model v2.3 - Shared across MCP Gateway and CRUDService.

This module provides comprehensive delegation management including:
- Delegation model and status enums aligned with Neo4j schema v2.3
- Capability pattern matching with deny rules
- Verification with TOCTOU-safe API (precheck vs enforce)
- Two-tier caching (L1 in-memory + L2 Redis)
- Kafka event-driven cache invalidation

API Overview:
    # For gateway-bound calls (CRUDService is NOT authoritative)
    result = await verifier.precheck_gateway_bound(delegator, delegate, tool_id)
    if result == PreCheckResult.DENY:
        raise DelegationDeniedError(...)
    # Continue - Gateway makes final decision

    # For CRUD-only calls (CRUDService IS authoritative)
    result = await verifier.enforce_local(delegator, delegate, tool_id)
    if result.decision != EnforceDecision.PERMIT:
        raise DelegationDeniedError(...)

Quick Start:
    from empowernow_common.delegation import (
        Delegation,
        DelegationStatus,
        DelegationVerifier,
        InMemoryDelegationCache,
        PreCheckResult,
        EnforceDecision,
    )

    # Create verifier with caching
    verifier = DelegationVerifier(
        membership_client=my_client,
        l1_cache=InMemoryDelegationCache(),
    )

    # Check delegation
    result = await verifier.enforce_local(
        delegator_arn="auth:account:entra:user@example.com",
        delegate_arn="agent:ai-travel",
        tool_id="tool:jira:create_issue",
    )
"""

from .models import (
    # Protocol versioning
    DELEGATION_PROTOCOL_VERSION,
    MIN_SUPPORTED_VERSION,
    MAX_SUPPORTED_VERSION,
    SUPPORTED_VERSIONS,
    is_version_supported,
    # Enums
    DelegationStatus,
    TrustLevel,
    PreCheckResult,
    EnforceDecision,
    VerificationSource,
    # Models
    Delegation,
    EnforceResult,
    DelegationVerifyRequest,
    DelegationVerifyResponse,
)

from .capability import (
    capability_allowed,
    capability_allowed_with_match,
    parse_capability_pattern,
    parse_tool_id,
    is_valid_tool_id,
    filter_allowed_tools,
    validate_patterns,
    clear_pattern_cache,
    # Constants
    MAX_PATTERNS_PER_DELEGATION,
    MAX_PATTERN_LENGTH,
    MAX_WILDCARDS_PER_PATTERN,
    # Classes
    ParsedCapabilityPattern,
)

from .verifier import (
    DelegationVerifier,
    MembershipClientProtocol,
)

from .exceptions import (
    DelegationError,
    DelegationNotFoundError,
    DelegationExpiredError,
    DelegationRevokedError,
    DelegationSuspendedError,
    CapabilityNotAllowedError,
    ProtocolVersionError,
    DelegationVerificationError,
)

from .cache import (
    DelegationCache,
    DelegationCacheConfig,
    InMemoryDelegationCache,
    RedisDelegationCache,
)

from .events import (
    DelegationEvent,
    DelegationEventType,
    DelegationEventPayload,
    DelegationEventHandler,
    DelegationEventHandlerConfig,
    KafkaConsumerProtocol,
    create_event_handler,
)

from .token import (
    DelegationTokenSettings,
    DelegationTokenClaims,
    DelegationTokenService,
    get_delegation_token_service,
    reset_delegation_token_service,
)

from .registry import (
    CapabilityDefinition,
    CapabilityRegistry,
    get_capability_registry,
    clear_registry_cache,
)

from .metering import (
    ConstraintResult,
    MeteringResult,
    ConstraintMeter,
    get_constraint_meter,
    reset_constraint_meter,
)


__all__ = [
    # Protocol versioning
    "DELEGATION_PROTOCOL_VERSION",
    "MIN_SUPPORTED_VERSION",
    "MAX_SUPPORTED_VERSION",
    "SUPPORTED_VERSIONS",
    "is_version_supported",
    # Enums
    "DelegationStatus",
    "TrustLevel",
    "PreCheckResult",
    "EnforceDecision",
    "VerificationSource",
    # Models
    "Delegation",
    "EnforceResult",
    "DelegationVerifyRequest",
    "DelegationVerifyResponse",
    # Capability
    "capability_allowed",
    "capability_allowed_with_match",
    "parse_capability_pattern",
    "parse_tool_id",
    "is_valid_tool_id",
    "filter_allowed_tools",
    "validate_patterns",
    "clear_pattern_cache",
    "MAX_PATTERNS_PER_DELEGATION",
    "MAX_PATTERN_LENGTH",
    "MAX_WILDCARDS_PER_PATTERN",
    "ParsedCapabilityPattern",
    # Verifier
    "DelegationVerifier",
    "MembershipClientProtocol",
    # Exceptions
    "DelegationError",
    "DelegationNotFoundError",
    "DelegationExpiredError",
    "DelegationRevokedError",
    "DelegationSuspendedError",
    "CapabilityNotAllowedError",
    "ProtocolVersionError",
    "DelegationVerificationError",
    # Cache
    "DelegationCache",
    "DelegationCacheConfig",
    "InMemoryDelegationCache",
    "RedisDelegationCache",
    # Events
    "DelegationEvent",
    "DelegationEventType",
    "DelegationEventPayload",
    "DelegationEventHandler",
    "DelegationEventHandlerConfig",
    "KafkaConsumerProtocol",
    "create_event_handler",
    # Token (GAP 7)
    "DelegationTokenSettings",
    "DelegationTokenClaims",
    "DelegationTokenService",
    "get_delegation_token_service",
    "reset_delegation_token_service",
    # Registry (GAP 8)
    "CapabilityDefinition",
    "CapabilityRegistry",
    "get_capability_registry",
    "clear_registry_cache",
    # Metering (GAP 9)
    "ConstraintResult",
    "MeteringResult",
    "ConstraintMeter",
    "get_constraint_meter",
    "reset_constraint_meter",
]
