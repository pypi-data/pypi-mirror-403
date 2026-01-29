from __future__ import annotations

"""
EmpowerNow OAuth Client – Enterprise-Grade, Developer-Delightful

A production-ready OAuth 2.1 client designed for:
- Zero-config deployment (environment variables)
- One-liner quick starts
- Full OAuth 2.1 feature support
- Bulletproof production hardening

Quick Start:
    # From environment (recommended)
    token = await OAuth.from_env().get_token()
    
    # One-liner for client_credentials
    token = await OAuth.client_credentials(
        "client-id", "secret", "https://idp.example.com"
    ).get_token()
    
    # With OIDC discovery
    async with await OAuth.from_issuer("https://idp.example.com", "client-id", "secret") as oauth:
        token = await oauth.get_token()

Features:
- Automatic token caching with thread-safe refresh
- PAR, DPoP, JARM, JAR, CIBA, RAR support
- mTLS and private_key_jwt authentication
- Retry with exponential backoff
- Prometheus metrics and structured logging
- Per-grant DPoP control
- RFC 8707 resource parameter support
- Correlation ID propagation
"""

import asyncio
import httpx
import json
import logging
import os
import time
import structlog
from typing import Any, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from base64 import urlsafe_b64encode
from jose import jwt as jose_jwt
from cryptography.hazmat.primitives import serialization
from enum import Enum
import anyio

# Import from focused modules
from .security import (
    SecurityError,
    SecurityContext,
    validate_url_security,
    validate_url_with_internal_http,
    sanitize_string_input,
    generate_secure_token,
    DEFAULT_INTERNAL_HTTP_HOSTS,
    validate_rfc8707_resource,
    ResourceValidationError,
)
from .dpop import DPoPManager, DPoPError
from .par import PARManager, PARError, PARResponse
from .jarm import JARMManager, JARMError
from .jar import JARManager, JARError as JARAuthError, generate_jar_signing_key
from .ciba import CIBAManager, CIBARequest, CIBAError
from .rar import (
    SecureAuthorizationDetail,
    RARError,
    RARBuilder,
    AuthZENCompatibleResource,
    AuthZENCompatibleAction,
    AuthZENCompatibleContext,
    StandardActionType,
    StandardResourceType,
    create_account_access_detail,
    create_api_access_detail,
)
from .network import RetryPolicy, DEFAULT_RETRY_POLICY
from .errors import (
    OAuthError,
    TokenRequestError,
    InvalidGrantError,
    RateLimitError,
    DPoPNonceError,
    CircuitOpenError,
    ConfigurationError,
)
from .config import HTTPPoolConfig, DPoPConfig, OAuthSettings
from .metrics import (
    track_token_request,
    record_cache_hit,
    record_cache_miss,
    record_cache_clear,
    record_dpop_nonce_challenge,
    record_retry_attempt,
    record_http_request,
    set_token_expiry,
)

# Optional: only import cryptography when mTLS is enabled
try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
except ImportError:
    x509 = None

logger = structlog.get_logger("empowernow_common.oauth")


@dataclass
class SecureOAuthConfig:
    """Secure OAuth configuration with validation."""

    client_id: str
    client_secret: str
    token_url: str
    authorization_url: str

    # Optional endpoints
    par_endpoint: str | None = None
    ciba_endpoint: str | None = None
    introspection_url: str | None = None
    revocation_url: str | None = None

    # Default scope
    scope: str | None = None
    
    # Token endpoint authentication method (RFC 7591)
    token_endpoint_auth_method: str = "client_secret_basic"
    
    # HTTP pool settings
    http_pool: HTTPPoolConfig = field(default_factory=HTTPPoolConfig)
    
    # Security settings
    allow_internal_http: bool = field(
        default_factory=lambda: os.getenv("OAUTH_ALLOW_INTERNAL_HTTP", "false").lower() in {"true", "1", "yes"}
    )
    internal_http_hosts: tuple[str, ...] = DEFAULT_INTERNAL_HTTP_HOSTS
    
    # Observability
    correlation_id_header: str = "X-Correlation-ID"
    propagate_correlation_id: bool = True

    def __post_init__(self):
        """Validate configuration"""
        self.client_id = sanitize_string_input(self.client_id, 256, "client_id")
        
        # Allow empty client_secret only for public clients
        if self.token_endpoint_auth_method == "none":
            self.client_secret = ""
        else:
            self.client_secret = sanitize_string_input(
                self.client_secret, 512, "client_secret"
            )
        
        # Validate token_url with internal HTTP support
        self.token_url = validate_url_with_internal_http(
            self.token_url,
            context="token_url",
            allow_internal_http=self.allow_internal_http,
            internal_http_hosts=self.internal_http_hosts,
        )
        
        # Authorization URL can be empty for client_credentials only
        if self.authorization_url:
            self.authorization_url = validate_url_with_internal_http(
                self.authorization_url,
                context="authorization_url",
                allow_internal_http=self.allow_internal_http,
                internal_http_hosts=self.internal_http_hosts,
            )

        if self.par_endpoint:
            self.par_endpoint = validate_url_with_internal_http(
                self.par_endpoint,
                context="par_endpoint",
                allow_internal_http=self.allow_internal_http,
                internal_http_hosts=self.internal_http_hosts,
            )

        if self.ciba_endpoint:
            self.ciba_endpoint = validate_url_with_internal_http(
                self.ciba_endpoint,
                context="ciba_endpoint",
                allow_internal_http=self.allow_internal_http,
                internal_http_hosts=self.internal_http_hosts,
            )
            
        # Validate token endpoint authentication method
        valid_auth_methods = {
            "client_secret_basic",
            "client_secret_post", 
            "private_key_jwt",
            "none"
        }
        if self.token_endpoint_auth_method not in valid_auth_methods:
            raise ValueError(
                f"Invalid token_endpoint_auth_method: {self.token_endpoint_auth_method}. "
                f"Must be one of: {', '.join(sorted(valid_auth_methods))}"
            )


@dataclass
class HardenedToken:
    """OAuth token with comprehensive metadata and expiry tracking.
    
    Supports standard OAuth 2.0 token response fields plus RFC 8693 extensions.
    """

    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None
    id_token: str | None = None
    
    # RFC 8693 Token Exchange response field
    issued_token_type: str | None = None  # e.g., "urn:ietf:params:oauth:token-type:access_token"

    # Security metadata
    client_fingerprint: str | None = None
    issued_at: datetime | None = None
    token_binding: dict[str, Any] | None = None

    def __post_init__(self):
        """Validate token data"""
        self.access_token = sanitize_string_input(
            self.access_token, 4096, "access_token", allow_special_chars=True
        )

        if not self.issued_at:
            self.issued_at = datetime.now(timezone.utc)
    
    def __repr__(self) -> str:
        """Rich, informative representation for debugging."""
        remaining = self.expires_in_seconds
        remaining_str = f"{remaining // 60}m {remaining % 60}s remaining" if remaining > 0 else "EXPIRED"
        
        token_preview = f"{self.access_token[:10]}...{self.access_token[-6:]}" if len(self.access_token) > 20 else "***"
        
        return (
            f"HardenedToken(\n"
            f"    access_token='{token_preview}' ({len(self.access_token)} chars),\n"
            f"    token_type='{self.token_type}',\n"
            f"    expires_at={self.expires_at.isoformat() if self.expires_at else 'never'} ({remaining_str}),\n"
            f"    scope='{self.scope or 'none'}',\n"
            f"    has_refresh_token={bool(self.refresh_token)},\n"
            f")"
        )

    @property
    def expires_at(self) -> datetime | None:
        """Get token expiry datetime."""
        if not self.expires_in or not self.issued_at:
            return None
        return self.issued_at + timedelta(seconds=self.expires_in)
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_in or not self.issued_at:
            return False
        return datetime.now(timezone.utc) >= self.expires_at
    
    @property
    def expires_in_seconds(self) -> int:
        """Seconds until token expires (0 if expired)."""
        if not self.expires_at:
            return 0
        remaining = (self.expires_at - datetime.now(timezone.utc)).total_seconds()
        return max(0, int(remaining))

    def is_dpop_bound(self) -> bool:
        """Check if token is DPoP-bound"""
        return (
            self.token_binding
            and self.token_binding.get("method") == "dpop"
            and "jwk_thumbprint" in self.token_binding
        )


