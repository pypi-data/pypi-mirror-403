"""Capability Registry - Canonical capability definitions loaded from YAML.

This module provides a centralized registry of all capability definitions,
ensuring consistent capability naming and matching across BFF, CRUDService,
and other services.

GAP 8 FIX: Previously, three different naming schemes for capabilities
caused accidental bypasses. This registry provides a single source of truth.

Features:
    - Load capabilities from YAML configuration
    - Match BFF route patterns to capabilities
    - Match CRUD tool names to capabilities
    - Support wildcards in patterns
    - Cache parsed patterns for performance

Usage:
    from empowernow_common.delegation.registry import (
        CapabilityRegistry,
        get_capability_registry,
    )
    
    registry = get_capability_registry("/app/config/capabilities.yaml")
    
    # Find capability for a BFF route
    cap_id = registry.match_route("GET", "/api/external/salesforce/sobjects/Opportunity/123")
    
    # Find capability for a CRUD tool
    cap_id = registry.match_tool("salesforce.opportunity.get")
    
    # Get all capabilities for a system
    caps = registry.get_all_for_system("salesforce")

Author: AI Agent Governance Team
Date: 2026-01-15
Version: 1.0.0
"""

from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass(frozen=True)
class CapabilityDefinition:
    """Single capability definition from registry.
    
    This represents a canonical capability that can be matched against
    BFF routes or CRUD tool names.
    
    Attributes:
        id: Canonical capability ID (e.g., "tool:salesforce:opportunity.read")
        system: System name (e.g., "salesforce", "jira")
        display_name: Human-readable name for UI
        risk_level: "low" | "medium" | "high"
        required_trust_level: Minimum trust level required ("basic" | "elevated" | "full")
        bff_route_patterns: List of BFF route patterns (METHOD:/path/*)
        crud_tool_names: List of CRUD tool names that map to this capability
        resource: Optional resource type (e.g., "opportunity")
        action: Optional action (e.g., "read", "write", "delete")
        description: Optional longer description
    """
    
    id: str
    system: str
    display_name: str
    risk_level: str = "medium"
    required_trust_level: str = "basic"
    bff_route_patterns: tuple = field(default_factory=tuple)
    crud_tool_names: tuple = field(default_factory=tuple)
    resource: Optional[str] = None
    action: Optional[str] = None
    description: Optional[str] = None


# =============================================================================
# Registry
# =============================================================================


