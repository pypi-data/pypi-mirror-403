"""Vault provider protocols with capability splitting.

Per design Decision 4: Protocol Capability Splitting
- Separate protocols for different capability levels
- Providers implement only the protocols they support
- No NotImplementedError scatter

Protocol Hierarchy:
    ReadableVaultProvider       - Minimum: read operations
    WritableVaultProvider       - Extends with write operations  
    EnumerableVaultProvider     - Extends with list operations
    FullVaultProvider           - All CRUD + list operations

Per Playbook §16.5: Use @runtime_checkable Protocol for interfaces.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class ReadableVaultProvider(Protocol):
    """Minimum required interface: read operations.
    
    All vault providers MUST implement this protocol.
    
    Attributes:
        VAULT_TYPE: Provider type identifier (e.g., "openbao", "yaml")
        CAPABILITIES: Dictionary of supported capabilities
    
    Methods:
        get_secret: Get a single secret value by reference
        get_credentials: Get credentials as a dictionary
        get_secret_or_none: Get secret value or None if not found
        close: Cleanup resources
    
    Per design Decision 3: Fail-closed semantics
    - get_secret() raises VaultSecretNotFoundError if not found
    - get_secret_or_none() is the explicit Optional variant
    """
    
    VAULT_TYPE: str
    CAPABILITIES: Dict[str, bool]
    
    async def get_secret(self, reference: str) -> str:
        """Get secret value by reference.
        
        Args:
            reference: Secret URI or path (e.g., "openbao://secret/app#token")
        
        Returns:
            The secret value as a string
        
        Raises:
            VaultSecretNotFoundError: Secret does not exist
            VaultAuthenticationError: Auth failure
            VaultAuthorizationError: Permission denied
            VaultOperationError: Other failures
        """
        ...
    
    async def get_credentials(self, reference: str) -> Dict[str, Any]:
        """Get credentials as a dictionary.
        
        Similar to get_secret() but returns the full secret payload
        as a dictionary (for multi-field credentials).
        
        Args:
            reference: Secret URI or path
        
        Returns:
            Dictionary containing all credential fields
        
        Raises:
            VaultSecretNotFoundError: Secret does not exist
            VaultAuthenticationError: Auth failure
            VaultAuthorizationError: Permission denied
            VaultOperationError: Other failures
        """
        ...
    
    async def get_secret_or_none(self, reference: str) -> Optional[str]:
        """Get secret value or None if not found.
        
        Convenience method for callers who want Optional semantics.
        
        Args:
            reference: Secret URI or path
        
        Returns:
            The secret value or None if not found
        
        Raises:
            VaultAuthenticationError: Auth failure
            VaultAuthorizationError: Permission denied
            VaultOperationError: Other failures (not including not-found)
        """
        ...
    
    async def close(self) -> None:
        """Close and cleanup any resources (HTTP clients, connections).
        
        Should be called when the provider is no longer needed.
        Safe to call multiple times.
        """
        ...


@runtime_checkable
class WritableVaultProvider(ReadableVaultProvider, Protocol):
    """Extends ReadableVaultProvider with write operations.
    
    Providers that support creating, updating, and deleting secrets
    should implement this protocol.
    """
    
    async def create_or_update_secret(
        self,
        path: str,
        data: Dict[str, Any],
        *,
        custom_metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create or update a secret at the specified path.
        
        Args:
            path: The secret path (e.g., "secret/app/api")
            data: Dictionary of secret key-value pairs
            custom_metadata: Optional metadata to attach (OpenBao/Vault KV v2)
        
        Returns:
            Dictionary with operation result (version, created_time, etc.)
        
        Raises:
            VaultAuthenticationError: Auth failure
            VaultAuthorizationError: Permission denied
            VaultOperationError: Other failures
        """
        ...
    
    async def delete_secret(
        self,
        path: str,
        *,
        permanent: bool = False,
    ) -> None:
        """Delete a secret at the specified path.
        
        Args:
            path: The secret path
            permanent: If True, permanently destroy all versions.
                      If False, soft-delete (recoverable).
        
        Raises:
            VaultSecretNotFoundError: Secret does not exist
            VaultAuthenticationError: Auth failure
            VaultAuthorizationError: Permission denied
            VaultOperationError: Other failures
        """
        ...