@dataclass
class PrivateKeyJWTConfig:
    signing_key: Any
    signing_alg: str = "RS256"
    assertion_ttl: int = 300
    kid: str | None = None

    def to_jwt(self, client_id: str, token_url: str) -> str:
        now = int(time.time())
        payload = {
            "iss": client_id,
            "sub": client_id,
            "aud": token_url,
            "iat": now,
            "exp": now + self.assertion_ttl,
            "jti": generate_secure_token(16),
        }

        headers = {"kid": self.kid} if self.kid else None
        return jose_jwt.encode(payload, self.signing_key, algorithm=self.signing_alg, headers=headers)


class OAuthBuilder:
    """Fluent builder for HardenedOAuth client.
    
    Provides IDE-friendly, discoverable configuration with method chaining.
    
    Example:
        client = (
            OAuth.builder()
            .client_id("my-client")
            .client_secret("my-secret")
            .issuer("https://idp.example.com")
            .with_dpop()
            .with_retry(attempts=5)
            .debug()
            .build()
        )
    """
    
    def __init__(self):
        self._client_id: str | None = None
        self._client_secret: str = ""
        self._issuer: str | None = None
        self._token_url: str | None = None
        self._authorization_url: str = ""
        self._scope: str = ""
        self._auth_method: str = "client_secret_basic"
        self._debug_mode: bool = False
        self._dpop_config: DPoPConfig | None = None
        self._mtls_cert: str | None = None
        self._mtls_key: str | None = None
        self._retry_attempts: int = 3
        self._retry_backoff: float = 1.5
        self._timeout: float = 30.0
        self._allow_internal_http: bool = False
        self._internal_http_hosts: tuple[str, ...] = DEFAULT_INTERNAL_HTTP_HOSTS
        self._http_pool: HTTPPoolConfig | None = None
    
    def client_id(self, client_id: str) -> "OAuthBuilder":
        """Set OAuth client ID."""
        self._client_id = client_id
        return self
    
    def client_secret(self, client_secret: str) -> "OAuthBuilder":
        """Set OAuth client secret."""
        self._client_secret = client_secret
        return self
    
    def issuer(self, issuer_url: str) -> "OAuthBuilder":
        """Set OAuth issuer URL (for endpoint discovery)."""
        self._issuer = issuer_url.rstrip("/")
        return self
    
    def token_url(self, token_url: str) -> "OAuthBuilder":
        """Set token endpoint URL directly."""
        self._token_url = token_url
        return self
    
    def authorization_url(self, auth_url: str) -> "OAuthBuilder":
        """Set authorization endpoint URL."""
        self._authorization_url = auth_url
        return self
    
    def scope(self, scope: str) -> "OAuthBuilder":
        """Set default scope for token requests."""
        self._scope = scope
        return self
    
    def auth_method(self, method: str) -> "OAuthBuilder":
        """Set token endpoint authentication method."""
        self._auth_method = method
        return self
    
    def with_dpop(
        self,
        algorithm: str = "ES256",
        *,
        for_client_credentials: bool = False,
        for_authorization_code: bool = True,
        for_refresh_token: bool = True,
    ) -> "OAuthBuilder":
        """Enable DPoP with optional per-grant control."""
        self._dpop_config = DPoPConfig(
            enabled=True,
            algorithm=algorithm,
            enable_for_client_credentials=for_client_credentials,
            enable_for_authorization_code=for_authorization_code,
            enable_for_refresh_token=for_refresh_token,
        )
        return self
    
    def with_mtls(self, cert_path: str, key_path: str) -> "OAuthBuilder":
        """Enable mTLS client authentication."""
        self._mtls_cert = cert_path
        self._mtls_key = key_path
        return self
    
    def with_retry(self, attempts: int = 3, backoff: float = 1.5) -> "OAuthBuilder":
        """Configure retry behavior."""
        self._retry_attempts = attempts
        self._retry_backoff = backoff
        return self
    
    def timeout(self, seconds: float) -> "OAuthBuilder":
        """Set request timeout."""
        self._timeout = seconds
        return self
    
    def allow_internal_http(self, hosts: tuple[str, ...] | None = None) -> "OAuthBuilder":
        """Allow HTTP for internal services (Docker/K8s)."""
        self._allow_internal_http = True
        if hosts:
            self._internal_http_hosts = hosts
        return self
    
    def http_pool(self, config: HTTPPoolConfig) -> "OAuthBuilder":
        """Set HTTP pool configuration."""
        self._http_pool = config
        return self
    
    def debug(self, enabled: bool = True) -> "OAuthBuilder":
        """Enable debug mode with detailed logging."""
        self._debug_mode = enabled
        return self
    
    def from_env(self, prefix: str = "OAUTH_") -> "OAuthBuilder":
        """Load configuration from environment variables."""
        try:
            settings = OAuthSettings()
            self._client_id = settings.client_id
            self._client_secret = settings.client_secret
            self._issuer = settings.issuer
            self._token_url = settings.token_url
            self._authorization_url = settings.authorization_url or ""
            self._scope = settings.scope
            self._auth_method = settings.token_endpoint_auth_method
            self._debug_mode = settings.debug
            self._allow_internal_http = settings.allow_internal_http
            self._timeout = settings.timeout_seconds
            self._retry_attempts = settings.max_retries
            self._http_pool = settings.get_http_pool_config()
        except Exception as e:
            raise ConfigurationError(
                message=f"Failed to load configuration from environment: {e}",
                error_code="env_config_failed",
                how_to_fix=[
                    f"Set {prefix}CLIENT_ID environment variable",
                    f"Set {prefix}CLIENT_SECRET environment variable",
                    f"Set either {prefix}ISSUER or {prefix}TOKEN_URL",
                    "Check your .env file if using dotenv",
                ],
            )
        return self
    
    def build(self) -> "HardenedOAuth":
        """Build the OAuth client."""
        if not self._client_id:
            raise ConfigurationError.missing_env_var("CLIENT_ID")
        
        # Determine token URL
        token_url = self._token_url
        if not token_url and self._issuer:
            token_url = f"{self._issuer}/oauth/token"
        if not token_url:
            raise ConfigurationError(
                message="Either issuer or token_url must be provided",
                error_code="missing_token_url",
                how_to_fix=[
                    "Call .issuer('https://idp.example.com')",
                    "Or call .token_url('https://idp.example.com/oauth/token')",
                    "Or set OAUTH_ISSUER or OAUTH_TOKEN_URL environment variable",
                ],
            )
        
        # Determine authorization URL
        auth_url = self._authorization_url
        if not auth_url and self._issuer:
            auth_url = f"{self._issuer}/authorize"
        
        config = SecureOAuthConfig(
            client_id=self._client_id,
            client_secret=self._client_secret,
            token_url=token_url,
            authorization_url=auth_url,
            scope=self._scope or None,
            token_endpoint_auth_method=self._auth_method,
            http_pool=self._http_pool or HTTPPoolConfig(timeout=self._timeout),
            allow_internal_http=self._allow_internal_http,
            internal_http_hosts=self._internal_http_hosts,
        )
        
        retry_policy = RetryPolicy(
            attempts=self._retry_attempts,
            backoff_factor=self._retry_backoff,
        )
        
        client = HardenedOAuth(config, retry_policy=retry_policy)
        
        # Apply optional configurations
        if self._debug_mode:
            client.debug(True)
        
        if self._dpop_config and self._dpop_config.enabled:
            client.configure_dpop(
                algorithm=self._dpop_config.algorithm,
                enable_for_client_credentials=self._dpop_config.enable_for_client_credentials,
                enable_for_authorization_code=self._dpop_config.enable_for_authorization_code,
                enable_for_refresh_token=self._dpop_config.enable_for_refresh_token,
            )
        
        if self._mtls_cert and self._mtls_key:
            client.enable_mtls(self._mtls_cert, self._mtls_key)
        
        return client


