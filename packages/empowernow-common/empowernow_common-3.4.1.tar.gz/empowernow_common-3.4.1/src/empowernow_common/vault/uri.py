"""Secret URI parsing with canonical rules.

Per design Decision 1: URI Scheme Semantics
- Scheme = Instance Name (the registered provider instance)
- Engine type is an optional modifier (+kv2)
- DB provider uses colon format, NOT supported here (see Decision 2)

Canonical URI Format:
    <instance>://[mount/]<path>[#fragment][?params]
    
    Examples:
        openbao://secret/app/api#token           → instance="openbao", path="secret/app/api", key="token"
        openbao-prod://secret/app#key            → instance="openbao-prod"
        akv-prod-eu://secret-name#key            → instance="akv-prod-eu"
        openbao+kv2://secret/app#token           → instance="openbao", engine="kv2"
        yaml://dev/secrets#db_pass               → instance="yaml"
        file://dc-infra/kafka-password           → instance="file" (file provider)
        
    NOT SUPPORTED (handled separately):
        db:credentials:uuid                      → DB provider, colon format
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from empowernow_common.vault.exceptions import VaultURIError


# Allowed providers (instance name prefixes)
_ALLOWED_PROVIDERS = frozenset({
    "openbao",
    "hashicorp", 
    "vault",  # Alias for hashicorp
    "yaml",
    "file",
    "azure",  # Azure Key Vault
    "akv",    # Alias for azure
})

# Provider-specific allowed engines
_ALLOWED_ENGINES = {
    "openbao": frozenset({"kv2", "kv1"}),
    "hashicorp": frozenset({"kv2", "kv1"}),
    "vault": frozenset({"kv2", "kv1"}),
    "yaml": frozenset(),
    "file": frozenset(),
    "azure": frozenset(),
    "akv": frozenset(),
}

# Valid segment pattern: alphanumeric, dots, dashes, underscores
_SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")

# Instance name pattern: allows hyphens for multi-instance names like "openbao-prod"
_INSTANCE_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")


@dataclass(frozen=True)
class SecretURI:
    """Parsed secret URI with all components.
    
    Attributes:
        instance: The provider instance name (scheme without engine)
        engine: Optional engine type (e.g., "kv2")
        mount: The mount point (first path segment)
        path_segments: Remaining path segments after mount
        fragment_key: The key to extract from the secret (#token)
        params: Sorted query parameters as tuple of (key, value)
        original: The original URI string
    """
    instance: str
    engine: Optional[str]
    mount: str
    path_segments: Tuple[str, ...]
    fragment_key: Optional[str]
    params: Tuple[Tuple[str, str], ...]
    original: str
    
    @property
    def provider(self) -> str:
        """Get the base provider type (normalizes aliases)."""
        if self.instance.startswith("openbao"):
            return "openbao"
        if self.instance.startswith(("hashicorp", "vault")):
            return "hashicorp"
        if self.instance.startswith(("azure", "akv")):
            return "azure"
        # For custom instance names, return the base provider
        base = self.instance.split("-")[0]
        return base if base in _ALLOWED_PROVIDERS else self.instance
    
    @property
    def full_path(self) -> str:
        """Get the full path including mount."""
        return "/".join([self.mount, *self.path_segments])
    
    def to_canonical(self) -> str:
        """Convert back to canonical URI string."""
        scheme = self.instance if self.engine is None else f"{self.instance}+{self.engine}"
        path = self.full_path
        canonical = f"{scheme}://{path}"
        
        if self.fragment_key:
            canonical += f"#{self.fragment_key}"
        
        if self.params:
            query = "&".join(f"{k}={v}" for k, v in self.params)
            canonical += f"?{query}"
        
        return canonical
    
    def with_version(self, version: int) -> "SecretURI":
        """Create a new URI with a specific version parameter."""
        # Filter out existing version param
        new_params = tuple((k, v) for k, v in self.params if k != "version")
        new_params = (*new_params, ("version", str(version)))
        new_params = tuple(sorted(new_params, key=lambda x: x[0]))
        
        return SecretURI(
            instance=self.instance,
            engine=self.engine,
            mount=self.mount,
            path_segments=self.path_segments,
            fragment_key=self.fragment_key,
            params=new_params,
            original=self.original,
        )


def _extract_base_provider(instance: str) -> str:
    """Extract base provider from instance name for validation."""
    # Handle multi-instance names like "openbao-prod", "akv-prod-eu"
    base = instance.split("-")[0]
    return base


def _validate_scheme(scheme: str) -> Tuple[str, Optional[str]]:
    """Validate and parse scheme into instance and engine."""
    scheme = scheme.lower()
    
    # Check for engine modifier (e.g., openbao+kv2)
    if "+" in scheme:
        instance, engine = scheme.split("+", 1)
    else:
        instance, engine = scheme, None
    
    # Validate instance name format
    if not _INSTANCE_PATTERN.match(instance):
        raise VaultURIError(
            VaultURIError.UNSUPPORTED_SCHEME,
            f"Invalid instance name format: {instance}. "
            f"Must start with lowercase letter and contain only alphanumeric and hyphens.",
        )
    
    # Validate that the base provider is known
    base = _extract_base_provider(instance)
    if base not in _ALLOWED_PROVIDERS:
        raise VaultURIError(
            VaultURIError.UNSUPPORTED_SCHEME,
            f"Unsupported provider: {instance}. "
            f"Valid provider prefixes: {', '.join(sorted(_ALLOWED_PROVIDERS))}",
        )
    
    # Validate engine if specified
    if engine:
        allowed_engines = _ALLOWED_ENGINES.get(base, frozenset())
        if engine not in allowed_engines:
            raise VaultURIError(
                VaultURIError.UNSUPPORTED_SCHEME,
                f"Unsupported engine '{engine}' for provider '{instance}'. "
                f"Allowed: {', '.join(sorted(allowed_engines)) if allowed_engines else 'none'}",
            )
    
    return instance, engine


def _parse_path_and_query(rest: str) -> Tuple[str, Optional[str], dict]:
    """Parse path, fragment, and query from URI rest.
    
    Standard URI format: path?query#fragment
    """
    fragment: Optional[str] = None
    query_str: Optional[str] = None
    path = rest
    
    # Standard URI format: query comes before fragment
    # Split fragment first (everything after #)
    if "#" in path:
        path, fragment = path.split("#", 1)
        if "#" in fragment:
            raise VaultURIError(
                VaultURIError.ILLEGAL_SEGMENT,
                "Multiple fragments not allowed",
            )
    
    # Split query (everything between ? and # or end)
    if "?" in path:
        path, query_str = path.split("?", 1)
    
    # Parse query params
    params: dict = {}
    if query_str:
        for pair in query_str.split("&"):
            if not pair:
                continue
            if "=" in pair:
                k, v = pair.split("=", 1)
            else:
                k, v = pair, ""
            if k in params:
                raise VaultURIError(
                    VaultURIError.AMBIGUOUS_QUERY,
                    f"Duplicate query parameter: {k}",
                )
            params[k] = v
    
    # Check for mount in query (not allowed)
    if "mount" in params:
        raise VaultURIError(
            VaultURIError.DOUBLE_MOUNT_SOURCE,
            "Mount must be in path, not query parameters",
        )
    
    return path, fragment, params


def _validate_path_segments(path: str) -> List[str]:
    """Validate and split path into segments."""
    # Security checks
    lowered = path.lower()
    if "%2f" in lowered:
        raise VaultURIError(
            VaultURIError.ILLEGAL_SEGMENT,
            "URL-encoded slashes not allowed",
        )
    if ".." in path:
        raise VaultURIError(
            VaultURIError.ILLEGAL_SEGMENT,
            "Path traversal (..) not allowed",
        )
    
    # Normalize trailing slash
    path = path.rstrip("/")
    
    # Split into segments
    segments = path.split("/") if path else []
    
    # Validate each segment
    for seg in segments:
        if not seg:
            raise VaultURIError(
                VaultURIError.ILLEGAL_SEGMENT,
                "Empty path segment (duplicate slashes)",
            )
        if "*" in seg:
            raise VaultURIError(
                VaultURIError.INVALID_WILDCARD,
                "Wildcards not allowed in path",
            )
        if not _SEGMENT_PATTERN.match(seg):
            raise VaultURIError(
                VaultURIError.ILLEGAL_SEGMENT,
                f"Invalid characters in segment: {seg}",
            )
    
    if not segments:
        raise VaultURIError(
            VaultURIError.ILLEGAL_SEGMENT,
            "Path must have at least one segment (mount)",
        )
    
    return segments


def parse_secret_uri(
    uri: str,
    *,
    tenant_id: str = "default",
    allowed_mounts: Optional[List[str]] = None,
) -> SecretURI:
    """Parse a secret URI into its components.
    
    Args:
        uri: The secret URI to parse
        tenant_id: Tenant identifier for mount validation
        allowed_mounts: List of allowed mount names for this tenant.
                       If None, all mounts are allowed.
    
    Returns:
        Parsed SecretURI object
    
    Raises:
        VaultURIError: If URI is invalid or mount not allowed
    
    Examples:
        >>> uri = parse_secret_uri("openbao://secret/app/api#token")
        >>> uri.instance
        'openbao'
        >>> uri.full_path
        'secret/app/api'
        >>> uri.fragment_key
        'token'
    
    Note:
        DB provider format (db:credentials:xxx) is NOT supported here.
        Use VaultService's special case handling for DB URIs.
    """
    if not uri:
        raise VaultURIError(VaultURIError.ILLEGAL_SEGMENT, "Empty URI")
    
    # Check for non-URI format (db:credentials:xxx)
    if "://" not in uri:
        raise VaultURIError(
            VaultURIError.UNSUPPORTED_SCHEME,
            f"Invalid URI format (missing ://). "
            f"DB provider format (db:credentials:xxx) is not supported by the unified registry.",
        )
    
    # Split scheme and rest
    scheme, rest = uri.split("://", 1)
    if not scheme:
        raise VaultURIError(VaultURIError.ILLEGAL_SEGMENT, "Empty scheme")
    
    # Validate and parse scheme
    instance, engine = _validate_scheme(scheme)
    
    # Parse path, fragment, and query
    path, fragment, params = _parse_path_and_query(rest)
    
    # Validate path segments
    segments = _validate_path_segments(path)
    
    # Extract mount (first segment)
    mount = segments[0]
    path_segments = tuple(segments[1:])
    
    # Validate mount against allowed list
    if allowed_mounts and mount not in allowed_mounts:
        raise VaultURIError(
            VaultURIError.TENANT_MOUNT_MISMATCH,
            f"Mount '{mount}' not allowed for tenant '{tenant_id}'. "
            f"Allowed: {', '.join(allowed_mounts)}",
        )
    
    # Sort params for canonical representation
    sorted_params = tuple(sorted(params.items(), key=lambda x: x[0]))
    
    return SecretURI(
        instance=instance,
        engine=engine,
        mount=mount,
        path_segments=path_segments,
        fragment_key=fragment,
        params=sorted_params,
        original=uri,
    )


# Convenience alias
parse = parse_secret_uri
