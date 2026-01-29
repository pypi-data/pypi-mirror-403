"""CDA Value Normalizers.

Provides normalization functions for the x-normalize CDA field.
These are deterministic string transformations that can be applied
without external service calls.

Complex normalizations (email canonicalization, phone formatting, etc.)
require tool execution and are handled by the service layer, not here.

Usage:
    from empowernow_common.mcp.cda import apply_normalization, NORMALIZERS

    # Apply built-in normalizer
    value = apply_normalization("Hello World", "lowercase_underscore")
    # Returns: "hello_world"

    # Check if normalizer is built-in
    if is_builtin_normalizer("lowercase"):
        # Can apply locally without tool call
        pass

Copyright (c) 2026 EmpowerNow. All rights reserved.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Final, Optional


# =============================================================================
# Type Definitions
# =============================================================================

NormalizerFunc = Callable[[Any], Any]
"""Type alias for normalizer functions.

Normalizers take any value and return the normalized form.
Non-string values should be passed through unchanged.
"""


# =============================================================================
# Built-in Normalizer Functions
# =============================================================================

def _normalize_lowercase(value: Any) -> Any:
    """Convert string to lowercase.

    Args:
        value: Value to normalize

    Returns:
        Lowercase string, or original value if not a string
    """
    if isinstance(value, str):
        return value.lower()
    return value


def _normalize_uppercase(value: Any) -> Any:
    """Convert string to uppercase.

    Args:
        value: Value to normalize

    Returns:
        Uppercase string, or original value if not a string
    """
    if isinstance(value, str):
        return value.upper()
    return value


def _normalize_trim(value: Any) -> Any:
    """Strip leading and trailing whitespace.

    Args:
        value: Value to normalize

    Returns:
        Trimmed string, or original value if not a string
    """
    if isinstance(value, str):
        return value.strip()
    return value


def _normalize_lowercase_underscore(value: Any) -> Any:
    """Convert to lowercase with underscores.

    Replaces spaces, hyphens, and other separators with underscores.

    Args:
        value: Value to normalize

    Returns:
        Normalized string (e.g., "Hello World" -> "hello_world")

    Example:
        >>> _normalize_lowercase_underscore("Hello World")
        'hello_world'
        >>> _normalize_lowercase_underscore("hello-world")
        'hello_world'
    """
    if isinstance(value, str):
        return re.sub(r"[\s\-]+", "_", value.lower())
    return value


def _normalize_slug(value: Any) -> Any:
    """Convert to URL-safe slug.

    Lowercase, hyphens only, no special characters.
    Multiple separators collapsed to single hyphen.

    Args:
        value: Value to normalize

    Returns:
        URL-safe slug (e.g., "Hello World!" -> "hello-world")

    Example:
        >>> _normalize_slug("Hello World!")
        'hello-world'
        >>> _normalize_slug("foo--bar")
        'foo-bar'
    """
    if isinstance(value, str):
        # Replace non-alphanumeric with hyphens, collapse multiples, strip edges
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
        return slug.strip("-")
    return value


def _normalize_snake_case(value: Any) -> Any:
    """Convert camelCase/PascalCase to snake_case.

    Args:
        value: Value to normalize

    Returns:
        snake_case string (e.g., "myClassName" -> "my_class_name")

    Example:
        >>> _normalize_snake_case("myClassName")
        'my_class_name'
        >>> _normalize_snake_case("HTTPServer")
        'http_server'
    """
    if isinstance(value, str):
        # Insert underscore before uppercase letters (handling acronyms)
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
        s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
        return s2.lower()
    return value


def _normalize_kebab_case(value: Any) -> Any:
    """Convert camelCase/PascalCase to kebab-case.

    Args:
        value: Value to normalize

    Returns:
        kebab-case string (e.g., "myClassName" -> "my-class-name")

    Example:
        >>> _normalize_kebab_case("myClassName")
        'my-class-name'
        >>> _normalize_kebab_case("HTTPServer")
        'http-server'
    """
    if isinstance(value, str):
        # Insert hyphen before uppercase letters (handling acronyms)
        s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", value)
        s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s1)
        return s2.lower()
    return value


def _normalize_title_case(value: Any) -> Any:
    """Convert string to Title Case.

    Args:
        value: Value to normalize

    Returns:
        Title case string (e.g., "hello world" -> "Hello World")
    """
    if isinstance(value, str):
        return value.title()
    return value


def _normalize_capitalize(value: Any) -> Any:
    """Capitalize first character, lowercase rest.

    Args:
        value: Value to normalize

    Returns:
        Capitalized string (e.g., "hELLO" -> "Hello")
    """
    if isinstance(value, str):
        return value.capitalize()
    return value


def _normalize_remove_whitespace(value: Any) -> Any:
    """Remove all whitespace from string.

    Args:
        value: Value to normalize

    Returns:
        String with no whitespace (e.g., "hello world" -> "helloworld")
    """
    if isinstance(value, str):
        return re.sub(r"\s+", "", value)
    return value


def _normalize_collapse_whitespace(value: Any) -> Any:
    """Collapse multiple whitespace to single space.

    Args:
        value: Value to normalize

    Returns:
        String with collapsed whitespace (e.g., "hello   world" -> "hello world")
    """
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value.strip())
    return value


# =============================================================================
# Normalizer Registry
# =============================================================================

NORMALIZERS: Final[Dict[str, NormalizerFunc]] = {
    # Primary names
    "lowercase": _normalize_lowercase,
    "uppercase": _normalize_uppercase,
    "trim": _normalize_trim,
    "lowercase_underscore": _normalize_lowercase_underscore,
    "slug": _normalize_slug,
    "snake_case": _normalize_snake_case,
    "kebab_case": _normalize_kebab_case,
    "title_case": _normalize_title_case,
    "capitalize": _normalize_capitalize,
    "remove_whitespace": _normalize_remove_whitespace,
    "collapse_whitespace": _normalize_collapse_whitespace,
    # Aliases for common naming conventions
    "lower": _normalize_lowercase,
    "upper": _normalize_uppercase,
    "strip": _normalize_trim,
    "snakecase": _normalize_snake_case,
    "snake": _normalize_snake_case,
    "kebabcase": _normalize_kebab_case,
    "kebab": _normalize_kebab_case,
    "title": _normalize_title_case,
}
"""Registry of built-in normalizer functions.