class HardenedOAuth:
    """Enterprise-grade OAuth client with modular security features.
    
    Quick Start (3 lines or less):
        # From environment (zero config!)
        token = await OAuth.from_env().get_token()
        
        # Client credentials flow
        client = OAuth.client_credentials("id", "secret", "https://idp.example.com")
        token = await client.get_token()
        
        # With OIDC discovery
        client = await OAuth.from_issuer("https://idp.example.com", "id", "secret")
        token = await client.get_token()
    
    Features:
        - Automatic token caching with thread-safe refresh
        - Smart grant type inference
        - RFC 8707 resource parameter support
        - Correlation ID propagation
        - Per-grant DPoP control
        - PAR, DPoP, JARM, JAR, CIBA, RAR support
        - mTLS and private_key_jwt authentication
        - Retry with exponential backoff
        - Prometheus metrics and structured logging
        - Debug mode for development
    
    Documentation:
        Call OAuth.help() for quick reference.
    """
    
    # ==================== FACTORY METHODS ====================
    
    @classmethod
    def builder(cls) -> OAuthBuilder:
        """Create fluent builder for advanced configuration.
        
        Returns:
            OAuthBuilder for method chaining
        
        Example:
            client = (
                OAuth.builder()
                .client_id("my-client")
                .client_secret("my-secret")
                .issuer("https://idp.example.com")
                .with_dpop()
                .debug()
                .build()
            )
        """
        return OAuthBuilder()
    
    @classmethod
    def from_env(cls, prefix: str = "OAUTH_", **kwargs) -> "HardenedOAuth":
        """Create OAuth client from environment variables.
        
        This is the recommended way to create a client - it automatically
        reads configuration from environment variables with zero code changes
        between dev, staging, and production.
        
        Environment Variables:
            {prefix}CLIENT_ID: OAuth client ID (required)
            {prefix}CLIENT_SECRET: OAuth client secret
            {prefix}ISSUER: IdP issuer URL for OIDC discovery
            {prefix}TOKEN_URL: Direct token endpoint URL
            {prefix}SCOPE: Default scope for token requests
            {prefix}DEBUG: Enable debug mode (true/false)
            {prefix}TIMEOUT_SECONDS: Request timeout
            {prefix}ALLOW_INTERNAL_HTTP: Allow HTTP for internal services
        
        Args:
            prefix: Environment variable prefix (default: "OAUTH_")
            **kwargs: Additional HardenedOAuth constructor arguments
        
        Returns:
            Configured HardenedOAuth instance
        
        Example:
            # Set environment variables:
            # OAUTH_CLIENT_ID=my-client
            # OAUTH_CLIENT_SECRET=my-secret
            # OAUTH_ISSUER=https://idp.example.com
            
            client = OAuth.from_env()
            token = await client.get_token()
        """
        return cls.builder().from_env(prefix).build()
    
    @classmethod
    def client_credentials(
        cls,
        client_id: str,
        client_secret: str,
        issuer_or_token_url: str,
        *,
        scope: str = "",
        **kwargs,
    ) -> "HardenedOAuth":
        """Create OAuth client for client_credentials flow.
        
        The simplest way to get a service-to-service token.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            issuer_or_token_url: OAuth issuer URL or direct token URL
            scope: Default scope for token requests
            **kwargs: Additional configuration options
        
        Returns:
            Configured HardenedOAuth instance
        
        Example:
            client = OAuth.client_credentials(
                "my-client",
                "my-secret",
                "https://idp.example.com"
            )
            token = await client.get_token()
        """
        # Detect if it's an issuer URL or direct token URL
        if "/oauth/" in issuer_or_token_url or issuer_or_token_url.endswith("/token"):
            token_url = issuer_or_token_url
            auth_url = ""
        else:
            issuer = issuer_or_token_url.rstrip("/")
            token_url = f"{issuer}/oauth/token"
            auth_url = f"{issuer}/authorize"
        
        config = SecureOAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            token_url=token_url,
            authorization_url=auth_url,
            scope=scope or None,
            **kwargs,
        )
        return cls(config)
    
    @classmethod
    def simple(
        cls,
        token_url: str,
        client_id: str,
        client_secret: str = "",
        *,
        scope: str = "",
    ) -> "HardenedOAuth":
        """Create a simple OAuth client for client_credentials flow.
        
        The simplest way to get started - just token URL and credentials.
        
        Args:
            token_url: OAuth token endpoint URL
            client_id: OAuth client ID
            client_secret: OAuth client secret (empty for public clients)
            scope: Optional default scope
            
        Returns:
            Configured HardenedOAuth instance
            
        Example:
            oauth = HardenedOAuth.simple(
                "https://auth.example.com/oauth/token",
                "my-app",
                "my-secret"
            )
            async with oauth:
                token = await oauth.get_token()
        """
        config = SecureOAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            token_url=token_url,
            authorization_url="",
            scope=scope or None,
        )
        return cls(config)
    
    @classmethod
    async def from_issuer(
        cls,
        issuer_url: str,
        client_id: str,
        client_secret: str = "",
        *,
        token_endpoint_auth_method: str = "client_secret_basic",
        scope: str = "",
        **kwargs,
    ) -> "HardenedOAuth":
        """Create OAuth client using OIDC discovery.
        
        Automatically discovers endpoints from .well-known/openid-configuration.
        This is the recommended way to configure the client for IdPs that
        support OIDC discovery.
        
        Args:
            issuer_url: OAuth/OIDC issuer URL (e.g., https://auth.example.com)
            client_id: OAuth client ID
            client_secret: OAuth client secret (empty for public clients)
            token_endpoint_auth_method: Authentication method
            scope: Optional default scope
            **kwargs: Additional HardenedOAuth constructor arguments
        
        Returns:
            Configured HardenedOAuth instance
            
        Raises:
            DiscoveryError: If discovery fails
            
        Example:
            oauth = await HardenedOAuth.from_issuer(
                "https://auth.example.com",
                "my-app",
                "my-secret"
            )
            token = await oauth.get_token()
        """
        from .errors import DiscoveryError
        
        discovery_url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(discovery_url)
                response.raise_for_status()
                metadata = response.json()
            except httpx.HTTPStatusError as e:
                raise DiscoveryError(
                    message=f"OIDC discovery failed: HTTP {e.response.status_code}",
                    discovery_url=discovery_url,
                    status_code=e.response.status_code,
                    how_to_fix=[
                        f"Verify the issuer URL is correct: {issuer_url}",
                        f"Try accessing {discovery_url} in a browser",
                        "Check that the IdP supports OIDC discovery",
                    ],
                )
            except httpx.RequestError as e:
                raise DiscoveryError(
                    message=f"Failed to connect to OIDC discovery endpoint: {e}",
                    discovery_url=discovery_url,
                    how_to_fix=[
                        "Check network connectivity",
                        "Verify the issuer URL is reachable",
                        "Check DNS resolution",
                    ],
                )
        
        config = SecureOAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            token_url=metadata["token_endpoint"],
            authorization_url=metadata.get("authorization_endpoint", ""),
            introspection_url=metadata.get("introspection_endpoint"),
            revocation_url=metadata.get("revocation_endpoint"),
            par_endpoint=metadata.get("pushed_authorization_request_endpoint"),
            ciba_endpoint=metadata.get("backchannel_authentication_endpoint"),
            token_endpoint_auth_method=token_endpoint_auth_method,
            scope=scope or None,
        )
        
        return cls(config, **kwargs)
    
    @classmethod
    def help(cls) -> None:
        """Print quick reference for common operations."""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                 EmpowerNow OAuth Quick Reference                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  QUICK START                                                     ║
