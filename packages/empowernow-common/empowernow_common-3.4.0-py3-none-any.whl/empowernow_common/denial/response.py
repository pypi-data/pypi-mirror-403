"""
Denial response models for EmpowerNow services.

Per GAP-016: All denial responses MUST use these Pydantic models to ensure
consistent payload shapes that the frontend AccessDeniedCard can parse.

Contract tests validate that API responses match these schemas.
"""

from datetime import datetime
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from empowernow_common.denial.reasons import DenialReason


class BudgetExceededData(BaseModel):
    """
    Data payload for BUDGET_EXCEEDED denial.

    Frontend: Renders budget meter with color gradients.
    - Green at <80%
    - Yellow at 80-99%
    - Red at 100%
    """

    spent: float = Field(..., description="Amount spent in current period")
    limit: float = Field(..., description="Budget limit for the period")
    reset_at: datetime = Field(..., description="When budget resets")
    currency: str = Field(default="USD", description="Currency code")

    @property
    def percentage(self) -> float:
        """Calculate usage percentage."""
        if self.limit <= 0:
            return 100.0
        return min((self.spent / self.limit) * 100, 100.0)


class RateLimitedData(BaseModel):
    """
    Data payload for RATE_LIMITED denial.

    Frontend: Renders countdown timer with pulsing animation.
    """

    retry_after_seconds: int = Field(
        ..., description="Seconds until rate limit resets", ge=0
    )
    limit: Optional[int] = Field(None, description="Requests per window")
    window_seconds: Optional[int] = Field(None, description="Rate limit window size")
    current_count: Optional[int] = Field(None, description="Current request count")


class DelegationRequiredData(BaseModel):
    """
    Data payload for DELEGATION_REQUIRED denial.

    Frontend: Shows delegation card with "Configure Delegation" link.
    """

    permission: str = Field(..., description="Permission that requires delegation")
    agent_id: str = Field(..., description="Agent requiring delegation")
    agent_name: Optional[str] = Field(None, description="Human-readable agent name")
    delegator_arn: Optional[str] = Field(
        None, description="Who can grant the delegation"
    )


class TimeRestrictedData(BaseModel):
    """
    Data payload for TIME_RESTRICTED denial.

    Frontend: Shows allowed hours and next availability window.
    """

    allowed_hours: str = Field(
        ..., description="Human-readable allowed time window (e.g., '9AM-5PM EST')"
    )
    available_at: datetime = Field(
        ..., description="Next time access will be available"
    )
    timezone: str = Field(default="UTC", description="Timezone for allowed_hours")


class ModelRestrictedData(BaseModel):
    """
    Data payload for MODEL_RESTRICTED denial.

    Frontend: Shows current model and alternatives.
    """

    requested_model: str = Field(..., description="Model that was requested")
    allowed_models: list[str] = Field(
        default_factory=list, description="Models the user can access"
    )
    reason: Optional[str] = Field(
        None, description="Why the model is restricted (e.g., 'tier', 'policy')"
    )


class ContentBlockedData(BaseModel):
    """
    Data payload for CONTENT_BLOCKED denial.

    Frontend: Shows ML confidence badge with source indicator.
    """

    category: str = Field(..., description="Content category (e.g., 'pii', 'harmful')")
    confidence: float = Field(
        ..., description="ML confidence score (0.0-1.0)", ge=0.0, le=1.0
    )
    source: str = Field(
        default="ml", description="Detection source: 'ml' or 'rule'"
    )
    help_url: Optional[str] = Field(
        None, description="URL for more information about the block"
    )


class CapabilityNotAllowedData(BaseModel):
    """
    Data payload for CAPABILITY_NOT_ALLOWED denial.

    Frontend: Shows which capability was denied.
    """

    capability: str = Field(..., description="Capability that was denied")
    agent_id: str = Field(..., description="Agent that required the capability")
    required_trust_level: Optional[str] = Field(
        None, description="Trust level required for this capability"
    )
    current_trust_level: Optional[str] = Field(
        None, description="User's current trust level with the agent"
    )


class CandidateLimitExceededData(BaseModel):
    """
    Data payload for CANDIDATE_LIMIT_EXCEEDED denial.

    Frontend: Shows actionable guidance for narrowing search.
    Per GAP-013C: Returns suggested filters to help users fix the query.
    """

    candidate_count: int = Field(..., description="Number of candidates returned")
    limit: int = Field(..., description="Maximum allowed candidates")
    suggested_filters: list[str] = Field(
        default_factory=list,
        description="Filter fields that could narrow results (e.g., 'status', 'created_after')",
    )
    resource_type: str = Field(..., description="Type of resource being queried")


# Union type for type-safe data access
DenialDataType = Union[
    BudgetExceededData,
    RateLimitedData,
    DelegationRequiredData,
    TimeRestrictedData,
    ModelRestrictedData,
    ContentBlockedData,
    CapabilityNotAllowedData,
    CandidateLimitExceededData,
    dict[str, Any],  # For extensibility
]


class DenialResponse(BaseModel):
    """
    Standardized denial response for all EmpowerNow services.

    This model ensures consistent API responses that the frontend
    AccessDeniedCard can reliably parse.

    Usage:
        from empowernow_common.denial import DenialResponse, DenialReason, RateLimitedData

        return DenialResponse(
            reason=DenialReason.RATE_LIMITED,
            message="Too many requests",
            data=RateLimitedData(retry_after_seconds=60)
        ).model_dump()
    """

    reason: DenialReason = Field(..., description="Standardized denial reason code")
    message: str = Field(..., description="Human-readable denial message")
    data: DenialDataType = Field(
        default_factory=dict, description="Reason-specific payload data"
    )

    # Optional metadata
    correlation_id: Optional[str] = Field(
        None, description="Request correlation ID for debugging"
    )
    help_url: Optional[str] = Field(
        None, description="URL with more information about resolving the denial"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reason": "rate_limited",
                    "message": "You have exceeded the rate limit. Please try again later.",
                    "data": {"retry_after_seconds": 60},
                },
                {
                    "reason": "budget_exceeded",
                    "message": "Your usage budget has been exceeded.",
                    "data": {
                        "spent": 95.50,
                        "limit": 100.00,
                        "reset_at": "2026-02-01T00:00:00Z",
                    },
                },
            ]
        }
    }

    def to_http_response(self) -> tuple[dict[str, Any], int]:
        """
        Convert to HTTP response tuple (body, status_code).

        Returns 403 Forbidden for authorization denials,
        429 for rate limiting.
        """
        status_code = 403
        if self.reason == DenialReason.RATE_LIMITED:
            status_code = 429

        body = self.model_dump(mode="json")

        # Ensure data is properly serialized (handle Pydantic models)
        if hasattr(self.data, "model_dump"):
            body["data"] = self.data.model_dump(mode="json")

        return body, status_code