Keys are normalizer names (used in x-normalize field).
Values are functions that take Any and return Any.

Built-in normalizers can be applied without external tool calls,
making them suitable for use in the Gate Planner.
"""


# =============================================================================
# Public API
# =============================================================================

def apply_normalization(
    value: Any,
    normalizer_name: str,
    custom_normalizers: Optional[Dict[str, NormalizerFunc]] = None,
) -> Any:
    """Apply a normalizer to a value.

    Looks up the normalizer by name and applies it to the value.
    Custom normalizers take precedence over built-in ones.

    Args:
        value: The value to normalize
        normalizer_name: Name of the normalizer (e.g., "lowercase", "slug")
        custom_normalizers: Optional dict of additional normalizers

    Returns:
        Normalized value (unchanged if normalizer not found for non-string)

    Raises:
        ValueError: If normalizer_name is not found in either registry

    Example:
        >>> apply_normalization("Hello World", "lowercase_underscore")
        'hello_world'
        >>> apply_normalization("MyClassName", "snake_case")
        'my_class_name'
        >>> apply_normalization(123, "lowercase")  # Non-string passthrough
        123
    """
    # Normalize the normalizer name (case-insensitive, strip whitespace)
    name = normalizer_name.lower().strip()

    # Check custom normalizers first (allows override)
    if custom_normalizers and name in custom_normalizers:
        return custom_normalizers[name](value)

    # Check built-in normalizers
    if name in NORMALIZERS:
        return NORMALIZERS[name](value)

    raise ValueError(
        f"Unknown normalizer: {normalizer_name!r}. "
        f"Available built-in: {sorted(NORMALIZERS.keys())}"
    )


def is_builtin_normalizer(normalizer_name: str) -> bool:
    """Check if a normalizer is a built-in (no external call needed).

    Built-in normalizers can be applied directly by the Gate Planner
    without making tool calls. Tool-based normalizers (email, phone,
    secret URI, etc.) are NOT built-in and require service-layer handling.

    Args:
        normalizer_name: Name of the normalizer

    Returns:
        True if this is a built-in normalizer

    Example:
        >>> is_builtin_normalizer("lowercase")
        True
        >>> is_builtin_normalizer("email")  # Requires tool call
        False
    """
    return normalizer_name.lower().strip() in NORMALIZERS


def get_available_normalizers() -> list[str]:
    """Get list of available built-in normalizer names.

    Returns:
        Sorted list of normalizer names (primary names only, no aliases)
    """
    # Return primary names only (filter out aliases by checking if multiple keys
    # map to the same function)
    seen_funcs: set[int] = set()
    primary_names: list[str] = []

    for name, func in sorted(NORMALIZERS.items()):
        func_id = id(func)
        if func_id not in seen_funcs:
            seen_funcs.add(func_id)
            primary_names.append(name)

    return primary_names


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "NORMALIZERS",
    "NormalizerFunc",
    "apply_normalization",
    "is_builtin_normalizer",
    "get_available_normalizers",
]
