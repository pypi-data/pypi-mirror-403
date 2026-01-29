"""Request Principal extraction for Identity Resolution v1.1.

This module provides a standardized way to extract and normalize
principal information from JWT claims across all services.

Services should use `extract_principal()` instead of manual claim extraction
to ensure consistent handling of:
- Account ARN (from sub)
- Identity ARN (if resolved)
- Connection ID (federation source)
- Provenance data (orig_iss, orig_sub_hash)
- Resolution status (cached, fallback)

Usage:
    from empowernow_common.auth.principal import extract_principal

    # In a FastAPI route handler:
    principal = extract_principal(request.state.claims)
    
    # Use principal for delegation verification
    result = await membership_client.verify_delegation_v1(
        subject_arn=principal.subject_arn,
        identity_arn=principal.identity_arn,
        delegate_arn=agent_arn,
    )

Reference: IDENTITY_RESOLUTION_IMPLEMENTATION_PLAN.md
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import warnings


# URI-namespaced claim keys (v1.1)
CLAIM_ACCOUNT_ARN = "https://schemas.empowernow.dev/identity/account_arn"
CLAIM_IDENTITY_ARN = "https://schemas.empowernow.dev/identity/identity_arn"
CLAIM_RESOLUTION = "https://schemas.empowernow.dev/identity/resolution"
CLAIM_CONNECTION_ID = "https://schemas.empowernow.dev/federation/connection_id"
CLAIM_ORIG_ISS = "https://schemas.empowernow.dev/federation/orig_iss"
CLAIM_ORIG_SUB = "https://schemas.empowernow.dev/federation/orig_sub"
CLAIM_ORIG_SUB_HASH = "https://schemas.empowernow.dev/federation/orig_sub_hash"

# Legacy claim keys - DEPRECATED
# Removal target: July 1, 2026
# Migration: Use URI-namespaced claims (CLAIM_ACCOUNT_ARN, CLAIM_IDENTITY_ARN)
# Tracking: TECH-DEBT-001 - Remove legacy emp_* claim support
LEGACY_CLAIM_ACCOUNT_ARN = "emp_account_arn"
LEGACY_CLAIM_IDENTITY_ARN = "emp_identity_arn"


@dataclass(frozen=True)
class RequestPrincipal:
    """Normalized principal extracted from JWT claims.
    
    This dataclass provides a consistent interface for accessing
    identity information regardless of claim format (new or legacy).
    
    Attributes:
        subject_arn: Account ARN from JWT sub claim (primary identifier)
        account_arn: Same as subject_arn (explicit name for clarity)
        identity_arn: Identity ARN if resolved, None for fallback
        connection_id: Federation connection ID (e.g., "conn_okta_prod")
        orig_iss: Original issuer from external IdP
        orig_sub_hash: Peppered hash of original subject (safe to log)
        resolution: How identity was resolved ("cached", "fallback", None)
    """
    subject_arn: str
    account_arn: str
    identity_arn: Optional[str]
    connection_id: str
    orig_iss: str
    orig_sub_hash: str
    resolution: Optional[str]
    
    def has_identity(self) -> bool:
        """Check if identity was successfully resolved (not fallback)."""
        return self.identity_arn is not None and self.resolution != "fallback"
    
    def is_fallback(self) -> bool:
        """Check if this principal is using fallback resolution."""
        return self.resolution == "fallback" or self.identity_arn is None
    
    def for_logging(self) -> Dict[str, Any]:
        """Return a dict safe for logging (no PII)."""
        return {
            "subject_arn": self.subject_arn,
            "has_identity": self.has_identity(),
            "connection_id": self.connection_id,
            "resolution": self.resolution,
            # Note: orig_sub_hash is peppered, safe to log
            "orig_sub_hash": self.orig_sub_hash[:8] + "..." if self.orig_sub_hash else None,
        }


def extract_principal(claims: Dict[str, Any]) -> RequestPrincipal:
    """Extract normalized principal from validated JWT claims.
    
    Services should use this instead of manual claim extraction to ensure
    consistent handling across the codebase.
    
    Handles both new URI-namespaced claims and legacy emp_* claims with
    appropriate fallback and deprecation warnings.
    
    Args:
        claims: JWT claims dict from validated token
        
    Returns:
        RequestPrincipal with normalized identity information
        
    Raises:
        KeyError: If required 'sub' claim is missing
        
    Example:
        claims = {"sub": "auth:account:conn_okta:abc123", ...}
        principal = extract_principal(claims)
        print(principal.subject_arn)  # "auth:account:conn_okta:abc123"
    """
    # Required: sub claim must always be present
    subject_arn = claims["sub"]
    
    # Account ARN: prefer new format, fall back to legacy
    account_arn = (
        claims.get(CLAIM_ACCOUNT_ARN) or
        claims.get(LEGACY_CLAIM_ACCOUNT_ARN) or
        subject_arn
    )
    
    # Emit deprecation warning if using legacy claims
    # Legacy support will be removed July 1, 2026 (TECH-DEBT-001)
    if LEGACY_CLAIM_ACCOUNT_ARN in claims and CLAIM_ACCOUNT_ARN not in claims:
        warnings.warn(
            f"Legacy claim '{LEGACY_CLAIM_ACCOUNT_ARN}' will be removed July 1, 2026. "
            f"Migrate to URI-namespaced '{CLAIM_ACCOUNT_ARN}' claim.",
            DeprecationWarning,
            stacklevel=2,
        )
    
    # Identity ARN: may be None for fallback resolution
    identity_arn = (
        claims.get(CLAIM_IDENTITY_ARN) or
        claims.get(LEGACY_CLAIM_IDENTITY_ARN)
    )
    
    # Federation metadata
    connection_id = claims.get(CLAIM_CONNECTION_ID, "unknown")
    orig_iss = claims.get(CLAIM_ORIG_ISS, claims.get("iss", "unknown"))
    orig_sub_hash = claims.get(CLAIM_ORIG_SUB_HASH, "")
    
    # Resolution status
    resolution = claims.get(CLAIM_RESOLUTION)
    
    return RequestPrincipal(
        subject_arn=subject_arn,
        account_arn=account_arn,
        identity_arn=identity_arn,
        connection_id=connection_id,
        orig_iss=orig_iss,
        orig_sub_hash=orig_sub_hash,
        resolution=resolution,
    )


def extract_principal_safe(claims: Dict[str, Any]) -> Optional[RequestPrincipal]:
    """Extract principal without raising on missing claims.
    
    Use this when claims may be incomplete (e.g., during migration).
    
    Args:
        claims: JWT claims dict (may be incomplete)
        
    Returns:
        RequestPrincipal if extraction succeeds, None otherwise
    """
    try:
        return extract_principal(claims)
    except (KeyError, TypeError):
        return None


__all__ = [
    "RequestPrincipal",
    "extract_principal",
    "extract_principal_safe",
    # Claim keys (for reference)
    "CLAIM_ACCOUNT_ARN",
    "CLAIM_IDENTITY_ARN",
    "CLAIM_RESOLUTION",
    "CLAIM_CONNECTION_ID",
    "CLAIM_ORIG_ISS",
    "CLAIM_ORIG_SUB",
    "CLAIM_ORIG_SUB_HASH",
]
