"""
Denial response normalization for EmpowerNow services.

This module provides centralized denial reason enum and response models
to ensure consistent denial responses across all services.

Per GAP-016: All services must use DenialReason from this module instead
of string literals to prevent frontend/backend contract drift.

Usage:
    from empowernow_common.denial import DenialReason, DenialResponse

    # Create a denial response
    response = DenialResponse(
        reason=DenialReason.RATE_LIMITED,
        message="You have exceeded the rate limit",
        data={"retry_after_seconds": 60}
    )

    # Serialize for API response
    return response.model_dump()
"""

from empowernow_common.denial.reasons import DenialReason
from empowernow_common.denial.response import (
    DenialResponse,
    BudgetExceededData,
    RateLimitedData,
    DelegationRequiredData,
    TimeRestrictedData,
    ModelRestrictedData,
    ContentBlockedData,
    CapabilityNotAllowedData,
    CandidateLimitExceededData,
)

__all__ = [
    "DenialReason",
    "DenialResponse",
    "BudgetExceededData",
    "RateLimitedData",
    "DelegationRequiredData",
    "TimeRestrictedData",
    "ModelRestrictedData",
    "ContentBlockedData",
    "CapabilityNotAllowedData",
    "CandidateLimitExceededData",
]
