"""Delegation Model v2.3 - Canonical data models.

This module defines the core data models for the delegation system,
aligned with the Neo4j Delegation Model v2.3 schema.

Key Models:
    - Delegation: The main delegation record
    - DelegationStatus: Lifecycle states (active, suspended, revoked, etc.)
    - TrustLevel: Trust levels (basic, elevated, full)
    - PreCheckResult: Advisory pre-check results (DENY, UNKNOWN - no PERMIT!)
    - EnforceResult: Authoritative enforcement results with evidence

Protocol Versioning:
    - DELEGATION_PROTOCOL_VERSION = "2.3"
    - Only exact major.minor matches are supported
    - Services MUST reject unsupported versions (fail-closed)
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    pass  # For forward references

# =============================================================================
# Protocol Versioning
# =============================================================================

DELEGATION_PROTOCOL_VERSION = "2.3"
"""Current protocol version for delegation messages."""

MIN_SUPPORTED_VERSION = "2.3"
"""Minimum supported protocol version."""

MAX_SUPPORTED_VERSION = "2.3"
"""Maximum supported protocol version."""

SUPPORTED_VERSIONS: frozenset[str] = frozenset({"2.3"})
"""Set of all supported protocol versions."""


def is_version_supported(version: str) -> bool:
    """Check if a protocol version is supported.

    Args:
        version: Version string to check (e.g., "2.3").

    Returns:
        True if the version is in SUPPORTED_VERSIONS.
    """
    return version in SUPPORTED_VERSIONS


# =============================================================================
# Enums
# =============================================================================


class DelegationStatus(str, Enum):
    """Delegation lifecycle states per Neo4j schema v2.3.

    State Transitions:
        pending -> active (approved)
        active -> suspended (temp pause)
        active -> paused (user pause)
        active -> revoked (explicit revocation)
        active -> expired (TTL reached)
        suspended -> active (resumed)
        paused -> active (resumed)
    """

    ACTIVE = "active"
    """Delegation is active and can be used."""

    SUSPENDED = "suspended"
    """Delegation is suspended by admin (can be resumed)."""

    PAUSED = "paused"
    """Delegation is paused by user (can be resumed)."""

    REVOKED = "revoked"
    """Delegation has been explicitly revoked (terminal)."""

    EXPIRED = "expired"
    """Delegation has expired based on expires_at (terminal)."""

    PENDING = "pending"
    """Delegation is awaiting approval."""


class TrustLevel(str, Enum):
    """Trust levels per Neo4j schema v2.3.

    Higher trust levels grant more capabilities:
        basic: Standard operations only
        elevated: Required for identity chaining
        full: Maximum trust, all operations permitted
    """

    BASIC = "basic"
    """Standard operations, explicit capability_ids required."""

    ELEVATED = "elevated"
    """Required for identity chaining, broader access."""

    FULL = "full"
    """Maximum trust, all operations permitted when capability_ids is None."""


class PreCheckResult(str, Enum):
    """Advisory pre-check result for gateway-bound calls.

    IMPORTANT: This can ONLY return DENY or UNKNOWN.
    PERMIT is intentionally not available - the gateway is authoritative.

    Use Case:
        CRUDService performs pre-check before forwarding to MCP Gateway.
        If DENY, fail fast. If UNKNOWN, let gateway decide.
    """

    DENY = "deny"
    """Definitely not allowed - fail fast."""

    UNKNOWN = "unknown"
    """Uncertain - let the authoritative PEP decide."""


class EnforceDecision(str, Enum):
    """Authoritative enforcement decision for local/CRUD-only calls.

    Used when the calling service IS the authoritative PEP.
    """

    PERMIT = "permit"
    """Access is allowed."""

    DENY = "deny"
    """Access is denied."""


class VerificationSource(str, Enum):
    """Where the delegation data came from.

    Used for debugging and observability to understand cache behavior.
    """

    L1_CACHE = "l1_cache"
    """In-memory per-process cache (fastest, shortest TTL)."""

    L2_CACHE = "l2_cache"
    """Redis shared cache (shared across instances)."""

    MEMBERSHIP = "membership"
    """Authoritative source (Membership Service)."""

    NEGATIVE_CACHE = "negative_cache"
    """Cached "not found" result."""


# =============================================================================
# Result Models
# =============================================================================


class EnforceResult(BaseModel):
    """Result of authoritative enforcement (enforce_local).

    Contains full evidence for audit/debugging including:
    - The decision (PERMIT/DENY)
    - The delegation record (if found)
    - Why the decision was made (reason_code, reason_detail)
    - What pattern matched (for capability checks)
    - Where the data came from (source)
    - How long it took (verification_time_ms)

    Example:
        result = EnforceResult.permit(
            delegation=delegation,
            matched_pattern="tool:jira:*",
            source=VerificationSource.L2_CACHE,
            verification_time_ms=2.5,
        )
    """

    model_config = ConfigDict(frozen=True)

    decision: EnforceDecision
    """The enforcement decision (PERMIT or DENY)."""

    delegation: Optional["Delegation"] = None
    """The delegation record, if found."""

    # Evidence fields for audit trail
    reason_code: str = Field(..., description="Machine-readable reason code")
    reason_detail: Optional[str] = Field(None, description="Human-readable explanation")
    matched_pattern: Optional[str] = Field(None, description="Capability pattern that matched")
    source: VerificationSource = Field(..., description="Where delegation was fetched from")

    # Timing info
    verification_time_ms: float = Field(0.0, description="Time to verify in milliseconds")
    delegation_version: Optional[str] = Field(None, description="Delegation version_token")
    ttl_remaining_seconds: Optional[float] = Field(None, description="TTL remaining if cached")

    @classmethod
    def permit(
        cls,
        delegation: "Delegation",
        *,
        matched_pattern: Optional[str] = None,
        source: VerificationSource,
        verification_time_ms: float = 0.0,
        ttl_remaining: Optional[float] = None,
    ) -> "EnforceResult":
        """Factory for PERMIT result with evidence.

        Args:
            delegation: The active delegation.
            matched_pattern: The capability pattern that allowed access.
            source: Where the delegation was fetched from.
            verification_time_ms: How long verification took.
            ttl_remaining: Remaining TTL if from cache.

        Returns:
            EnforceResult with PERMIT decision.
        """
        return cls(
            decision=EnforceDecision.PERMIT,
            delegation=delegation,
            reason_code="DELEGATION_VALID",
            reason_detail="Delegation is active and capability is allowed",
            matched_pattern=matched_pattern,
            source=source,
            verification_time_ms=verification_time_ms,
            delegation_version=delegation.version_token,
            ttl_remaining_seconds=ttl_remaining,
        )

    @classmethod
    def deny(
        cls,
        reason_code: str,
        reason_detail: str,
        *,
        delegation: Optional["Delegation"] = None,
        source: VerificationSource,
        verification_time_ms: float = 0.0,
    ) -> "EnforceResult":
        """Factory for DENY result with evidence.

        Args:
            reason_code: Machine-readable denial reason.
            reason_detail: Human-readable explanation.
            delegation: The delegation record (if exists but invalid).
            source: Where the data came from.
            verification_time_ms: How long verification took.

        Returns:
            EnforceResult with DENY decision.
        """
        return cls(
            decision=EnforceDecision.DENY,
            delegation=delegation,
            reason_code=reason_code,
            reason_detail=reason_detail,
            matched_pattern=None,
            source=source,
            verification_time_ms=verification_time_ms,
            delegation_version=delegation.version_token if delegation else None,
        )


# =============================================================================
# Main Delegation Model
# =============================================================================


class Delegation(BaseModel):
    """Delegation model v2.3 - aligned with Neo4j schema.

    Represents a user's delegation to an agent with capability scoping,
    constraints, and full lifecycle tracking.

    Field Naming Convention:
        - Uses Neo4j canonical names (user_id, agent_id)
        - Provides aliases for backward compatibility (delegator_arn, delegate_arn)
        - New code should prefer canonical names

    Example:
        delegation = Delegation(
            id="del_abc123",
            user_id="auth:account:entra:user@example.com",
            agent_id="agent:ai-travel",
            status=DelegationStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            created_by="auth:account:entra:user@example.com",
            version_token="v1-hash",
            capability_ids=["tool:jira:*", "tool:slack:send_message"],
        )
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,  # Allow both field name and alias
    )

    # =========================================================================
    # Required Fields (Neo4j schema)
    # =========================================================================

    id: str = Field(..., description="Unique delegation identifier (UUID)")

    user_id: str = Field(
        ...,
        alias="delegator_arn",
        description="Delegating user's identity ARN",
    )

    agent_id: str = Field(
        ...,
        alias="delegate_arn",
        description="Target agent ID",
    )

    status: DelegationStatus = Field(..., description="Current lifecycle status")

    created_at: datetime = Field(..., description="Creation timestamp")

    created_by: str = Field(..., description="Identity who created the delegation")

    version_token: str = Field(
        ...,
        description="Hash of effective delegation state (for cache invalidation)",
    )

    # =========================================================================
    # Optional Fields (Neo4j schema)
    # =========================================================================

    # Capability scoping
    capability_ids: Optional[List[str]] = Field(
        default=None,
        description="Allowed tool IDs in canonical format (tool:{mcp_server}:{key})",
    )

    deny_capability_ids: Optional[List[str]] = Field(
        default=None,
        description="Explicitly denied tool IDs (overrides allows)",
    )

    # Trust and constraints
    trust_level: TrustLevel = Field(default=TrustLevel.BASIC)

    constraints: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Inline constraint document (e.g., spend_cap, ip_range)",
    )

    constraints_ref: Optional[str] = Field(
        default=None,
        description="Pointer to external constraint definition",
    )

    # Lifecycle
    valid_from: Optional[datetime] = Field(
        default=None,
        description="When delegation becomes active (default: now)",
    )

    expires_at: Optional[datetime] = Field(
        default=None,
        description="When delegation expires (null = never)",
    )

    # Security binding
    service_id: Optional[str] = Field(
        default=None,
        description="Bound service principal (optional)",
    )

    jkt: Optional[str] = Field(
        default=None,
        description="DPoP key thumbprint for proof-of-possession",
    )

    # Verification tracking
    last_verified: Optional[datetime] = Field(
        default=None,
        description="Last user verification timestamp",
    )

    verification_count: int = Field(
        default=0,
        description="Number of verifications",
    )

    # Revocation audit
    revoked_by: Optional[str] = Field(default=None, description="Identity who revoked")
    revoked_at: Optional[datetime] = Field(default=None, description="Revocation timestamp")
    revocation_reason: Optional[str] = Field(default=None, description="Why delegation was revoked")

    # Protocol version
    protocol_version: str = Field(default=DELEGATION_PROTOCOL_VERSION)

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # =========================================================================
    # Validators
    # =========================================================================

    @field_validator("id", "user_id", "agent_id", "created_by")
    @classmethod
    def validate_non_empty(cls, v: str, info: Any) -> str:
        """Ensure required string fields are not empty."""
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()

    @field_validator("user_id", "agent_id")
    @classmethod
    def validate_identity_format(cls, v: str, info: Any) -> str:
        """Validate identity format.

        Supports multiple formats per Neo4j schema:
        - auth:<type>:<provider>:<id>  (e.g., auth:account:empowernow:bob)
        - <type>:<id>                   (e.g., person:patrick-parker)
        - <type>:<provider>:<id>        (e.g., agent:ai-travel)
        """
        parts = v.split(":")
        if len(parts) < 2:
            raise ValueError(
                f"{info.field_name} must be a valid identity format "
                f"(e.g., 'auth:account:provider:id' or 'person:id'), got: {v}"
            )
        # First part should be a type identifier
        identity_type = parts[0]
        if not identity_type or not identity_type.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"{info.field_name} type '{identity_type}' is invalid")
        return v

    @field_validator("protocol_version")
    @classmethod
    def validate_protocol_version(cls, v: str) -> str:
        """Ensure protocol version is supported."""
        if not is_version_supported(v):
            raise ValueError(f"Unsupported protocol version: {v}. Supported: {SUPPORTED_VERSIONS}")
        return v

    # =========================================================================
    # Methods
    # =========================================================================

    def is_active(self) -> bool:
        """Check if delegation is currently active (status + expiry).

        Returns:
            True if status is ACTIVE and not expired.
        """
        if self.status != DelegationStatus.ACTIVE:
            return False

        if self.expires_at is not None:
            now = datetime.now(timezone.utc)
            expires = self.expires_at
            # Handle naive datetimes
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if now > expires:
                return False

        # Check valid_from if set
        if self.valid_from is not None:
            now = datetime.now(timezone.utc)
            valid_from = self.valid_from
            if valid_from.tzinfo is None:
                valid_from = valid_from.replace(tzinfo=timezone.utc)
            if now < valid_from:
                return False

        return True

    def allows_capability(self, tool_id: str) -> Tuple[bool, Optional[str]]:
        """Check if tool is allowed by capability patterns.

        This delegates to the capability module to perform pattern matching.

        Args:
            tool_id: The tool ID to check.

        Returns:
            Tuple of (allowed: bool, matched_pattern: Optional[str])
        """
        # Import here to avoid circular dependency
        from .capability import capability_allowed_with_match

        return capability_allowed_with_match(
            tool_id,
            self.capability_ids,
            self.deny_capability_ids,
            self.trust_level,
        )

    def time_until_expiry(self) -> Optional[float]:
        """Get seconds until expiry, or None if no expiry set.

        Returns:
            Seconds until expiry, or None if expires_at is not set.
        """
        if self.expires_at is None:
            return None

        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        return max(0.0, (expires - now).total_seconds())

    # Convenience properties for backward compatibility
    @property
    def delegator_arn(self) -> str:
        """Alias for user_id (backward compatibility)."""
        return self.user_id

    @property
    def delegate_arn(self) -> str:
        """Alias for agent_id (backward compatibility)."""
        return self.agent_id


# =============================================================================
# Request/Response Models
# =============================================================================


class DelegationVerifyRequest(BaseModel):
    """Request to verify a delegation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    delegator_arn: str = Field(..., description="ARN of the delegating user")
    delegate_arn: str = Field(..., description="ARN of the delegate agent")
    tool_id: Optional[str] = Field(None, description="Tool ID to check capability for")
    protocol_version: str = Field(default=DELEGATION_PROTOCOL_VERSION)


class DelegationVerifyResponse(BaseModel):
    """Response from delegation verification."""

    model_config = ConfigDict(str_strip_whitespace=True)

    delegation: Optional[Delegation] = None
    allowed: bool
    reason: Optional[str] = None
    reason_code: Optional[str] = None
    matched_pattern: Optional[str] = None
    protocol_version: str = Field(default=DELEGATION_PROTOCOL_VERSION)


# Update forward references
EnforceResult.model_rebuild()


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
]
