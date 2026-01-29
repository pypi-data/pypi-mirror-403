"""Delegation verification service.

This module provides two distinct verification APIs to enforce the TOCTOU contract:

1. precheck_gateway_bound() - Advisory pre-check for gateway-bound calls
   - Returns: DENY or UNKNOWN only
   - Used by: CRUDService when Gateway is authoritative PEP
   - CANNOT return PERMIT (prevents accidental authorization)

2. enforce_local() - Authoritative enforcement for local calls
   - Returns: PERMIT or DENY with full evidence
   - Used by: CRUD-only mode, or when calling service IS the PEP
   - Full audit trail with matched patterns, source, timing

Usage:
    # Gateway-bound flow (CRUDService is NOT authoritative)
    result = await verifier.precheck_gateway_bound(delegator, delegate, tool_id)
    if result == PreCheckResult.DENY:
        raise DelegationDeniedError(...)
    # If UNKNOWN, continue - Gateway will make final decision

    # CRUD-only flow (CRUDService IS authoritative)
    result = await verifier.enforce_local(delegator, delegate, tool_id)
    if result.decision != EnforceDecision.PERMIT:
        raise DelegationDeniedError(...)
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Optional, Protocol, Tuple

from .exceptions import (
    CapabilityNotAllowedError,
    DelegationError,
    DelegationExpiredError,
    DelegationNotFoundError,
    DelegationRevokedError,
    DelegationSuspendedError,
    DelegationVerificationError,
    ProtocolVersionError,
)
from .models import (
    SUPPORTED_VERSIONS,
    Delegation,
    DelegationStatus,
    DelegationVerifyResponse,
    EnforceDecision,
    EnforceResult,
    PreCheckResult,
    VerificationSource,
)

if TYPE_CHECKING:
    from .cache import DelegationCache

logger = logging.getLogger(__name__)


class MembershipClientProtocol(Protocol):
    """Protocol for membership service client.

    Implement this protocol to integrate with your membership service.
    The verifier uses this to fetch delegations when not in cache.
    """

    async def verify_delegation(
        self,
        delegator_arn: str,
        delegate_arn: str,
        tool_id: Optional[str] = None,
    ) -> DelegationVerifyResponse:
        """Verify a delegation exists and is valid.

        Args:
            delegator_arn: ARN of the delegating user.
            delegate_arn: ARN of the delegate agent.
            tool_id: Optional tool ID to check capability for.

        Returns:
            DelegationVerifyResponse with delegation details.
        """
        ...


class DelegationVerifier:
    """High-level delegation verification with caching.

    Provides two APIs to enforce TOCTOU contract:
    - precheck_gateway_bound(): Advisory, returns DENY|UNKNOWN
    - enforce_local(): Authoritative, returns PERMIT|DENY

    The verifier implements a two-tier cache hierarchy:
    - L1: In-memory per-process cache (very short TTL, ~3s)
    - L2: Redis shared cache (longer TTL, ~30s)

    On cache miss, it fetches from the membership service and populates
    both cache tiers.

    Example:
        verifier = DelegationVerifier(
            membership_client=my_client,
            l1_cache=InMemoryDelegationCache(),
            l2_cache=RedisDelegationCache(redis),
        )

        # Pre-check (advisory)
        result = await verifier.precheck_gateway_bound(
            delegator_arn="auth:account:entra:user@example.com",
            delegate_arn="agent:ai-travel",
            tool_id="tool:jira:create_issue",
        )

        # Enforce (authoritative)
        result = await verifier.enforce_local(
            delegator_arn="auth:account:entra:user@example.com",
            delegate_arn="agent:ai-travel",
            tool_id="tool:jira:create_issue",
            raise_on_deny=True,  # Raises exception on DENY
        )
    """

    def __init__(
        self,
        membership_client: MembershipClientProtocol,
        l1_cache: Optional["DelegationCache"] = None,
        l2_cache: Optional["DelegationCache"] = None,
        strict_protocol_version: bool = True,
    ) -> None:
        """Initialize verifier.

        Args:
            membership_client: Client to fetch delegations from membership service.
            l1_cache: In-memory per-process cache (short TTL, ~3s).
            l2_cache: Redis shared cache (longer TTL, ~30s).
            strict_protocol_version: If True, reject unsupported protocol versions.
        """
        self._client = membership_client
        self._l1_cache = l1_cache
        self._l2_cache = l2_cache
        self._strict_protocol_version = strict_protocol_version

    async def precheck_gateway_bound(
        self,
        delegator_arn: str,
        delegate_arn: str,
        tool_id: Optional[str] = None,
    ) -> PreCheckResult:
        """Advisory pre-check for gateway-bound calls.

        IMPORTANT: This method can ONLY return DENY or UNKNOWN.
        It CANNOT return PERMIT - the gateway is the authoritative PEP.

        Use this when:
        - CRUDService receives a call that will be forwarded to MCP Gateway
        - You want fast fail on obvious denials
        - Gateway will make the final authorization decision

        The pre-check only uses cached data - it does not fetch from the
        membership service. This ensures low latency for the common case.

        Args:
            delegator_arn: ARN of the user who granted delegation.
            delegate_arn: ARN of the agent acting on behalf of user.
            tool_id: Optional tool being accessed.

        Returns:
            PreCheckResult.DENY - Definitely not allowed, fail fast.
            PreCheckResult.UNKNOWN - Uncertain, let gateway decide.
        """
        try:
            # Try L1 cache first (fastest)
            delegation = None
            if self._l1_cache:
                delegation = await self._l1_cache.get(delegator_arn, delegate_arn)

            # Try L2 cache if L1 miss
            if delegation is None and self._l2_cache:
                delegation = await self._l2_cache.get(delegator_arn, delegate_arn)

            # No cached data - can't make a decision
            if delegation is None:
                return PreCheckResult.UNKNOWN

            # Check status
            if delegation.status != DelegationStatus.ACTIVE:
                logger.debug(
                    "Precheck DENY: delegation status is %s for %s->%s",
                    delegation.status,
                    delegator_arn,
                    delegate_arn,
                )
                return PreCheckResult.DENY

            # Check expiry
            if not delegation.is_active():
                logger.debug(
                    "Precheck DENY: delegation expired for %s->%s",
                    delegator_arn,
                    delegate_arn,
                )
                return PreCheckResult.DENY

            # Check capability if tool specified
            if tool_id:
                allowed, _ = delegation.allows_capability(tool_id)
                if not allowed:
                    logger.debug(
                        "Precheck DENY: tool %s not in capabilities for %s->%s",
                        tool_id,
                        delegator_arn,
                        delegate_arn,
                    )
                    return PreCheckResult.DENY

            # Can't definitively permit - return UNKNOWN
            return PreCheckResult.UNKNOWN

        except Exception as e:
            logger.warning("Precheck error (returning UNKNOWN): %s", e)
            return PreCheckResult.UNKNOWN

    async def enforce_local(
        self,
        delegator_arn: str,
        delegate_arn: str,
        tool_id: Optional[str] = None,
        raise_on_deny: bool = False,
    ) -> EnforceResult:
        """Authoritative enforcement for local/CRUD-only calls.

        Use this when:
        - The calling service IS the authoritative PEP
        - CRUD-only mode (no gateway available)
        - You need full audit trail with evidence

        Unlike precheck, this will fetch from the membership service
        if the delegation is not in cache.

        Args:
            delegator_arn: ARN of the user who granted delegation.
            delegate_arn: ARN of the agent acting on behalf of user.
            tool_id: Optional tool being accessed.
            raise_on_deny: If True, raise exception on DENY instead of returning result.

        Returns:
            EnforceResult with decision (PERMIT|DENY) and evidence.

        Raises:
            DelegationError subclass if raise_on_deny=True and decision is DENY.
        """
        start = time.perf_counter()

        try:
            # Lookup with cache hierarchy
            delegation, source, ttl_remaining = await self._lookup_delegation(
                delegator_arn, delegate_arn
            )

            verification_time_ms = (time.perf_counter() - start) * 1000

            if delegation is None:
                result = EnforceResult.deny(
                    reason_code="DELEGATION_NOT_FOUND",
                    reason_detail=f"No delegation from {delegator_arn} to {delegate_arn}",
                    source=source,
                    verification_time_ms=verification_time_ms,
                )
            else:
                result = self._validate_delegation(
                    delegation, tool_id, source, ttl_remaining, verification_time_ms
                )

            if raise_on_deny and result.decision == EnforceDecision.DENY:
                self._raise_denial_error(result, delegator_arn, delegate_arn, tool_id)

            return result

        except DelegationError:
            raise
        except Exception as e:
            logger.exception("Enforcement error: %s", e)
            raise DelegationVerificationError(
                f"Verification failed: {e}",
                cause=e,
                delegator_arn=delegator_arn,
                delegate_arn=delegate_arn,
            ) from e

    async def _lookup_delegation(
        self,
        delegator_arn: str,
        delegate_arn: str,
    ) -> Tuple[Optional[Delegation], VerificationSource, Optional[float]]:
        """Look up delegation through cache hierarchy.

        Cache lookup order:
        1. L1 (in-memory, per-process) - fastest
        2. L2 (Redis, shared) - fast
        3. Membership service - authoritative

        Args:
            delegator_arn: ARN of the delegating user.
            delegate_arn: ARN of the delegate agent.

        Returns:
            Tuple of (delegation, source, ttl_remaining).
        """
        # L1 cache (in-memory, per-process)
        if self._l1_cache:
            delegation = await self._l1_cache.get(delegator_arn, delegate_arn)
            if delegation is not None:
                ttl = await self._l1_cache.get_ttl(delegator_arn, delegate_arn)
                return (delegation, VerificationSource.L1_CACHE, ttl)

        # L2 cache (Redis, shared)
        if self._l2_cache:
            delegation = await self._l2_cache.get(delegator_arn, delegate_arn)
            if delegation is not None:
                ttl = await self._l2_cache.get_ttl(delegator_arn, delegate_arn)
                # Populate L1 on L2 hit
                if self._l1_cache:
                    await self._l1_cache.set(delegator_arn, delegate_arn, delegation, ttl=3)
                return (delegation, VerificationSource.L2_CACHE, ttl)

        # Fetch from membership service
        response = await self._client.verify_delegation(
            delegator_arn=delegator_arn,
            delegate_arn=delegate_arn,
        )

        # Validate protocol version
        if self._strict_protocol_version:
            if response.protocol_version not in SUPPORTED_VERSIONS:
                raise ProtocolVersionError(
                    f"Unsupported protocol version: {response.protocol_version}",
                    expected_versions=SUPPORTED_VERSIONS,
                    received_version=response.protocol_version,
                )

        delegation = response.delegation

        # Populate caches
        if delegation:
            if self._l2_cache:
                await self._l2_cache.set(delegator_arn, delegate_arn, delegation, ttl=30)
            if self._l1_cache:
                await self._l1_cache.set(delegator_arn, delegate_arn, delegation, ttl=3)
        elif self._l2_cache:
            # Negative cache (shorter TTL)
            await self._l2_cache.set_negative(delegator_arn, delegate_arn, ttl=10)

        return (delegation, VerificationSource.MEMBERSHIP, None)

    def _validate_delegation(
        self,
        delegation: Delegation,
        tool_id: Optional[str],
        source: VerificationSource,
        ttl_remaining: Optional[float],
        verification_time_ms: float,
    ) -> EnforceResult:
        """Validate a delegation and return enforcement result.

        Args:
            delegation: The delegation to validate.
            tool_id: Optional tool ID to check capability for.
            source: Where the delegation came from.
            ttl_remaining: Remaining TTL if from cache.
            verification_time_ms: How long verification took.

        Returns:
            EnforceResult with PERMIT or DENY.
        """
        # Check status
        if delegation.status == DelegationStatus.REVOKED:
            return EnforceResult.deny(
                reason_code="DELEGATION_REVOKED",
                reason_detail="Delegation has been revoked",
                delegation=delegation,
                source=source,
                verification_time_ms=verification_time_ms,
            )

        if delegation.status == DelegationStatus.SUSPENDED:
            return EnforceResult.deny(
                reason_code="DELEGATION_SUSPENDED",
                reason_detail="Delegation is suspended",
                delegation=delegation,
                source=source,
                verification_time_ms=verification_time_ms,
            )

        if delegation.status == DelegationStatus.EXPIRED:
            return EnforceResult.deny(
                reason_code="DELEGATION_EXPIRED",
                reason_detail="Delegation has expired",
                delegation=delegation,
                source=source,
                verification_time_ms=verification_time_ms,
            )

        if delegation.status == DelegationStatus.PENDING:
            return EnforceResult.deny(
                reason_code="DELEGATION_PENDING",
                reason_detail="Delegation is pending approval",
                delegation=delegation,
                source=source,
                verification_time_ms=verification_time_ms,
            )

        if delegation.status != DelegationStatus.ACTIVE:
            return EnforceResult.deny(
                reason_code="DELEGATION_INVALID_STATUS",
                reason_detail=f"Delegation status is {delegation.status}",
                delegation=delegation,
                source=source,
                verification_time_ms=verification_time_ms,
            )

        # Check expiry and valid_from
        if not delegation.is_active():
            return EnforceResult.deny(
                reason_code="DELEGATION_EXPIRED",
                reason_detail="Delegation has expired or is not yet valid",
                delegation=delegation,
                source=source,
                verification_time_ms=verification_time_ms,
            )

        # Check capability if tool specified
        matched_pattern = None
        if tool_id:
            allowed, matched_pattern = delegation.allows_capability(tool_id)
            if not allowed:
                return EnforceResult.deny(
                    reason_code="CAPABILITY_NOT_ALLOWED",
                    reason_detail=f"Tool '{tool_id}' not allowed by delegation capabilities",
                    delegation=delegation,
                    source=source,
                    verification_time_ms=verification_time_ms,
                )

        # All checks passed
        return EnforceResult.permit(
            delegation=delegation,
            matched_pattern=matched_pattern,
            source=source,
            verification_time_ms=verification_time_ms,
            ttl_remaining=ttl_remaining,
        )

    # =========================================================================
    # Public Helper Methods (P1 Enhancement)
    # =========================================================================

    async def get_delegation(
        self,
        delegator_arn: str,
        delegate_arn: str,
    ) -> Optional[Delegation]:
        """Get the delegation between delegator and delegate (public API).

        This is a convenience method for cases where you need the raw
        delegation object, e.g., for tool filtering or UI display.

        Args:
            delegator_arn: ARN of the delegating user.
            delegate_arn: ARN of the delegate agent.

        Returns:
            Delegation object if found, None otherwise.

        Example:
            delegation = await verifier.get_delegation(user_arn, agent_arn)
            if delegation:
                print(f"Trust level: {delegation.trust_level}")
        """
        delegation, _, _ = await self._lookup_delegation(delegator_arn, delegate_arn)
        return delegation

    def filter_tools_by_capability(
        self,
        tool_ids: list[str],
        capability_patterns: Optional[list[str]],
        deny_patterns: Optional[list[str]] = None,
        trust_level: "TrustLevel" = None,
    ) -> list[str]:
        """Filter tool IDs to only those allowed by capability patterns (public API).

        This is a convenience method for filtering available tools based on
        a delegation's capability_ids. Use this instead of accessing internal
        pattern matching methods.

        Args:
            tool_ids: List of tool IDs to filter.
            capability_patterns: Allowed capability patterns (from delegation.capability_ids).
            deny_patterns: Denied capability patterns (from delegation.deny_capability_ids).
            trust_level: Trust level for full-trust handling.

        Returns:
            List of tool IDs that are allowed.

        Example:
            delegation = await verifier.get_delegation(user_arn, agent_arn)
            if delegation:
                allowed_tools = verifier.filter_tools_by_capability(
                    all_tools,
                    delegation.capability_ids,
                    delegation.deny_capability_ids,
                    delegation.trust_level,
                )
        """
        # Import here to avoid circular dependency at module level
        from .capability import filter_allowed_tools
        from .models import TrustLevel as TL

        effective_trust = trust_level if trust_level is not None else TL.BASIC

        return filter_allowed_tools(
            tool_ids,
            capability_patterns,
            deny_patterns,
            effective_trust,
        )

    def _raise_denial_error(
        self,
        result: EnforceResult,
        delegator_arn: str,
        delegate_arn: str,
        tool_id: Optional[str],
    ) -> None:
        """Raise appropriate exception for denial.

        Args:
            result: The denial result.
            delegator_arn: ARN of the delegating user.
            delegate_arn: ARN of the delegate agent.
            tool_id: Optional tool ID that was denied.

        Raises:
            Appropriate DelegationError subclass.
        """
        d = result.delegation

        if d is None:
            raise DelegationNotFoundError(
                "No delegation found",
                delegator_arn=delegator_arn,
                delegate_arn=delegate_arn,
            )

        if result.reason_code == "DELEGATION_REVOKED":
            raise DelegationRevokedError(
                "Delegation has been revoked",
                delegation_id=d.id,
                delegator_arn=delegator_arn,
                delegate_arn=delegate_arn,
                revoked_at=str(d.revoked_at) if d.revoked_at else None,
                revoked_by=d.revoked_by,
            )

        if result.reason_code == "DELEGATION_SUSPENDED":
            raise DelegationSuspendedError(
                "Delegation is suspended",
                delegation_id=d.id,
                delegator_arn=delegator_arn,
                delegate_arn=delegate_arn,
            )

        if result.reason_code == "DELEGATION_EXPIRED":
            raise DelegationExpiredError(
                "Delegation has expired",
                delegation_id=d.id,
                expired_at=str(d.expires_at) if d.expires_at else "unknown",
                delegator_arn=delegator_arn,
                delegate_arn=delegate_arn,
            )

        if result.reason_code == "CAPABILITY_NOT_ALLOWED" and tool_id:
            raise CapabilityNotAllowedError(
                f"Tool '{tool_id}' not allowed by delegation",
                tool_id=tool_id,
                delegation_id=d.id,
                delegator_arn=delegator_arn,
                delegate_arn=delegate_arn,
            )

        raise DelegationError(
            result.reason_detail or "Delegation denied",
            reason_code=result.reason_code,
            delegator_arn=delegator_arn,
            delegate_arn=delegate_arn,
        )


__all__ = [
    "MembershipClientProtocol",
    "DelegationVerifier",
    # Public helper methods are on DelegationVerifier class:
    # - get_delegation(delegator_arn, delegate_arn) -> Optional[Delegation]
    # - filter_tools_by_capability(tool_ids, patterns, deny_patterns, trust) -> list[str]
]
