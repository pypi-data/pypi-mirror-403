"""OAuth client error classes with rich context and actionable guidance.

These error classes provide detailed, actionable error messages that help
developers quickly diagnose and fix OAuth integration issues.

Per Excellence Playbook Section 9.2: Domain-specific exceptions with context.

Usage:
    try:
        token = await oauth.get_token()
    except OAuthTokenError as e:
        print(f"Error: {e.error_code}")
        print(f"How to fix: {e.how_to_fix}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from ..exceptions import EmpowerNowError


@dataclass
class OAuthError(Exception):
    """Base OAuth error with actionable guidance.
    
    All OAuth errors include:
    - Human-readable message
    - Machine-readable error code
    - How-to-fix guidance
    - Request context (URLs, auth methods, etc.)
    - Optional documentation URL
    """
    
    message: str
    error_code: str = "oauth_error"
    how_to_fix: list[str] = field(default_factory=list)
    docs_url: str | None = None
    correlation_id: str | None = None
    
    # Additional context
    status_code: int | None = None
    url: str | None = None
    auth_method: str | None = None
    client_id: str | None = None
    grant_type: str | None = None
    details: dict[str, Any] | None = None
    
    def __str__(self) -> str:
        """Format error with all available context and guidance."""
        parts = [self.message]
        
        if self.status_code:
            parts.append(f"  Status: {self.status_code}")
        if self.error_code and self.error_code != "oauth_error":
            parts.append(f"  Error Code: {self.error_code}")
        if self.url:
            parts.append(f"  URL: {self.url}")
        if self.auth_method:
            parts.append(f"  Auth Method: {self.auth_method}")
        if self.client_id:
            parts.append(f"  Client ID: {self.client_id}")
        if self.grant_type:
            parts.append(f"  Grant Type: {self.grant_type}")
        if self.correlation_id:
            parts.append(f"  Correlation ID: {self.correlation_id}")
        
        if self.how_to_fix:
            parts.append("")
            parts.append("How to fix:")
            for i, fix in enumerate(self.how_to_fix, 1):
                parts.append(f"  {i}. {fix}")
        
        if self.docs_url:
            parts.append(f"\nDocumentation: {self.docs_url}")
        
        return "\n".join(parts)
    
    def to_dict(self) -> dict:
        """Convert error to dictionary for logging/serialization."""
        return {
            "message": self.message,
            "error_code": self.error_code,
            "how_to_fix": self.how_to_fix,
            "docs_url": self.docs_url,
            "correlation_id": self.correlation_id,
            "status_code": self.status_code,
            "url": self.url,
            "auth_method": self.auth_method,
            "client_id": self.client_id,
            "grant_type": self.grant_type,
            "details": self.details,
        }


@dataclass
class TokenRequestError(OAuthError):
    """Token request failed."""
    
    error_code: str = "token_request_failed"
    oauth_error: str | None = None  # error field from OAuth response
    oauth_error_description: str | None = None
    
    @classmethod
    def from_response(
        cls,
        status_code: int,
        response_body: dict | None,
        token_url: str,
        auth_method: str,
        client_id: str,
        grant_type: str = "client_credentials",
        correlation_id: str | None = None,
    ) -> TokenRequestError:
        """Create error from HTTP response with helpful guidance."""
        oauth_error = None
        oauth_error_description = None
        how_to_fix = []
        
        if response_body:
            oauth_error = response_body.get("error")
            oauth_error_description = response_body.get("error_description")
        
        # Add troubleshooting guidance based on status and error
        if status_code == 401:
            how_to_fix = [
                "Verify client_id matches exactly (case-sensitive)",
                "Check client_secret is correct and not URL-encoded",
                f"Ensure IdP expects '{auth_method}' authentication method",
            ]
            if auth_method == "private_key_jwt":
                how_to_fix.extend([
                    "Verify private key matches public key registered with IdP",
                    "Check that the key ID (kid) is correct",
                ])
            if oauth_error == "invalid_client":
                how_to_fix.insert(0, "Client credentials are incorrect or client doesn't exist")
        
        elif status_code == 400:
            how_to_fix = [
                f"Check grant_type '{grant_type}' is supported by the IdP",
                "Verify scope values are valid and allowed for this client",
                "Ensure all required parameters are provided",
            ]
            if oauth_error == "invalid_grant":
                how_to_fix.insert(0, "The authorization grant is invalid, expired, or revoked")
            elif oauth_error == "invalid_scope":
                how_to_fix.insert(0, "One or more requested scopes are invalid")
            elif oauth_error == "unsupported_grant_type":
                how_to_fix.insert(0, f"Grant type '{grant_type}' is not supported by this IdP")
        
        elif status_code == 403:
            how_to_fix = [
                "Client may not be authorized for the requested scope",
                f"Check if client is allowed to use '{grant_type}' grant",
                "Verify client has necessary permissions in IdP",
            ]
        
        elif status_code == 429:
            how_to_fix = [
                "Rate limit exceeded - implement exponential backoff",
                "Check Retry-After header for wait time",
                "Consider caching tokens to reduce requests",
            ]
        
        elif status_code >= 500:
            how_to_fix = [
                "IdP may be experiencing issues - check status page",
                "Retry the request with exponential backoff",
                "If persistent, contact IdP support",
            ]
        
        message = f"Token request failed: HTTP {status_code}"
        if oauth_error:
            message = f"Token request failed: {oauth_error}"
            if oauth_error_description:
                message += f" - {oauth_error_description}"
        
        return cls(
            message=message,
            error_code=f"token_{oauth_error or 'request_failed'}",
            how_to_fix=how_to_fix,
            status_code=status_code,
            url=token_url,
            auth_method=auth_method,
            client_id=client_id,
            grant_type=grant_type,
            correlation_id=correlation_id,
            oauth_error=oauth_error,
            oauth_error_description=oauth_error_description,
        )
    
    @classmethod
    def connection_error(
        cls,
        exception: Exception,
        token_url: str,
        client_id: str,
        correlation_id: str | None = None,
    ) -> TokenRequestError:
        """Create error for connection failures."""
        return cls(
            message=f"Failed to connect to token endpoint: {exception}",
            error_code="connection_failed",
            url=token_url,
            client_id=client_id,
            correlation_id=correlation_id,
            how_to_fix=[
                "Verify the token URL is correct and reachable",
                "Check network connectivity and firewall rules",
                "Ensure DNS is resolving correctly",
                "If using HTTPS, verify TLS certificates are valid",
            ],
        )
    
    @classmethod
    def timeout_error(
        cls,
        token_url: str,
        timeout_seconds: float,
        client_id: str,
        correlation_id: str | None = None,
    ) -> TokenRequestError:
        """Create error for timeout failures."""
        return cls(
            message=f"Token request timed out after {timeout_seconds}s",
            error_code="timeout",
            url=token_url,
            client_id=client_id,
            correlation_id=correlation_id,
            how_to_fix=[
                "IdP may be overloaded or experiencing issues",
                "Consider increasing timeout if IdP is known to be slow",
                "Check if there are network latency issues",
            ],
        )


@dataclass
class TokenExpiredError(OAuthError):
    """Token has expired."""
    error_code: str = "token_expired"


@dataclass
class TokenRefreshError(OAuthError):
    """Token refresh failed."""
    error_code: str = "token_refresh_failed"
    refresh_token_hint: str | None = None  # First 8 chars for debugging


@dataclass
class InvalidGrantError(OAuthError):
    """Invalid grant (e.g., expired auth code, revoked refresh token)."""
    error_code: str = "invalid_grant"


@dataclass
class CircuitOpenError(OAuthError):
    """Circuit breaker is open - IdP unavailable."""
    error_code: str = "circuit_open"
    retry_after_seconds: float | None = None
    failure_count: int | None = None


@dataclass
class RateLimitError(OAuthError):
    """Rate limited by IdP."""
    error_code: str = "rate_limited"
    retry_after_seconds: int | None = None


@dataclass
class DPoPNonceError(OAuthError):
    """DPoP nonce challenge received."""
    error_code: str = "dpop_nonce_required"
    nonce: str | None = None


@dataclass
class MTLSError(OAuthError):
    """mTLS authentication failed."""
    error_code: str = "mtls_failed"
    cert_path: str | None = None


@dataclass
class ConfigurationError(OAuthError):
    """OAuth client is misconfigured."""
    error_code: str = "configuration_error"
    
    @classmethod
    def missing_env_var(cls, var_name: str, prefix: str = "OAUTH_") -> ConfigurationError:
        """Create error for missing environment variable."""
        return cls(
            message=f"Required environment variable not set: {prefix}{var_name}",
            error_code="missing_env_var",
            how_to_fix=[
                f"Set the {prefix}{var_name} environment variable",
                f"Or pass {var_name.lower()} explicitly to the client",
                "Check your .env file if using dotenv",
            ],
            details={"variable": f"{prefix}{var_name}"},
        )
    
    @classmethod
    def invalid_url(cls, url: str, context: str) -> ConfigurationError:
        """Create error for invalid URL."""
        return cls(
            message=f"Invalid URL for {context}: '{url}'",
            error_code="invalid_url",
            url=url,
            how_to_fix=[
                "URL must start with http:// or https://",
                "Check for typos in the URL",
                "Ensure the URL is properly formatted",
            ],
        )


@dataclass  
class SecurityError(OAuthError):
    """Security validation failed."""
    error_code: str = "security_error"
    
    @classmethod
    def https_required(cls, url: str, context: str = "url") -> SecurityError:
        """Create error when HTTPS is required but HTTP was provided."""
        https_url = url.replace("http://", "https://", 1)
        return cls(
            message=f"OAuth {context} must use HTTPS (got '{url}')",
            error_code="https_required",
            url=url,
            how_to_fix=[
                f"Use HTTPS URL: '{https_url}'",
                "For internal services in Docker/K8s, enable internal HTTP:",
                "    client = OAuth.builder().allow_internal_http().build()",
                "Or set: OAUTH_ALLOW_INTERNAL_HTTP=true",
            ],
            docs_url="https://docs.empowernow.com/oauth/internal-services",
        )
    
    @classmethod
    def localhost_blocked(cls, url: str, context: str = "url") -> SecurityError:
        """Create error when localhost is blocked."""
        return cls(
            message=f"Localhost not allowed in {context}: '{url}'",
            error_code="localhost_blocked",
            url=url,
            how_to_fix=[
                "Set EMPOWERNOW_ALLOW_LOCALHOST=true for local development",
                "Or use a real hostname/IP instead of localhost",
            ],
        )


@dataclass
class DiscoveryError(OAuthError):
    """OIDC discovery failed."""
    error_code: str = "discovery_failed"
    discovery_url: str | None = None


@dataclass
class IntrospectionError(OAuthError):
    """Token introspection failed."""
    error_code: str = "introspection_failed"


@dataclass
class RevocationError(OAuthError):
    """Token revocation failed."""
    error_code: str = "revocation_failed"


# Backward compatibility aliases
OAuthTokenError = TokenRequestError
OAuthCircuitBreakerError = CircuitOpenError
OAuthDiscoveryError = DiscoveryError
OAuthConfigurationError = ConfigurationError
OAuthIntrospectionError = IntrospectionError
OAuthRevocationError = RevocationError
