"""CDA Constants and Configuration.

Shared constants for Contract-Driven Autonomy (CDA) x-field processing.
These constants define the canonical set of CDA x-fields and their behaviors
used across MCP Gateway and CRUDService.

CDA x-fields enable declarative tool configuration:
- Runtime behavior (defaults, normalization, validation)
- User experience (elicitation prompts, suggestions)
- Security/governance (risk levels, redaction, confirmation)

Copyright (c) 2026 EmpowerNow. All rights reserved.
"""

from __future__ import annotations

from enum import Enum
from typing import FrozenSet, Final


# =============================================================================
# CDA x-Field Categories
# =============================================================================

CDA_TRANSFORM_FIELDS: Final[FrozenSet[str]] = frozenset({
    "x-suggest",
    "x-default",
})
"""x-fields that transform into standard JSON Schema (Level 0 compatibility).

These fields are converted to standard JSON Schema properties during tools/list:
- x-suggest (static list) → enum
- x-default → default

This enables any MCP client to benefit from these features without
understanding CDA-specific extensions.
"""

CDA_PRESERVE_FIELDS: Final[FrozenSet[str]] = frozenset({
    "x-normalize",
    "x-redact",
    "x-elicit",
    "x-risk",
    "x-confirm-message",
})
"""x-fields preserved for server-side processing (Level 1+ features).

These fields are NOT transformed to standard JSON Schema but are used
by the Gate Planner during tool invocation for:
- x-normalize: Value canonicalization
- x-redact: Sensitive data masking
- x-elicit: Missing parameter prompts
- x-risk: Risk-based confirmation
- x-confirm-message: Custom confirmation text
"""

CDA_ALL_FIELDS: Final[FrozenSet[str]] = CDA_TRANSFORM_FIELDS | CDA_PRESERVE_FIELDS
"""All recognized CDA x-fields (transform + preserve)."""

CDA_EXTENDED_FIELDS: Final[FrozenSet[str]] = frozenset({
    "x-extract",
    "x-compose",
    "x-decompose",
    "x-default-when",
    "x-next-actions",
})
"""Extended x-fields (CRUDService-specific, not in shared SDK).

These fields require execution context not available at the Gateway layer:
- x-extract: Entity extraction from LLM conversation context
- x-compose: Template composition with execution-time variables
- x-decompose: Value decomposition into multiple fields
- x-default-when: Conditional defaults based on pattern matching
- x-next-actions: Suggested follow-up actions after tool success
"""


# =============================================================================
# Risk Levels
# =============================================================================

class RiskLevel(str, Enum):
    """Tool risk levels for CDA gating.

    Risk levels determine what gating is required before execution.
    Per CDA design, this is a UX gate, not a cryptographic security boundary.
    PDP authorization is always the authoritative security check.

    Levels:
        READ: No gating required (read-only operations)
        LOW: No gating required (safe write operations)
        MEDIUM: Confirmation recommended
        HIGH: Confirmation required
        CRITICAL: Requires WAITING protocol / enterprise approval
    """

    READ = "read"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_string(cls, value: str | None) -> RiskLevel | None:
        """Parse risk level from string (case-insensitive).

        Args:
            value: Risk level string or None

        Returns:
            RiskLevel enum or None if invalid/missing

        Example:
            >>> RiskLevel.from_string("HIGH")
            <RiskLevel.HIGH: 'high'>
            >>> RiskLevel.from_string("invalid")
            None
        """
        if not value:
            return None
        try:
            return cls(value.lower().strip())
        except ValueError:
            return None

    def requires_confirmation(self) -> bool:
        """Check if this risk level requires user confirmation.

        Returns:
            True if user must confirm before execution (MEDIUM, HIGH, CRITICAL)
        """
        return self in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL)

    def requires_waiting(self) -> bool:
        """Check if this risk level requires WAITING protocol.

        The WAITING protocol enables enterprise approval workflows for
        critical operations that cannot be auto-confirmed.

        Returns:
            True if WAITING protocol required (CRITICAL only)
        """
        return self == RiskLevel.CRITICAL

    def __str__(self) -> str:
        """Return the risk level value for display."""
        return self.value


# =============================================================================
# Gate Actions
# =============================================================================

class GateAction(str, Enum):
    """Actions the CDA Gate Planner can recommend.

    These are the possible outcomes of CDA gate evaluation. The caller
    (Gateway or CRUDService) handles each action appropriately based
    on the transport protocol and client capabilities.

    Actions:
        EXECUTE: Ready to execute the tool
        NEED_FORM_INPUT: Need form elicitation for missing/invalid params
        NEED_URL_INPUT: Need URL elicitation for sensitive params (x-redact)
        NEED_CONFIRM: Need risk confirmation before execution
        REQUIRE_WAITING: Requires WAITING protocol (critical risk only)
        FAIL_TOOL_ERROR: Return tool error (isError: true) to model
    """

    EXECUTE = "execute"
    NEED_FORM_INPUT = "need_form_input"
    NEED_URL_INPUT = "need_url_input"
    NEED_CONFIRM = "need_confirm"
    REQUIRE_WAITING = "require_waiting"
    FAIL_TOOL_ERROR = "fail_tool_error"

    def is_terminal(self) -> bool:
        """Check if this action terminates the gating flow.

        Returns:
            True if no further gating iterations are possible
        """
        return self in (
            GateAction.EXECUTE,
            GateAction.REQUIRE_WAITING,
            GateAction.FAIL_TOOL_ERROR,
        )

    def requires_user_interaction(self) -> bool:
        """Check if this action requires user interaction.

        Returns:
            True if the action needs user input/confirmation
        """
        return self in (
            GateAction.NEED_FORM_INPUT,
            GateAction.NEED_URL_INPUT,
            GateAction.NEED_CONFIRM,
        )


# =============================================================================
# Limits and Thresholds
# =============================================================================

MAX_ENUM_VALUES: Final[int] = 100
"""Maximum enum values to include in schema enhancement.

MCP spec recommends limiting enum dropdowns for usability.
Values beyond this limit are truncated during schema enhancement.
"""

MAX_DISPLAY_VALUE_LENGTH: Final[int] = 50
"""Maximum display length for argument values in confirmation messages.

Longer values are truncated with ellipsis for readability.
"""

MAX_ELICITATION_ROUNDS: Final[int] = 5
"""Maximum elicitation rounds before failing.

Prevents infinite loops in gating flow when user keeps providing
invalid input or cancelling.
"""

ELICITABLE_TYPES: Final[FrozenSet[str]] = frozenset({
    "string",
    "number",
    "integer",
    "boolean",
})
"""JSON Schema types that can be elicited via MCP form mode.

MCP elicitation schema is limited to flat objects with primitive types.
Complex types (objects, arrays) cannot be elicited via form mode.
"""


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Field categories
    "CDA_TRANSFORM_FIELDS",
    "CDA_PRESERVE_FIELDS",
    "CDA_ALL_FIELDS",
    "CDA_EXTENDED_FIELDS",
    # Enums
    "RiskLevel",
    "GateAction",
    # Limits
    "MAX_ENUM_VALUES",
    "MAX_DISPLAY_VALUE_LENGTH",
    "MAX_ELICITATION_ROUNDS",
    "ELICITABLE_TYPES",
]
