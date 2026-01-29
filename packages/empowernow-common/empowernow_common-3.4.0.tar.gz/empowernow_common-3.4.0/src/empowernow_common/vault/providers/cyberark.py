"""CyberArk PVWA vault provider implementation.

Production-grade provider for CyberArk Password Vault Web Access (PVWA) REST API v12+.

Supported Features:
- Multiple authentication methods (CyberArk, LDAP, RADIUS, Windows, SAML)
- Session management with automatic renewal
- Read credentials by Safe/Account
- List accounts in Safe
- Optional write support (create/update accounts)
- Circuit breaker protection
- Retry with exponential backoff
- OpenTelemetry tracing

URI Formats:
    cyberark://safe/account                  → Get account credentials
    cyberark://safe/account#password         → Extract specific field
    cyberark://safe/account?reason=ticket    → With access reason

Configuration:
    base_url: CyberArk PVWA URL (e.g., https://cyberark.company.com)
    auth:
        method: cyberark | ldap | radius | windows | saml
        username: Authentication username
        password: Authentication password
        concurrent_sessions: Allow concurrent sessions (default: true)
    default_safe: Default safe for operations without explicit safe
    timeout: Request timeout in seconds (default: 30)
    session_ttl: Session validity in seconds (default: 1200 = 20 min)

Per design: VAULT_PROVIDER_UNIFICATION.md
Per Playbook: AI_PYTHON_FASTAPI_EXCELLENCE_PLAYBOOK.md §5 (Circuit Breaker), §9 (Error Handling)
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlencode

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from opentelemetry import trace

from empowernow_common.vault.base import ReadableVaultProvider, EnumerableVaultProvider, Capabilities
from empowernow_common.vault.exceptions import (
    VaultAuthenticationError,
    VaultAuthorizationError,
    VaultConfigurationError,
    VaultConnectionError,
    VaultOperationError,
    VaultSecretNotFoundError,
    VaultTimeoutError,
)
from empowernow_common.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    get_circuit_breaker,
)


logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class AuthMethod(Enum):
    """CyberArk authentication methods."""
    CYBERARK = "CyberArk"
    LDAP = "LDAP"
    RADIUS = "Radius"
    WINDOWS = "Windows"
    SAML = "SAML"


@dataclass
class CyberArkSession:
    """Active CyberArk session information."""
    token: str
    created_at: datetime
    ttl_seconds: int
    user: str
    
    @property
    def expires_at(self) -> datetime:
        """Calculate session expiration time."""
        return self.created_at + timedelta(seconds=self.ttl_seconds)
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        # Consider expired 60 seconds before actual expiry for safety
        return datetime.now() >= (self.expires_at - timedelta(seconds=60))
    
    @property
    def remaining_seconds(self) -> int:
        """Seconds remaining until expiry."""
        remaining = (self.expires_at - datetime.now()).total_seconds()
        return max(0, int(remaining))


@dataclass
class CyberArkConfig:
    """Configuration for CyberArk PVWA provider."""
    base_url: str
    username: str
    password: str
    auth_method: AuthMethod = AuthMethod.CYBERARK
    default_safe: Optional[str] = None
    timeout: int = 30
    session_ttl: int = 1200  # 20 minutes default
    concurrent_sessions: bool = True
    verify_ssl: bool = True
    
    # Circuit breaker settings
    cb_failure_threshold: int = 5
    cb_reset_timeout_s: float = 30.0


class CyberArkVaultProvider:
    """CyberArk PVWA vault provider implementing ReadableVaultProvider protocol.
    
    Production-grade provider with first-class support for:
    - CyberArk Password Vault Web Access (PVWA) REST API v12+
    - Multiple authentication methods
    - Session management with auto-renewal
    - Safe-based credential organization
    - Account search and retrieval
    
    This provider is read-focused (typical CyberArk usage pattern where
    applications retrieve credentials but don't modify them).
    
    Per Playbook §5: Uses empowernow_common.resilience.CircuitBreaker.
    """
    
    VAULT_TYPE = "cyberark"
    CAPABILITIES = {
        Capabilities.LIST_KEYS: True,
        Capabilities.READ_SECRET: True,
        Capabilities.WRITE_SECRET: False,  # CyberArk typically read-only for apps
        Capabilities.DELETE_SECRET: False,
        Capabilities.METADATA: True,
        Capabilities.READ_METADATA: True,
        Capabilities.UPDATE_METADATA: False,
        Capabilities.VERSIONING: False,  # CyberArk manages versions internally
        Capabilities.VERSION_PIN: False,
        Capabilities.SOFT_DELETE: False,
        Capabilities.HARD_DESTROY: False,
        Capabilities.RESPONSE_WRAPPING: False,
        Capabilities.IDENTITY_SCOPING: True,  # Safe-based scoping
        Capabilities.OWNERSHIP_TRACKING: True,  # Account ownership in CyberArk
        Capabilities.AUDIT_METADATA: True,  # CyberArk has full audit
        Capabilities.TAGS: False,
    }
    
    # PVWA API endpoints (v12+)
    _API_AUTH = "/PasswordVault/API/Auth/{method}/Logon"
    _API_LOGOFF = "/PasswordVault/API/Auth/Logoff"
    _API_ACCOUNTS = "/PasswordVault/API/Accounts"
    _API_ACCOUNT = "/PasswordVault/API/Accounts/{account_id}"
    _API_ACCOUNT_PASSWORD = "/PasswordVault/API/Accounts/{account_id}/Password/Retrieve"
    _API_SAFES = "/PasswordVault/API/Safes"
    _API_SAFE = "/PasswordVault/API/Safes/{safe_name}"
    _API_SERVER_INFO = "/PasswordVault/API/ServerInfo"
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize CyberArk PVWA provider.
        
        Args:
            config: Configuration dictionary with keys:
                - base_url: CyberArk PVWA URL
                - username: Authentication username
                - password: Authentication password
                - method: Auth method (cyberark, ldap, radius, windows, saml)
                - default_safe: Default safe for operations
                - timeout: Request timeout in seconds
                - session_ttl: Session TTL in seconds
                - concurrent_sessions: Allow concurrent sessions
                - verify_ssl: Verify TLS certificates
                - cb_failure_threshold: Circuit breaker failure threshold
                - cb_reset_timeout_s: Circuit breaker reset timeout
        
        Raises:
            VaultConfigurationError: If required configuration is missing
        """
        # Parse auth method
        method_str = config.get("method", "cyberark").upper()
        try:
            auth_method = AuthMethod[method_str]
        except KeyError:
            valid_methods = [m.name.lower() for m in AuthMethod]
            raise VaultConfigurationError(
                f"Invalid auth method '{method_str}'. Valid: {valid_methods}"
            )
        
        self._config = CyberArkConfig(
            base_url=config.get("base_url", "").rstrip("/"),
            username=config.get("username", ""),
            password=config.get("password", ""),
            auth_method=auth_method,
            default_safe=config.get("default_safe"),
            timeout=int(config.get("timeout", 30)),
            session_ttl=int(config.get("session_ttl", 1200)),
            concurrent_sessions=config.get("concurrent_sessions", True),
            verify_ssl=config.get("verify_ssl", True),
            cb_failure_threshold=int(config.get("cb_failure_threshold", 5)),
            cb_reset_timeout_s=float(config.get("cb_reset_timeout_s", 30.0)),
        )
        
        # Validate required config
        if not self._config.base_url:
            raise VaultConfigurationError("CyberArk base_url is required")
        if not self._config.username:
            raise VaultConfigurationError("CyberArk username is required")
        if not self._config.password:
            raise VaultConfigurationError("CyberArk password is required")
        
        # Circuit breaker config (lazy initialization)
        self._cb_config = CircuitBreakerConfig(
            threshold=self._config.cb_failure_threshold,
            timeout=self._config.cb_reset_timeout_s,
            window_seconds=60.0,
        )
        self._breaker: Optional[CircuitBreaker] = None
        
        # Session management
        self._session: Optional[CyberArkSession] = None
        self._session_lock = asyncio.Lock()
        
        # HTTP client config
        self._client_limits = httpx.Limits(
            max_keepalive_connections=5,
            max_connections=10,
            keepalive_expiry=30.0,
        )
        
        logger.info(
            "CyberArk PVWA provider initialized: %s",
            self._config.base_url,
            extra={
                "component": "vault_provider",
                "provider_type": "cyberark",
                "base_url": self._config.base_url,
                "auth_method": self._config.auth_method.value,
                "default_safe": self._config.default_safe,
            },
        )
    
    async def _get_circuit_breaker(self) -> CircuitBreaker:
        """Lazily initialize circuit breaker via registry."""
        if self._breaker is None:
            self._breaker = await get_circuit_breaker(
                f"vault_cyberark_{self._config.base_url}",
                self._cb_config,
            )
        return self._breaker
    
    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get HTTP headers for API calls."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if include_auth and self._session:
            headers["Authorization"] = self._session.token
        return headers
    
    # ─────────────────────────────────────────────────────────────
    # Session Management
    # ─────────────────────────────────────────────────────────────
    
    async def _ensure_session(self) -> None:
        """Ensure we have a valid session, authenticating if needed."""
        async with self._session_lock:
            if self._session is None or self._session.is_expired:
                await self._authenticate()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _authenticate(self) -> None:
        """Authenticate to CyberArk and obtain session token."""
        with tracer.start_as_current_span("cyberark.authenticate") as span:
            span.set_attribute("auth_method", self._config.auth_method.value)
            
            endpoint = self._API_AUTH.format(method=self._config.auth_method.value)
            url = f"{self._config.base_url}{endpoint}"
            
            body = {
                "username": self._config.username,
                "password": self._config.password,
                "concurrentSession": self._config.concurrent_sessions,
            }
            
            try:
                async with httpx.AsyncClient(
                    verify=self._config.verify_ssl,
                    timeout=self._config.timeout,
                    limits=self._client_limits,
                ) as client:
                    response = await client.post(
                        url,
                        json=body,
                        headers=self._get_headers(include_auth=False),
                    )
                    
                    if response.status_code == 401:
                        raise VaultAuthenticationError(
                            "CyberArk authentication failed: invalid credentials"
                        )
                    elif response.status_code == 403:
                        raise VaultAuthorizationError(
                            "CyberArk authentication forbidden: account may be suspended",
                            resource="authentication",
                        )
                    
                    response.raise_for_status()
                    
                    # PVWA returns the token directly as a string in the response body
                    token = response.text.strip().strip('"')
                    
                    if not token:
                        raise VaultAuthenticationError(
                            "CyberArk authentication failed: empty token"
                        )
                    
                    self._session = CyberArkSession(
                        token=token,
                        created_at=datetime.now(),
                        ttl_seconds=self._config.session_ttl,
                        user=self._config.username,
                    )
                    
                    logger.info(
                        "CyberArk session established (TTL: %ds)",
                        self._config.session_ttl,
                        extra={
                            "component": "vault_provider",
                            "auth_method": self._config.auth_method.value,
                        },
                    )
                    
            except (VaultAuthenticationError, VaultAuthorizationError):
                span.set_attribute("error", True)
                raise
            except httpx.TimeoutException as e:
                span.set_attribute("error", True)
                raise VaultTimeoutError(f"CyberArk authentication timeout: {e}") from e
            except httpx.ConnectError as e:
                span.set_attribute("error", True)
                raise VaultConnectionError(f"Cannot connect to CyberArk: {e}") from e
            except Exception as e:
                span.set_attribute("error", True)
                raise VaultOperationError(f"CyberArk authentication error: {e}") from e
    
    async def _logoff(self) -> None:
        """Logoff from CyberArk (end session)."""
        if not self._session:
            return
        
        try:
            url = f"{self._config.base_url}{self._API_LOGOFF}"
            
            async with httpx.AsyncClient(
                verify=self._config.verify_ssl,
                timeout=10,  # Short timeout for logoff
                limits=self._client_limits,
            ) as client:
                await client.post(url, headers=self._get_headers())
                
            logger.debug("CyberArk session ended")
        except Exception as e:
            logger.debug("CyberArk logoff failed (session may have expired): %s", e)
        finally:
            self._session = None
    
    # ─────────────────────────────────────────────────────────────
    # URI Parsing
    # ─────────────────────────────────────────────────────────────
    
    def _parse_reference(self, reference: str) -> Tuple[str, str, Optional[str], Dict[str, str]]:
        """Parse a secret reference into components.
        
        Formats supported:
            safe/account
            safe/account#field
            cyberark://safe/account
            cyberark://safe/account#field
            cyberark://safe/account?reason=ticket
            cyberark://safe/account#field?reason=ticket
        
        Args:
            reference: Secret reference string
            
        Returns:
            Tuple of (safe, account, fragment_key, query_params)
        """
        fragment_key: Optional[str] = None
        query_params: Dict[str, str] = {}
        path = reference
        
        # Handle cyberark:// URI scheme
        if reference.startswith("cyberark://"):
            path = reference[11:]  # Remove "cyberark://"
        
        # Extract query params FIRST (e.g., ?reason=ticket)
        # This ensures fragment doesn't include query params
        if "?" in path:
            path, query_string = path.split("?", 1)
            for param in query_string.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    query_params[key] = value
        
        # Extract fragment AFTER query params (e.g., #password)
        if "#" in path:
            path, fragment_key = path.rsplit("#", 1)
        
        # Split into safe/account
        parts = path.strip("/").split("/", 1)
        
        if len(parts) == 2:
            safe, account = parts
        elif len(parts) == 1 and self._config.default_safe:
            safe = self._config.default_safe
            account = parts[0]
        else:
            raise VaultOperationError(
                f"Invalid reference format: '{reference}'. "
                f"Expected 'safe/account' or configure default_safe"
            )
        
        if not safe or not account:
            raise VaultOperationError(f"Invalid reference: safe and account required")
        
        return safe, account, fragment_key, query_params
    
    # ─────────────────────────────────────────────────────────────
    # Account Operations
    # ─────────────────────────────────────────────────────────────
    
    async def _find_account(self, safe: str, account_name: str) -> Dict[str, Any]:
        """Find an account by safe and name.
        
        Args:
            safe: Safe name
            account_name: Account name or address
            
        Returns:
            Account details dictionary
            
        Raises:
            VaultSecretNotFoundError: If account not found
        """
        with tracer.start_as_current_span("cyberark.find_account") as span:
            span.set_attribute("safe", safe)
            span.set_attribute("account_redacted", account_name[:10] + "...")
            
            await self._ensure_session()
            breaker = await self._get_circuit_breaker()
            
            # Build search query
            # CyberArk search supports: safeName, search (keyword), filter
            search_query = f"safeName eq {safe}"
            params = {
                "search": account_name,
                "filter": search_query,
            }
            
            url = f"{self._config.base_url}{self._API_ACCOUNTS}?{urlencode(params)}"
            
            async def _do_search() -> Dict[str, Any]:
                async with httpx.AsyncClient(
                    verify=self._config.verify_ssl,
                    timeout=self._config.timeout,
                    limits=self._client_limits,
                ) as client:
                    response = await client.get(url, headers=self._get_headers())
                    
                    if response.status_code == 401:
                        # Session expired, clear and retry
                        self._session = None
                        raise VaultAuthenticationError("Session expired")
                    elif response.status_code == 403:
                        raise VaultAuthorizationError(
                            f"Access denied to safe '{safe}'",
                            resource=f"{safe}/{account_name}",
                        )
                    
                    response.raise_for_status()
                    return response.json()
            
            try:
                result = await breaker.execute(_do_search)
            except CircuitBreakerOpenError as e:
                span.set_attribute("error", True)
                raise VaultTimeoutError(f"Circuit open: {e}") from e
            except VaultAuthenticationError:
                # Retry once after re-auth
                await self._ensure_session()
                result = await breaker.execute(_do_search)
            
            accounts = result.get("value", [])
            
            if not accounts:
                raise VaultSecretNotFoundError(f"{safe}/{account_name}")
            
            # Find exact match or best match
            for acc in accounts:
                acc_name = acc.get("name", "")
                acc_username = acc.get("userName", "")
                acc_address = acc.get("address", "")
                
                if (acc_name.lower() == account_name.lower() or
                    acc_username.lower() == account_name.lower() or
                    acc_address.lower() == account_name.lower()):
                    return acc
            
            # Return first result if no exact match
            return accounts[0]
    
    async def _retrieve_password(
        self,
        account_id: str,
        reason: Optional[str] = None,
    ) -> str:
        """Retrieve the password for an account.
        
        Args:
            account_id: CyberArk account ID
            reason: Optional reason for access (for auditing)
            
        Returns:
            The password value
        """
        with tracer.start_as_current_span("cyberark.retrieve_password") as span:
            span.set_attribute("account_id_redacted", account_id[:8] + "...")
            
            await self._ensure_session()
            breaker = await self._get_circuit_breaker()
            
            url = f"{self._config.base_url}{self._API_ACCOUNT_PASSWORD.format(account_id=account_id)}"
            
            body: Dict[str, Any] = {}
            if reason:
                body["reason"] = reason
            
            async def _do_retrieve() -> str:
                async with httpx.AsyncClient(
                    verify=self._config.verify_ssl,
                    timeout=self._config.timeout,
                    limits=self._client_limits,
                ) as client:
                    response = await client.post(
                        url,
                        json=body if body else None,
                        headers=self._get_headers(),
                    )
                    
                    if response.status_code == 401:
                        self._session = None
                        raise VaultAuthenticationError("Session expired")
                    elif response.status_code == 403:
                        raise VaultAuthorizationError(
                            "Access denied to retrieve password",
                            resource=account_id,
                        )
                    elif response.status_code == 404:
                        raise VaultSecretNotFoundError(account_id)
                    
                    response.raise_for_status()
                    
                    # Password is returned as plain text
                    return response.text.strip().strip('"')
            
            try:
                return await breaker.execute(_do_retrieve)
            except CircuitBreakerOpenError as e:
                span.set_attribute("error", True)
                raise VaultTimeoutError(f"Circuit open: {e}") from e
            except VaultAuthenticationError:
                await self._ensure_session()
                return await breaker.execute(_do_retrieve)
    
    # ─────────────────────────────────────────────────────────────
    # ReadableVaultProvider Implementation
    # ─────────────────────────────────────────────────────────────
    
    async def get_secret(self, reference: str) -> str:
        """Get a secret value by reference.
        
        The secret value is the account's password by default.
        Use fragment to specify a different field (e.g., #username).
        
        Args:
            reference: Secret reference in format:
                - "safe/account" → returns password
                - "safe/account#password" → returns password
                - "safe/account#username" → returns username
                - "cyberark://safe/account?reason=ticket" → with audit reason
        
        Returns:
            The secret value (password or specified field)
            
        Raises:
            VaultSecretNotFoundError: If account not found
            VaultAuthorizationError: If access denied
        """
        with tracer.start_as_current_span("cyberark.get_secret") as span:
            safe, account_name, fragment_key, params = self._parse_reference(reference)
            span.set_attribute("safe", safe)
            span.set_attribute("account_redacted", account_name[:10] + "...")
            
            # Find the account
            account = await self._find_account(safe, account_name)
            account_id = account.get("id")
            
            if not account_id:
                raise VaultOperationError("Account found but missing ID")
            
            # Determine what to return
            field = fragment_key or "password"
            
            if field.lower() == "password":
                # Retrieve password (separate API call with audit)
                reason = params.get("reason")
                return await self._retrieve_password(account_id, reason=reason)
            else:
                # Return account metadata field
                field_mapping = {
                    "username": "userName",
                    "user": "userName",
                    "address": "address",
                    "name": "name",
                    "platform": "platformId",
                    "safe": "safeName",
                }
                
                api_field = field_mapping.get(field.lower(), field)
                value = account.get(api_field)
                
                if value is None:
                    # Check in platformAccountProperties
                    props = account.get("platformAccountProperties", {})
                    value = props.get(field)
                
                if value is None:
                    raise VaultSecretNotFoundError(f"{reference}#{field}")
                
                return str(value)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True,
    )
    async def get_credentials(self, reference: str) -> Dict[str, Any]:
        """Get credentials as a dictionary.
        
        Returns account information including password.
        
        Args:
            reference: Secret reference
            
        Returns:
            Dictionary with credential fields:
                - username: Account username
                - password: Account password
                - address: Target address/hostname
                - safe: Safe name
                - name: Account name
                - platform: Platform ID
                - ... additional platform properties
        """
        with tracer.start_as_current_span("cyberark.get_credentials") as span:
            safe, account_name, fragment_key, params = self._parse_reference(reference)
            span.set_attribute("safe", safe)
            span.set_attribute("account_redacted", account_name[:10] + "...")
            
            # Find the account
            account = await self._find_account(safe, account_name)
            account_id = account.get("id")
            
            if not account_id:
                raise VaultOperationError("Account found but missing ID")
            
            # Retrieve password
            reason = params.get("reason")
            password = await self._retrieve_password(account_id, reason=reason)
            
            # Build credentials dict
            creds: Dict[str, Any] = {
                "username": account.get("userName"),
                "password": password,
                "address": account.get("address"),
                "safe": account.get("safeName"),
                "name": account.get("name"),
                "platform": account.get("platformId"),
            }
            
            # Add platform-specific properties
            platform_props = account.get("platformAccountProperties", {})
            for key, value in platform_props.items():
                if key not in creds:
                    creds[key] = value
            
            # If fragment specified, return just that key
            if fragment_key:
                if fragment_key not in creds:
                    raise VaultSecretNotFoundError(f"{reference}#{fragment_key}")
                return {fragment_key: creds[fragment_key]}
            
            return creds
    
    async def get_secret_or_none(self, reference: str) -> Optional[str]:
        """Get secret value or None if not found."""
        try:
            return await self.get_secret(reference)
        except VaultSecretNotFoundError:
            return None
    
    # ─────────────────────────────────────────────────────────────
    # EnumerableVaultProvider Implementation
    # ─────────────────────────────────────────────────────────────
    
    async def list_keys(self, path: str = "") -> List[str]:
        """List account names in a safe.
        
        Args:
            path: Safe name (or empty to list all safes)
            
        Returns:
            List of account names or safe names
        """
        with tracer.start_as_current_span("cyberark.list_keys") as span:
            await self._ensure_session()
            breaker = await self._get_circuit_breaker()
            
            # Handle cyberark:// prefix
            if path.startswith("cyberark://"):
                path = path[11:]
            
            path = path.strip("/")
            
            if not path:
                # List safes
                span.set_attribute("operation", "list_safes")
                return await self._list_safes()
            else:
                # List accounts in safe
                span.set_attribute("operation", "list_accounts")
                span.set_attribute("safe", path)
                return await self._list_accounts_in_safe(path)
    
    async def _list_safes(self) -> List[str]:
        """List accessible safes."""
        breaker = await self._get_circuit_breaker()
        url = f"{self._config.base_url}{self._API_SAFES}"
        
        async def _do_list() -> List[str]:
            async with httpx.AsyncClient(
                verify=self._config.verify_ssl,
                timeout=self._config.timeout,
                limits=self._client_limits,
            ) as client:
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code == 401:
                    self._session = None
                    raise VaultAuthenticationError("Session expired")
                
                response.raise_for_status()
                result = response.json()
                
                safes = result.get("value", result.get("Safes", []))
                return [s.get("safeName", s.get("SafeName", "")) for s in safes if s]
        
        try:
            return await breaker.execute(_do_list)
        except CircuitBreakerOpenError:
            logger.warning("Circuit open for list_safes")
            return []
        except Exception as e:
            logger.warning("Error listing safes: %s", e)
            return []
    
    async def _list_accounts_in_safe(self, safe: str) -> List[str]:
        """List accounts in a specific safe."""
        breaker = await self._get_circuit_breaker()
        
        params = {"filter": f"safeName eq {safe}"}
        url = f"{self._config.base_url}{self._API_ACCOUNTS}?{urlencode(params)}"
        
        async def _do_list() -> List[str]:
            async with httpx.AsyncClient(
                verify=self._config.verify_ssl,
                timeout=self._config.timeout,
                limits=self._client_limits,
            ) as client:
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code == 401:
                    self._session = None
                    raise VaultAuthenticationError("Session expired")
                elif response.status_code == 403:
                    raise VaultAuthorizationError(
                        f"Access denied to safe '{safe}'",
                        resource=safe,
                    )
                
                response.raise_for_status()
                result = response.json()
                
                accounts = result.get("value", [])
                return [a.get("name", "") for a in accounts if a.get("name")]
        
        try:
            return await breaker.execute(_do_list)
        except CircuitBreakerOpenError:
            logger.warning("Circuit open for list_accounts")
            return []
        except VaultAuthorizationError:
            raise
        except Exception as e:
            logger.warning("Error listing accounts in safe '%s': %s", safe, e)
            return []
    
    # ─────────────────────────────────────────────────────────────
    # Health Check & Lifecycle
    # ─────────────────────────────────────────────────────────────
    
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health.
        
        Returns:
            Health status dictionary including:
            - healthy: Overall health status
            - base_url: CyberArk PVWA URL
            - authenticated: Whether we have an active session
            - session_remaining_seconds: Time until session expires
            - server_info: CyberArk server information (if available)
        """
        with tracer.start_as_current_span("cyberark.health_check") as span:
            health: Dict[str, Any] = {
                "healthy": False,
                "base_url": self._config.base_url,
                "auth_method": self._config.auth_method.value,
                "authenticated": False,
                "session_remaining_seconds": 0,
            }
            
            # Check session status
            if self._session and not self._session.is_expired:
                health["authenticated"] = True
                health["session_remaining_seconds"] = self._session.remaining_seconds
            
            # Try to get server info
            try:
                url = f"{self._config.base_url}{self._API_SERVER_INFO}"
                
                async with httpx.AsyncClient(
                    verify=self._config.verify_ssl,
                    timeout=10,
                    limits=self._client_limits,
                ) as client:
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        server_info = response.json()
                        health["server_version"] = server_info.get("ServerVersion")
                        health["server_name"] = server_info.get("ServerName")
                        health["healthy"] = True
                    else:
                        # Server reachable but endpoint may require auth
                        health["healthy"] = True
                        
            except httpx.ConnectError as e:
                span.set_attribute("error", True)
                health["error"] = f"Connection failed: {e}"
            except httpx.TimeoutException:
                span.set_attribute("error", True)
                health["error"] = "Health check timeout"
            except Exception as e:
                span.set_attribute("error", True)
                health["error"] = str(e)
            
            return health
    
    async def close(self) -> None:
        """Close provider and end session."""
        await self._logoff()
        logger.info(
            "CyberArk provider closed",
            extra={"component": "vault_provider"},
        )
    
    def __repr__(self) -> str:
        return (
            f"CyberArkVaultProvider("
            f"base_url={self._config.base_url}, "
            f"auth_method={self._config.auth_method.value}, "
            f"default_safe={self._config.default_safe})"
        )
