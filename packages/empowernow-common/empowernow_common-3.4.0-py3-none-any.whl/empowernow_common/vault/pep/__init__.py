"""Policy Enforcement Point (PEP) components for vault access.

This subpackage provides PDP-enforced vault access, ensuring that
all secret reads/writes go through policy checks.

Components:
    - GrantCache: Caches authorization decisions (not secret values!)
    - SecretPolicyService: PDP facade for secret access policies
    - VaultClient: PDP-enforced wrapper for vault providers

Architecture:
    VaultProvider = Raw access (no policy enforcement)
    VaultClient = PDP-enforced wrapper (recommended for app code)

Security Model:
    - Decisions are cached with TTL (reduces PDP load)
    - Secret values are NEVER cached
    - JTI replay protection prevents token reuse
    - Sender binding (DPoP/mTLS) prevents credential sharing
"""
from __future__ import annotations

from empowernow_common.vault.pep.grant_cache import (
    Grant,
    GrantCache,
    GrantKey,
)
from empowernow_common.vault.pep.policy_service import (
    SecretPolicyService,
    BatchFailure,
)
from empowernow_common.vault.pep.enforced_client import (
    VaultClient,
    ExecutionContext,
)


__all__ = [
    # Grant cache
    "Grant",
    "GrantCache",
    "GrantKey",
    # Policy service
    "SecretPolicyService",
    "BatchFailure",
    # Enforced client
    "VaultClient",
    "ExecutionContext",
]