║  ──────────                                                      ║
║  from empowernow_common.oauth import OAuth                       ║
║                                                                  ║
║  # From environment (recommended - zero config!)                 ║
║  client = OAuth.from_env()                                       ║
║  token = await client.get_token()                                ║
║                                                                  ║
║  # Explicit configuration                                        ║
║  client = OAuth.client_credentials(                              ║
║      "client-id", "secret", "https://idp.example.com"            ║
║  )                                                               ║
║                                                                  ║
║  # With OIDC discovery                                           ║
║  client = await OAuth.from_issuer(                               ║
║      "https://idp.example.com", "client-id", "secret"            ║
║  )                                                               ║
║                                                                  ║
║  COMMON OPERATIONS                                               ║
║  ─────────────────                                               ║
║  token = await client.get_token()           # Get/cache token    ║
║  token = await client.get_token(scope="x")  # With specific scope║
║  token = await client.get_token(            # With resource      ║
║      resource="https://api.example.com"                          ║
║  )                                                               ║
║  await client.revoke_token(token)           # Revoke token       ║
║  info = await client.introspect_token(t)    # Check token status ║
║                                                                  ║
║  REFRESH TOKENS                                                  ║
║  ──────────────                                                  ║
║  new_token = await client.refresh_access_token(                  ║
║      token.refresh_token                                         ║
║  )                                                               ║
║                                                                  ║
║  ADVANCED FEATURES                                               ║
║  ─────────────────                                               ║
║  client.configure_dpop()                    # Enable DPoP        ║
║  client.enable_mtls("cert", "key")          # Enable mTLS        ║
║  client.debug()                             # Debug mode         ║
║                                                                  ║
║  FLUENT BUILDER                                                  ║
║  ─────────────                                                   ║
║  client = (                                                      ║
║      OAuth.builder()                                             ║
║      .client_id("my-client")                                     ║
║      .client_secret("my-secret")                                 ║
║      .issuer("https://idp.example.com")                          ║
║      .with_dpop()                                                ║
║      .debug()                                                    ║
║      .build()                                                    ║
║  )                                                               ║
║                                                                  ║
║  ENVIRONMENT VARIABLES                                           ║
║  ─────────────────────                                           ║
║  OAUTH_CLIENT_ID       Client ID (required)                      ║
║  OAUTH_CLIENT_SECRET   Client secret                             ║
║  OAUTH_ISSUER          IdP issuer URL                            ║
║  OAUTH_TOKEN_URL       Direct token URL                          ║
║  OAUTH_SCOPE           Default scope                             ║
║  OAUTH_DEBUG           Enable debug mode                         ║
║                                                                  ║
║  More: https://docs.empowernow.com/oauth                         ║
╚══════════════════════════════════════════════════════════════════╝
        """)

    def __init__(
        self,
        config: SecureOAuthConfig | None = None,
        user_agent: str = "EmpowerNow-SecureOAuth/2.0",
        *,
        retry_policy: RetryPolicy = DEFAULT_RETRY_POLICY,
        issuer_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        token_endpoint_auth_method: str = "client_secret_basic",
        fips_mode: bool = False,
        timeout_seconds: int = 30,
        max_retries: int = 3,
    ):
        """Initialize secure OAuth client."""
        # Handle alternative initialization with individual parameters
        if config is None:
            if not issuer_url or not client_id:
                raise ValueError("Either config must be provided, or issuer_url and client_id must be specified")
            
            issuer_base = issuer_url.rstrip('/')
            config = SecureOAuthConfig(
                client_id=client_id,
                client_secret=client_secret or "",
                token_url=f"{issuer_base}/token",
                authorization_url=f"{issuer_base}/authorize",
                token_endpoint_auth_method=token_endpoint_auth_method,
            )
        
        self.config = config
        self.user_agent = user_agent

        # Create security context
        self._security_context = SecurityContext.create(
            user_agent=user_agent, client_id=config.client_id
        )

        # Initialize feature modules
        self._dpop_manager = DPoPManager()
        self._dpop_config: DPoPConfig | None = None
        self._par_manager = PARManager()
        self._jarm_manager = JARMManager(config.client_id)
        self._jar_manager = JARManager(config.client_id)
        self._ciba_manager = CIBAManager(config.client_id, config.client_secret)

        # mTLS settings
        self._mtls_cert: str | None = None
        self._mtls_key: str | None = None

        # PKJWT
        self._pkjwt_config: PrivateKeyJWTConfig | None = None

        self._retry_policy = retry_policy

        # Connection pooling
        self._http_client: httpx.AsyncClient | None = None
        self._dpop_nonce: str | None = None

        # Token caching - thread-safe with async lock
        self._cached_token: HardenedToken | None = None
        self._token_lock = asyncio.Lock()
        self._token_refresh_buffer_seconds = 60

        # Debug mode
        self._debug_mode = False
        
        # Correlation ID
        self._correlation_id: str | None = None

        logger.info(
            "oauth_client_initialized",
            client_id=config.client_id,
            token_url=config.token_url,
            auth_method=config.token_endpoint_auth_method,
        )
    
    def __repr__(self) -> str:
        """Rich, informative representation for debugging."""
        features = []
        if self._dpop_manager.is_enabled():
            features.append("DPoP")
        if self.is_mtls_enabled():
            features.append("mTLS")
        if self._debug_mode:
            features.append("Debug")
        
        cached_status = "none"
        if self._cached_token:
            if self._is_token_expired(self._cached_token):
                cached_status = "expired"
            else:
                cached_status = f"valid ({self._cached_token.expires_in_seconds}s remaining)"
        
        return (
            f"HardenedOAuth(\n"
            f"    client_id='{self.config.client_id}',\n"
            f"    token_url='{self.config.token_url}',\n"
            f"    auth_method='{self.config.token_endpoint_auth_method}',\n"
            f"    features={features or ['none']},\n"
            f"    cached_token={cached_status},\n"
            f")"
        )
    
    # ==================== DEBUG MODE ====================
    
    def debug(self, enabled: bool = True) -> "HardenedOAuth":
        """Enable debug mode for development.
        
        When enabled, logs detailed information about:
        - Configuration being used
        - Token requests (without secrets)
        - Response metadata
        - Cache operations
        - Retry attempts
        
        Args:
            enabled: Enable or disable debug mode
        
        Returns:
            Self for method chaining
        
        Warning:
            Do not enable in production - may log sensitive metadata.
        """
        self._debug_mode = enabled
        if enabled:
            self._debug_log("🔐", f"Debug mode enabled for '{self.config.client_id}'")
            self._debug_log("📡", f"Token URL: {self.config.token_url}")
            self._debug_log("🔑", f"Auth method: {self.config.token_endpoint_auth_method}")
        return self
    
    def _debug_log(self, emoji: str, message: str) -> None:
        """Log debug message with emoji prefix."""
        if self._debug_mode:
            print(f"[OAuth Debug] {emoji} {message}")
    
    # ==================== CORRELATION ID ====================
    
    def set_correlation_id(self, correlation_id: str | None) -> None:
        """Set correlation ID for subsequent requests."""
        self._correlation_id = correlation_id
    
    # ==================== GRANT TYPE INFERENCE ====================
    
    def _infer_grant_type(self, params: dict[str, Any]) -> str:
        """Infer OAuth grant type from parameters.
        
        Priority order:
        1. Explicit grant_type in params
        2. authorization_code if code/redirect_uri present
        3. refresh_token if refresh_token present
        4. client_credentials (default)
        """
        if "grant_type" in params:
            return params["grant_type"]
        
        if any(k in params for k in ("authorization_code", "code", "redirect_uri", "code_verifier")):
            return "authorization_code"
        
        if "refresh_token" in params:
            return "refresh_token"
        
        return "client_credentials"
    
    def _build_token_request_data(
        self,
        grant_type: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Build grant-type-specific token request payload."""
        data: dict[str, Any] = {"grant_type": grant_type}
        
        if grant_type == "authorization_code":
            code = params.get("authorization_code") or params.get("code")
            if not code:
                raise ValueError("authorization_code grant requires 'code' parameter")
            data["code"] = code
            if params.get("redirect_uri"):
                data["redirect_uri"] = params["redirect_uri"]
            if params.get("code_verifier"):
                data["code_verifier"] = params["code_verifier"]
                
        elif grant_type == "refresh_token":
            refresh = params.get("refresh_token")
            if not refresh:
                raise ValueError("refresh_token grant requires 'refresh_token' parameter")
            data["refresh_token"] = refresh
            
        elif grant_type == "urn:ietf:params:oauth:grant-type:token-exchange":
            # RFC 8693 Token Exchange
            subject_token = params.get("subject_token")
            if not subject_token:
                raise ValueError("token-exchange grant requires 'subject_token' parameter")
            data["subject_token"] = subject_token
            data["subject_token_type"] = params.get(
                "subject_token_type", 
                "urn:ietf:params:oauth:token-type:access_token"
            )
            if params.get("actor_token"):
                data["actor_token"] = params["actor_token"]
                data["actor_token_type"] = params.get(
                    "actor_token_type",
                    "urn:ietf:params:oauth:token-type:access_token"
                )
            if params.get("requested_token_type"):
                data["requested_token_type"] = params["requested_token_type"]
            if params.get("audience"):
                data["audience"] = params["audience"]
            
        # Scope for all grants
        if params.get("scope"):
            data["scope"] = params["scope"]
        elif self.config.scope:
            data["scope"] = self.config.scope
        
        # RFC 8707: resource parameter for all grants
        # Supports single resource (str) or multiple resources (list)
        resource = params.get("resource")
        if resource:
            # Already validated by validate_rfc8707_resource which returns list
            if isinstance(resource, list):
                # Multiple resources: httpx will encode as resource=uri1&resource=uri2
                data["resource"] = resource
            else:
                # Single resource (legacy path for audience fallback)
                data["resource"] = resource
        elif params.get("audience"):
            # Fallback to audience as resource (for compatibility)
            data["resource"] = params["audience"]
        
        return data
    
    def _should_use_dpop(self, grant_type: str) -> bool:
        """Check if DPoP should be used for this grant type."""
        if not self._dpop_manager.is_enabled():
            return False
        
        if not self._dpop_config:
            return True  # Legacy behavior: always use if enabled
        
        return self._dpop_config.should_use_dpop(grant_type)

    # ==================== MTLS METHODS ====================

    def enable_mtls(
        self, cert_path: str, key_path: str, *, hot_reload: bool = False
    ) -> None:
        """Enable Mutual-TLS client authentication."""
        if not Path(cert_path).exists():
            raise FileNotFoundError(f"Client certificate not found: {cert_path}")
        if not Path(key_path).exists():
            raise FileNotFoundError(f"Client key not found: {key_path}")

        cert_path = Path(cert_path).expanduser().resolve()
        key_path = Path(key_path).expanduser().resolve()

        self._mtls_cert = str(cert_path)
        self._mtls_key = str(key_path)

        self._mtls_cert_mtime = cert_path.stat().st_mtime
        self._mtls_key_mtime = key_path.stat().st_mtime
        self._mtls_hot_reload = hot_reload

        if x509:
            try:
                with open(cert_path, "rb") as f:
                    cert_data = f.read()
                cert_obj = x509.load_pem_x509_certificate(cert_data, default_backend())
                digest = cert_obj.fingerprint(hashes.SHA256())
                thumb_b64 = urlsafe_b64encode(digest).rstrip(b"=").decode()
                self._mtls_cert_thumbprint = thumb_b64
            except Exception as e:
                logger.warning("mtls_thumbprint_failed", error=str(e))
                self._mtls_cert_thumbprint = None
        else:
            self._mtls_cert_thumbprint = None

        logger.info("mtls_enabled", cert=self._mtls_cert)

    def is_mtls_enabled(self) -> bool:
        """Return True if Mutual-TLS is configured."""
        return bool(self._mtls_cert and self._mtls_key)

    def _maybe_reload_mtls_credentials(self):
        if not (self.is_mtls_enabled() and getattr(self, "_mtls_hot_reload", False)):
            return

        cert_path = Path(self._mtls_cert)
        key_path = Path(self._mtls_key)

        if cert_path.stat().st_mtime != getattr(
            self, "_mtls_cert_mtime", 0
        ) or key_path.stat().st_mtime != getattr(self, "_mtls_key_mtime", 0):
            logger.info("mtls_credentials_reloading")
            self._mtls_cert_mtime = cert_path.stat().st_mtime
            self._mtls_key_mtime = key_path.stat().st_mtime

            if x509:
                try:
                    with open(cert_path, "rb") as f:
                        cert_obj = x509.load_pem_x509_certificate(
                            f.read(), default_backend()
                        )
                    digest = cert_obj.fingerprint(hashes.SHA256())
                    self._mtls_cert_thumbprint = (
                        urlsafe_b64encode(digest).rstrip(b"=").decode()
                    )
                except Exception as e:
                    logger.warning("mtls_thumbprint_reload_failed", error=str(e))

    # ==================== DPoP METHODS ====================

    def enable_dpop(self, algorithm: str = "ES256") -> str:
        """Enable DPoP (Demonstrating Proof of Possession)."""
        return self._dpop_manager.enable_dpop()
    
    def configure_dpop(
        self,
        *,
        algorithm: str = "ES256",
        enable_for_client_credentials: bool = False,
        enable_for_authorization_code: bool = True,
        enable_for_refresh_token: bool = True,
    ) -> str:
        """Configure DPoP with per-grant control.
        
        Args:
            algorithm: DPoP signing algorithm (ES256 recommended)
            enable_for_client_credentials: Enable DPoP for CC flow (default: False)
            enable_for_authorization_code: Enable DPoP for auth code flow
            enable_for_refresh_token: Enable DPoP for refresh token flow
        
        Returns:
            JWK thumbprint of the DPoP key
        """
        self._dpop_config = DPoPConfig(
            enabled=True,
            algorithm=algorithm,
            enable_for_client_credentials=enable_for_client_credentials,
            enable_for_authorization_code=enable_for_authorization_code,
            enable_for_refresh_token=enable_for_refresh_token,
        )
        # DPoPManager.enable_dpop() doesn't take algorithm - it uses ES256 by default
        return self._dpop_manager.enable_dpop()

    async def get_dpop_bound_token(self, **kwargs) -> HardenedToken:
        """Get DPoP-bound access token (async)."""
        if not self._dpop_manager.is_enabled():
            raise DPoPError("DPoP not enabled. Call enable_dpop() first.")
        return await self.get_token(**kwargs)

    # ==================== PAR METHODS ====================

    async def create_par_request(
        self,
        redirect_uri: str,
        scope: str | None = None,
        authorization_details: list[SecureAuthorizationDetail] | None = None,
        **kwargs,
    ) -> PARResponse:
        """Create Pushed Authorization Request."""
        if not self.config.par_endpoint:
            raise PARError("PAR not configured - missing par_endpoint")

        par_request, code_verifier = self._par_manager.create_par_request(
            client_id=self.config.client_id,
            redirect_uri=redirect_uri,
            scope=scope or self.config.scope,
            authorization_details=(
                [detail.to_dict() for detail in authorization_details]
                if authorization_details
                else None
            ),
            **kwargs,
        )

        client = await self._get_secure_http_client()

        headers = self._get_security_headers()
        headers = self._dpop_manager.add_dpop_header(
            headers, "POST", self.config.par_endpoint
        )

        response = await client.post(
            self.config.par_endpoint,
            data=par_request.to_dict(),
            auth=(self.config.client_id, self.config.client_secret),
            headers=headers,
        )
        response.raise_for_status()

        par_data = response.json()
        return PARResponse(
            request_uri=par_data["request_uri"], expires_in=par_data["expires_in"]
        )

    def build_authorization_url(self, par_response: PARResponse, **kwargs) -> str:
        """Build authorization URL using PAR request URI."""
        return self._par_manager.build_authorization_url(
            authorization_url=self.config.authorization_url,
            client_id=self.config.client_id,
            request_uri=par_response.request_uri,
            **kwargs,
        )

    # ==================== JARM/JAR METHODS ====================

    def enable_jarm(self, response_mode: str = "jwt", **kwargs) -> None:
        """Enable JARM (JWT Secured Authorization Response Mode)."""
        self._jarm_manager.enable_jarm(response_mode=response_mode, **kwargs)

    def process_jarm_response(self, response_data) -> dict[str, Any]:
        """Process JARM authorization response."""
        return self._jarm_manager.process_response(response_data)

    def configure_jar(
        self, signing_algorithm: str = "RS256", signing_key=None, **kwargs
    ) -> None:
        """Configure JAR (JWT Secured Authorization Request)."""
        if not signing_key:
            signing_key = generate_jar_signing_key(signing_algorithm)
        self._jar_manager.configure_jar(
            signing_algorithm=signing_algorithm, signing_key=signing_key, **kwargs
        )

    def create_jar_request_object(
        self, authorization_params: dict[str, Any], audience: str, expires_in: int = 600
    ) -> str:
        """Create JAR request object."""
        if not self._jar_manager.is_configured():
            raise JARAuthError("JAR not configured. Call configure_jar() first.")
        return self._jar_manager.create_request_object(
            authorization_params=authorization_params,
            audience=audience,
            expires_in=expires_in,
        )

    # ==================== CORE TOKEN METHODS ====================

    async def get_token(
        self,
        *,
        force_refresh: bool = False,
        scope: str | None = None,
        resource: str | list[str] | None = None,
        correlation_id: str | None = None,
        **params,
    ) -> HardenedToken:
        """Get OAuth access token with automatic caching.
        
        Thread-safe. Multiple concurrent calls will only trigger one token refresh.
        Tokens are cached and automatically refreshed before expiry.
        
        Args:
            force_refresh: Force token refresh even if cached token is valid
            scope: OAuth scope(s) to request
            resource: RFC 8707 resource indicator(s) - single URI or list of URIs
            correlation_id: Correlation ID for distributed tracing
            **params: Additional parameters for token request
        
        Returns:
            Valid OAuth access token
            
        Raises:
            TokenRequestError: If token acquisition fails
            RateLimitError: If rate limited by IdP
            CircuitOpenError: If circuit breaker is open
            ResourceValidationError: If resource URI is invalid per RFC 8707
            
        Example:
            # Basic usage
            token = await client.get_token()
            
            # With specific scope
            token = await client.get_token(scope="read:users write:users")
            
            # With RFC 8707 resource indicator (single)
            token = await client.get_token(resource="https://api.example.com")
            
            # With multiple RFC 8707 resource indicators
            token = await client.get_token(resource=[
                "https://api.example.com/v1",
                "https://reports.example.com",
            ])
            
            # Force refresh after permission change
            token = await client.get_token(force_refresh=True)
        """
        async with self._token_lock:
            # Return cached token if valid (unless force refresh)
            if not force_refresh and self._cached_token:
                if not self._is_token_expired(self._cached_token):
                    self._debug_log("💾", "Returning cached token")
                    record_cache_hit(self.config.client_id)
                    return self._cached_token
            
            record_cache_miss(self.config.client_id)
            
            # Build params
            if scope:
                params["scope"] = scope
            if resource:
                # Validate RFC 8707 resource(s)
                validated_resources = validate_rfc8707_resource(resource)
                params["resource"] = validated_resources
            
            self._debug_log("🚀", f"Requesting new token")
            self._cached_token = await self._secure_request_token(
                correlation_id=correlation_id,
                **params,
            )
            
            # Update expiry metric
            if self._cached_token.expires_at:
                set_token_expiry(
                    self.config.client_id,
                    self._cached_token.expires_at.timestamp(),
                )
            
            self._debug_log("✅", f"Token received (expires_in={self._cached_token.expires_in}s)")
            return self._cached_token
    
    async def refresh_access_token(
        self,
        refresh_token: str,
        *,
        scope: str | None = None,
        resource: str | None = None,
        correlation_id: str | None = None,
    ) -> HardenedToken:
        """Refresh an access token using a refresh token.
        
        Args:
            refresh_token: The refresh token from a previous token response
            scope: Optional scope to request (may be subset of original)
            resource: RFC 8707 resource indicator
            correlation_id: Correlation ID for distributed tracing
        
        Returns:
            New access token (may include new refresh token)
        
        Raises:
            InvalidGrantError: If refresh token is invalid or expired
            
        Example:
            new_token = await client.refresh_access_token(
                old_token.refresh_token
            )
        """
        return await self._secure_request_token(
            grant_type="refresh_token",
            refresh_token=refresh_token,
            scope=scope,
            resource=resource,
            correlation_id=correlation_id,
        )
    
    async def token_exchange(
        self,
        subject_token: str,
        subject_token_type: str = "urn:ietf:params:oauth:token-type:access_token",
        *,
        actor_token: str | None = None,
        actor_token_type: str | None = None,
        requested_token_type: str | None = None,
        resource: str | list[str] | None = None,
        audience: str | None = None,
        scope: str | None = None,
        correlation_id: str | None = None,
    ) -> HardenedToken:
        """Exchange a token for another token (RFC 8693 Token Exchange).
        
        Enables delegation and impersonation scenarios where a service needs
        to act on behalf of a user or another service.
        
        Args:
            subject_token: The token being exchanged (required)
            subject_token_type: Type of subject token (default: access_token)
            actor_token: Token representing the acting party (optional)
            actor_token_type: Type of actor token (required if actor_token provided)
            requested_token_type: Desired token type (optional)
            resource: RFC 8707 resource indicator(s) - single URI or list of URIs
            audience: Logical name of the target service
            scope: Requested scope for the new token
            correlation_id: Correlation ID for distributed tracing
        
        Returns:
            New token from the exchange
        
        Raises:
            TokenRequestError: If the exchange fails
            ResourceValidationError: If resource URI is invalid per RFC 8707
            
        Token Type URNs:
            - urn:ietf:params:oauth:token-type:access_token
            - urn:ietf:params:oauth:token-type:refresh_token
            - urn:ietf:params:oauth:token-type:id_token
            - urn:ietf:params:oauth:token-type:saml1
            - urn:ietf:params:oauth:token-type:saml2
            - urn:ietf:params:oauth:token-type:jwt
        
        Example:
            # Exchange user token for service-specific token
            service_token = await client.token_exchange(
                subject_token=user_access_token,
                audience="backend-api",
                scope="read:data",
            )
            
            # Delegation with actor token
            delegated_token = await client.token_exchange(
                subject_token=user_token,
                actor_token=service_token,
                actor_token_type="urn:ietf:params:oauth:token-type:access_token",
                audience="downstream-service",
            )
            
            # With multiple RFC 8707 resources
            token = await client.token_exchange(
                subject_token=user_token,
                resource=["https://api1.example.com", "https://api2.example.com"],
            )
        """
        # Build token exchange parameters
        params: dict[str, Any] = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": subject_token,
            "subject_token_type": subject_token_type,
        }
        
        if actor_token:
            params["actor_token"] = actor_token
            params["actor_token_type"] = actor_token_type or "urn:ietf:params:oauth:token-type:access_token"
        
        if requested_token_type:
            params["requested_token_type"] = requested_token_type
        
        if resource:
            # Validate RFC 8707 resource(s)
            validated_resources = validate_rfc8707_resource(resource)
            params["resource"] = validated_resources
        
        if audience:
            params["audience"] = audience
        
        if scope:
            params["scope"] = scope
        
        self._debug_log("🔄", f"Token exchange: subject_type={subject_token_type}")
        
        return await self._secure_request_token(
            correlation_id=correlation_id,
            **params,
        )
    
    def _is_token_expired(self, token: HardenedToken) -> bool:
        """Check if token is expired or about to expire."""
        if not token.expires_in or not token.issued_at:
            return False
        
        expiry_time = token.issued_at + timedelta(seconds=token.expires_in)
        buffer_time = expiry_time - timedelta(seconds=self._token_refresh_buffer_seconds)
        return datetime.now(timezone.utc) >= buffer_time
    
    def clear_token_cache(self) -> None:
        """Clear the cached token. Next get_token() call will acquire a new token."""
        self._cached_token = None
        record_cache_clear(self.config.client_id)
        self._debug_log("🗑️", "Token cache cleared")

    async def exchange_authorization_code(
        self, authorization_code: str, state: str, redirect_uri: str, **kwargs
    ) -> HardenedToken:
        """Exchange authorization code for tokens with PKCE validation."""
        token_params = self._par_manager.validate_authorization_code_params(
            authorization_code, state, redirect_uri
        )
        token_params.update(kwargs)
        return await self._secure_request_token(**token_params)

    # ==================== SECURE AUTHORIZATION FLOWS ====================

    async def secure_authorization_flow(
        self,
        redirect_uri: str,
        scope: str | None = None,
        authorization_details: list[SecureAuthorizationDetail] | None = None,
        **kwargs,
    ) -> tuple[str, str]:
        """Complete secure authorization flow with PAR + PKCE."""
        par_response = await self.create_par_request(
            redirect_uri=redirect_uri,
            scope=scope,
            authorization_details=authorization_details,
            **kwargs,
        )

        authorization_url = self.build_authorization_url(par_response)
        state = generate_secure_token(32)

        return authorization_url, state

    async def secure_authorization_flow_with_jarm(
        self,
        redirect_uri: str,
        scope: str | None = None,
        authorization_details: list[SecureAuthorizationDetail] | None = None,
        **kwargs,
    ) -> tuple[str, str]:
        """Complete secure authorization flow with PAR + PKCE + JARM."""
        if not self._jarm_manager.is_enabled():
            raise JARMError("JARM not enabled. Call enable_jarm() first.")

        kwargs["response_mode"] = self._jarm_manager.get_response_mode()

        return await self.secure_authorization_flow(
            redirect_uri=redirect_uri,
            scope=scope,
            authorization_details=authorization_details,
            **kwargs,
        )

    async def secure_authorization_flow_with_jar_and_jarm(
        self,
        redirect_uri: str,
        scope: str | None = None,
        authorization_details: list[SecureAuthorizationDetail] | None = None,
        **kwargs,
    ) -> tuple[str, str]:
        """Complete secure authorization flow with JAR + PAR + PKCE + JARM."""
        if not self._jar_manager.is_configured():
            raise JARAuthError("JAR not configured. Call configure_jar() first.")

        if not self._jarm_manager.is_enabled():
            raise JARMError("JARM not enabled. Call enable_jarm() first.")

        auth_params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": redirect_uri,
            "scope": scope or self.config.scope,
            "response_mode": self._jarm_manager.get_response_mode(),
        }

        if authorization_details:
            auth_params["authorization_details"] = [
                detail.to_dict() for detail in authorization_details
            ]

        auth_params.update(kwargs)

        request_object = self.create_jar_request_object(
            authorization_params=auth_params, audience=self.config.authorization_url
        )

        from urllib.parse import urlencode
        query = urlencode({"client_id": self.config.client_id, "request": request_object})
        authorization_url = f"{self.config.authorization_url}?{query}"
        state = generate_secure_token(32)

        return authorization_url, state

    # ==================== CIBA METHODS ====================

    def configure_ciba(
        self, ciba_endpoint: str = None, token_endpoint: str = None
    ) -> None:
        """Configure CIBA (Client Initiated Backchannel Authentication)."""
        ciba_endpoint = ciba_endpoint or self.config.ciba_endpoint
        token_endpoint = token_endpoint or self.config.token_url

        if not ciba_endpoint:
            raise CIBAError("CIBA endpoint required")
        if not token_endpoint:
            raise CIBAError("Token endpoint required")

        self._ciba_manager.configure_ciba(
            ciba_endpoint=ciba_endpoint, token_endpoint=token_endpoint
        )

    async def initiate_ciba_authentication(self, request: CIBARequest):
        """Initiate CIBA authentication."""
        if not self._ciba_manager.is_configured():
            if self.config.ciba_endpoint:
                self.configure_ciba()
            else:
                raise CIBAError("CIBA not configured. Call configure_ciba() first.")
        return await self._ciba_manager.initiate_authentication(request)

    async def ciba_authenticate_user(
        self, scope: str, login_hint: str = None, **kwargs
    ):
        """Complete CIBA authentication flow."""
        if not self._ciba_manager.is_configured():
            if self.config.ciba_endpoint:
                self.configure_ciba()
            else:
                raise CIBAError("CIBA not configured. Call configure_ciba() first.")
        return await self._ciba_manager.authenticate_user(
            scope=scope, login_hint=login_hint, **kwargs
        )

    # ==================== RAR METHODS ====================

    def create_rar_builder(self) -> RARBuilder:
        """Create RAR builder for AuthZEN-compatible authorization details."""
        return RARBuilder()

    def create_account_access_request(
        self, account_id: str, actions: list[str] = None, **kwargs
    ):
        """Create account access authorization detail."""
        return create_account_access_detail(account_id, actions, **kwargs)

    def create_api_access_request(
        self, api_endpoint: str, methods: list[str] = None, **kwargs
    ):
        """Create API access authorization detail."""
        return create_api_access_detail(api_endpoint, methods, **kwargs)

    def convert_rar_to_authzen(
        self,
        authorization_details: list[SecureAuthorizationDetail],
        subject: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Convert RAR authorization details to AuthZEN requests."""
        authzen_requests = []
        for detail in authorization_details:
            authzen_requests.append(detail.to_authzen_request(subject))
        return authzen_requests

    # ==================== INTERNAL METHODS ====================

    def _get_security_headers(
        self,
        correlation_id: str | None = None,
    ) -> dict[str, str]:
        """Get standard security headers with optional correlation ID."""
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": self.user_agent,
            "X-Request-ID": generate_secure_token(16),
            "X-Client-Fingerprint": self._security_context.client_fingerprint,
        }
        
        # Correlation ID (parameter > instance > none)
        cid = correlation_id or self._correlation_id
        if cid and self.config.propagate_correlation_id:
            headers[self.config.correlation_id_header] = cid
        
        return headers

    async def _get_secure_http_client(self) -> httpx.AsyncClient:
        """Get shared HTTP client."""
        if self._http_client:
            return self._http_client

        http_pool = self.config.http_pool
        
        client_kwargs = dict(
            timeout=http_pool.to_httpx_timeout(),
            verify=True,
            limits=http_pool.to_httpx_limits(),
        )

        if self.is_mtls_enabled():
            client_kwargs["cert"] = (self._mtls_cert, self._mtls_key)

        self._http_client = httpx.AsyncClient(**client_kwargs)
        return self._http_client

    async def aclose(self):
        if self._http_client:
            await self._http_client.aclose()

    async def _secure_request_token(
        self,
        correlation_id: str | None = None,
        **params,
    ) -> HardenedToken:
        """Internal secure token request with comprehensive error handling."""
        grant_type = self._infer_grant_type(params)
        cid = correlation_id or self._correlation_id
        
        logger.info(
            "oauth_token_request_start",
            grant_type=grant_type,
            client_id=self.config.client_id,
            correlation_id=cid,
            has_resource=bool(params.get("resource")),
            dpop_enabled=self._should_use_dpop(grant_type),
        )
        
        with track_token_request(grant_type, self.config.client_id):
            max_attempts = self._retry_policy.attempts

            for attempt in range(max_attempts):
                try:
                    token_url = self.config.token_url
                    client = await self._get_secure_http_client()

                    headers = self._get_security_headers(correlation_id=cid)
                    
                    # Add DPoP header if enabled for this grant type
                    if self._should_use_dpop(grant_type):
                        headers = self._dpop_manager.add_dpop_header(
                            headers, "POST", token_url, nonce=self._dpop_nonce
                        )

                    # Build request data
                    data = self._build_token_request_data(grant_type, params)

                    auth = None
                    # Handle token endpoint authentication methods
                    if self.config.token_endpoint_auth_method == "private_key_jwt" and self._pkjwt_config:
                        assertion = self._pkjwt_config.to_jwt(
                            self.config.client_id, self.config.token_url
                        )
                        data.update({
                            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                            "client_assertion": assertion,
                        })
                    elif self.config.token_endpoint_auth_method == "client_secret_post":
                        data.update({
                            "client_id": self.config.client_id,
                            "client_secret": self.config.client_secret,
                        })
                    elif self.config.token_endpoint_auth_method == "client_secret_basic":
                        auth = (self.config.client_id, self.config.client_secret)
                    elif self.config.token_endpoint_auth_method == "none":
                        data.update({"client_id": self.config.client_id})
                    else:
                        if self._pkjwt_config:
                            assertion = self._pkjwt_config.to_jwt(
                                self.config.client_id, self.config.token_url
                            )
                            data.update({
                                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                                "client_assertion": assertion,
                            })
                        else:
                            auth = (self.config.client_id, self.config.client_secret)

                    self._debug_log("📤", f"POST {token_url} (grant_type={grant_type})")
                    
                    response = await client.post(token_url, data=data, headers=headers, auth=auth)
                    
                    record_http_request(
                        self.config.client_id,
                        "token",
                        response.status_code,
                    )
                    
                    response.raise_for_status()

                    token_data = response.json()
                    
                    self._debug_log("📥", f"Response: {response.status_code} OK")

                    # Handle token binding
                    if self._should_use_dpop(grant_type) and self._dpop_manager.is_enabled():
                        token_data["token_binding"] = {
                            "method": "dpop",
                            "jwk_thumbprint": self._dpop_manager.get_jwk_thumbprint(),
                        }
                    elif self.is_mtls_enabled() and getattr(self, "_mtls_cert_thumbprint", None):
                        token_data["token_binding"] = {
                            "method": "mtls",
                            "cert_thumbprint": self._mtls_cert_thumbprint,
                        }

                    # Filter token_data to HardenedToken fields
                    filtered_token_data = {
                        k: v for k, v in token_data.items() 
                        if k in {
                            'access_token', 'token_type', 'expires_in', 'refresh_token', 
                            'scope', 'id_token', 'issued_at', 'token_binding',
                            'issued_token_type',  # RFC 8693 Token Exchange response
                        }
                    }
                    
                    token = HardenedToken(
                        **filtered_token_data,
                        client_fingerprint=self._security_context.client_fingerprint,
                    )
                    
                    logger.info(
                        "oauth_token_request_success",
                        grant_type=grant_type,
                        client_id=self.config.client_id,
                        correlation_id=cid,
                        expires_in=token.expires_in,
                        has_refresh_token=bool(token.refresh_token),
                    )
                    
                    return token
                    
                except httpx.HTTPStatusError as exc:
                    status = exc.response.status_code
                    
                    # Parse OAuth error response
                    try:
                        error_body = exc.response.json()
                        oauth_error = error_body.get("error")
                        oauth_desc = error_body.get("error_description")
                    except Exception:
                        error_body = None
                        oauth_error = None
                        oauth_desc = None
                    
                    # DPoP nonce challenge
                    if status == 401:
                        www = exc.response.headers.get("WWW-Authenticate", "")
                        nonce = exc.response.headers.get("DPoP-Nonce") or exc.response.headers.get("dpop-nonce")
                        if ("use_dpop_nonce" in www or nonce) and attempt < max_attempts - 1:
                            self._dpop_nonce = nonce or self._dpop_nonce
                            record_dpop_nonce_challenge(self.config.client_id)
                            record_retry_attempt(self.config.client_id, grant_type, "dpop_nonce")
                            self._debug_log("🔄", f"DPoP nonce challenge, retrying")
                            continue
                    
                    # Rate limiting
                    if status == 429:
                        retry_after = self._parse_retry_after(exc.response)
                        if attempt < max_attempts - 1:
                            record_retry_attempt(self.config.client_id, grant_type, "rate_limit")
                            self._debug_log("⏳", f"Rate limited, waiting {retry_after}s")
                            await anyio.sleep(retry_after or 1)
                            continue
                        raise RateLimitError(
                            message="Rate limited by IdP",
                            retry_after_seconds=retry_after,
                            correlation_id=cid,
                            client_id=self.config.client_id,
                        )
                    
                    # Invalid grant
                    if oauth_error == "invalid_grant":
                        raise InvalidGrantError(
                            message=oauth_desc or "Invalid grant",
                            grant_type=grant_type,
                            correlation_id=cid,
                            client_id=self.config.client_id,
                            how_to_fix=[
                                "The authorization grant is invalid, expired, or revoked",
                                "For refresh tokens: the token may have been revoked or expired",
                                "For authorization codes: codes are single-use and expire quickly",
                            ],
                        )
                    
                    # Server errors (retry)
                    if 500 <= status < 600 and attempt < max_attempts - 1:
                        record_retry_attempt(self.config.client_id, grant_type, "server_error")
                        self._debug_log("🔄", f"Server error {status}, retrying")
                        await self._retry_policy.sleep(attempt)
                        continue
                    
                    # All other errors
                    logger.error(
                        "oauth_token_request_failed",
                        grant_type=grant_type,
                        client_id=self.config.client_id,
                        correlation_id=cid,
                        status_code=status,
                        oauth_error=oauth_error,
                    )
                    
                    raise TokenRequestError.from_response(
                        status_code=status,
                        response_body=error_body,
                        token_url=self.config.token_url,
                        auth_method=self.config.token_endpoint_auth_method,
                        client_id=self.config.client_id,
                        grant_type=grant_type,
                        correlation_id=cid,
                    )
                    
                except (httpx.TransportError, asyncio.TimeoutError) as exc:
                    if not self._retry_policy.is_retryable(exc) or attempt >= max_attempts - 1:
                        raise TokenRequestError.connection_error(
                            exception=exc,
                            token_url=self.config.token_url,
                            client_id=self.config.client_id,
                            correlation_id=cid,
                        )
                    record_retry_attempt(self.config.client_id, grant_type, "transport_error")
                    self._debug_log("🔄", f"Transport error, retrying")

                # Exponential backoff via policy
                await self._retry_policy.sleep(attempt)

            raise TokenRequestError(
                message="Token request failed after retries",
                error_code="max_retries_exceeded",
                client_id=self.config.client_id,
                correlation_id=cid,
                how_to_fix=[
                    "Check network connectivity",
                    "Verify IdP is healthy",
                    "Increase retry attempts or timeout",
                ],
            )
    
    def _parse_retry_after(self, response: httpx.Response) -> int | None:
        """Parse Retry-After header."""
        try:
            ra = response.headers.get("retry-after", "")
            try:
                return int(ra)
            except ValueError:
                import email.utils
                ts = email.utils.parsedate_to_datetime(ra)
                return max(0, int(ts.timestamp() - time.time()))
        except Exception:
            return None

    # ==================== PRIVATE KEY JWT ====================

    def configure_private_key_jwt(
        self, signing_key, signing_alg: str = "RS256", assertion_ttl: int = 300, *, kid: str | None = None
    ):
        """Configure private_key_jwt client authentication (RFC 7523)."""
        self._pkjwt_config = PrivateKeyJWTConfig(
            signing_key=signing_key,
            signing_alg=signing_alg,
            assertion_ttl=assertion_ttl,
            kid=kid,
        )
        logger.info("private_key_jwt_configured", alg=signing_alg)

    async def introspect_token(self, token: str) -> dict[str, Any]:
        """RFC 7662 token introspection."""
        if not self.config.introspection_url:
            raise SecurityError("introspection_url not configured")

        introspect_url = self.config.introspection_url
        client = await self._get_secure_http_client()
        headers = self._get_security_headers()
        data = {"token": token, "token_type_hint": "access_token"}

        if self._pkjwt_config:
            assertion = self._pkjwt_config.to_jwt(
                self.config.client_id, self.config.introspection_url
            )
            data.update({
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": assertion,
            })
            auth = None
        else:
            auth = (self.config.client_id, self.config.client_secret)

        response = await client.post(introspect_url, data=data, headers=headers, auth=auth)
        response.raise_for_status()
        return response.json()

    async def revoke_token(
        self, token: str, token_type_hint: str = "access_token"
    ) -> None:
        """RFC 7009 token revocation."""
        if not self.config.revocation_url:
            raise SecurityError("revocation_url not configured")

        revoke_url = self.config.revocation_url
        client = await self._get_secure_http_client()
        headers = self._get_security_headers()
        data = {"token": token, "token_type_hint": token_type_hint}

        if self._pkjwt_config:
            assertion = self._pkjwt_config.to_jwt(
                self.config.client_id, self.config.revocation_url
            )
            data.update({
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": assertion,
            })
            auth = None
        else:
            auth = (self.config.client_id, self.config.client_secret)

        response = await client.post(revoke_url, data=data, headers=headers, auth=auth)
        response.raise_for_status()

    # ==================== GRANT MANAGEMENT ====================

    def create_authorization_url_with_grant(
        self,
        par_response: PARResponse,
        *,
        action: "GrantManagementAction",
        grant_id: str = None,
        **kwargs,
    ) -> str:
        """Return authorization URL with grant_management_* parameters."""
        base = self.build_authorization_url(par_response, **kwargs)
        gm_params = build_grant_management_params(action, grant_id)
        import urllib.parse as _u
        return base + "&" + _u.urlencode(gm_params)

    # ==================== LIFECYCLE ====================

    def close(self) -> None:
        """Close the underlying pooled HTTP client (sync)."""
        if self._http_client and not self._http_client.is_closed:
            anyio.run(self.aclose)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.aclose()

    # Backward-compat alias
    async def secure_get_token(self, **params) -> HardenedToken:
        """Deprecated wrapper around _secure_request_token (async)."""
        return await self._secure_request_token(**params)


# Public aliases
OAuth = HardenedOAuth
Token = HardenedToken
AdvancedToken = HardenedToken
OAuthConfig = SecureOAuthConfig


# ==================== GRANT MANAGEMENT ====================

class GrantManagementAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"


def build_grant_management_params(
    action: GrantManagementAction, grant_id: str | None = None
) -> dict[str, str]:
    """Return RFC 8707 compliant query/body parameters."""
    params = {"grant_management_action": action.value}
    if grant_id:
        params["grant_id"] = grant_id
    return params