class CapabilityRegistry:
    """Canonical capability registry loaded from YAML configuration.
    
    This registry provides a centralized source of truth for all capability
    definitions, enabling consistent capability matching across services.
    
    Thread Safety:
        The registry is immutable after construction. Pattern matching
        is thread-safe.
    
    Example:
        registry = CapabilityRegistry("/app/config/capabilities.yaml")
        
        # Match a BFF route
        cap_id = registry.match_route("GET", "/api/external/salesforce/sobjects/Opportunity/123")
        # Returns: "tool:salesforce:opportunity.read"
        
        # Match a CRUD tool
        cap_id = registry.match_tool("salesforce.opportunity.get")
        # Returns: "tool:salesforce:opportunity.read"
    """
    
    def __init__(self, config_path: str) -> None:
        """Initialize registry from YAML config.
        
        Args:
            config_path: Path to YAML capabilities file.
            
        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config is invalid YAML.
        """
        self._capabilities: Dict[str, CapabilityDefinition] = {}
        self._route_index: Dict[str, str] = {}
        self._tool_index: Dict[str, str] = {}
        self._route_patterns: List[tuple[str, str]] = []  # (pattern, cap_id)
        self._load(config_path)
    
    def _load(self, config_path: str) -> None:
        """Load capabilities from YAML file.
        
        Args:
            config_path: Path to YAML file.
        """
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Capabilities config not found: {config_path}")
            return
        except yaml.YAMLError as e:
            logger.error(f"Invalid capabilities YAML: {e}")
            raise
        
        if not data or 'capabilities' not in data:
            logger.warning(f"No capabilities found in {config_path}")
            return
        
        for cap_data in data.get('capabilities', []):
            cap = CapabilityDefinition(
                id=cap_data['id'],
                system=cap_data['system'],
                display_name=cap_data['display_name'],
                risk_level=cap_data.get('risk_level', 'medium'),
                required_trust_level=cap_data.get('required_trust_level', 'basic'),
                bff_route_patterns=tuple(cap_data.get('bff_route_patterns', [])),
                crud_tool_names=tuple(cap_data.get('crud_tool_names', [])),
                resource=cap_data.get('resource'),
                action=cap_data.get('action'),
                description=cap_data.get('description'),
            )
            
            self._capabilities[cap.id] = cap
            
            # Build route index (exact matches)
            for pattern in cap.bff_route_patterns:
                if '*' not in pattern:
                    self._route_index[pattern] = cap.id
                else:
                    self._route_patterns.append((pattern, cap.id))
            
            # Build tool index
            for tool_name in cap.crud_tool_names:
                self._tool_index[tool_name] = cap.id
        
        logger.info(
            "Capability registry loaded",
            extra={
                "count": len(self._capabilities),
                "config_path": config_path,
            }
        )
    
    def get(self, capability_id: str) -> Optional[CapabilityDefinition]:
        """Get capability definition by ID.
        
        Args:
            capability_id: The canonical capability ID.
            
        Returns:
            CapabilityDefinition or None if not found.
        """
        return self._capabilities.get(capability_id)
    
    def match_route(self, method: str, path: str) -> Optional[str]:
        """Find capability_id for a BFF route.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path (/api/external/...)
            
        Returns:
            Capability ID or None if no match.
        """
        pattern = f"{method}:{path}"
        
        # Try exact match first
        if pattern in self._route_index:
            return self._route_index[pattern]
        
        # Try pattern matching
        for route_pattern, cap_id in self._route_patterns:
            if self._pattern_matches(route_pattern, pattern):
                return cap_id
        
        return None
    
    def match_tool(self, tool_name: str) -> Optional[str]:
        """Find capability_id for a CRUD tool name.
        
        Args:
            tool_name: CRUD tool name (e.g., "salesforce.opportunity.get")
            
        Returns:
            Capability ID or None if not found.
        """
        return self._tool_index.get(tool_name)
    
    def get_all_for_system(self, system: str) -> List[CapabilityDefinition]:
        """Get all capabilities for a system (for UI display).
        
        Args:
            system: System name (e.g., "salesforce")
            
        Returns:
            List of capabilities for the system.
        """
        return [
            cap for cap in self._capabilities.values()
            if cap.system.lower() == system.lower()
        ]
    
    def get_all_systems(self) -> List[str]:
        """Get list of unique system names.
        
        Returns:
            List of system names.
        """
        return list(set(cap.system for cap in self._capabilities.values()))
    
    def get_all(self) -> List[CapabilityDefinition]:
        """Get all capability definitions.
        
        Returns:
            List of all capabilities.
        """
        return list(self._capabilities.values())
    
    @staticmethod
    def _pattern_matches(pattern: str, value: str) -> bool:
        """Check if value matches a glob pattern.
        
        Args:
            pattern: Glob pattern (e.g., "GET:/api/external/salesforce/*")
            value: Value to match (e.g., "GET:/api/external/salesforce/sobjects/Opportunity/123")
            
        Returns:
            True if matches.
        """
        return fnmatch.fnmatch(value, pattern)
    
    def __len__(self) -> int:
        """Return number of capabilities."""
        return len(self._capabilities)
    
    def __contains__(self, capability_id: str) -> bool:
        """Check if capability ID exists."""
        return capability_id in self._capabilities


# =============================================================================
# Singleton Factory
# =============================================================================


_registry_cache: Dict[str, CapabilityRegistry] = {}


def get_capability_registry(
    config_path: str = "/app/config/capabilities.yaml",
) -> CapabilityRegistry:
    """Get or create a capability registry singleton.
    
    Registries are cached by config path, so multiple calls with the
    same path return the same instance.
    
    Args:
        config_path: Path to YAML capabilities file.
        
    Returns:
        CapabilityRegistry instance.
    """
    if config_path not in _registry_cache:
        _registry_cache[config_path] = CapabilityRegistry(config_path)
    
    return _registry_cache[config_path]


def clear_registry_cache() -> None:
    """Clear all cached registries (for testing)."""
    _registry_cache.clear()


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "CapabilityDefinition",
    "CapabilityRegistry",
    "get_capability_registry",
    "clear_registry_cache",
]
