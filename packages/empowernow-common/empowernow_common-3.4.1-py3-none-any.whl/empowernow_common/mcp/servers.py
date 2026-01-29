"""MCP Server Registry and Loopback Detection.

This module provides server configuration and loopback detection for
MCP tool routing. It determines whether a tool call should be routed
internally (loopback) or to an external MCP server.

⚠️ SECURITY WARNING ⚠️
    is_loopback_server() is a ROUTING HINT, not a security property.
    It determines whether a tool call should be routed internally vs externally.
    It does NOT authenticate the caller or authorize the operation.
    All loopback calls MUST still be cryptographically signed (see auth module).

Default Loopback Servers:
    - empowernow-crud: CRUDService internal tools
    - empowernow-workflow: Workflow engine tools
    - empowernow-agent: Agent orchestration tools

Configuration:
    Loopback servers can be configured via:
    1. Environment variable: LOOPBACK_SERVERS (comma-separated)
    2. Constructor parameter: loopback_servers frozenset

Usage:
    from empowernow_common.mcp import is_loopback_server, ServerConfig

    # Check if server is loopback
    if is_loopback_server("empowernow-crud"):
        # Route internally (still verify signature!)
        pass
    else:
        # Route to external MCP server
        pass
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import FrozenSet, Optional


# =============================================================================
# Default Configuration
# =============================================================================

DEFAULT_LOOPBACK_SERVERS: FrozenSet[str] = frozenset(
    {
        "empowernow-crud",
        "empowernow-workflow",
        "empowernow-agent",
        "crud-service-loopback",  # Legacy alias
    }
)
"""Default set of loopback server IDs.

These servers are routed internally rather than to external MCP servers.
Can be overridden via environment variable or parameter.
"""


# =============================================================================
# Server Configuration
# =============================================================================


@dataclass(frozen=True)
class ServerConfig:
    """Configuration for an MCP server.

    Attributes:
        server_id: Unique identifier for the server.
        is_loopback: Whether this is an internal loopback server.
        display_name: Human-readable name (optional).
        description: Description of the server (optional).
    """

    server_id: str
    """Unique identifier for the server (lowercase, hyphens allowed)."""

    is_loopback: bool = False
    """Whether this is an internal loopback server."""

    display_name: Optional[str] = None
    """Human-readable name for the server."""

    description: Optional[str] = None
    """Description of the server's purpose."""

    def __post_init__(self) -> None:
        """Validate and normalize server_id format."""
        if not self.server_id:
            raise ValueError("server_id cannot be empty")
        # Normalize to lowercase for consistent lookups
        normalized = self.server_id.strip().lower()
        object.__setattr__(self, "server_id", normalized)
        if not normalized.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Invalid server_id format: {self.server_id}")


# =============================================================================
# Server Registry
# =============================================================================


