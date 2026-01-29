"""CDA (Contract-Driven Autonomy) Module.

Provides canonical CDA logic for x-field processing shared between
MCP Gateway and CRUDService. This module is the SINGLE source of truth
for CDA behavior, eliminating duplication and ensuring consistency.

CDA Levels:
    Level 0 (Any MCP Client):
        - Schema enhancement (x-suggest → enum, x-default → default)
        - Works with ANY MCP-compliant client

    Level 1+ (Clients with elicitation):
        - Gate planning (missing params, risk confirmation)
        - Requires client support for MCP elicitation

Components:
    CDASchemaEnhancer:
        Transforms CDA x-fields to standard JSON Schema for tools/list.
        Enables Level 0 compatibility for all clients.

    CDAGatePlanner:
        Evaluates tool calls and determines next action (execute, elicit, confirm).
        Central gating logic for Level 1+ features.

    Normalizers:
        Built-in value normalization functions for x-normalize.
        Tool-based normalizers (email, phone) handled by service layer.

Usage:
    # Schema Enhancement (tools/list)
    from empowernow_common.mcp.cda import CDASchemaEnhancer

    enhancer = CDASchemaEnhancer()
    enhanced_tools = enhancer.enhance_tools_list(tools)

    # Gate Planning (tools/invoke)
    from empowernow_common.mcp.cda import CDAGatePlanner, GateAction

    planner = CDAGatePlanner(tool_schema, supports_elicitation=True)
    result = planner.plan(arguments)

    match result.action:
        case GateAction.EXECUTE:
            execute_tool(result.resolved_args)
        case GateAction.NEED_FORM_INPUT:
            send_elicitation(result.requested_schema)

    # Value Normalization
    from empowernow_common.mcp.cda import apply_normalization

    normalized = apply_normalization("Hello World", "snake_case")
    # "hello_world"

Copyright (c) 2026 EmpowerNow. All rights reserved.
"""

from __future__ import annotations

# Constants and Enums
from .constants import (
    # Field categories
    CDA_ALL_FIELDS,
    CDA_EXTENDED_FIELDS,
    CDA_PRESERVE_FIELDS,
    CDA_TRANSFORM_FIELDS,
    # Enums
    GateAction,
    RiskLevel,
    # Limits
    ELICITABLE_TYPES,
    MAX_DISPLAY_VALUE_LENGTH,
    MAX_ELICITATION_ROUNDS,
    MAX_ENUM_VALUES,
)

# Normalizers
from .normalizers import (
    NORMALIZERS,
    NormalizerFunc,
    apply_normalization,
    get_available_normalizers,
    is_builtin_normalizer,
)

# Schema Enhancer
from .schema_enhancer import (
    CDASchemaEnhancer,
    enhance_tool_schema,
    enhance_tools_list,
)

# Gate Planner
from .gate_planner import (
    CDAGatePlanner,
    GatePlanResult,
    MissingParam,
)


# =============================================================================
# Version
# =============================================================================

__version__ = "1.0.0"
"""CDA module version (SemVer)."""


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Version
    "__version__",
    # Constants - Field Categories
    "CDA_ALL_FIELDS",
    "CDA_EXTENDED_FIELDS",
    "CDA_PRESERVE_FIELDS",
    "CDA_TRANSFORM_FIELDS",
    # Constants - Limits
    "ELICITABLE_TYPES",
    "MAX_DISPLAY_VALUE_LENGTH",
    "MAX_ELICITATION_ROUNDS",
    "MAX_ENUM_VALUES",
    # Enums
    "GateAction",
    "RiskLevel",
    # Normalizers
    "NORMALIZERS",
    "NormalizerFunc",
    "apply_normalization",
    "get_available_normalizers",
    "is_builtin_normalizer",
    # Schema Enhancer
    "CDASchemaEnhancer",
    "enhance_tool_schema",
    "enhance_tools_list",
    # Gate Planner
    "CDAGatePlanner",
    "GatePlanResult",
    "MissingParam",
]