@runtime_checkable
class EnumerableVaultProvider(ReadableVaultProvider, Protocol):
    """Extends ReadableVaultProvider with list operations.
    
    Providers that support listing secrets should implement this protocol.
    """
    
    async def list_keys(self, path: str = "") -> List[str]:
        """List secret keys at the specified path.
        
        Args:
            path: Path prefix to list (e.g., "secret/app/")
                 Empty string lists from root.
        
        Returns:
            List of key names at the path
        
        Raises:
            VaultAuthenticationError: Auth failure
            VaultAuthorizationError: Permission denied
            VaultOperationError: Other failures
        
        Note:
            Returns empty list if path doesn't exist (not an error).
        """
        ...


@runtime_checkable
class FullVaultProvider(WritableVaultProvider, EnumerableVaultProvider, Protocol):
    """Full CRUD + list operations.
    
    OpenBao, Azure Key Vault, and similar full-featured providers
    should implement this protocol.
    """
    
    pass


# Type alias for "any vault provider" (minimum interface)
VaultProvider = ReadableVaultProvider


# Capability constants for provider registration
class Capabilities:
    """Standard capability flags for providers."""
    
    LIST_KEYS = "list_keys"
    READ_SECRET = "read_secret"
    WRITE_SECRET = "write_secret"
    DELETE_SECRET = "delete_secret"
    METADATA = "metadata"
    READ_METADATA = "read_metadata"
    UPDATE_METADATA = "update_metadata"
    VERSIONING = "versioning"
    VERSION_PIN = "version_pin"
    SOFT_DELETE = "soft_delete"
    HARD_DESTROY = "hard_destroy"
    RESPONSE_WRAPPING = "response_wrapping"
    IDENTITY_SCOPING = "identity_scoping"
    OWNERSHIP_TRACKING = "ownership_tracking"
    AUDIT_METADATA = "audit_metadata"
    TAGS = "tags"
    
    @classmethod
    def full_capabilities(cls) -> Dict[str, bool]:
        """Return capabilities for a full-featured provider (OpenBao)."""
        return {
            cls.LIST_KEYS: True,
            cls.READ_SECRET: True,
            cls.WRITE_SECRET: True,
            cls.DELETE_SECRET: True,
            cls.METADATA: True,
            cls.READ_METADATA: True,
            cls.UPDATE_METADATA: True,
            cls.VERSIONING: True,
            cls.VERSION_PIN: True,
            cls.SOFT_DELETE: True,
            cls.HARD_DESTROY: True,
            cls.RESPONSE_WRAPPING: True,
            cls.IDENTITY_SCOPING: True,
            cls.OWNERSHIP_TRACKING: True,
            cls.AUDIT_METADATA: True,
            cls.TAGS: True,
        }
    
    @classmethod
    def read_only_capabilities(cls) -> Dict[str, bool]:
        """Return capabilities for a read-only provider (DB)."""
        return {
            cls.LIST_KEYS: False,
            cls.READ_SECRET: True,
            cls.WRITE_SECRET: False,
            cls.DELETE_SECRET: False,
            cls.METADATA: False,
            cls.READ_METADATA: False,
            cls.UPDATE_METADATA: False,
            cls.VERSIONING: False,
            cls.VERSION_PIN: False,
            cls.SOFT_DELETE: False,
            cls.HARD_DESTROY: False,
            cls.RESPONSE_WRAPPING: False,
            cls.IDENTITY_SCOPING: False,
            cls.OWNERSHIP_TRACKING: False,
            cls.AUDIT_METADATA: False,
            cls.TAGS: False,
        }
    
    @classmethod
    def yaml_capabilities(cls) -> Dict[str, bool]:
        """Return capabilities for YAML provider (dev only)."""
        return {
            cls.LIST_KEYS: True,
            cls.READ_SECRET: True,
            cls.WRITE_SECRET: True,  # Dev only!
            cls.DELETE_SECRET: False,
            cls.METADATA: False,
            cls.READ_METADATA: False,
            cls.UPDATE_METADATA: False,
            cls.VERSIONING: False,
            cls.VERSION_PIN: False,
            cls.SOFT_DELETE: False,
            cls.HARD_DESTROY: False,
            cls.RESPONSE_WRAPPING: False,
            cls.IDENTITY_SCOPING: True,
            cls.OWNERSHIP_TRACKING: True,
            cls.AUDIT_METADATA: False,
            cls.TAGS: True,
        }
