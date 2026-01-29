"""Synchronous OAuth client wrapper.

This module provides a synchronous wrapper around the async HardenedOAuth client
for use cases where async/await is inconvenient:
- CLI scripts and tools
- Jupyter notebooks
- Legacy synchronous codebases
- Quick prototyping

For production services, prefer the async HardenedOAuth client for better
performance and resource utilization.

Usage:
    from empowernow_common.oauth import SyncOAuth
    
    # From environment variables (zero config!)
    client = SyncOAuth.from_env()
    token = client.get_token()
    
    # Or with explicit configuration
    client = SyncOAuth.client_credentials(
        "my-client", "my-secret", "https://idp.example.com"
    )
    token = client.get_token()
    print(f"Token expires in {token.expires_in_seconds}s")
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any

from .client import HardenedOAuth, SecureOAuthConfig, HardenedToken

__all__ = ["SyncOAuth"]


class SyncOAuth:
    """Synchronous wrapper around HardenedOAuth.
    
    Use this for scripts, CLI tools, or Jupyter notebooks where
    async/await is inconvenient. For production services, prefer
    the async HardenedOAuth client.
    
    Example:
        # From environment (recommended)
        client = SyncOAuth.from_env()
        token = client.get_token()
        
        # Explicit configuration
        client = SyncOAuth.client_credentials(
            "my-client", "my-secret", "https://idp.example.com"
        )
        token = client.get_token()
        print(f"Token: {token.access_token[:20]}...")
    """
    
    def __init__(self, async_client: HardenedOAuth):
        """Initialize sync wrapper with async client.
        
        Prefer using factory methods like from_env() or client_credentials().
        """
        self._async_client = async_client
    
    # ------------------------------------------------------------------
    # Factory Methods (mirror HardenedOAuth)
    # ------------------------------------------------------------------
    
    @classmethod
    def from_env(cls, prefix: str = "OAUTH_", **kwargs) -> SyncOAuth:
        """Create sync OAuth client from environment variables.
        
        This is the recommended way to create a client - it automatically
        reads configuration from environment variables with the given prefix.
        
        Args:
            prefix: Environment variable prefix (default: "OAUTH_")
            **kwargs: Additional arguments passed to HardenedOAuth
        
        Returns:
            Configured SyncOAuth client
        
        Example:
            # Set environment variables:
            # OAUTH_CLIENT_ID=my-client
            # OAUTH_CLIENT_SECRET=my-secret
            # OAUTH_ISSUER=https://idp.example.com
            
            client = SyncOAuth.from_env()
            token = client.get_token()
        """
        async_client = HardenedOAuth.from_env(prefix=prefix, **kwargs)
        return cls(async_client)
    
    @classmethod
    def client_credentials(
        cls,
        client_id: str,
        client_secret: str,
        issuer_or_token_url: str,
        *,
        scope: str = "",
        **kwargs,
    ) -> SyncOAuth:
        """Create sync OAuth client for client_credentials flow.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            issuer_or_token_url: OAuth issuer URL or direct token URL
            scope: Default scope for token requests
            **kwargs: Additional arguments passed to HardenedOAuth
        
        Returns:
            Configured SyncOAuth client
        
        Example:
            client = SyncOAuth.client_credentials(
                "my-client",
                "my-secret",
                "https://idp.example.com"
            )
            token = client.get_token()
        """
        async_client = HardenedOAuth.client_credentials(
            client_id, client_secret, issuer_or_token_url,
            scope=scope, **kwargs
        )
        return cls(async_client)
    
    @classmethod
    def simple(
        cls,
        token_url: str,
        client_id: str,
        client_secret: str = "",
        *,
        scope: str = "",
    ) -> SyncOAuth:
        """Create a simple sync OAuth client.
        
        Args:
            token_url: OAuth token endpoint URL
            client_id: OAuth client ID
            client_secret: OAuth client secret
            scope: Default scope
        
        Returns:
            Configured SyncOAuth client
        """
        async_client = HardenedOAuth.simple(
            token_url, client_id, client_secret, scope=scope
        )
        return cls(async_client)
    
    @classmethod
    def from_issuer(
        cls,
        issuer_url: str,
        client_id: str,
        client_secret: str = "",
        **kwargs,
    ) -> SyncOAuth:
        """Create sync OAuth client using OIDC discovery.
        
        Args:
            issuer_url: OAuth/OIDC issuer URL
            client_id: OAuth client ID
            client_secret: OAuth client secret
            **kwargs: Additional arguments
        
        Returns:
            Configured SyncOAuth client
        """
        async_client = cls._run(
            HardenedOAuth.from_issuer(issuer_url, client_id, client_secret, **kwargs)
        )
        return cls(async_client)
    
    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    
    @property
    def async_client(self) -> HardenedOAuth:
        """Access the underlying async client for advanced operations."""
        return self._async_client
    
    @property
    def config(self) -> SecureOAuthConfig:
        """Get the OAuth configuration."""
        return self._async_client.config
    
    # ------------------------------------------------------------------
    # Token Operations
    # ------------------------------------------------------------------
    
    def get_token(
        self,
        *,
        force_refresh: bool = False,
        scope: str | None = None,
        resource: str | list[str] | None = None,
        correlation_id: str | None = None,
        **params,
    ) -> HardenedToken:
        """Get OAuth access token (blocking).
        
        Tokens are automatically cached and reused until they expire.
        
        Args:
            force_refresh: Force a new token even if cached is valid
            scope: OAuth scope(s) to request
            resource: RFC 8707 resource indicator
            correlation_id: Correlation ID for tracing
            **params: Additional token request parameters
        
        Returns:
            OAuth access token
        
        Example:
            token = client.get_token()
            token = client.get_token(scope="read:users")
            token = client.get_token(force_refresh=True)
        """
        return self._run(
            self._async_client.get_token(
                force_refresh=force_refresh,
                scope=scope,
                resource=resource,
                correlation_id=correlation_id,
                **params,
            )
        )
    
    def refresh_access_token(
        self,
        refresh_token: str,
        *,
        scope: str | None = None,
        resource: str | list[str] | None = None,
        correlation_id: str | None = None,
    ) -> HardenedToken:
        """Refresh an access token using a refresh token (blocking).
        
        Args:
            refresh_token: The refresh token from a previous token response
            scope: Optional scope (may be subset of original)
            resource: RFC 8707 resource indicator
            correlation_id: Correlation ID for tracing
        
        Returns:
            New access token
        """
        return self._run(
            self._async_client.refresh_access_token(
                refresh_token,
                scope=scope,
                resource=resource,
                correlation_id=correlation_id,
            )
        )
    
    def introspect_token(self, token: str) -> dict[str, Any]:
        """Introspect a token (RFC 7662).
        
        Args:
            token: The token to introspect
        
        Returns:
            Introspection response dict
        """
        return self._run(self._async_client.introspect_token(token))
    
    def revoke_token(
        self,
        token: str,
        token_type_hint: str = "access_token",
    ) -> None:
        """Revoke a token (RFC 7009).
        
        Args:
            token: The token to revoke
            token_type_hint: Token type (access_token or refresh_token)
        """
        return self._run(
            self._async_client.revoke_token(token, token_type_hint)
        )
    
    def token_exchange(
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
        
        This enables delegation and impersonation scenarios where a service
        needs to act on behalf of a user or another service.
        
        Args:
            subject_token: The token to be exchanged (required)
            subject_token_type: Type URI of the subject token (default: access_token)
            actor_token: Token representing the acting party (optional)
            actor_token_type: Type URI of the actor token (required if actor_token set)
            requested_token_type: Desired type of the new token (optional)
            resource: RFC 8707 resource indicator(s) (optional)
            audience: Target audience for the token (optional)
            scope: Requested scope (optional, may be subset of original)
            correlation_id: Correlation ID for tracing
        
        Returns:
            HardenedToken: The exchanged token with issued_token_type populated
        
        Example:
            # Basic token exchange (delegation)
            new_token = client.token_exchange(
                subject_token=user_token.access_token,
                audience="https://backend-api.example.com",
            )
            
            # Impersonation with actor token
            new_token = client.token_exchange(
                subject_token=user_token.access_token,
                actor_token=service_token.access_token,
                actor_token_type="urn:ietf:params:oauth:token-type:access_token",
            )
        """
        return self._run(
            self._async_client.token_exchange(
                subject_token,
                subject_token_type,
                actor_token=actor_token,
                actor_token_type=actor_token_type,
                requested_token_type=requested_token_type,
                resource=resource,
                audience=audience,
                scope=scope,
                correlation_id=correlation_id,
            )
        )
    
    def clear_token_cache(self) -> None:
        """Clear the cached token."""
        self._async_client.clear_token_cache()
    
    # ------------------------------------------------------------------
    # Configuration Methods
    # ------------------------------------------------------------------
    
    def debug(self, enabled: bool = True) -> SyncOAuth:
        """Enable debug mode.
        
        Args:
            enabled: Enable or disable debug mode
        
        Returns:
            Self for method chaining
        """
        self._async_client.debug(enabled)
        return self
    
    def enable_dpop(self, algorithm: str = "ES256") -> str:
        """Enable DPoP (Demonstrating Proof of Possession).
        
        Args:
            algorithm: DPoP signing algorithm
        
        Returns:
            JWK thumbprint of the DPoP key
        """
        return self._async_client.enable_dpop(algorithm)
    
    def enable_mtls(
        self,
        cert_path: str,
        key_path: str,
        *,
        hot_reload: bool = False,
    ) -> None:
        """Enable mTLS client authentication.
        
        Args:
            cert_path: Path to PEM-encoded client certificate
            key_path: Path to PEM-encoded private key
            hot_reload: Enable automatic certificate reload
        """
        self._async_client.enable_mtls(cert_path, key_path, hot_reload=hot_reload)
    
    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    
    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._run(self._async_client.aclose())
    
    def __enter__(self) -> SyncOAuth:
        """Enter sync context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit sync context manager and close client."""
        self.close()
    
    def __repr__(self) -> str:
        """Informative string representation."""
        return (
            f"SyncOAuth(\n"
            f"    client_id='{self.config.client_id}',\n"
            f"    token_url='{self.config.token_url}',\n"
            f")"
        )
    
    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    
    @staticmethod
    def _run(coro):
        """Run coroutine synchronously.
        
        Handles both running inside and outside an existing event loop.
        """
        try:
            loop = asyncio.get_running_loop()
            # Already in async context - use thread pool
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        except RuntimeError:
            # No running loop - safe to use asyncio.run
            return asyncio.run(coro)


# Backward compatibility alias
SyncOAuthClient = SyncOAuth
