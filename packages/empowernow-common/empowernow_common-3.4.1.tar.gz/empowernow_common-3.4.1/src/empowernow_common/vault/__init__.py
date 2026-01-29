"""Unified vault provider module for EmpowerNow.

This module provides a single source of truth for vault operations across
all EmpowerNow services. It follows the architecture defined in:
docs/VAULT_PROVIDER_UNIFICATION.md

Quick Start:
    # Load providers from configuration
    from empowernow_common.vault import load_vault_providers
    
    registry = await load_vault_providers(
        "/app/config/vault_providers.yaml",
        required_providers=["openbao"],
    )
    
    # Get a provider and read a secret
    provider = registry.get_provider("openbao")
    secret = await provider.get_secret("openbao://secret/app#token")

For PDP-enforced access (recommended for most app code):
    from empowernow_common.vault import VaultClient
    
    client = app.state.vault_client  # Pre-configured with PEP
    credentials = await client.get_credentials("openbao://secret/app#token", ctx)

Direct provider access is available but explicitly named:
    from empowernow_common.vault import VaultProviderRegistry, load_vault_providers

Architecture:
    - VaultProvider protocols (ReadableVaultProvider, WritableVaultProvider, etc.)
    - VaultProviderRegistry for multi-instance provider management
    - VaultClient (PEP-enforced) for application code
    - Provider implementations in vault.providers subpackage

Per Playbook §16.12: Extract to empowernow_common for shared library usage.
Per Playbook §19.2: Maintain backward compatibility with existing SDKs.
"""
from __future__ import annotations

# Base protocols and types
from empowernow_common.vault.base import (
    ReadableVaultProvider,
    WritableVaultProvider,
    EnumerableVaultProvider,
    FullVaultProvider,
    VaultProvider,
    Capabilities,
)

# Registry and configuration
from empowernow_common.vault.registry import (
    VaultProviderRegistry,
    ProviderStatus,
)
from empowernow_common.vault.config import (
    load_vault_providers,
    load_vault_providers_sync,
    register_provider_factory,
    ProviderConfig,
)

# URI parsing
from empowernow_common.vault.uri import (
    SecretURI,
    parse_secret_uri,
    parse,
)

# Redaction utilities
from empowernow_common.vault.redaction import (
    safe_format_uri,
    safe_format_path,
    compute_resource_ref,
)

# Exceptions
from empowernow_common.vault.exceptions import (
    VaultError,
    VaultConfigurationError,
    VaultConnectionError,
    VaultAuthenticationError,
    VaultAuthorizationError,
    VaultOperationError,
    VaultSecretNotFoundError,
    VaultSecretVersionError,
    VaultSecretVersionDeletedError,
    VaultSecretVersionDestroyedError,
    VaultTimeoutError,
    VaultURIError,
    StartupValidationError,
    UnsupportedURISchemeError,
)

# PEP components (Policy Enforcement Point)
from empowernow_common.vault.pep import (
    Grant,
    GrantCache,
    GrantKey,
    SecretPolicyService,
    BatchFailure,
    VaultClient,
    ExecutionContext,
)

# Re-export PEP errors
from empowernow_common.vault.pep.policy_service import (
    AuthzDeniedError,
    PDPUnavailableError,
    BindingDriftError,
)


__all__ = [
    # Protocols
    "ReadableVaultProvider",
    "WritableVaultProvider",
    "EnumerableVaultProvider",
    "FullVaultProvider",
    "VaultProvider",
    "Capabilities",
    # Registry
    "VaultProviderRegistry",
    "ProviderStatus",
    # Configuration
    "load_vault_providers",
    "load_vault_providers_sync",
    "register_provider_factory",
    "ProviderConfig",
    # URI
    "SecretURI",
    "parse_secret_uri",
    "parse",
    # Redaction
    "safe_format_uri",
    "safe_format_path",
    "compute_resource_ref",
    # Exceptions
    "VaultError",
    "VaultConfigurationError",
    "VaultConnectionError",
    "VaultAuthenticationError",
    "VaultAuthorizationError",
    "VaultOperationError",
    "VaultSecretNotFoundError",
    "VaultSecretVersionError",
    "VaultSecretVersionDeletedError",
    "VaultSecretVersionDestroyedError",
    "VaultTimeoutError",
    "VaultURIError",
    "StartupValidationError",
    "UnsupportedURISchemeError",
    # PEP components
    "Grant",
    "GrantCache",
    "GrantKey",
    "SecretPolicyService",
    "BatchFailure",
    "VaultClient",
    "ExecutionContext",
    "AuthzDeniedError",
    "PDPUnavailableError",
    "BindingDriftError",
]
