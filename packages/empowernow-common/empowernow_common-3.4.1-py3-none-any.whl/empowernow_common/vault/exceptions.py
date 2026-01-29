"""Unified exception hierarchy for vault operations.

Per Playbook §9 - Centralized exception handling with proper error codes.

Exception Hierarchy:
    VaultError (base)
    ├── VaultConfigurationError     - Invalid configuration
    ├── VaultConnectionError        - Network/connectivity issues
    ├── VaultAuthenticationError    - Auth failures (token, approle)
    ├── VaultAuthorizationError     - Permission denied
    ├── VaultOperationError         - General operation failures
    │   ├── VaultSecretNotFoundError    - Secret doesn't exist
    │   ├── VaultSecretVersionError     - Version-specific errors
    │   └── VaultTimeoutError           - Operation timed out
    └── VaultURIError               - Invalid secret URI format
"""
from __future__ import annotations

from typing import Optional

from empowernow_common.vault.redaction import safe_format_uri


class VaultError(Exception):
    """Base exception for all vault-related errors.
    
    Attributes:
        code: Machine-readable error code for API responses
        message: Human-readable error message
        details: Optional additional context
    """
    
    def __init__(
        self,
        message: str,
        *,
        code: str = "VAULT_ERROR",
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        result = {"code": self.code, "message": self.message}
        if self.details:
            result["details"] = self.details
        return result


class VaultConfigurationError(VaultError):
    """Invalid vault configuration."""
    
    def __init__(self, message: str, *, details: Optional[dict] = None) -> None:
        super().__init__(message, code="VAULT_CONFIG_ERROR", details=details)


class VaultConnectionError(VaultError):
    """Failed to connect to vault backend."""
    
    def __init__(self, message: str, *, details: Optional[dict] = None) -> None:
        super().__init__(message, code="VAULT_CONNECTION_ERROR", details=details)


class VaultAuthenticationError(VaultError):
    """Authentication failed (invalid token, expired credentials, etc.)."""
    
    def __init__(self, message: str, *, details: Optional[dict] = None) -> None:
        super().__init__(message, code="VAULT_AUTH_ERROR", details=details)


class VaultAuthorizationError(VaultError):
    """Authorization denied (insufficient permissions)."""
    
    def __init__(self, message: str, *, resource: Optional[str] = None) -> None:
        # Redact resource path in error message for security
        safe_resource = safe_format_uri(resource) if resource else None
        details = {"resource": safe_resource} if safe_resource else None
        super().__init__(message, code="VAULT_AUTHZ_ERROR", details=details)


class VaultOperationError(VaultError):
    """General vault operation failure."""
    
    def __init__(self, message: str, *, code: str = "VAULT_OPERATION_ERROR", details: Optional[dict] = None) -> None:
        super().__init__(message, code=code, details=details)


class VaultSecretNotFoundError(VaultOperationError):
    """Secret not found at specified path.
    
    Per design Decision 3: Fail-closed semantics - all methods raise on not-found.
    """
    
    def __init__(self, path: str) -> None:
        # Redact path for security per design §A
        safe_path = safe_format_uri(path)
        super().__init__(
            f"Secret not found: {safe_path}",
            code="SECRET_NOT_FOUND",
        )
        self._raw_path = path  # Available for debugging if needed


class VaultSecretVersionError(VaultOperationError):
    """Version-specific error (deleted, destroyed, etc.)."""
    
    def __init__(self, path: str, version: int, reason: str) -> None:
        safe_path = safe_format_uri(path)
        super().__init__(
            f"Secret version {version} {reason}: {safe_path}",
            code="SECRET_VERSION_ERROR",
            details={"version": version, "reason": reason},
        )


class VaultSecretVersionDeletedError(VaultSecretVersionError):
    """Secret version has been soft-deleted (recoverable)."""
    
    def __init__(self, path: str, version: int) -> None:
        super().__init__(path, version, "is deleted (soft-delete)")


class VaultSecretVersionDestroyedError(VaultSecretVersionError):
    """Secret version has been permanently destroyed (unrecoverable)."""
    
    def __init__(self, path: str, version: int) -> None:
        super().__init__(path, version, "is destroyed (permanent)")


class VaultTimeoutError(VaultOperationError):
    """Vault operation timed out."""
    
    def __init__(self, message: str = "Vault operation timed out") -> None:
        super().__init__(message, code="VAULT_TIMEOUT")


class VaultURIError(VaultError):
    """Invalid secret URI format.
    
    Error codes:
        - ILLEGAL_SEGMENT: Invalid characters or traversal
        - UNSUPPORTED_SCHEME: Unknown provider/engine
        - TENANT_MOUNT_MISMATCH: Mount not allowed for tenant
        - DOUBLE_MOUNT_SOURCE: Mount specified multiple ways
        - AMBIGUOUS_QUERY: Duplicate query parameters
        - INVALID_WILDCARD: Wildcards not allowed
    """
    
    # Standard error codes
    ILLEGAL_SEGMENT = "ILLEGAL_SEGMENT"
    UNSUPPORTED_SCHEME = "UNSUPPORTED_SCHEME"
    TENANT_MOUNT_MISMATCH = "TENANT_MOUNT_MISMATCH"
    DOUBLE_MOUNT_SOURCE = "DOUBLE_MOUNT_SOURCE"
    AMBIGUOUS_QUERY = "AMBIGUOUS_QUERY"
    INVALID_WILDCARD = "INVALID_WILDCARD"
    
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message, code=code)


class StartupValidationError(VaultError):
    """Provider failed startup validation (connectivity check)."""
    
    def __init__(self, provider_name: str, message: str) -> None:
        super().__init__(
            f"Provider '{provider_name}' startup validation failed: {message}",
            code="STARTUP_VALIDATION_ERROR",
            details={"provider": provider_name},
        )


# Aliases for backward compatibility
UnsupportedURISchemeError = VaultURIError
