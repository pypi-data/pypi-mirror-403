"""OAuth CLI testing tool.

A command-line tool for testing OAuth configurations without writing code.

Usage:
    # Test from environment variables
    $ python -m empowernow_common.oauth.cli test --from-env
    
    # Test with explicit configuration
    $ python -m empowernow_common.oauth.cli test \
        --client-id my-client \
        --client-secret my-secret \
        --issuer https://idp.example.com
    
    # With debug mode
    $ python -m empowernow_common.oauth.cli test --from-env --debug
"""

from __future__ import annotations

import asyncio
import os
import sys
import time

# Check for optional dependencies
try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def _print_simple(message: str, style: str = "") -> None:
    """Simple print fallback when rich is not available."""
    prefix_map = {
        "green": "✅ ",
        "red": "❌ ",
        "yellow": "⚠️ ",
        "bold": "",
    }
    prefix = prefix_map.get(style, "")
    print(f"{prefix}{message}")


def _create_console():
    """Create console (rich or fallback)."""
    if RICH_AVAILABLE:
        return Console()
    
    class SimpleConsole:
        def print(self, message: str, style: str = "", **kwargs):
            # Extract color from style string
            if "green" in str(style):
                _print_simple(str(message).replace("[green]", "").replace("[/green]", ""), "green")
            elif "red" in str(style):
                _print_simple(str(message).replace("[red]", "").replace("[/red]", ""), "red")
            elif "yellow" in str(style):
                _print_simple(str(message).replace("[yellow]", "").replace("[/yellow]", ""), "yellow")
            else:
                print(message)
    
    return SimpleConsole()


if CLICK_AVAILABLE:
    @click.group()
    def cli():
        """EmpowerNow OAuth CLI tools.
        
        Test OAuth configurations, validate credentials, and debug token requests.
        
        Examples:
            # Test from environment variables
            empowernow-oauth test --from-env
            
            # Test with explicit config
            empowernow-oauth test --client-id my-client --client-secret secret --issuer https://idp.example.com
        """
        pass

    @cli.command()
    @click.option("--client-id", help="OAuth client ID")
    @click.option("--client-secret", help="OAuth client secret", default="")
    @click.option("--issuer", help="IdP issuer URL (for OIDC discovery)")
    @click.option("--token-url", help="Direct token endpoint URL")
    @click.option("--scope", help="OAuth scope to request", default="")
    @click.option("--from-env", is_flag=True, help="Read configuration from environment variables")
    @click.option("--env-prefix", default="OAUTH_", help="Environment variable prefix (default: OAUTH_)")
    @click.option("--debug", is_flag=True, help="Enable debug output")
    @click.option("--timeout", default=30, help="Request timeout in seconds")
    @click.option("--allow-http", is_flag=True, help="Allow HTTP for internal services")
    def test(
        client_id: str | None,
        client_secret: str,
        issuer: str | None,
        token_url: str | None,
        scope: str,
        from_env: bool,
        env_prefix: str,
        debug: bool,
        timeout: int,
        allow_http: bool,
    ):
        """Test OAuth configuration and connectivity.
        
        Validates configuration, tests endpoint connectivity, and performs
        a token request to verify credentials.
        
        Examples:
        
            # Test from environment
            empowernow-oauth test --from-env
            
            # Test with explicit config
            empowernow-oauth test --client-id my-client --client-secret secret --issuer https://idp.example.com
            
            # Debug mode for troubleshooting
            empowernow-oauth test --from-env --debug
        """
        asyncio.run(_test_oauth(
            client_id=client_id,
            client_secret=client_secret,
            issuer=issuer,
            token_url=token_url,
            scope=scope,
            from_env=from_env,
            env_prefix=env_prefix,
            debug=debug,
            timeout=timeout,
            allow_http=allow_http,
        ))

    @cli.command()
    def env_template():
        """Print environment variable template.
        
        Outputs a template of environment variables that can be used
        with OAuth.from_env().
        """
        template = """# EmpowerNow OAuth Environment Variables
# Copy to .env file or export in shell

# Required
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret

# One of these is required:
OAUTH_ISSUER=https://idp.example.com
# OR
OAUTH_TOKEN_URL=https://idp.example.com/oauth/token

# Optional
OAUTH_SCOPE=openid profile email
OAUTH_DEBUG=false
OAUTH_ALLOW_INTERNAL_HTTP=false
OAUTH_HTTP_TIMEOUT=30
OAUTH_HTTP_MAX_CONNECTIONS=10
"""
        print(template)

    @cli.command()
    def version():
        """Print SDK version."""
        try:
            from empowernow_common import __version__
            print(f"empowernow-common {__version__}")
        except ImportError:
            print("empowernow-common (version unknown)")


