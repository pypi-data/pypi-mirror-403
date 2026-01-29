"""CDA Gate Planner.

Single deterministic function that analyzes tool calls and produces next-step
actions. This is the SINGLE source of truth for CDA gating logic, ensuring
consistent behavior across MCP Gateway and CRUDService.

The Gate Planner evaluates tool calls in this order:
1. Apply x-default values to arguments
2. Apply x-normalize transformations (built-in only)
3. Check for missing required parameters
4. Separate sensitive (x-redact) vs regular missing params
5. Check risk level (x-risk) for confirmation requirements
6. Determine final action

Usage:
    from empowernow_common.mcp.cda import CDAGatePlanner, GateAction

    planner = CDAGatePlanner(tool_schema)
    result = planner.plan(arguments)

    match result.action:
        case GateAction.EXECUTE:
            # Execute tool with result.resolved_args
        case GateAction.NEED_FORM_INPUT:
            # Send elicitation with result.missing_params
        case GateAction.NEED_CONFIRM:
            # Show confirmation with result.confirm_message

Copyright (c) 2026 EmpowerNow. All rights reserved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Final, List, Optional, Set, Tuple

from .constants import (
    ELICITABLE_TYPES,
    GateAction,
    MAX_DISPLAY_VALUE_LENGTH,
    RiskLevel,
)
from .normalizers import apply_normalization, is_builtin_normalizer


# =============================================================================
# Data Classes
# =============================================================================

@dataclass(frozen=True, slots=True)
class MissingParam:
    """Information about a missing required parameter.

    Used to build elicitation requests and error messages.

    Attributes:
        name: Parameter name
        param_schema: JSON Schema for the parameter
        x_elicit: Elicitation prompt from x-elicit field (if any)
        is_sensitive: Whether parameter is marked x-redact
        is_elicitable: Whether parameter type supports form elicitation
    """

    name: str
    param_schema: Dict[str, Any]
    x_elicit: Optional[str] = None
    is_sensitive: bool = False
    is_elicitable: bool = True

    @property
    def description(self) -> str:
        """Get parameter description for display."""
        return (
            self.x_elicit
            or self.param_schema.get("description")
            or self.param_schema.get("title")
            or self.name
        )


@dataclass(slots=True)
class GatePlanResult:
    """Output of CDA Gate Planner.

    Contains the recommended action and all data needed to execute it.
    Callers should switch on the `action` field to determine next steps.

    Attributes:
        action: The recommended GateAction
        resolved_args: Arguments after defaults and normalization applied
        missing_params: List of missing required parameters
        requested_schema: JSON Schema for form elicitation
        message: User-facing message explaining the action
        url: URL for URL-based elicitation
        elicitation_id: Unique ID for tracking elicitation state
        error_message: Error message for FAIL_TOOL_ERROR
        risk_level: Risk level that triggered confirmation
        confirm_message: Confirmation message for NEED_CONFIRM
    """

    action: GateAction

    # Always populated
    resolved_args: Dict[str, Any] = field(default_factory=dict)

    # For NEED_FORM_INPUT / NEED_URL_INPUT
    missing_params: List[MissingParam] = field(default_factory=list)
    requested_schema: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

    # For NEED_URL_INPUT
    url: Optional[str] = None
    elicitation_id: Optional[str] = None

    # For FAIL_TOOL_ERROR / REQUIRE_WAITING
    error_message: Optional[str] = None

    # For NEED_CONFIRM
    risk_level: Optional[RiskLevel] = None
    confirm_message: Optional[str] = None


# =============================================================================
# Schema Key Constants
# =============================================================================

_INPUT_SCHEMA_KEYS: Final[Tuple[str, str]] = ("inputSchema", "input_schema")
_MCP_KEYS: Final[Tuple[str, str]] = ("mcp", "metadata")


# =============================================================================
# CDA Gate Planner Class
# =============================================================================

class CDAGatePlanner:
    """Single deterministic function that analyzes tool call and produces next action.

    This is the SINGLE source of truth for CDA gating logic. All CDA-related
    decisions flow through this planner, ensuring consistent behavior across
    MCP Gateway and CRUDService.

    Thread-safe: No mutable instance state. Safe for concurrent use.
    Deterministic: Same inputs always produce same outputs.

    Example:
        planner = CDAGatePlanner(
            tool_schema=tool_def,
            supports_elicitation=True,
        )
        result = planner.plan({"user_id": "john"})

        if result.action == GateAction.EXECUTE:
            execute_tool(result.resolved_args)
        elif result.action == GateAction.NEED_FORM_INPUT:
            send_elicitation(result.requested_schema, result.message)
    """

    __slots__ = (
        "_schema",
        "_supports_elicitation",
        "_supports_url_elicitation",
        "_input_schema",
        "_properties",
        "_required",
        "_risk_level",
        "_confirm_message",
        "_tool_name",
    )

    def __init__(
        self,
        tool_schema: Dict[str, Any],
        supports_elicitation: bool = False,
        supports_url_elicitation: bool = False,
    ) -> None:
        """Initialize the Gate Planner for a specific tool.

        Args:
            tool_schema: Complete tool definition including inputSchema and mcp metadata
            supports_elicitation: Whether the client supports MCP form elicitation
            supports_url_elicitation: Whether the client supports MCP URL elicitation

        Example:
            # For MCP Gateway with client capabilities from session
            planner = CDAGatePlanner(
                tool_schema=tool_def,
                supports_elicitation=session.supports_elicitation,
                supports_url_elicitation=session.supports_url_elicitation,
            )
        """
        self._schema = tool_schema
        self._supports_elicitation = supports_elicitation
        self._supports_url_elicitation = supports_url_elicitation

        # Extract tool name
        self._tool_name: str = tool_schema.get("name", "unknown_tool")

        # Extract input schema (support both naming conventions)
        self._input_schema = self._extract_input_schema(tool_schema)
        self._properties: Dict[str, Any] = self._input_schema.get("properties", {})
        self._required: Set[str] = set(self._input_schema.get("required", []))

        # Extract tool-level metadata
        self._risk_level, self._confirm_message = self._extract_risk_metadata(tool_schema)

    @staticmethod
    def _extract_input_schema(tool_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract input schema from tool definition."""
        for key in _INPUT_SCHEMA_KEYS:
            schema = tool_schema.get(key)
            if isinstance(schema, dict):
                return schema
        return {}

    @staticmethod
    def _extract_risk_metadata(
        tool_schema: Dict[str, Any],
    ) -> Tuple[Optional[RiskLevel], Optional[str]]:
        """Extract risk level and confirm message from tool metadata."""
        risk_level: Optional[RiskLevel] = None
        confirm_message: Optional[str] = None

        for key in _MCP_KEYS:
            section = tool_schema.get(key)
            if not isinstance(section, dict):
                continue

            if risk_level is None and "x-risk" in section:
                risk_level = RiskLevel.from_string(section["x-risk"])

            if confirm_message is None and "x-confirm-message" in section:
                confirm_message = section["x-confirm-message"]

        return risk_level, confirm_message

    def plan(
        self,
        args: Optional[Dict[str, Any]] = None,
        already_confirmed: bool = False,
    ) -> GatePlanResult:
        """Evaluate a tool call and determine the next action.

        This is the main entry point for CDA gating. Call this method
        with the current arguments to get the next action to take.

        Args:
            args: Current tool arguments (may be partial or empty)
            already_confirmed: Whether risk has already been confirmed by user

        Returns:
            GatePlanResult with action and supporting data

        Example:
            # Initial call
            result = planner.plan({"user_id": "john"})

            # After elicitation
            result = planner.plan({"user_id": "john", "action": "disable"})

            # After confirmation
            result = planner.plan(args, already_confirmed=True)
        """
        # Start with a copy of args (or empty dict)
        resolved = dict(args) if args else {}

        # Step 1: Apply x-default values
        resolved = self._apply_defaults(resolved)

        # Step 2: Apply x-normalize (built-in normalizers only)
        resolved = self._apply_normalizations(resolved)

        # Step 3: Check for missing required parameters
        missing = self._check_missing_required(resolved)

        # Step 4: Separate sensitive vs regular missing params
        sensitive_missing = [p for p in missing if p.is_sensitive]
        regular_missing = [p for p in missing if not p.is_sensitive]

        # Step 5: Determine action based on state

        # 5a: If sensitive params missing
        if sensitive_missing:
            return self._handle_sensitive_missing(resolved, sensitive_missing)

        # 5b: If regular params missing
        if regular_missing:
            return self._handle_regular_missing(resolved, regular_missing)

        # 5c: If risk requires confirmation and not yet confirmed
        if self._needs_confirmation(already_confirmed):
            return self._handle_risk_confirmation(resolved)

        # 5d: Ready to execute
        return GatePlanResult(
            action=GateAction.EXECUTE,
            resolved_args=resolved,
        )

    def _apply_defaults(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Apply x-default values for missing arguments.

        Checks both x-default (CDA) and default (JSON Schema) fields.
        """
        result = dict(args)

        for prop_name, prop_schema in self._properties.items():
            if not isinstance(prop_schema, dict):
                continue

            # Skip if value already provided
            if prop_name in result and result[prop_name] is not None:
                continue

            # Check x-default first (CDA), then standard default
            if "x-default" in prop_schema:
                result[prop_name] = prop_schema["x-default"]
            elif "default" in prop_schema:
                result[prop_name] = prop_schema["default"]

        return result

    def _apply_normalizations(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Apply x-normalize transformations (built-in only).

        Tool-based normalizations (email, phone, etc.) must be handled
        by the service layer after gate planning.
        """
        result = dict(args)

        for prop_name, prop_schema in self._properties.items():
            if not isinstance(prop_schema, dict):
                continue

            if prop_name not in result:
                continue

            x_normalize = prop_schema.get("x-normalize")
            if not x_normalize or not isinstance(x_normalize, str):
                continue

            # Only apply built-in normalizers (tool-based handled by service layer)
            if is_builtin_normalizer(x_normalize):
                result[prop_name] = apply_normalization(
                    result[prop_name],
                    x_normalize,
                )

        return result

    def _check_missing_required(self, args: Dict[str, Any]) -> List[MissingParam]:
        """Check for missing required parameters."""
        missing: List[MissingParam] = []

        for prop_name in self._required:
            value = args.get(prop_name)

            # Check if missing or effectively empty
            if self._is_value_missing(value):
                prop_schema = self._properties.get(prop_name, {})
                missing.append(self._create_missing_param(prop_name, prop_schema))

        return missing

    @staticmethod
    def _is_value_missing(value: Any) -> bool:
        """Check if a value should be considered missing."""
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        return False

    def _create_missing_param(
        self,
        prop_name: str,
        prop_schema: Dict[str, Any],
    ) -> MissingParam:
        """Create a MissingParam from property schema."""
        prop_type = prop_schema.get("type", "string")

        return MissingParam(
            name=prop_name,
            param_schema=prop_schema,
            x_elicit=prop_schema.get("x-elicit"),
            is_sensitive=bool(prop_schema.get("x-redact")),
            is_elicitable=prop_type in ELICITABLE_TYPES,
        )

    def _needs_confirmation(self, already_confirmed: bool) -> bool:
        """Check if risk confirmation is needed."""
        if already_confirmed:
            return False
        if self._risk_level is None:
            return False
        return self._risk_level.requires_confirmation()

    def _handle_sensitive_missing(
        self,
        resolved: Dict[str, Any],
        sensitive: List[MissingParam],
    ) -> GatePlanResult:
        """Handle missing sensitive parameters (x-redact)."""
        if self._supports_url_elicitation:
            return GatePlanResult(
                action=GateAction.NEED_URL_INPUT,
                resolved_args=resolved,
                missing_params=sensitive,
                message=self._build_sensitive_message(sensitive),
            )

        # Client doesn't support URL elicitation
        return GatePlanResult(
            action=GateAction.FAIL_TOOL_ERROR,
            resolved_args=resolved,
            missing_params=sensitive,
            error_message=(
                f"This operation requires sensitive data "
                f"({', '.join(p.name for p in sensitive)}) that cannot be collected "
                f"via standard elicitation. Please use a client that supports "
                f"URL-based secure input."
            ),
        )

    def _handle_regular_missing(
        self,
        resolved: Dict[str, Any],
        missing: List[MissingParam],
    ) -> GatePlanResult:
        """Handle missing regular (non-sensitive) parameters."""
        if self._supports_elicitation:
            elicitable = [p for p in missing if p.is_elicitable]
            non_elicitable = [p for p in missing if not p.is_elicitable]

            if non_elicitable:
                # Some params can't be elicited via form
                return GatePlanResult(
                    action=GateAction.FAIL_TOOL_ERROR,
                    resolved_args=resolved,
                    missing_params=missing,
                    error_message=self._build_non_elicitable_error(non_elicitable),
                )

            return GatePlanResult(
                action=GateAction.NEED_FORM_INPUT,
                resolved_args=resolved,
                missing_params=elicitable,
                requested_schema=self._build_elicitation_schema(elicitable),
                message=self._build_missing_message(elicitable),
            )

        # No elicitation support - return error for model self-correction
        return GatePlanResult(
            action=GateAction.FAIL_TOOL_ERROR,
            resolved_args=resolved,
            missing_params=missing,
            error_message=self._build_missing_error(missing),
        )

    def _handle_risk_confirmation(
        self,
        resolved: Dict[str, Any],
    ) -> GatePlanResult:
        """Handle risk-based confirmation requirement."""
        assert self._risk_level is not None

        # Critical risk requires WAITING protocol
        if self._risk_level.requires_waiting():
            return GatePlanResult(
                action=GateAction.REQUIRE_WAITING,
                resolved_args=resolved,
                risk_level=self._risk_level,
                error_message=(
                    self._confirm_message
                    or "This operation requires enterprise approval."
                ),
            )

        # Medium/High risk - elicitation-based confirmation
        if self._supports_elicitation:
            confirm_msg = self._confirm_message or self._build_confirm_message(resolved)
            return GatePlanResult(
                action=GateAction.NEED_CONFIRM,
                resolved_args=resolved,
                risk_level=self._risk_level,
                confirm_message=confirm_msg,
                message=confirm_msg,
            )

        # No elicitation - proceed without confirmation
        # (Confirmation is UX, not security boundary. PDP is authoritative.)
        return GatePlanResult(
            action=GateAction.EXECUTE,
            resolved_args=resolved,
        )

    # =========================================================================
    # Message Building
    # =========================================================================

    def _build_elicitation_schema(
        self,
        missing: List[MissingParam],
    ) -> Dict[str, Any]:
        """Build JSON Schema for form elicitation."""
        properties: Dict[str, Any] = {}
        required: List[str] = []

        for param in missing:
            prop = dict(param.param_schema)

            # Use x-elicit as description if not already set
            if param.x_elicit and "description" not in prop:
                prop["description"] = param.x_elicit

            properties[param.name] = prop
            required.append(param.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def _build_missing_message(self, missing: List[MissingParam]) -> str:
        """Build user-friendly message for missing params."""
        if len(missing) == 1:
            param = missing[0]
            return param.x_elicit or f"Please provide: {param.name}"

        names = ", ".join(p.name for p in missing)
        return f"Please provide the following: {names}"

    def _build_missing_error(self, missing: List[MissingParam]) -> str:
        """Build error message for missing params (no elicitation support)."""
        lines = ["Missing required parameters:"]
        for param in missing:
            hint = f" - {param.x_elicit}" if param.x_elicit else ""
            lines.append(f"  * {param.name}{hint}")
        lines.append("\nPlease provide these values and try again.")
        return "\n".join(lines)

    def _build_non_elicitable_error(self, params: List[MissingParam]) -> str:
        """Build error for params that can't be elicited via form."""
        names = ", ".join(p.name for p in params)
        types = ", ".join(p.param_schema.get("type", "unknown") for p in params)
        return (
            f"Cannot elicit parameters via form: {names}. "
            f"Types ({types}) are not supported by MCP form elicitation. "
            f"Please provide these values directly."
        )

    def _build_sensitive_message(self, sensitive: List[MissingParam]) -> str:
        """Build message for sensitive params requiring URL elicitation."""
        names = ", ".join(p.name for p in sensitive)
        return f"This operation requires secure input for: {names}"

    def _build_confirm_message(self, args: Dict[str, Any]) -> str:
        """Build default confirmation message."""
        risk = self._risk_level.value if self._risk_level else "elevated"

        # Build args summary (truncated values)
        arg_parts: List[str] = []
        for key, value in args.items():
            display_value = self._truncate_value(value)
            arg_parts.append(f"{key}={display_value}")

        args_summary = ", ".join(arg_parts) if arg_parts else "no arguments"

        return (
            f"Confirm {self._tool_name}?\n"
            f"Risk level: {risk}\n"
            f"Arguments: {args_summary}"
        )

    @staticmethod
    def _truncate_value(value: Any) -> str:
        """Truncate value for display in confirmation message."""
        str_value = str(value)
        if len(str_value) > MAX_DISPLAY_VALUE_LENGTH:
            return str_value[: MAX_DISPLAY_VALUE_LENGTH - 3] + "..."
        return str_value


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "CDAGatePlanner",
    "GatePlanResult",
    "MissingParam",
]
