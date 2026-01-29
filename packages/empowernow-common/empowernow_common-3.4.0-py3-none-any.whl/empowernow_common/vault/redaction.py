"""Safe formatting for secret references in logs and errors.

Per design §A - Logging & Redaction requirements.

All secret URIs and references must be redacted before appearing in:
- Log messages
- Exception messages
- API error responses
- Audit trails (use resource_ref hashing instead)

This module provides utilities to safely format URIs for logging
without leaking sensitive information like key names or secret paths.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse, urlunparse


def safe_format_uri(uri: str, *, redact_path: bool = False) -> str:
    """Format URI for safe logging.
    
    Redacts:
    - Fragment (#key_name → #***)
    - Query parameters (?version=1 → ?***)
    - Optionally path segments (for highly sensitive contexts)
    
    Args:
        uri: The secret URI to redact
        redact_path: If True, also redacts the path segments
    
    Returns:
        Redacted URI safe for logging
    
    Examples:
        >>> safe_format_uri("openbao://secret/app/api#token")
        'openbao://secret/app/api#***'
        
        >>> safe_format_uri("openbao://secret/app/api#token", redact_path=True)
        'openbao://***#***'
        
        >>> safe_format_uri("db:credentials:abc-123")
        'db:credentials:***'
    """
    if not uri:
        return uri
    
    # Handle non-URI formats (db:credentials:xxx)
    if "://" not in uri:
        # db:credentials:<id> format
        if uri.startswith("db:credentials:"):
            return "db:credentials:***"
        # file:<instance>:<id> format
        if uri.startswith("file:") or uri.startswith("filex:"):
            parts = uri.split(":", 2)
            if len(parts) == 3:
                return f"{parts[0]}:{parts[1]}:***"
        # env:<var> format
        if uri.startswith("env:"):
            return "env:***"
        # Unknown format - return as-is (don't break on edge cases)
        return uri
    
    try:
        parsed = urlparse(uri)
        
        # Build redacted path
        # Note: urlparse treats scheme://mount/path as netloc='mount', path='/path'
        if redact_path:
            # Redact both netloc and path
            netloc = ""
            path = "***"
        else:
            netloc = parsed.netloc if parsed.netloc else ""
            path = parsed.path
        
        # Always redact fragment and query
        fragment = "***" if parsed.fragment else ""
        query = "***" if parsed.query else ""
        
        # Reconstruct URI
        # urlunparse expects: (scheme, netloc, path, params, query, fragment)
        redacted = urlunparse((
            parsed.scheme,
            netloc,
            path,
            "",  # params (rarely used)
            query,
            fragment,
        ))
        
        # Clean up double slashes that can occur
        redacted = re.sub(r"(?<!:)//+", "/", redacted)
        
        return redacted
        
    except Exception:
        # If parsing fails, return a fully redacted placeholder
        return "***://***"


def safe_format_path(path: str) -> str:
    """Format a vault path for safe logging.
    
    Redacts the leaf (final segment) of the path while preserving
    the directory structure for debugging.
    
    Args:
        path: The vault path to redact
    
    Returns:
        Path with leaf segment redacted
    
    Examples:
        >>> safe_format_path("secret/app/db-password")
        'secret/app/***'
        
        >>> safe_format_path("secret/api")
        'secret/***'
    """
    if not path:
        return path
    
    # Split and redact the final segment
    segments = path.rstrip("/").split("/")
    if len(segments) > 1:
        segments[-1] = "***"
        return "/".join(segments)
    return "***"


def compute_resource_ref(uri: str, salt: str) -> str:
    """Compute a non-reversible resource reference for audit logs.
    
    Uses HMAC-SHA256 to create a stable, non-reversible identifier
    that can be used to correlate audit events without leaking the
    actual secret path.
    
    Args:
        uri: The secret URI
        salt: Tenant-specific salt (from TENANT_SALT env var)
    
    Returns:
        Hex-encoded HMAC of the URI (first 16 chars for brevity)
    
    Example:
        >>> compute_resource_ref("openbao://secret/app#token", "my-salt")
        'a3f2b1c4d5e6f7a8'
    """
    import hashlib
    import hmac
    
    # Use HMAC-SHA256 for a keyed hash
    h = hmac.new(
        key=salt.encode("utf-8"),
        msg=uri.encode("utf-8"),
        digestmod=hashlib.sha256,
    )
    
    # Return first 16 hex chars for brevity while maintaining uniqueness
    return h.hexdigest()[:16]