class ServerRegistry:
    """Registry for MCP server configurations.

    Provides lookup and management of server configurations including
    loopback detection and server metadata.

    Example:
        registry = ServerRegistry()
        registry.register(ServerConfig("jira", is_loopback=False))
        registry.register(ServerConfig("empowernow-crud", is_loopback=True))

        if registry.is_loopback("empowernow-crud"):
            # Route internally
            pass
    """

    def __init__(
        self,
        loopback_servers: Optional[FrozenSet[str]] = None,
    ) -> None:
        """Initialize server registry.

        Args:
            loopback_servers: Set of loopback server IDs. If None, uses
                DEFAULT_LOOPBACK_SERVERS merged with LOOPBACK_SERVERS env var.
        """
        self._servers: dict[str, ServerConfig] = {}
        self._loopback_servers = self._resolve_loopback_servers(loopback_servers)

    def _resolve_loopback_servers(
        self, configured: Optional[FrozenSet[str]]
    ) -> FrozenSet[str]:
        """Resolve loopback servers from config and environment."""
        if configured is not None:
            return configured

        # Start with defaults
        servers = set(DEFAULT_LOOPBACK_SERVERS)

        # Add from environment variable
        env_servers = os.getenv("LOOPBACK_SERVERS", "")
        if env_servers:
            for server in env_servers.split(","):
                server = server.strip().lower()
                if server:
                    servers.add(server)

        return frozenset(servers)

    def register(self, config: ServerConfig) -> None:
        """Register a server configuration.

        Args:
            config: The server configuration to register.
        """
        self._servers[config.server_id] = config

    def get(self, server_id: str) -> Optional[ServerConfig]:
        """Get server configuration by ID.

        Args:
            server_id: The server ID to look up (case-insensitive).

        Returns:
            ServerConfig if registered, None otherwise.
        """
        return self._servers.get(server_id.lower())

    def is_loopback(self, server_id: str) -> bool:
        """Check if a server is a loopback server.

        ⚠️ WARNING: This is a ROUTING HINT, not an authentication check.
        Attackers can craft tool IDs with any server_id.
        Always verify calls via HMAC signature.

        Args:
            server_id: The server ID to check (case-insensitive).

        Returns:
            True if the server should be routed internally.
        """
        normalized = server_id.lower()
        # Check explicit config first
        config = self._servers.get(normalized)
        if config is not None:
            return config.is_loopback

        # Fall back to loopback server set
        return normalized in self._loopback_servers

    def list_servers(self) -> list[ServerConfig]:
        """List all registered servers.

        Returns:
            List of registered ServerConfig objects.
        """
        return list(self._servers.values())

    def list_loopback_servers(self) -> FrozenSet[str]:
        """List all loopback server IDs.

        Returns:
            Set of loopback server IDs.
        """
        # Combine explicit configs with default set
        loopback = set(self._loopback_servers)
        for config in self._servers.values():
            if config.is_loopback:
                loopback.add(config.server_id)
        return frozenset(loopback)


# =============================================================================
# Module-Level Functions
# =============================================================================

# Default registry instance (lazy initialization)
_default_registry: Optional[ServerRegistry] = None


def _get_default_registry() -> ServerRegistry:
    """Get or create the default server registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ServerRegistry()
    return _default_registry


def is_loopback_server(
    server_id: str,
    loopback_servers: Optional[FrozenSet[str]] = None,
) -> bool:
    """Check if a server is a loopback (internal) server.

    ⚠️ WARNING: This is a ROUTING HINT, not a security property.

    It determines whether a tool call should be routed internally vs externally.
    It does NOT authenticate the caller or authorize the operation.
    Attackers can craft tool IDs with any server_id.
    Always verify calls via HMAC signature.

    Args:
        server_id: The server ID to check.
        loopback_servers: Optional set of loopback server IDs.
            If None, uses defaults + LOOPBACK_SERVERS env var.

    Returns:
        True if the server should be routed internally.

    Example:
        >>> is_loopback_server("empowernow-crud")
        True
        >>> is_loopback_server("jira")
        False
        >>> is_loopback_server("custom", frozenset({"custom"}))
        True
    """
    normalized = server_id.lower()
    if loopback_servers is not None:
        return normalized in loopback_servers

    return _get_default_registry().is_loopback(normalized)


def register_server(config: ServerConfig) -> None:
    """Register a server configuration in the default registry.

    Args:
        config: The server configuration to register.
    """
    _get_default_registry().register(config)


def get_server(server_id: str) -> Optional[ServerConfig]:
    """Get server configuration from the default registry.

    Args:
        server_id: The server ID to look up.

    Returns:
        ServerConfig if registered, None otherwise.
    """
    return _get_default_registry().get(server_id)


def list_loopback_servers() -> FrozenSet[str]:
    """List all loopback server IDs from the default registry.

    Returns:
        Set of loopback server IDs.
    """
    return _get_default_registry().list_loopback_servers()


def reset_registry() -> None:
    """Reset the default registry.

    Useful for testing to clear registered servers.
    """
    global _default_registry
    _default_registry = None


__all__ = [
    # Constants
    "DEFAULT_LOOPBACK_SERVERS",
    # Classes
    "ServerConfig",
    "ServerRegistry",
    # Functions
    "is_loopback_server",
    "register_server",
    "get_server",
    "list_loopback_servers",
    "reset_registry",
]
