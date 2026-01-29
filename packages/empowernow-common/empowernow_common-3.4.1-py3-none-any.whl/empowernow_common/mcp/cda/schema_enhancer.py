"""CDA Schema Enhancer.

Transforms CDA x-fields into standard JSON Schema properties that any
MCP-compliant client can understand. This provides "Level 0" CDA
compatibility - benefits for ALL clients without requiring CDA awareness.

Transformations:
    x-suggest (static list) → enum
    x-suggest (dynamic, with precomputed values) → enum
    x-default → default

Preserved (for server-side processing):
    x-normalize, x-redact, x-elicit, x-risk, x-confirm-message

Per CDA design: "CDA x-fields are server-side configuration, not client
protocol extensions. The server translates CDA declarations into standard
MCP protocol messages. Clients don't need to know about CDA."

Usage:
    from empowernow_common.mcp.cda import CDASchemaEnhancer

    enhancer = CDASchemaEnhancer()
    enhanced_tool = enhancer.enhance_tool_schema(tool_definition)

    # Or use convenience function
    from empowernow_common.mcp.cda import enhance_tool_schema
    enhanced = enhance_tool_schema(tool_def)

Copyright (c) 2026 EmpowerNow. All rights reserved.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Final, List, Optional

from .constants import (
    CDA_ALL_FIELDS,
    MAX_ENUM_VALUES,
    RiskLevel,
)


# =============================================================================
# Constants
# =============================================================================

_SCHEMA_KEYS: Final[tuple[str, str]] = ("inputSchema", "input_schema")
"""Supported schema key names (camelCase and snake_case)."""


# =============================================================================
# CDA Schema Enhancer Class
# =============================================================================

class CDASchemaEnhancer:
    """Enhances tool schemas by translating CDA x-fields to standard JSON Schema.

    This enables "Level 0" CDA compatibility - even clients without elicitation
    support benefit from:
    - Static suggestions appearing as enum dropdowns
    - Sensible defaults pre-populated in tool calls

    Thread-safe: No mutable instance state. Safe for concurrent use.
    Reusable: Create once, use for multiple tool schemas.

    Example:
        enhancer = CDASchemaEnhancer()

        # Enhance single tool
        enhanced = enhancer.enhance_tool_schema(tool_def)

        # Enhance list of tools
        enhanced_list = enhancer.enhance_tools_list(tools)

        # With precomputed dynamic suggestions
        enhanced = enhancer.enhance_tool_schema(
            tool_def,
            precomputed_suggestions={"system_name": ["SAP", "Jira", "GitHub"]}
        )
    """

    __slots__ = ("_max_enum_values",)

    def __init__(
        self,
        max_enum_values: int = MAX_ENUM_VALUES,
    ) -> None:
        """Initialize the schema enhancer.

        Args:
            max_enum_values: Maximum enum values to include in enhanced schema.
                Prevents UI issues with huge dropdowns. Default: 100.
        """
        if max_enum_values < 1:
            raise ValueError("max_enum_values must be at least 1")
        self._max_enum_values = max_enum_values

    def enhance_tool_schema(
        self,
        tool_definition: Dict[str, Any],
        precomputed_suggestions: Optional[Dict[str, List[Any]]] = None,
    ) -> Dict[str, Any]:
        """Enhance a single tool definition with CDA transformations.

        Creates a deep copy of the tool definition and applies:
        - x-suggest (static) → enum
        - x-suggest (dynamic) → enum (if precomputed_suggestions provided)
        - x-default → default

        The original tool_definition is NOT modified.

        Args:
            tool_definition: MCP tool definition dict with inputSchema
            precomputed_suggestions: Optional pre-fetched dynamic suggestions
                keyed by parameter name. Use for x-suggest with "source" config.

        Returns:
            Enhanced tool definition (deep copy with transformations applied)

        Example:
            tool = {
                "name": "create_user",
                "inputSchema": {
                    "properties": {
                        "role": {
                            "type": "string",
                            "x-suggest": ["admin", "user", "guest"]
                        }
                    }
                }
            }
            enhanced = enhancer.enhance_tool_schema(tool)
            # enhanced["inputSchema"]["properties"]["role"]["enum"] == ["admin", "user", "guest"]
        """
        # Deep copy to avoid mutating original
        enhanced = deepcopy(tool_definition)

        # Find input schema (support both naming conventions)
        input_schema = self._get_input_schema(enhanced)
        if not input_schema:
            return enhanced

        properties = input_schema.get("properties")
        if not properties or not isinstance(properties, dict):
            return enhanced

        # Enhance each property
        suggestions = precomputed_suggestions or {}
        for prop_name, prop_schema in properties.items():
            if not isinstance(prop_schema, dict):
                continue

            enhanced_prop = self._enhance_property(
                prop_schema,
                suggestions.get(prop_name),
            )

            # Only update if actually enhanced (preserves object identity when unchanged)
            if enhanced_prop is not prop_schema:
                properties[prop_name] = enhanced_prop

        return enhanced

    def enhance_tools_list(
        self,
        tools: List[Dict[str, Any]],
        precomputed_suggestions: Optional[Dict[str, Dict[str, List[Any]]]] = None,
    ) -> List[Dict[str, Any]]:
        """Enhance a list of tool definitions.

        Args:
            tools: List of MCP tool definitions
            precomputed_suggestions: Optional nested dict keyed by tool name,
                with values being dicts of param_name -> suggestion values.

        Returns:
            List of enhanced tool definitions

        Example:
            tools = [tool1, tool2, tool3]
            suggestions = {
                "create_user": {"role": ["admin", "user"]},
                "delete_user": {"reason": ["terminated", "resigned"]},
            }
            enhanced = enhancer.enhance_tools_list(tools, suggestions)
        """
        suggestions_map = precomputed_suggestions or {}

        return [
            self.enhance_tool_schema(
                tool,
                suggestions_map.get(tool.get("name", "")),
            )
            for tool in tools
        ]

    def _get_input_schema(self, tool: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract input schema from tool definition.

        Supports both camelCase (inputSchema) and snake_case (input_schema).
        """
        for key in _SCHEMA_KEYS:
            schema = tool.get(key)
            if schema and isinstance(schema, dict):
                return schema
        return None

    def _enhance_property(
        self,
        prop_schema: Dict[str, Any],
        precomputed_suggestions: Optional[List[Any]],
    ) -> Dict[str, Any]:
        """Enhance a single property schema with CDA transformations.

        Returns the original prop_schema if no changes needed,
        or a shallow copy with enhancements applied.
        """
        modifications: Dict[str, Any] = {}

        # Transform x-suggest → enum
        x_suggest = prop_schema.get("x-suggest")
        if x_suggest is not None and "enum" not in prop_schema:
            enum_values = self._resolve_suggestions(x_suggest, precomputed_suggestions)
            if enum_values:
                modifications["enum"] = self._truncate_enum(enum_values)

        # Transform x-default → default
        if "x-default" in prop_schema and "default" not in prop_schema:
            modifications["default"] = prop_schema["x-default"]

        # Return original if no modifications
        if not modifications:
            return prop_schema

        # Return shallow copy with modifications
        enhanced = dict(prop_schema)
        enhanced.update(modifications)
        return enhanced

    def _resolve_suggestions(
        self,
        x_suggest: Any,
        precomputed: Optional[List[Any]],
    ) -> Optional[List[Any]]:
        """Resolve x-suggest to enum values.

        Args:
            x_suggest: The x-suggest field value (list or dict)
            precomputed: Pre-fetched values for dynamic x-suggest

        Returns:
            List of enum values, or None if cannot resolve
        """
        # Static list: use directly
        if isinstance(x_suggest, list) and x_suggest:
            return x_suggest

        # Dynamic source: use precomputed values
        if isinstance(x_suggest, dict) and "source" in x_suggest:
            if precomputed:
                return precomputed

        return None

    def _truncate_enum(self, values: List[Any]) -> List[Any]:
        """Truncate enum values to configured maximum."""
        if len(values) <= self._max_enum_values:
            return values
        return values[: self._max_enum_values]

    # =========================================================================
    # Static Analysis Methods
    # =========================================================================

    @staticmethod
    def extract_cda_metadata(
        input_schema: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """Extract CDA metadata from input schema for server-side processing.

        Returns a dict keyed by property name with CDA fields as values.
        Used by Gate Planner to determine gating requirements.

        Args:
            input_schema: Tool input schema

        Returns:
            Dict of {property_name: {cda_field: value, ...}}

        Example:
            metadata = CDASchemaEnhancer.extract_cda_metadata(schema)
            # {"user_id": {"x-elicit": "Enter user ID", "x-normalize": "lowercase"}}
        """
        properties = input_schema.get("properties", {})
        cda_metadata: Dict[str, Dict[str, Any]] = {}

        for prop_name, prop_schema in properties.items():
            if not isinstance(prop_schema, dict):
                continue

            prop_cda: Dict[str, Any] = {}
            for field in CDA_ALL_FIELDS:
                if field in prop_schema:
                    prop_cda[field] = prop_schema[field]

            if prop_cda:
                cda_metadata[prop_name] = prop_cda

        return cda_metadata

    @staticmethod
    def get_dynamic_suggest_sources(
        input_schema: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """Get all dynamic x-suggest sources from a schema.

        Used to pre-fetch suggestions before returning tools/list.
        Only returns x-suggest configs that have a "source" key
        (indicating dynamic fetch is needed).

        Args:
            input_schema: Tool input schema

        Returns:
            Dict of {property_name: x_suggest_config}
        """
        properties = input_schema.get("properties", {})
        dynamic_sources: Dict[str, Dict[str, Any]] = {}

        for prop_name, prop_schema in properties.items():
            if not isinstance(prop_schema, dict):
                continue

            x_suggest = prop_schema.get("x-suggest")
            if isinstance(x_suggest, dict) and "source" in x_suggest:
                dynamic_sources[prop_name] = x_suggest

        return dynamic_sources

    @staticmethod
    def has_cda_metadata(input_schema: Dict[str, Any]) -> bool:
        """Check if schema has any CDA x-fields.

        Args:
            input_schema: Tool input schema

        Returns:
            True if any property has CDA x-fields
        """
        properties = input_schema.get("properties", {})

        for prop_schema in properties.values():
            if not isinstance(prop_schema, dict):
                continue

            for field in CDA_ALL_FIELDS:
                if field in prop_schema:
                    return True

        return False

    @staticmethod
    def get_tool_risk_level(tool_definition: Dict[str, Any]) -> Optional[RiskLevel]:
        """Get the risk level for a tool from its CDA metadata.

        Checks both the "mcp" section and "metadata" section for x-risk.

        Args:
            tool_definition: Tool definition dict

        Returns:
            RiskLevel enum or None if not specified

        Example:
            tool = {"name": "delete", "mcp": {"x-risk": "high"}}
            risk = CDASchemaEnhancer.get_tool_risk_level(tool)
            # risk == RiskLevel.HIGH
        """
        # Check mcp section first (standard location)
        mcp = tool_definition.get("mcp")
        if isinstance(mcp, dict) and "x-risk" in mcp:
            return RiskLevel.from_string(mcp["x-risk"])

        # Check metadata section (alternative location)
        metadata = tool_definition.get("metadata")
        if isinstance(metadata, dict) and "x-risk" in metadata:
            return RiskLevel.from_string(metadata["x-risk"])

        return None

    @staticmethod
    def get_confirm_message(tool_definition: Dict[str, Any]) -> Optional[str]:
        """Get custom confirmation message from tool definition.

        Args:
            tool_definition: Tool definition dict

        Returns:
            Custom confirmation message or None
        """
        mcp = tool_definition.get("mcp")
        if isinstance(mcp, dict) and "x-confirm-message" in mcp:
            return mcp["x-confirm-message"]

        metadata = tool_definition.get("metadata")
        if isinstance(metadata, dict) and "x-confirm-message" in metadata:
            return metadata["x-confirm-message"]

        return None


# =============================================================================
# Module-Level Convenience Functions
# =============================================================================

# Singleton enhancer for convenience functions
_default_enhancer: Optional[CDASchemaEnhancer] = None


def _get_default_enhancer() -> CDASchemaEnhancer:
    """Get or create the default schema enhancer."""
    global _default_enhancer
    if _default_enhancer is None:
        _default_enhancer = CDASchemaEnhancer()
    return _default_enhancer


def enhance_tool_schema(
    tool_definition: Dict[str, Any],
    precomputed_suggestions: Optional[Dict[str, List[Any]]] = None,
) -> Dict[str, Any]:
    """Convenience function to enhance a tool schema with CDA transformations.

    Uses a shared CDASchemaEnhancer instance with default settings.

    Args:
        tool_definition: MCP tool definition
        precomputed_suggestions: Optional pre-fetched dynamic suggestions

    Returns:
        Enhanced tool definition
    """
    return _get_default_enhancer().enhance_tool_schema(
        tool_definition,
        precomputed_suggestions,
    )


def enhance_tools_list(
    tools: List[Dict[str, Any]],
    precomputed_suggestions: Optional[Dict[str, Dict[str, List[Any]]]] = None,
) -> List[Dict[str, Any]]:
    """Convenience function to enhance a list of tools.

    Args:
        tools: List of MCP tool definitions
        precomputed_suggestions: Optional suggestions keyed by tool name

    Returns:
        List of enhanced tool definitions
    """
    return _get_default_enhancer().enhance_tools_list(tools, precomputed_suggestions)


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "CDASchemaEnhancer",
    "enhance_tool_schema",
    "enhance_tools_list",
]
