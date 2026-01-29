"""
Centralized denial reason enum for EmpowerNow services.

Per GAP-016: All services MUST use this enum for denial reasons.
String literals for denial reasons are prohibited in runtime code.

This ensures:
1. Frontend AccessDeniedCard matches backend reason codes exactly
2. No silent UI breakage from backend schema drift
3. Lint rules can enforce usage (no string literal denial patterns)
"""

from enum import Enum


class DenialReason(str, Enum):
    """
    Standardized denial reasons across all EmpowerNow services.

    Each value maps directly to AccessDeniedCard UI components:
    - BUDGET_EXCEEDED -> BudgetExceededCard with meter
    - RATE_LIMITED -> RateLimitedCard with countdown
    - DELEGATION_REQUIRED -> DelegationRequiredCard with settings link
    - TIME_RESTRICTED -> TimeRestrictedCard with schedule
    - MODEL_RESTRICTED -> ModelRestrictedCard with alternatives
    - CONTENT_BLOCKED -> ContentBlockedCard with ML confidence
    - CAPABILITY_NOT_ALLOWED -> CapabilityDeniedCard
    - CANDIDATE_LIMIT_EXCEEDED -> CandidateLimitCard with suggested filters

    Note: Enum values are lowercase snake_case for JSON serialization.
    Do NOT use uppercase (RATE_LIMITED) in API responses - use the .value.
    """

    BUDGET_EXCEEDED = "budget_exceeded"
    RATE_LIMITED = "rate_limited"
    DELEGATION_REQUIRED = "delegation_required"
    TIME_RESTRICTED = "time_restricted"
    MODEL_RESTRICTED = "model_restricted"
    CONTENT_BLOCKED = "content_blocked"
    CAPABILITY_NOT_ALLOWED = "capability_not_allowed"
    CANDIDATE_LIMIT_EXCEEDED = "candidate_limit_exceeded"

    # Generic authorization failure (use specific reasons when possible)
    AUTHORIZATION_DENIED = "authorization_denied"

    def __str__(self) -> str:
        """Return lowercase value for JSON serialization."""
        return self.value
