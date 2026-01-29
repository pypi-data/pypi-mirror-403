"""Capability pattern matching for delegation enforcement.

This module implements the capability pattern matching logic per the
Neo4j Delegation Model v2.3 specification.

Pattern Syntax:
    capability_pattern = "tool" ":" server_pattern ":" tool_pattern
    server_pattern     = "*" | identifier
    tool_pattern       = "*" | name | namespace ":" name

Matching Rules:
    1. Case-sensitive matching
    2. "*" matches any substring EXCEPT ":" (colon is the segment separator)
    3. Patterns are admin-provided (never user-supplied)
    4. Compiled at load time for performance

Precedence:
    1. Explicit deny overrides allow
    2. Most specific pattern wins
    3. Order-independent evaluation

Examples:
    Pattern: "tool:jira:*" matches "tool:jira:create_issue", "tool:jira:delete_issue"
    Pattern: "tool:*:read_*" matches "tool:jira:read_issue", "tool:slack:read_channel"
    Pattern: "tool:crud:users:create" matches exactly "tool:crud:users:create"
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List, Optional, Tuple

from .models import TrustLevel

logger = logging.getLogger(__name__)

# =============================================================================
# Complexity Limits (DoS Protection)
# =============================================================================

MAX_PATTERNS_PER_DELEGATION = 100
"""Maximum number of patterns allowed per delegation."""

MAX_PATTERN_LENGTH = 256
"""Maximum length of a single pattern string."""

MAX_WILDCARDS_PER_PATTERN = 3
"""Maximum number of wildcards (*) in a single pattern."""

# =============================================================================
# Regex Patterns
# =============================================================================

# Tool ID validation regex - stricter than patterns (no wildcards)
# Canonical format: tool:{mcp_server_id}:{tool_key}
# tool_key may contain additional colons for namespacing, dots for legacy
TOOL_ID_REGEX = re.compile(
    r"^tool:"  # Required prefix
    r"[a-z][a-z0-9\-]*"  # mcp_server_id (lowercase, starts with letter)
    r":"  # Separator
    r"[a-z][a-z0-9\-_:.]*"  # tool_key (may contain colons, dots for namespacing)
    r"$",
    re.ASCII,
)

# Capability pattern regex - allows wildcards
# NOTE: tool_key allows dots (.) for OpenAI-compatible tool naming like "opportunity.read"
# This matches TOOL_ID_REGEX which also allows dots
#
# Supported patterns (tool_key part):
#   - "opportunity.read"    → exact match (letters/nums/dots starting with letter)
#   - "*"                   → any tool (wildcard alone)
#   - "opportunity.*"       → any action on resource (ends with .*)
#   - "*.read"              → any resource with action (starts with *.)
#   - "*suffix"             → any tool ending with suffix (e.g., *_delete)
#
CAPABILITY_PATTERN_REGEX = re.compile(
    r"^tool:"  # Required prefix
    r"(?:[a-z][a-z0-9\-]*|\*)"  # mcp_server_id or * wildcard
    r":"  # Separator
    r"(?:"
    r"[a-z][a-z0-9\-_:.]*"  # Exact: starts with letter (e.g., opportunity.read)
    r"|\*"  # Full wildcard: matches anything
    r"|[a-z][a-z0-9\-_:.]*\*"  # Suffix wildcard: prefix.* (e.g., opportunity.*)
    r"|\*[a-z0-9\-_:.]+"  # Prefix wildcard: *.suffix (e.g., *.read, *_delete)
    r")"
    r"$",
    re.ASCII,
)


# =============================================================================
# Parsed Pattern
# =============================================================================


@dataclass(frozen=True)
class ParsedCapabilityPattern:
    """Compiled capability pattern for efficient matching.

    Patterns are parsed once and cached for performance. The regex
    is compiled during initialization.

    Attributes:
        original: The original pattern string.
        server_pattern: Pattern for mcp_server_id component.
        tool_key_pattern: Pattern for tool_key component.
        is_wildcard: Whether the pattern contains any wildcards.
        specificity: Higher = more specific (used for precedence).
    """

    original: str
    server_pattern: str
    tool_key_pattern: str
    is_wildcard: bool
    specificity: int = field(compare=False)

    # Compiled regex (not compared for equality)
    _server_regex: Optional[re.Pattern[str]] = field(
        compare=False, repr=False, default=None, hash=False
    )
    _tool_key_regex: Optional[re.Pattern[str]] = field(
        compare=False, repr=False, default=None, hash=False
    )

    def __post_init__(self) -> None:
        """Compile regexes for each component."""
        object.__setattr__(self, "_server_regex", _wildcard_to_regex(self.server_pattern))
        object.__setattr__(self, "_tool_key_regex", _wildcard_to_regex(self.tool_key_pattern))

    def matches(self, tool_id: str) -> bool:
        """Check if tool_id matches this pattern.

        Args:
            tool_id: The tool ID to match against.

        Returns:
            True if the tool_id matches this pattern.
        """
        parsed = parse_tool_id(tool_id)
        if parsed is None:
            return False

        server, tool_key = parsed

        # Match server
        if self._server_regex and not self._server_regex.fullmatch(server):
            return False

        # Match tool_key
        if self._tool_key_regex and not self._tool_key_regex.fullmatch(tool_key):
            return False

        return True


# =============================================================================
# Helper Functions
# =============================================================================


def _wildcard_to_regex(pattern: str) -> re.Pattern[str]:
    """Convert a wildcard pattern to regex.

    The * wildcard matches any character except ':' (which is the separator).

    Args:
        pattern: Pattern with * wildcards.

    Returns:
        Compiled regex pattern.
    """
    if pattern == "*":
        return re.compile(r"[^:]+", re.ASCII)

    # Escape special regex chars, then convert * to [^:]+
    escaped = re.escape(pattern)
    regex_pattern = escaped.replace(r"\*", r"[^:]*")
    return re.compile(f"^{regex_pattern}$", re.ASCII)


def _calculate_specificity(pattern: str) -> int:
    """Calculate pattern specificity (higher = more specific).

    Scoring:
    - Base score: 100 points
    - Each wildcard: -20 points
    - Each non-wildcard character: +1 point

    Args:
        pattern: The capability pattern.

    Returns:
        Specificity score (0-200 range typically).
    """
    score = 100

    # Deduct for wildcards
    wildcard_count = pattern.count("*")
    score -= wildcard_count * 20

    # Add for specific characters
    non_wildcard_len = len(pattern.replace("*", ""))
    score += non_wildcard_len

    return max(0, score)


# =============================================================================
# Public API
# =============================================================================


@lru_cache(maxsize=1024)
def parse_capability_pattern(pattern: str) -> ParsedCapabilityPattern:
    """Parse and validate a capability pattern.

    Patterns are cached for performance. Invalid patterns raise ValueError.

    Args:
        pattern: The capability pattern to parse.

    Returns:
        ParsedCapabilityPattern ready for matching.

    Raises:
        ValueError: If pattern is invalid.

    Examples:
        >>> p = parse_capability_pattern("tool:jira:*")
        >>> p.matches("tool:jira:create_issue")
        True
    """
    if not pattern:
        raise ValueError("Capability pattern cannot be empty")

    if len(pattern) > MAX_PATTERN_LENGTH:
        raise ValueError(f"Pattern exceeds max length {MAX_PATTERN_LENGTH}: {len(pattern)}")

    wildcard_count = pattern.count("*")
    if wildcard_count > MAX_WILDCARDS_PER_PATTERN:
        raise ValueError(f"Pattern has too many wildcards (max {MAX_WILDCARDS_PER_PATTERN}): {wildcard_count}")

    if not CAPABILITY_PATTERN_REGEX.match(pattern):
        raise ValueError(f"Invalid capability pattern format: {pattern}")

    # Parse components: tool:{server}:{tool_key}
    # Split on first two colons only
    parts = pattern.split(":", 2)
    if len(parts) != 3 or parts[0] != "tool":
        raise ValueError(f"Pattern must be 'tool:{{server}}:{{tool_key}}': {pattern}")

    _, server, tool_key = parts

    return ParsedCapabilityPattern(
        original=pattern,
        server_pattern=server,
        tool_key_pattern=tool_key,
        is_wildcard="*" in pattern,
        specificity=_calculate_specificity(pattern),
    )


@lru_cache(maxsize=4096)
def parse_tool_id(tool_id: str) -> Optional[Tuple[str, str]]:
    """Parse a tool ID into components.

    Args:
        tool_id: The tool ID to parse.

    Returns:
        Tuple of (server_id, tool_key) or None if invalid.

    Examples:
        >>> parse_tool_id("tool:jira:create_issue")
        ('jira', 'create_issue')
        >>> parse_tool_id("tool:mcp-server:travel:flight-search")
        ('mcp-server', 'travel:flight-search')
        >>> parse_tool_id("invalid")
        None
    """
    if not tool_id or not TOOL_ID_REGEX.match(tool_id):
        return None

    # Split: tool:{server}:{tool_key}
    parts = tool_id.split(":", 2)
    if len(parts) != 3 or parts[0] != "tool":
        return None

    return (parts[1], parts[2])


def is_valid_tool_id(tool_id: str) -> bool:
    """Check if a string is a valid tool ID.

    Args:
        tool_id: String to validate.

    Returns:
        True if valid tool ID format.
    """
    return parse_tool_id(tool_id) is not None


def capability_allowed(
    tool_id: str,
    capability_ids: Optional[List[str]],
    trust_level: TrustLevel = TrustLevel.BASIC,
) -> bool:
    """Check if a tool is allowed by capability patterns.

    Simple boolean version - use capability_allowed_with_match for audit trails.

    Args:
        tool_id: The tool ID to check.
        capability_ids: List of allowed capability patterns (or None).
        trust_level: Trust level of the delegation.

    Returns:
        True if tool is allowed.
    """
    allowed, _ = capability_allowed_with_match(tool_id, capability_ids, None, trust_level)
    return allowed


def capability_allowed_with_match(
    tool_id: str,
    allow_patterns: Optional[List[str]],
    deny_patterns: Optional[List[str]],
    trust_level: TrustLevel = TrustLevel.BASIC,
) -> Tuple[bool, Optional[str]]:
    """Check if a tool is allowed by capability patterns.

    Rules:
        1. FULL trust + None allow_patterns = all allowed
        2. None allow_patterns + not FULL = denied
        3. Empty allow list = denied
        4. Explicit deny overrides allow (checked first)
        5. Most specific matching allow pattern wins

    Args:
        tool_id: The tool to check.
        allow_patterns: List of allowed capability patterns (or None).
        deny_patterns: List of denied capability patterns (or None).
        trust_level: Trust level of the delegation.

    Returns:
        Tuple of (allowed: bool, matched_pattern: Optional[str])
    """
    # Validate tool_id format
    if not is_valid_tool_id(tool_id):
        logger.debug("Invalid tool_id format: %s", tool_id)
        return (False, None)

    # Rule 1: FULL trust with no restrictions
    if trust_level == TrustLevel.FULL and allow_patterns is None:
        return (True, "trust:full")

    # Rule 2: No patterns and not FULL = denied
    if allow_patterns is None:
        return (False, None)

    # Rule 3: Empty allow list = denied
    if len(allow_patterns) == 0:
        return (False, None)

    # Validate pattern count
    if len(allow_patterns) > MAX_PATTERNS_PER_DELEGATION:
        logger.warning("Too many allow patterns: %d", len(allow_patterns))
        return (False, None)

    # Rule 4: Check deny patterns first
    if deny_patterns:
        if len(deny_patterns) > MAX_PATTERNS_PER_DELEGATION:
            logger.warning("Too many deny patterns: %d", len(deny_patterns))
            return (False, None)

        for pattern_str in deny_patterns:
            try:
                pattern = parse_capability_pattern(pattern_str)
                if pattern.matches(tool_id):
                    logger.debug("Tool %s denied by pattern %s", tool_id, pattern_str)
                    return (False, f"deny:{pattern_str}")
            except ValueError as e:
                logger.warning("Invalid deny pattern '%s': %s", pattern_str, e)
                continue

    # Rule 5: Find most specific matching allow pattern
    best_match: Optional[ParsedCapabilityPattern] = None

    for pattern_str in allow_patterns:
        try:
            pattern = parse_capability_pattern(pattern_str)
            if pattern.matches(tool_id):
                if best_match is None or pattern.specificity > best_match.specificity:
                    best_match = pattern
        except ValueError as e:
            logger.warning("Invalid allow pattern '%s': %s", pattern_str, e)
            continue

    if best_match:
        return (True, best_match.original)

    return (False, None)


def filter_allowed_tools(
    tool_ids: List[str],
    allow_patterns: Optional[List[str]],
    deny_patterns: Optional[List[str]] = None,
    trust_level: TrustLevel = TrustLevel.BASIC,
) -> List[str]:
    """Filter a list of tools to only those allowed.

    Args:
        tool_ids: List of tool IDs to filter.
        allow_patterns: List of allowed capability patterns.
        deny_patterns: List of denied capability patterns.
        trust_level: Trust level of the delegation.

    Returns:
        List of allowed tool IDs.
    """
    return [
        tid
        for tid in tool_ids
        if capability_allowed_with_match(tid, allow_patterns, deny_patterns, trust_level)[0]
    ]


def validate_patterns(patterns: List[str]) -> List[str]:
    """Validate a list of capability patterns.

    Args:
        patterns: List of patterns to validate.

    Returns:
        List of validation error messages (empty if all valid).
    """
    errors: List[str] = []

    if len(patterns) > MAX_PATTERNS_PER_DELEGATION:
        errors.append(f"Too many patterns: {len(patterns)} (max {MAX_PATTERNS_PER_DELEGATION})")

    for i, pattern in enumerate(patterns):
        try:
            parse_capability_pattern(pattern)
        except ValueError as e:
            errors.append(f"Pattern {i} '{pattern}': {e}")

    return errors


def clear_pattern_cache() -> None:
    """Clear the pattern parsing cache.

    Useful for testing or when patterns are updated.
    """
    parse_capability_pattern.cache_clear()
    parse_tool_id.cache_clear()


__all__ = [
    # Constants
    "MAX_PATTERNS_PER_DELEGATION",
    "MAX_PATTERN_LENGTH",
    "MAX_WILDCARDS_PER_PATTERN",
    # Classes
    "ParsedCapabilityPattern",
    # Functions
    "parse_capability_pattern",
    "parse_tool_id",
    "is_valid_tool_id",
    "capability_allowed",
    "capability_allowed_with_match",
    "filter_allowed_tools",
    "validate_patterns",
    "clear_pattern_cache",
]
