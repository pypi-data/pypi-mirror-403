"""Delegation Token Service - FIPS-compliant JWT minting and validation.

This module implements cryptographically-bound delegation tokens per GAP 7
of the OAuth Vault Delegation Gap Analysis.

Problem Solved:
    Previously, agents could claim to act for any user without cryptographic
    proof. This token binds agent identity to delegation and is short-lived.

Token Structure:
    - sub: agent_arn (who the token is for)
    - aud: empowernow-services (who can accept it)
    - delegation_id: unique delegation ID
    - delegator_arn: the user who delegated
    - capability_ids: what the agent can do
    - trust_level: basic | elevated | full
    - constraints: inline constraints (spend_cap, etc.)
    - iat/exp: issued at / expiration (short TTL: 5-15 min)

Security:
    - RS256 algorithm (FIPS 140-3 compliant)
    - Short TTL (default 15 minutes)
    - Agent ARN must match sub claim on validation

Usage:
    from empowernow_common.delegation.token import (
        DelegationTokenService,
        DelegationTokenSettings,
        DelegationTokenClaims,
    )
    
    settings = DelegationTokenSettings()
    service = DelegationTokenService(settings)
    
    # Mint a token
    claims = DelegationTokenClaims(
        delegation_id="del_abc123",
        agent_arn="agent:ai-travel",
        delegator_arn="auth:account:entra:user@example.com",
        capability_ids=["tool:jira:*"],
        trust_level="basic",
        constraints={},
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    token = service.mint(claims)
    
    # Validate a token
    validated_claims = service.validate(token, expected_agent_arn="agent:ai-travel")

Author: AI Agent Governance Team
Date: 2026-01-15
Version: 1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# =============================================================================
# Try to import JWT library
# =============================================================================

try:
    import jwt
    _HAS_JWT = True
except ImportError:
    jwt = None  # type: ignore
    _HAS_JWT = False
    logger.warning("PyJWT not installed - delegation token functionality disabled")


# =============================================================================
# Settings
# =============================================================================


class DelegationTokenSettings(BaseSettings):
    """Configuration for delegation token service.
    
    Environment Variables:
        DELEGATION_SIGNING_KEY: RS256 private key (path or inline PEM)
        DELEGATION_VERIFICATION_KEY: RS256 public key (path or inline PEM)
        DELEGATION_TOKEN_TTL_MINUTES: Token TTL (default: 15)
        DELEGATION_TOKEN_AUDIENCE: Audience claim (default: empowernow-services)
    """
    
    delegation_signing_key: str = ""
    """RS256 private key - path to PEM file or inline PEM string."""
    
    delegation_verification_key: str = ""
    """RS256 public key - path to PEM file or inline PEM string."""
    
    delegation_token_ttl_minutes: int = 15
    """Token TTL in minutes (default: 15, max recommended: 60)."""
    
    delegation_token_audience: str = "empowernow-services"
    """JWT audience claim for delegation tokens."""
    
    class Config:
        env_prefix = "DELEGATION_"
        env_file = ".env"
        extra = "ignore"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class DelegationTokenClaims:
    """Claims embedded in a delegation token.
    
    These claims prove that an agent has been delegated specific capabilities
    by a specific user, with cryptographic binding.
    
    Attributes:
        delegation_id: Unique identifier for the delegation
        agent_arn: The agent's ARN (goes in 'sub' claim)
        delegator_arn: The delegating user's ARN
        capability_ids: List of allowed capability patterns
        trust_level: Trust level (basic, elevated, full)
        constraints: Inline constraints (spend_cap, max_actions, etc.)
        issued_at: When the token was issued
        expires_at: When the token expires
    """
    
    delegation_id: str
    agent_arn: str
    delegator_arn: str
    capability_ids: List[str]
    trust_level: str
    constraints: Dict[str, Any]
    issued_at: datetime
    expires_at: datetime


# =============================================================================
# Token Service
# =============================================================================


class DelegationTokenService:
    """FIPS-compliant delegation token minting and validation (RS256).
    
    This service creates short-lived JWTs that cryptographically bind
    an agent to a delegation from a specific user.
    
    Security Features:
        - RS256 algorithm (RSA with SHA-256, FIPS 140-3 compliant)
        - Short TTL (default 15 minutes)
        - Audience validation
        - Agent ARN binding (sub must match expected)
    
    Example:
        settings = DelegationTokenSettings()
        service = DelegationTokenService(settings)
        
        # Mint token for agent
        token = service.mint(claims)
        
        # Validate token (must provide expected agent_arn)
        validated = service.validate(token, "agent:ai-travel")
    """
    
    def __init__(self, settings: DelegationTokenSettings) -> None:
        """Initialize token service with settings.
        
        Args:
            settings: Configuration including signing keys and TTL.
            
        Raises:
            RuntimeError: If PyJWT is not installed.
        """
        if not _HAS_JWT:
            raise RuntimeError(
                "PyJWT is required for delegation tokens. "
                "Install with: pip install PyJWT[crypto]"
            )
        
        self._private_key = self._load_key(settings.delegation_signing_key)
        self._public_key = self._load_key(settings.delegation_verification_key)
        self._ttl_minutes = settings.delegation_token_ttl_minutes
        self._audience = settings.delegation_token_audience
    
    @staticmethod
    def _load_key(key_path_or_value: str) -> str:
        """Load key from file path or return as-is if inline PEM.
        
        Args:
            key_path_or_value: Path to PEM file or inline PEM string.
            
        Returns:
            The key contents as a string.
        """
        if not key_path_or_value:
            return ""
        
        # If it looks like an inline PEM, return as-is
        if key_path_or_value.strip().startswith("-----"):
            return key_path_or_value
        
        # Otherwise, try to load from file
        try:
            with open(key_path_or_value, 'r') as f:
                return f.read()
        except (FileNotFoundError, IOError) as e:
            logger.warning(f"Could not load key from {key_path_or_value}: {e}")
            return key_path_or_value
    
    @property
    def ttl_minutes(self) -> int:
        """Get the token TTL in minutes."""
        return self._ttl_minutes
    
    def mint(self, claims: DelegationTokenClaims) -> str:
        """Mint a signed delegation token (RS256 - FIPS compliant).
        
        Args:
            claims: The delegation claims to embed in the token.
            
        Returns:
            Signed JWT string.
            
        Raises:
            ValueError: If signing key is not configured.
            jwt.PyJWTError: If token encoding fails.
        """
        if not self._private_key:
            raise ValueError("Delegation signing key not configured")
        
        payload = {
            "sub": claims.agent_arn,
            "aud": self._audience,
            "delegation_id": claims.delegation_id,
            "delegator_arn": claims.delegator_arn,
            "capability_ids": claims.capability_ids,
            "trust_level": claims.trust_level,
            "constraints": claims.constraints,
            "iat": int(claims.issued_at.timestamp()),
            "exp": int(claims.expires_at.timestamp()),
        }
        
        token = jwt.encode(payload, self._private_key, algorithm="RS256")
        
        logger.debug(
            "Delegation token minted",
            extra={
                "delegation_id": claims.delegation_id,
                "agent_arn": claims.agent_arn,
                "expires_at": claims.expires_at.isoformat(),
            }
        )
        
        return token
    
    def validate(
        self,
        token: str,
        expected_agent_arn: str,
    ) -> DelegationTokenClaims:
        """Validate token signature and decode claims.
        
        Performs the following validations:
        1. Signature verification (RS256)
        2. Audience claim matches expected
        3. Token is not expired
        4. Subject (agent ARN) matches expected
        
        Args:
            token: The JWT token string to validate.
            expected_agent_arn: The agent ARN to verify against 'sub' claim.
            
        Returns:
            Validated DelegationTokenClaims.
            
        Raises:
            ValueError: If token is invalid, expired, or agent mismatch.
        """
        if not self._public_key:
            raise ValueError("Delegation verification key not configured")
        
        try:
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=["RS256"],
                audience=self._audience,
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("Delegation token expired")
        except jwt.InvalidAudienceError:
            raise ValueError(f"Invalid audience - expected {self._audience}")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid delegation token: {e}")
        
        # Verify agent ARN matches
        token_agent_arn = payload.get("sub")
        if token_agent_arn != expected_agent_arn:
            raise ValueError(
                f"Token agent mismatch: token has '{token_agent_arn}' "
                f"but expected '{expected_agent_arn}'"
            )
        
        # Build claims object
        claims = DelegationTokenClaims(
            delegation_id=payload["delegation_id"],
            agent_arn=payload["sub"],
            delegator_arn=payload["delegator_arn"],
            capability_ids=payload.get("capability_ids", []),
            trust_level=payload.get("trust_level", "basic"),
            constraints=payload.get("constraints", {}),
            issued_at=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
        
        logger.debug(
            "Delegation token validated",
            extra={
                "delegation_id": claims.delegation_id,
                "agent_arn": claims.agent_arn,
            }
        )
        
        return claims
    
    def create_claims_for_delegation(
        self,
        delegation_id: str,
        agent_arn: str,
        delegator_arn: str,
        capability_ids: Optional[List[str]] = None,
        trust_level: str = "basic",
        constraints: Optional[Dict[str, Any]] = None,
        ttl_override_minutes: Optional[int] = None,
    ) -> DelegationTokenClaims:
        """Helper to create claims from delegation data.
        
        Args:
            delegation_id: Unique delegation identifier.
            agent_arn: Agent's ARN.
            delegator_arn: Delegating user's ARN.
            capability_ids: Allowed capabilities (None = use delegation settings).
            trust_level: Trust level string.
            constraints: Inline constraints dict.
            ttl_override_minutes: Override default TTL if provided.
            
        Returns:
            DelegationTokenClaims ready for minting.
        """
        now = datetime.now(timezone.utc)
        ttl = ttl_override_minutes or self._ttl_minutes
        
        return DelegationTokenClaims(
            delegation_id=delegation_id,
            agent_arn=agent_arn,
            delegator_arn=delegator_arn,
            capability_ids=capability_ids or [],
            trust_level=trust_level,
            constraints=constraints or {},
            issued_at=now,
            expires_at=now + timedelta(minutes=ttl),
        )


# =============================================================================
# Factory Function
# =============================================================================


_token_service_instance: Optional[DelegationTokenService] = None


def get_delegation_token_service(
    settings: Optional[DelegationTokenSettings] = None,
) -> DelegationTokenService:
    """Get or create the delegation token service singleton.
    
    Args:
        settings: Optional settings override. If not provided and no instance
                 exists, creates with default DelegationTokenSettings().
                 
    Returns:
        DelegationTokenService instance.
    """
    global _token_service_instance
    
    if _token_service_instance is None:
        _token_service_instance = DelegationTokenService(
            settings or DelegationTokenSettings()
        )
    
    return _token_service_instance


def reset_delegation_token_service() -> None:
    """Reset the singleton (for testing)."""
    global _token_service_instance
    _token_service_instance = None


# =============================================================================
# Exports
# =============================================================================


__all__ = [
    "DelegationTokenSettings",
    "DelegationTokenClaims",
    "DelegationTokenService",
    "get_delegation_token_service",
    "reset_delegation_token_service",
]
