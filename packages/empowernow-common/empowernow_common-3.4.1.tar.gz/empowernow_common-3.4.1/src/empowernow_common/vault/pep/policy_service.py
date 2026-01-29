"""Secret policy service - PDP facade for authorization.

This is the interface between the vault system and the PDP.
Production deployments should configure a real PDP client;
the default implementation is a permissive stub for development.

Per design §B - Authorization Boundary Clarity:
    - VaultProvider = raw access (no policy enforcement)
    - VaultClient = PDP-enforced wrapper (use this!)
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from empowernow_common.vault.pep.grant_cache import Grant


@dataclass
class BatchFailure:
    """Represents a failed authorization in a batch request."""
    
    uri: str
    code: str  # "DENY" | "PDP_UNAVAILABLE" | other
    reason: str


class AuthzDeniedError(Exception):
    """Authorization denied by PDP."""
    
    def __init__(self, code: str = "DENY", message: str = "Authorization denied") -> None:
        super().__init__(message)
        self.code = code


class PDPUnavailableError(Exception):
    """PDP service is unavailable."""
    
    def __init__(self, message: str = "PDP service unavailable") -> None:
        super().__init__(message)


class BindingDriftError(Exception):
    """Sender binding (DPoP/mTLS) changed within grant TTL."""
    
    def __init__(self, message: str = "Sender binding drift detected") -> None:
        super().__init__(message)


class SecretPolicyService:
    """PDP facade for secret access authorization.
    
    This is a minimal implementation for development/testing.
    Production deployments should:
    1. Configure ENABLE_AUTHORIZATION=true
    2. Set PDP_AVAILABLE=true and provide PDP_URL
    3. Optionally implement a real PDP client
    
    The interface is designed to be swappable with a real PDP client
    while maintaining the same return type (Grant) and behavior contract.
    
    Usage:
        service = SecretPolicyService()
        
        # Single authorization
        grant = await service.authorize_use(
            subject_arn="arn:empowernow:identity::user/alice",
            tenant_id="acme",
            canonical_uri="openbao://secret/app#token",
            purpose="execute",
            cnf_binding="sha256-thumbprint",
        )
        
        # Batch authorization
        grants, failures = await service.authorize_batch(
            subject_arn="...",
            tenant_id="acme",
            required=["openbao://secret/db#password"],
            optional=["openbao://secret/api#key"],
        )
    """
    
    def __init__(self) -> None:
        """Initialize policy service from environment."""
        self.default_ttl = int(os.getenv("GRANT_TTL_DEFAULT", "300"))
        self.default_max_uses = int(os.getenv("GRANT_MAX_USES_DEFAULT", "1"))
        self.pdp_available = os.getenv("PDP_AVAILABLE", "true").lower() in ("true", "1", "yes")
        
        enable_flag = os.getenv("ENABLE_AUTHORIZATION")
        if enable_flag is not None:
            self.enable_authorization = enable_flag.lower() in ("true", "1", "yes")
        else:
            # Default: disabled for dev (safe-off)
            self.enable_authorization = False
    
    async def authorize_use(
        self,
        subject_arn: str,
        tenant_id: str,
        canonical_uri: str,
        purpose: Optional[str],
        cnf_binding: Optional[str],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Grant:
        """Authorize access to a secret.
        
        Args:
            subject_arn: Identity ARN of the requester
            tenant_id: Tenant identifier
            canonical_uri: Canonical secret URI
            purpose: Access purpose (e.g., "execute", "read")
            cnf_binding: Sender binding (DPoP jkt or mTLS thumbprint)
            context: Additional context for policy evaluation
        
        Returns:
            Grant authorizing the access
        
        Raises:
            AuthzDeniedError: If authorization is denied
            PDPUnavailableError: If PDP service is unavailable
        """
        if self.enable_authorization:
            if not self.pdp_available:
                raise PDPUnavailableError("PDP_UNAVAILABLE")
            
            # Stub: deny if URI contains "deny" (for testing)
            if "deny" in canonical_uri.lower():
                raise AuthzDeniedError("DENY", "Policy denied access")
            
            # In production, this would call the real PDP
            # response = await self._call_pdp(subject_arn, tenant_id, canonical_uri, purpose)
            # if response.decision != "PERMIT":
            #     raise AuthzDeniedError(response.code, response.message)
        
        # Extract wrap_ttl from context if provided
        wrap_ttl = None
        if context and isinstance(context, dict):
            wrap_ttl = context.get("wrap_ttl")
        
        return Grant(
            grant_id=str(uuid.uuid4()),
            ttl_s=self.default_ttl,
            max_uses=self.default_max_uses,
            uses=0,
            decision_id=str(uuid.uuid4()),
            policy_version="local-dev",
            classification=None,
            must_revalidate_on=None,
            cnf_binding=cnf_binding,
            wrap_ttl=wrap_ttl,
        )
    
    async def authorize_batch(
        self,
        subject_arn: str,
        tenant_id: str,
        required: List[str],
        optional: Optional[List[str]] = None,
        *,
        purpose: Optional[str] = None,
        cnf_binding: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Grant], List[BatchFailure]]:
        """Authorize access to multiple secrets.
        
        Batch authorization for efficiency when accessing multiple secrets.
        Required URIs must all succeed; optional URIs may fail.
        
        Args:
            subject_arn: Identity ARN of the requester
            tenant_id: Tenant identifier
            required: List of required secret URIs (all must succeed)
            optional: List of optional secret URIs (may fail)
            purpose: Access purpose
            cnf_binding: Sender binding
            context: Additional context
        
        Returns:
            Tuple of:
            - Dictionary mapping URIs to granted permissions
            - List of failures (for optional URIs that failed)
        
        Raises:
            AuthzDeniedError: If any required URI is denied
            PDPUnavailableError: If PDP service is unavailable
        """
        optional = optional or []
        
        # De-duplicate keeping first occurrence (required first)
        seen: set = set()
        ordered: List[Tuple[str, bool]] = []
        
        for uri in required:
            if uri not in seen:
                seen.add(uri)
                ordered.append((uri, True))
        
        for uri in optional:
            if uri not in seen:
                seen.add(uri)
                ordered.append((uri, False))
        
        grants: Dict[str, Grant] = {}
        failures: List[BatchFailure] = []
        
        for uri, is_required in ordered:
            try:
                grant = await self.authorize_use(
                    subject_arn,
                    tenant_id,
                    uri,
                    purpose,
                    cnf_binding,
                    context=context,
                )
                grants[uri] = grant
                
            except AuthzDeniedError as e:
                if is_required:
                    raise
                failures.append(BatchFailure(uri=uri, code=e.code, reason="policy"))
                
            except PDPUnavailableError:
                if is_required:
                    raise
                failures.append(BatchFailure(uri=uri, code="PDP_UNAVAILABLE", reason="unavailable"))
        
        return grants, failures
    
    async def revoke_grant(self, grant_id: str) -> bool:
        """Revoke a previously issued grant.
        
        Args:
            grant_id: The grant ID to revoke
        
        Returns:
            True if revocation succeeded
        
        Note:
            This is a stub - real implementation would call PDP.
        """
        # In production, this would call the PDP to revoke
        return True
