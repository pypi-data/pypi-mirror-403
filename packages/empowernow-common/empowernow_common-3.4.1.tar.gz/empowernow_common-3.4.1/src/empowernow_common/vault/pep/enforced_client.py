"""PDP-enforced vault client.

Per design §B - Authorization Boundary Clarity:
    - VaultProvider = raw access (admin/internal tooling only)
    - VaultClient = PDP-enforced wrapper (recommended for app code)

Most application code should use VaultClient, not direct provider access.
This ensures all secret access goes through policy checks.
"""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from empowernow_common.vault.registry import VaultProviderRegistry
from empowernow_common.vault.uri import parse_secret_uri
from empowernow_common.vault.pep.grant_cache import GrantCache, GrantKey
from empowernow_common.vault.pep.policy_service import (
    SecretPolicyService,
    AuthzDeniedError,
    PDPUnavailableError,
    BindingDriftError,
)
from empowernow_common.vault.exceptions import VaultURIError


logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context for a vault request, extracted from the incoming request.
    
    Contains identity, authentication, and request metadata needed
    for policy evaluation and audit logging.
    
    Attributes:
        subject: Identity ARN of the requester
        tenant_id: Tenant identifier
        cnf_jkt: DPoP confirmation key thumbprint
        mtls_thumbprint: mTLS certificate thumbprint
        token_jti: JWT ID for replay protection
        aud: Token audience(s)
        issuer: Token issuer
        client_id: OAuth client ID
        correlation_id: Request correlation ID for tracing
        workflow_run_id: Workflow execution ID (if applicable)
        node_id: Workflow node ID (if applicable)
        system_id: Target system ID (if applicable)
    """
    
    subject: Optional[str] = None
    tenant_id: str = "default"
    cnf_jkt: Optional[str] = None
    mtls_thumbprint: Optional[str] = None
    token_jti: Optional[str] = None
    aud: Optional[list] = None
    issuer: Optional[str] = None
    client_id: Optional[str] = None
    correlation_id: Optional[str] = None
    workflow_run_id: Optional[str] = None
    node_id: Optional[str] = None
    system_id: Optional[str] = None
    
    @property
    def cnf_binding(self) -> Optional[str]:
        """Get the sender binding (prefers DPoP over mTLS)."""
        return self.cnf_jkt or self.mtls_thumbprint


@dataclass
class VaultClient:
    """PDP-enforced vault client.
    
    This is the recommended way to access secrets in application code.
    It wraps the provider registry and enforces policy checks on every
    access.
    
    Usage:
        # In FastAPI lifespan
        registry = await load_vault_providers(...)
        vault_client = VaultClient(registry=registry)
        app.state.vault_client = vault_client
        
        # In route handler
        @app.get("/api/data")
        async def get_data(
            vault: VaultClient = Depends(get_vault_client),
            ctx: ExecutionContext = Depends(get_execution_context),
        ):
            creds = await vault.get_credentials(
                "openbao://secret/db#password",
                ctx,
            )
            ...
    
    Per design:
        - Uses GrantCache for authorization decisions (not values!)
        - Enforces sender binding (DPoP/mTLS)
        - JTI replay protection
        - Audience validation
    """
    
    registry: VaultProviderRegistry
    cache: GrantCache = field(default_factory=GrantCache)
    policy: SecretPolicyService = field(default_factory=SecretPolicyService)
    expected_aud: str = field(default_factory=lambda: os.getenv("SECRETS_AUDIENCE", "crud.secrets"))
    default_tenant_id: str = field(default_factory=lambda: os.getenv("TENANT_ID", "default"))
    allowed_mounts: list = field(default_factory=lambda: [
        m.strip() for m in os.getenv("TENANT_ALLOWED_MOUNTS", "secret").split(",")
        if m.strip()
    ])
    
    async def get_credentials(
        self,
        canonical_uri: str,
        ctx: Optional[ExecutionContext] = None,
    ) -> Dict[str, Any]:
        """Get credentials with PDP enforcement.
        
        Args:
            canonical_uri: Canonical secret URI (e.g., "openbao://secret/app#token")
            ctx: Execution context with identity and request metadata
        
        Returns:
            Dictionary of credential key-value pairs
        
        Raises:
            AuthzDeniedError: Authorization denied by policy
            PDPUnavailableError: PDP service unavailable
            BindingDriftError: Sender binding changed
            VaultURIError: Invalid URI format
            VaultSecretNotFoundError: Secret not found
            VaultOperationError: Other vault errors
        """
        # Parse and validate URI
        tenant_id = (ctx.tenant_id if ctx else None) or self.default_tenant_id
        
        try:
            uri = parse_secret_uri(
                canonical_uri,
                tenant_id=tenant_id,
                allowed_mounts=self.allowed_mounts,
            )
        except VaultURIError:
            raise
        
        canonical = uri.to_canonical()
        subject = (ctx.subject if ctx else None) or "anonymous"
        cnf_binding = ctx.cnf_binding if ctx else None
        token_jti = ctx.token_jti if ctx else None
        audiences = set(ctx.aud or []) if ctx and ctx.aud else set()
        
        # Build grant key (ignoring binding to detect drift)
        grant_key: GrantKey = (subject, tenant_id, canonical, "execute", None)
        
        # Quick deny from negative cache
        if self.cache.is_negative(grant_key):
            raise AuthzDeniedError("SECRET_AUTHZ_FAILED")
        
        grant = self.cache.get(grant_key)
        
        if grant is None:
            # Audience check (if provided)
            if audiences and self.expected_aud not in audiences:
                self.cache.set_negative(grant_key)
                raise AuthzDeniedError("SECRET_AUTHZ_FAILED")
            
            # Anti-replay (if JTI provided)
            if token_jti and not self.cache.mark_jti(str(token_jti)):
                self.cache.set_negative(grant_key)
                raise AuthzDeniedError("SECRET_AUTHZ_FAILED")
            
            # Call PDP for authorization
            try:
                grant = await self.policy.authorize_use(
                    subject,
                    tenant_id,
                    canonical,
                    "execute",
                    cnf_binding,
                )
            except AuthzDeniedError:
                self.cache.set_negative(grant_key)
                raise
            except PDPUnavailableError:
                self.cache.set_negative(grant_key)
                raise
            
            self.cache.put(grant_key, grant)
        
        else:
            # Enforce sender binding drift
            if grant.cnf_binding and cnf_binding and grant.cnf_binding != cnf_binding:
                self.cache.set_negative(grant_key)
                raise BindingDriftError("BINDING_DRIFT")
        
        # Increment use count
        if not self.cache.increment_uses_atomically(grant_key):
            self.cache.set_negative(grant_key)
            raise AuthzDeniedError("SECRET_AUTHZ_FAILED")
        
        # Get provider and fetch credentials
        provider = self.registry.get_provider(uri.instance)
        return await provider.get_credentials(canonical)
    
    async def get_secret(
        self,
        canonical_uri: str,
        ctx: Optional[ExecutionContext] = None,
    ) -> str:
        """Get a single secret value with PDP enforcement.
        
        Convenience method when you only need one key from the secret.
        
        Args:
            canonical_uri: Canonical secret URI (must include fragment)
            ctx: Execution context
        
        Returns:
            The secret value as a string
        
        Raises:
            Same as get_credentials()
        """
        creds = await self.get_credentials(canonical_uri, ctx)
        
        # Parse URI to get fragment key
        uri = parse_secret_uri(
            canonical_uri,
            tenant_id=(ctx.tenant_id if ctx else None) or self.default_tenant_id,
            allowed_mounts=self.allowed_mounts,
        )
        
        if uri.fragment_key:
            value = creds.get(uri.fragment_key)
            if value is not None:
                return str(value)
        
        # If no fragment or key not found, return first value
        if creds:
            return str(next(iter(creds.values())))
        
        return ""
    
    def get_credentials_sync(
        self,
        canonical_uri: str,
        ctx: Optional[ExecutionContext] = None,
    ) -> Dict[str, Any]:
        """Synchronous wrapper for get_credentials.
        
        For use in non-async contexts. Creates a new event loop if needed.
        
        Args:
            canonical_uri: Canonical secret URI
            ctx: Execution context
        
        Returns:
            Dictionary of credential key-value pairs
        """
        import asyncio
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop is None:
            return asyncio.run(self.get_credentials(canonical_uri, ctx))
        else:
            # Already in async context - run in thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, self.get_credentials(canonical_uri, ctx))
                return future.result()
