"""OAuth client configuration with environment variable support.

This module provides enterprise-grade configuration for OAuth clients:
- Environment-variable-driven with Pydantic Settings
- HTTPPoolConfig for connection tuning
- DPoPConfig for per-grant DPoP control
- Full validation with helpful error messages

Environment Variables:
    OAUTH_CLIENT_ID: OAuth client ID (required)
    OAUTH_CLIENT_SECRET: OAuth client secret
    OAUTH_ISSUER: OAuth issuer URL (for OIDC discovery)
    OAUTH_TOKEN_URL: Token endpoint URL
    OAUTH_SCOPE: Default scope
    OAUTH_DEBUG: Enable debug mode (true/false)
    OAUTH_ALLOW_INTERNAL_HTTP: Allow HTTP for internal services
    OAUTH_TIMEOUT: Request timeout in seconds
    OAUTH_HTTP_MAX_CONNECTIONS: Max HTTP connections
    
Usage:
    # Load from environment variables (zero config!)
    config = OAuthSettings()
    oauth = HardenedOAuth(config.to_oauth_config())
    
    # Or with explicit values
    config = OAuthSettings(
        client_id="my-app",
        client_secret="secret",
        token_url="https://auth.example.com/oauth/token",
    )
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from difflib import get_close_matches


@dataclass
class HTTPPoolConfig:
    """HTTP connection pool configuration.
    
    Controls connection pooling for optimal performance and resource usage.
    All values can be overridden via environment variables.
    
    Example:
        config = HTTPPoolConfig(
            timeout=30.0,
            max_connections=20,
        )
    """
    
    timeout: float = field(
        default_factory=lambda: float(os.getenv("OAUTH_HTTP_TIMEOUT", "30.0"))
    )
    connect_timeout: float = field(
        default_factory=lambda: float(os.getenv("OAUTH_HTTP_CONNECT_TIMEOUT", "10.0"))
    )
    max_connections: int = field(
        default_factory=lambda: int(os.getenv("OAUTH_HTTP_MAX_CONNECTIONS", "10"))
    )
    max_keepalive_connections: int = field(
        default_factory=lambda: int(os.getenv("OAUTH_HTTP_MAX_KEEPALIVE", "5"))
    )
    
    def to_httpx_limits(self):
        """Convert to httpx.Limits for AsyncClient."""
        import httpx
        return httpx.Limits(
            max_connections=self.max_connections,
            max_keepalive_connections=self.max_keepalive_connections,
        )
    
    def to_httpx_timeout(self):
        """Convert to httpx.Timeout for AsyncClient."""
        import httpx
        return httpx.Timeout(
            timeout=self.timeout,
            connect=self.connect_timeout,
        )


@dataclass
class DPoPConfig:
    """DPoP configuration with per-grant control.
    
    Allows fine-grained control over which grant types use DPoP binding.
    By default, DPoP is enabled for user-facing flows but not for
    service-to-service (client_credentials) tokens.
    
    Example:
        config = DPoPConfig(
            enabled=True,
            algorithm="ES256",
            enable_for_client_credentials=False,  # No DPoP for CC tokens
        )
    """
    
    enabled: bool = False
    algorithm: str = "ES256"
    
    # Per-grant control
    enable_for_authorization_code: bool = True
    enable_for_refresh_token: bool = True
    enable_for_client_credentials: bool = False  # Often disabled for service tokens
    
    def should_use_dpop(self, grant_type: str) -> bool:
        """Check if DPoP should be used for this grant type."""
        if not self.enabled:
            return False
        
        if grant_type == "client_credentials":
            return self.enable_for_client_credentials
        elif grant_type == "authorization_code":
            return self.enable_for_authorization_code
        elif grant_type == "refresh_token":
            return self.enable_for_refresh_token
        
        return True  # Default: use DPoP for unknown grants


class OAuthSettings(BaseSettings):
    """OAuth client configuration with environment variable support.
    
    All settings can be configured via environment variables with OAUTH_ prefix,
    or via a .env file. This enables zero-config deployments where the OAuth
    client automatically picks up configuration from the environment.
    
    Example:
        # Set environment variables
        export OAUTH_CLIENT_ID=my-app
        export OAUTH_CLIENT_SECRET=secret
        export OAUTH_ISSUER=https://auth.example.com
        
        # Create config from environment (zero config!)
        config = OAuthSettings()
        
        # Use with HardenedOAuth
        oauth = HardenedOAuth(config.to_oauth_config())
    """
    
    model_config = SettingsConfigDict(
        env_prefix="OAUTH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )
    
    # Required credentials
    client_id: str = Field(
        ...,
        description="OAuth client ID",
        examples=["my-application"],
    )
    
    # Issuer OR token_url (at least one required)
    issuer: str | None = Field(
        default=None,
        description="OAuth issuer URL (for OIDC discovery)",
        examples=["https://auth.example.com"],
    )
    token_url: str | None = Field(
        default=None,
        description="Token endpoint URL (required if issuer not set)",
        examples=["https://auth.example.com/oauth/token"],
    )
    
    # Optional credentials
    client_secret: str = Field(
        default="",
        description="OAuth client secret (empty for public clients)",
    )
    
    # Optional endpoints
    authorization_url: str | None = Field(
        default=None,
        description="Authorization endpoint URL",
    )
    introspection_url: str | None = Field(
        default=None,
        description="Token introspection endpoint URL",
    )
    revocation_url: str | None = Field(
        default=None,
        description="Token revocation endpoint URL",
    )
    par_endpoint: str | None = Field(
        default=None,
        description="Pushed Authorization Request (PAR) endpoint URL",
    )
    ciba_endpoint: str | None = Field(
        default=None,
        description="Client Initiated Backchannel Authentication (CIBA) endpoint URL",
    )
    
    # Authentication settings
    token_endpoint_auth_method: str = Field(
        default="client_secret_basic",
        description="Token endpoint authentication method",
    )
    scope: str = Field(
        default="",
        description="Default scope for token requests",
    )
    
    # Security settings
    allow_internal_http: bool = Field(
        default=False,
        description="Allow HTTP for internal services (Docker/K8s)",
    )
    internal_http_hosts: str = Field(
        default="localhost,127.0.0.1,::1,idp-app,auth-service",
        description="Comma-separated hosts allowed to use HTTP",
    )
    
    # Debug settings
    debug: bool = Field(
        default=False,
        description="Enable debug logging",
    )
    
    # Resilience settings
    timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Request timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts",
    )
    
    # Circuit breaker settings
    circuit_failure_threshold: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of failures before circuit breaker opens",
    )
    circuit_reset_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=600.0,
        description="Seconds before circuit breaker resets",
    )
    
    # Token caching settings
    token_cache_buffer_seconds: int = Field(
        default=60,
        ge=0,
        le=600,
        description="Seconds before expiry to refresh token",
    )
    
    # HTTP pool settings
    http_max_connections: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum HTTP connections",
    )
    http_max_keepalive: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum keepalive connections",
    )
    http_connect_timeout: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="HTTP connect timeout in seconds",
    )
    
    # Correlation ID settings
    correlation_id_header: str = Field(
        default="X-Correlation-ID",
        description="Header name for correlation ID",
    )
    propagate_correlation_id: bool = Field(
        default=True,
        description="Propagate correlation ID to IdP",
    )
    
    @field_validator("token_endpoint_auth_method")
    @classmethod
    def validate_auth_method(cls, v: str) -> str:
        """Validate authentication method with helpful error messages."""
        valid_methods = {
            "client_secret_basic",
            "client_secret_post",
            "private_key_jwt",
            "none",
        }
        
        v_lower = v.lower().strip()
        if v_lower not in valid_methods:
            suggestions = get_close_matches(v_lower, valid_methods, n=2, cutoff=0.5)
            
            msg = f"Invalid token_endpoint_auth_method: '{v}'"
            if suggestions:
                msg += f"\n  Did you mean: {' or '.join(repr(s) for s in suggestions)}?"
            msg += f"\n  Valid options: {', '.join(sorted(valid_methods))}"
            raise ValueError(msg)
        
        return v_lower
    
    @field_validator("issuer", "token_url", "authorization_url")
    @classmethod
    def validate_url(cls, v: str | None, info) -> str | None:
        """Validate URLs are well-formed."""
        if not v:
            return v
        
        if not v.startswith(("http://", "https://")):
            raise ValueError(
                f"{info.field_name} must start with http:// or https://. Got: {v}"
            )
        
        return v.rstrip("/")
    
    @model_validator(mode="after")
    def validate_issuer_or_token_url(self):
        """Ensure either issuer or token_url is provided."""
        if not self.issuer and not self.token_url:
            raise ValueError(
                "Either 'issuer' or 'token_url' must be provided. "
                "Set OAUTH_ISSUER for OIDC discovery or OAUTH_TOKEN_URL for direct configuration."
            )
        return self
    
    def get_internal_http_hosts(self) -> tuple[str, ...]:
        """Get tuple of hosts allowed to use HTTP."""
        return tuple(h.strip() for h in self.internal_http_hosts.split(",") if h.strip())
    
    def get_http_pool_config(self) -> HTTPPoolConfig:
        """Get HTTP pool configuration."""
        return HTTPPoolConfig(
            timeout=self.timeout_seconds,
            connect_timeout=self.http_connect_timeout,
            max_connections=self.http_max_connections,
            max_keepalive_connections=self.http_max_keepalive,
        )
    
    def to_oauth_config(self):
        """Convert to SecureOAuthConfig for use with HardenedOAuth.
        
        Returns:
            SecureOAuthConfig instance
        """
        from .client import SecureOAuthConfig
        
        # Determine token URL
        token_url = self.token_url
        if not token_url and self.issuer:
            token_url = f"{self.issuer}/oauth/token"
        
        # Determine authorization URL
        authorization_url = self.authorization_url or ""
        if not authorization_url and self.issuer:
            authorization_url = f"{self.issuer}/authorize"
        
        return SecureOAuthConfig(
            client_id=self.client_id,
            client_secret=self.client_secret,
            token_url=token_url,
            authorization_url=authorization_url,
            introspection_url=self.introspection_url,
            revocation_url=self.revocation_url,
            par_endpoint=self.par_endpoint,
            ciba_endpoint=self.ciba_endpoint,
            token_endpoint_auth_method=self.token_endpoint_auth_method,
            scope=self.scope or None,
        )
    
    def get_env_template(self) -> str:
        """Generate a .env template with all available settings.
        
        Returns:
            String containing .env file template with comments
        """
        return '''# OAuth Client Configuration
# Copy this to .env and customize

# Required settings
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret

# Option 1: OIDC Discovery (recommended)
OAUTH_ISSUER=https://auth.example.com

# Option 2: Direct configuration
# OAUTH_TOKEN_URL=https://auth.example.com/oauth/token
# OAUTH_AUTHORIZATION_URL=https://auth.example.com/authorize

# Optional endpoints
# OAUTH_INTROSPECTION_URL=https://auth.example.com/oauth/introspect
# OAUTH_REVOCATION_URL=https://auth.example.com/oauth/revoke
# OAUTH_PAR_ENDPOINT=https://auth.example.com/oauth/par
# OAUTH_CIBA_ENDPOINT=https://auth.example.com/oauth/ciba

# Authentication method (client_secret_basic, client_secret_post, private_key_jwt, none)
OAUTH_TOKEN_ENDPOINT_AUTH_METHOD=client_secret_basic

# Default scope
# OAUTH_SCOPE=read write

# Security settings
OAUTH_ALLOW_INTERNAL_HTTP=false
# OAUTH_INTERNAL_HTTP_HOSTS=localhost,127.0.0.1,idp-app

# Debug mode (do not enable in production!)
OAUTH_DEBUG=false

# Resilience settings
OAUTH_TIMEOUT_SECONDS=30
OAUTH_MAX_RETRIES=3
OAUTH_CIRCUIT_FAILURE_THRESHOLD=5
OAUTH_CIRCUIT_RESET_TIMEOUT=30

# HTTP pool settings
OAUTH_HTTP_MAX_CONNECTIONS=10
OAUTH_HTTP_MAX_KEEPALIVE=5
OAUTH_HTTP_CONNECT_TIMEOUT=10

# Token caching
OAUTH_TOKEN_CACHE_BUFFER_SECONDS=60

# Correlation ID propagation
OAUTH_CORRELATION_ID_HEADER=X-Correlation-ID
OAUTH_PROPAGATE_CORRELATION_ID=true
'''


class PrivateKeyJWTSettings(BaseSettings):
    """Settings for private_key_jwt authentication.
    
    Environment Variables:
        OAUTH_PKJWT_KEY_PATH: Path to private key PEM file
        OAUTH_PKJWT_KEY_ID: Key ID (kid) for JWT header
        OAUTH_PKJWT_ALGORITHM: Signing algorithm (RS256, ES256, etc.)
        OAUTH_PKJWT_TTL: Assertion TTL in seconds
    """
    
    model_config = SettingsConfigDict(
        env_prefix="OAUTH_PKJWT_",
        env_file=".env",
        extra="ignore",
    )
    
    key_path: str | None = Field(
        default=None,
        description="Path to private key PEM file",
    )
    key_id: str | None = Field(
        default=None,
        description="Key ID (kid) for JWT header",
    )
    algorithm: str = Field(
        default="RS256",
        description="Signing algorithm",
    )
    ttl: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="Assertion TTL in seconds",
    )
    
    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        """Validate signing algorithm is supported."""
        valid_algorithms = {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"}
        v_upper = v.upper()
        if v_upper not in valid_algorithms:
            raise ValueError(
                f"Invalid algorithm: {v}. "
                f"Valid options: {', '.join(sorted(valid_algorithms))}"
            )
        return v_upper
    
    def load_key(self) -> bytes:
        """Load private key from file.
        
        Returns:
            Private key bytes
            
        Raises:
            FileNotFoundError: If key file doesn't exist
            ValueError: If key_path not configured
        """
        if not self.key_path:
            raise ValueError(
                "OAUTH_PKJWT_KEY_PATH not configured. "
                "Set the environment variable or provide key_path."
            )
        
        with open(self.key_path, "rb") as f:
            return f.read()
