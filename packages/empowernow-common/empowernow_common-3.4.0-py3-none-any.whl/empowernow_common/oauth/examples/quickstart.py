#!/usr/bin/env python3
"""OAuth Quick Start Examples.

This module demonstrates the simplest ways to use the EmpowerNow OAuth client.
Each example is self-contained and ready to run.

For local development, set:
    export EMPOWERNOW_ALLOW_LOCALHOST=true
"""

import asyncio
from empowernow_common.oauth import HardenedOAuth, OAuthTokenError


async def example_simple_token():
    """Simplest possible OAuth client - 3 lines to get a token.
    
    Use this for basic client_credentials flow.
    """
    # Create client with just the essentials
    oauth = HardenedOAuth.simple(
        token_url="https://auth.example.com/oauth/token",
        client_id="my-app",
        client_secret="my-secret",
    )
    
    # Get a token (automatically cached!)
    async with oauth:
        token = await oauth.get_token()
        print(f"Access token: {token.access_token[:20]}...")
        print(f"Expires in: {token.expires_in} seconds")
        
        # Second call uses cache - no network request!
        token2 = await oauth.get_token()
        assert token.access_token == token2.access_token


async def example_oidc_discovery():
    """Use OIDC discovery to auto-configure endpoints.
    
    This is the recommended approach - the client discovers
    all endpoints from the IdP's well-known configuration.
    """
    # Create client using OIDC discovery
    oauth = await HardenedOAuth.from_issuer(
        issuer_url="https://auth.example.com",
        client_id="my-app",
        client_secret="my-secret",
    )
    
    async with oauth:
        token = await oauth.get_token()
        print(f"Token acquired via discovery: {token.access_token[:20]}...")


async def example_with_scope():
    """Request specific scopes."""
    oauth = HardenedOAuth.simple(
        token_url="https://auth.example.com/oauth/token",
        client_id="my-app",
        client_secret="my-secret",
        scope="read write admin",
    )
    
    async with oauth:
        token = await oauth.get_token()
        print(f"Granted scope: {token.scope}")


async def example_error_handling():
    """Proper error handling with rich error context."""
    oauth = HardenedOAuth.simple(
        token_url="https://auth.example.com/oauth/token",
        client_id="wrong-client",
        client_secret="wrong-secret",
    )
    
    try:
        async with oauth:
            await oauth.get_token()
    except OAuthTokenError as e:
        print(f"Token error: {e.error_code}")
        print(f"Status: {e.status_code}")
        print(f"URL: {e.url}")
        print("\nTroubleshooting tips:")
        for tip in e.troubleshooting:
            print(f"  - {tip}")


async def example_force_refresh():
    """Force token refresh even if cached token is valid."""
    oauth = HardenedOAuth.simple(
        token_url="https://auth.example.com/oauth/token",
        client_id="my-app",
        client_secret="my-secret",
    )
    
    async with oauth:
        # Get initial token
        token1 = await oauth.get_token()
        
        # Force refresh - gets a new token even if cached
        token2 = await oauth.get_token(force_refresh=True)
        
        # Tokens will be different
        print(f"Token refreshed: {token1.access_token != token2.access_token}")


async def example_private_key_jwt():
    """Use private_key_jwt authentication (for high-security clients)."""
    from empowernow_common.oauth import SecureOAuthConfig
    
    config = SecureOAuthConfig(
        client_id="my-confidential-app",
        client_secret="",  # Not needed for private_key_jwt
        token_url="https://auth.example.com/oauth/token",
        authorization_url="https://auth.example.com/authorize",
        token_endpoint_auth_method="private_key_jwt",
    )
    
    oauth = HardenedOAuth(config)
    
    # Configure the signing key
    with open("/path/to/private-key.pem", "rb") as f:
        private_key = f.read()
    
    oauth.configure_private_key_jwt(
        signing_key=private_key,
        signing_alg="RS256",
        kid="my-key-id",
    )
    
    async with oauth:
        token = await oauth.get_token()
        print(f"Token via private_key_jwt: {token.access_token[:20]}...")


async def example_with_dpop():
    """Use DPoP for sender-constrained tokens."""
    oauth = HardenedOAuth.simple(
        token_url="https://auth.example.com/oauth/token",
        client_id="my-app",
        client_secret="my-secret",
    )
    
    # Enable DPoP - tokens will be bound to this client
    thumbprint = oauth.enable_dpop()
    print(f"DPoP enabled with thumbprint: {thumbprint}")
    
    async with oauth:
        token = await oauth.get_dpop_bound_token()
        print(f"DPoP-bound token: {token.access_token[:20]}...")
        print(f"Token binding: {token.token_binding}")


# Run examples
if __name__ == "__main__":
    print("=== Simple Token Example ===")
    asyncio.run(example_simple_token())
    
    print("\n=== Error Handling Example ===")
    asyncio.run(example_error_handling())