async def _test_oauth(
    client_id: str | None,
    client_secret: str,
    issuer: str | None,
    token_url: str | None,
    scope: str,
    from_env: bool,
    env_prefix: str,
    debug: bool,
    timeout: int,
    allow_http: bool,
) -> None:
    """Internal async function to test OAuth configuration."""
    console = _create_console()
    
    console.print("\n[bold]EmpowerNow OAuth Configuration Test[/bold]\n")
    
    try:
        # Import OAuth client
        from empowernow_common.oauth import HardenedOAuth, SecureOAuthConfig
        from empowernow_common.oauth.config import OAuthSettings
        from empowernow_common.oauth.errors import OAuthError, ConfigurationError
        
        # Build client
        if from_env:
            console.print(f"📋 Reading configuration from environment (prefix: {env_prefix})")
            
            # Show which env vars are set
            env_vars = [
                f"{env_prefix}CLIENT_ID",
                f"{env_prefix}CLIENT_SECRET",
                f"{env_prefix}ISSUER",
                f"{env_prefix}TOKEN_URL",
                f"{env_prefix}SCOPE",
            ]
            
            for var in env_vars:
                value = os.getenv(var)
                if value:
                    # Mask secrets
                    if "SECRET" in var and value:
                        display = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "****"
                    else:
                        display = value
                    console.print(f"   {var} = {display}")
                else:
                    console.print(f"   {var} = (not set)")
            
            console.print("")
            
            try:
                client = HardenedOAuth.from_env(prefix=env_prefix)
            except Exception as e:
                console.print(f"❌ [red]Configuration Error: {e}[/red]")
                if hasattr(e, 'how_to_fix'):
                    console.print("\nHow to fix:")
                    for fix in e.how_to_fix:
                        console.print(f"  • {fix}")
                sys.exit(1)
        else:
            # Build from explicit parameters
            if not client_id:
                console.print("❌ [red]Error: --client-id is required (or use --from-env)[/red]")
                sys.exit(1)
            
            if not issuer and not token_url:
                console.print("❌ [red]Error: Either --issuer or --token-url is required[/red]")
                sys.exit(1)
            
            # Determine token URL
            if issuer and not token_url:
                # Use issuer to derive token URL (common pattern)
                token_url = f"{issuer.rstrip('/')}/oauth/token"
                console.print(f"📋 Using issuer-derived token URL: {token_url}")
            
            config = SecureOAuthConfig(
                client_id=client_id,
                client_secret=client_secret,
                token_url=token_url,
                authorization_url=issuer or "",
                scope=scope or None,
                allow_internal_http=allow_http,
            )
            client = HardenedOAuth(config)
        
        # Use async context manager to ensure proper client cleanup
        async with client:
            # Enable debug mode if requested
            if debug:
                client.debug(True)
            
            # Display configuration
            console.print("✅ [green]Configuration Valid[/green]")
            console.print(f"   Client ID: {client.config.client_id}")
            console.print(f"   Token URL: {client.config.token_url}")
            console.print(f"   Auth Method: {client.config.token_endpoint_auth_method}")
            if client.config.scope:
                console.print(f"   Scope: {client.config.scope}")
            console.print("")
            
            # Test token request
            console.print("🚀 Requesting token...")
            start_time = time.perf_counter()
            
            try:
                token = await client.get_token()
                elapsed = (time.perf_counter() - start_time) * 1000
                
                console.print(f"\n✅ [green]Token Request Successful[/green] ({elapsed:.0f}ms)")
                console.print(f"   Token Type: {token.token_type}")
                console.print(f"   Expires In: {token.expires_in}s")
                if token.scope:
                    console.print(f"   Scopes: {token.scope}")
                console.print(f"   Has Refresh Token: {bool(token.refresh_token)}")
                
                # Show token preview (first/last chars)
                if token.access_token:
                    preview = f"{token.access_token[:10]}...{token.access_token[-6:]}"
                    console.print(f"   Access Token: {preview} ({len(token.access_token)} chars)")
                
                console.print("\n✅ [green]All checks passed![/green]\n")
                
            except OAuthError as e:
                elapsed = (time.perf_counter() - start_time) * 1000
                console.print(f"\n❌ [red]Token Request Failed[/red] ({elapsed:.0f}ms)")
                console.print(f"   Error: {e.message}")
                if hasattr(e, 'error_code'):
                    console.print(f"   Error Code: {e.error_code}")
                if hasattr(e, 'status_code') and e.status_code:
                    console.print(f"   HTTP Status: {e.status_code}")
                
                if hasattr(e, 'how_to_fix') and e.how_to_fix:
                    console.print("\nHow to fix:")
                    for fix in e.how_to_fix:
                        console.print(f"  • {fix}")
                
                if hasattr(e, 'docs_url') and e.docs_url:
                    console.print(f"\nDocumentation: {e.docs_url}")
                
                sys.exit(1)
            
    except ImportError as e:
        console.print(f"❌ [red]Import Error: {e}[/red]")
        console.print("   Make sure empowernow-common is installed correctly.")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ [red]Unexpected Error: {e}[/red]")
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    if not CLICK_AVAILABLE:
        print("Error: The 'click' package is required for the CLI tool.")
        print("Install it with: pip install click")
        print("")
        print("Or install empowernow-common with CLI extras:")
        print("  pip install empowernow-common[cli]")
        sys.exit(1)
    
    cli()


if __name__ == "__main__":
    main()
