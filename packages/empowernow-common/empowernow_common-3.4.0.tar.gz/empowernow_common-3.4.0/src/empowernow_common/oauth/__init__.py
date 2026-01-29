"""
EmpowerNow OAuth – Enterprise-Grade, Developer-Delightful OAuth 2.1

Quick Start (3 lines or less):
    # From environment (zero config!)
    from empowernow_common.oauth import OAuth
    token = await OAuth.from_env().get_token()
    
    # Client credentials flow
    client = OAuth.client_credentials("id", "secret", "https://idp.example.com")
    token = await client.get_token()
    
    # With OIDC discovery
    client = await OAuth.from_issuer("https://idp.example.com", "id", "secret")
    token = await client.get_token()

Features:
- Zero-config deployment (environment variables)
- One-liner quick starts
- Automatic token caching with thread-safe refresh
- Full OAuth 2.1 feature support:
  - RFC 8693: Token Exchange
  - RFC 9126: Pushed Authorization Requests (PAR)
  - RFC 9449: DPoP (Demonstrating Proof-of-Possession)
  - RFC 9101: JARM (JWT Secured Authorization Response)
  - RFC 9101: JAR (JWT Secured Authorization Request)
  - RFC 8707: Resource Indicators
  - Rich Authorization Requests (RAR)
  - CIBA (Client Initiated Backchannel Authentication)
- Prometheus metrics and structured logging
- Per-grant DPoP control
- Correlation ID propagation
- Debug mode for development

Documentation:
    Call OAuth.help() for quick reference.
"""

# Core OAuth client
from .client import (
    HardenedOAuth,
    SecureOAuthConfig,
    HardenedToken,
    GrantManagementAction,
    OAuthBuilder,
    PrivateKeyJWTConfig,
)

# Sync wrapper
from .sync import SyncOAuth

# DPoP (Demonstrating Proof of Possession)
from .dpop import DPoPKeyPair, DPoPProofGenerator, DPoPError, generate_dpop_key_pair

# PAR (Pushed Authorization Requests)
from .par import PARRequest, PARResponse, PARError, generate_pkce_challenge

# JARM (JWT Secured Authorization Response Mode)
from .jarm import JARMConfiguration, JARMResponseProcessor, JARMError

# JAR (JWT Secured Authorization Request)
from .jar import JARConfiguration, JARRequestBuilder, JARError, generate_jar_signing_key

# Rich Authorization Requests
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

# CIBA (Client Initiated Backchannel Authentication)
from .ciba import CIBARequest, CIBAResponse, CIBAError

# Security and validation
from .security import (
    FIPSValidator,
    SecurityContext,
    validate_url_security,
    validate_url_with_internal_http,
    sanitize_string_input,
    generate_secure_token,
    DEFAULT_INTERNAL_HTTP_HOSTS,
    validate_rfc8707_resource,
    ResourceValidationError,
)

# Rich error classes
from .errors import (
    OAuthError,
    TokenRequestError,
    TokenExpiredError,
    TokenRefreshError,
    InvalidGrantError,
    CircuitOpenError,
    RateLimitError,
    DPoPNonceError,
    MTLSError,
    ConfigurationError,
    SecurityError,  # Domain-specific security error
    DiscoveryError,
    IntrospectionError,
    RevocationError,
    # Backward compatibility aliases
    OAuthTokenError,
    OAuthCircuitBreakerError,
    OAuthDiscoveryError,
    OAuthConfigurationError,
    OAuthIntrospectionError,
    OAuthRevocationError,
)

# Metrics (optional - gracefully degrades if prometheus_client not installed)
from .metrics import (
    is_metrics_available,
    track_token_request,
    record_token_request,
    record_cache_hit,
    record_cache_miss,
    record_cache_clear,
    record_dpop_nonce_challenge,
    record_http_request,
    record_retry_attempt,
    set_circuit_breaker_state,
    set_token_expiry,
)

# Pydantic Settings configuration
from .config import (
    OAuthSettings,
    PrivateKeyJWTSettings,
    HTTPPoolConfig,
    DPoPConfig,
)

# Compatibility aliases
OAuth = HardenedOAuth
Token = HardenedToken
AdvancedToken = HardenedToken

__all__ = [
    # Core Client
    "HardenedOAuth",
    "OAuth",  # Alias
    "SecureOAuthConfig",
    "HardenedToken",
    "Token",  # Alias
    "AdvancedToken",  # Alias
    "OAuthBuilder",
    "PrivateKeyJWTConfig",
    "GrantManagementAction",
    # Sync Wrapper
    "SyncOAuth",
    # DPoP
    "DPoPKeyPair",
    "DPoPProofGenerator",
    "DPoPError",
    "generate_dpop_key_pair",
    # PAR
    "PARRequest",
    "PARResponse",
    "PARError",
    "generate_pkce_challenge",
    # JARM
    "JARMConfiguration",
    "JARMResponseProcessor",
    "JARMError",
    # JAR
    "JARConfiguration",
    "JARRequestBuilder",
    "JARError",
    "generate_jar_signing_key",
    # RAR
    "SecureAuthorizationDetail",
    "RARError",
    "RARBuilder",
    "AuthZENCompatibleResource",
    "AuthZENCompatibleAction",
    "AuthZENCompatibleContext",
    "StandardActionType",
    "StandardResourceType",
    "create_account_access_detail",
    "create_api_access_detail",
    # CIBA
    "CIBARequest",
    "CIBAResponse",
    "CIBAError",
    # Security
    "FIPSValidator",
    "SecurityError",
    "SecurityContext",
    "validate_url_security",
    "validate_url_with_internal_http",
    "sanitize_string_input",
    "generate_secure_token",
    "DEFAULT_INTERNAL_HTTP_HOSTS",
    # Errors (new domain-specific)
    "OAuthError",
    "TokenRequestError",
    "TokenExpiredError",
    "TokenRefreshError",
    "InvalidGrantError",
    "CircuitOpenError",
    "RateLimitError",
    "DPoPNonceError",
    "MTLSError",
    "ConfigurationError",
    "DiscoveryError",
    "IntrospectionError",
    "RevocationError",
    # Errors (backward compatibility)
    "OAuthTokenError",
    "OAuthCircuitBreakerError",
    "OAuthDiscoveryError",
    "OAuthConfigurationError",
    "OAuthIntrospectionError",
    "OAuthRevocationError",
    # Metrics
    "is_metrics_available",
    "track_token_request",
    "record_token_request",
    "record_cache_hit",
    "record_cache_miss",
    "record_cache_clear",
    "record_dpop_nonce_challenge",
    "record_http_request",
    "record_retry_attempt",
    "set_circuit_breaker_state",
    "set_token_expiry",
    # Configuration
    "OAuthSettings",
    "PrivateKeyJWTSettings",
    "HTTPPoolConfig",
    "DPoPConfig",
]

# Version info
__version__ = "2.5.0"
__author__ = "EmpowerNow Security Team"
__description__ = "Enterprise-grade OAuth 2.1 with developer-delightful DX"
