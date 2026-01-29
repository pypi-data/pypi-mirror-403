"""MCP Tool ID parsing and validation.

This module implements tool ID parsing per the Neo4j Delegation Model v2.3.
Tool IDs follow the canonical format:

    tool:{mcp_server_id}:{tool_key}

Where:
    - mcp_server_id: Identifier of the MCP server (lowercase, hyphens allowed)
    - tool_key: The tool's unique key, may contain colons for namespacing

Examples:
    tool:jira:create-issue
    tool:mcp-server:travel:flight-search
    tool:mcp-server:google-docs:create_doc
    tool:crud-service-loopback:entra.users.create

Usage:
    from empowernow_common.mcp import ToolId, parse_tool_id

    # Parse a tool ID
    tool = parse_tool_id("tool:jira:create-issue")
    print(tool.server_id)  # "jira"
    print(tool.tool_key)   # "create-issue"

    # Validate without parsing
    if is_valid_tool_id("tool:jira:create-issue"):
        print("Valid!")

    # Create and serialize
    tool = ToolId(server_id="jira", tool_key="create-issue")
    print(str(tool))  # "tool:jira:create-issue"
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


# =============================================================================
# Regex Patterns
# =============================================================================

# Tool ID validation regex
# Canonical format: tool:{mcp_server_id}:{tool_key}
# mcp_server_id: lowercase letters, digits, hyphens (starts with letter)
# tool_key: lowercase letters, digits, hyphens, underscores, colons (for namespacing)
TOOL_ID_PATTERN = re.compile(
    r"^tool:"  # Required prefix
    r"[a-z][a-z0-9\-]*"  # mcp_server_id (lowercase, starts with letter)
    r":"  # Separator
    r"[a-z][a-z0-9\-_:.]*"  # tool_key (may contain colons, dots for legacy, allows short)
    r"$",
    re.ASCII,
)

# Server ID validation regex
SERVER_ID_PATTERN = re.compile(
    r"^[a-z][a-z0-9\-]*$",
    re.ASCII,
)

# Tool key validation regex
TOOL_KEY_PATTERN = re.compile(
    r"^[a-z][a-z0-9\-_:.]+$",
    re.ASCII,
)


# =============================================================================
# ToolId Data Class
# =============================================================================


@dataclass(frozen=True)
class ToolId:
    """Parsed MCP Tool ID.

    Represents a tool ID in canonical format with server and tool key components.
    Immutable (frozen) for safe use as dict keys and in sets.

    Attributes:
        server_id: The MCP server identifier (e.g., "jira", "mcp-server").
        tool_key: The tool's unique key, may contain namespace (e.g., "create-issue", "travel:flight-search").

    Example:
        tool = ToolId(server_id="jira", tool_key="create-issue")
        print(tool.canonical)  # "tool:jira:create-issue"
        print(str(tool))       # "tool:jira:create-issue"
    """

    server_id: str
    """MCP server identifier (lowercase, hyphens allowed)."""

    tool_key: str
    """Tool's unique key (may contain colons for namespacing)."""

    def __post_init__(self) -> None:
        """Validate components after initialization."""
        if not self.server_id:
            raise ValueError("server_id cannot be empty")
        if not self.tool_key:
            raise ValueError("tool_key cannot be empty")

        if not SERVER_ID_PATTERN.match(self.server_id):
            raise ValueError(
                f"Invalid server_id format: {self.server_id}. "
                f"Must be lowercase letters/digits/hyphens, starting with letter."
            )

        if not TOOL_KEY_PATTERN.match(self.tool_key):
            raise ValueError(
                f"Invalid tool_key format: {self.tool_key}. "
                f"Must be lowercase letters/digits/hyphens/underscores/colons."
            )

    @property
    def canonical(self) -> str:
        """Return the canonical tool ID string.

        Returns:
            Tool ID in format "tool:{server_id}:{tool_key}".
        """
        return f"tool:{self.server_id}:{self.tool_key}"

    def __str__(self) -> str:
        """Return canonical string representation."""
        return self.canonical

    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"ToolId(server_id={self.server_id!r}, tool_key={self.tool_key!r})"

    @property
    def namespace(self) -> Optional[str]:
        """Extract namespace from tool_key if present.

        Tool keys may contain namespacing via colons:
        - "travel:flight-search" -> namespace="travel"
        - "create-issue" -> namespace=None

        Returns:
            Namespace prefix if present, None otherwise.
        """
        if ":" in self.tool_key:
            return self.tool_key.split(":", 1)[0]
        return None

    @property
    def name(self) -> str:
        """Extract the tool name from tool_key.

        Tool keys may contain namespacing via colons:
        - "travel:flight-search" -> name="flight-search"
        - "create-issue" -> name="create-issue"

        Returns:
            The tool name (last component of tool_key).
        """
        if ":" in self.tool_key:
            return self.tool_key.split(":")[-1]
        return self.tool_key


# =============================================================================
# Parsing Functions
# =============================================================================


@lru_cache(maxsize=4096)
def parse_tool_id(tool_id: str) -> Optional[ToolId]:
    """Parse a tool ID string into components.

    Uses LRU cache for performance on repeated parses.

    Args:
        tool_id: The tool ID string to parse.

    Returns:
        ToolId if valid, None if invalid format.

    Examples:
        >>> parse_tool_id("tool:jira:create-issue")
        ToolId(server_id='jira', tool_key='create-issue')

        >>> parse_tool_id("tool:mcp-server:travel:flight-search")
        ToolId(server_id='mcp-server', tool_key='travel:flight-search')

        >>> parse_tool_id("invalid")
        None
    """
    if not tool_id or not TOOL_ID_PATTERN.match(tool_id):
        return None

    # Split: tool:{server}:{tool_key}
    # Note: tool_key may contain colons, so only split first two
    parts = tool_id.split(":", 2)
    if len(parts) != 3 or parts[0] != "tool":
        return None

    try:
        return ToolId(server_id=parts[1], tool_key=parts[2])
    except ValueError:
        return None


def is_valid_tool_id(tool_id: str) -> bool:
    """Check if a string is a valid tool ID.

    Args:
        tool_id: String to validate.

    Returns:
        True if the string is a valid tool ID.
    """
    return parse_tool_id(tool_id) is not None


def create_tool_id(server_id: str, tool_key: str) -> ToolId:
    """Create a ToolId from components.

    Args:
        server_id: The MCP server identifier.
        tool_key: The tool's unique key.

    Returns:
        ToolId instance.

    Raises:
        ValueError: If components are invalid.
    """
    return ToolId(server_id=server_id, tool_key=tool_key)


def clear_tool_id_cache() -> None:
    """Clear the tool ID parsing cache.

    Useful for testing or when tool ID format rules change.
    """
    parse_tool_id.cache_clear()


__all__ = [
    "ToolId",
    "parse_tool_id",
    "is_valid_tool_id",
    "create_tool_id",
    "clear_tool_id_cache",
    "TOOL_ID_PATTERN",
    "SERVER_ID_PATTERN",
    "TOOL_KEY_PATTERN",
]
