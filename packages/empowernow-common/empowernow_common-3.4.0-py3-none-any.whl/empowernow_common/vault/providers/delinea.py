"""Delinea Secret Server vault provider implementation.

Production-grade provider for Delinea Secret Server REST API v1/v2.

Supported Features:
- OAuth2 authentication (password grant, client credentials)
- Token refresh with automatic renewal
- Read secrets by ID or search by folder/name
- List secrets and folders
- Full CRUD operations (create, update, delete)
- Field extraction via fragment (#password, #username)
- Circuit breaker protection
- Retry with exponential backoff
- OpenTelemetry tracing

URI Formats:
    delinea://123                          → Get secret by ID
    delinea://123#password                 → Extract password field
    delinea://folder/secret-name           → Search by folder path and name
    delinea://folder/secret-name#username  → Extract specific field
    delinea+secret://123?version=1         → With version parameter

Configuration:
    base_url: Delinea Secret Server URL (e.g., https://secretserver.company.com)
    auth:
        grant_type: password | client_credentials
        username: Username for password grant
        password: Password for password grant
        client_id: Client ID for client credentials
        client_secret: Client secret for client credentials
        domain: Optional domain for Windows auth
    default_folder_id: Default folder ID for operations
    timeout: Request timeout in seconds (default: 30)
    verify_ssl: Verify TLS certificates (default: true)

Per design: VAULT_PROVIDER_UNIFICATION.md
Per Playbook: AI_PYTHON_FASTAPI_EXCELLENCE_PLAYBOOK.md §5 (Circuit Breaker), §9 (Error Handling)
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from opentelemetry import trace

from empowernow_common.vault.base import (
    ReadableVaultProvider,
    WritableVaultProvider,
    EnumerableVaultProvider,
    Capabilities,
)
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


class GrantType(Enum):
    """Delinea OAuth2 grant types."""
    PASSWORD = "password"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"


@dataclass
class DelineaToken:
    """Active Delinea OAuth2 token information."""
    access_token: str
    refresh_token: Optional[str]
    token_type: str
    expires_in: int
    created_at: datetime
    expiry_buffer_s: int = 60
    
    @property
    def expires_at(self) -> datetime:
        """Calculate token expiration time."""
        return self.created_at + timedelta(seconds=self.expires_in)
    
    @property
    def is_expired(self) -> bool:
        """Check if token has expired (with configurable buffer)."""
        return datetime.now() >= (self.expires_at - timedelta(seconds=self.expiry_buffer_s))
    
    @property
    def remaining_seconds(self) -> int:
        """Seconds remaining until expiry."""
        remaining = (self.expires_at - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    @property
    def can_refresh(self) -> bool:
        """Check if token can be refreshed."""
        return self.refresh_token is not None


@dataclass
class DelineaConfig:
    """Configuration for Delinea Secret Server provider."""
    base_url: str
    grant_type: GrantType = GrantType.PASSWORD
    
    # Password grant credentials
    username: Optional[str] = None
    password: Optional[str] = None
    domain: Optional[str] = None
    
    # Client credentials grant
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    
    # Operational settings
    default_folder_id: Optional[int] = None
    default_field: str = "password"  # Default field when no fragment specified
    timeout: int = 30
    verify_ssl: bool = True
    
    # Token settings
    token_expiry_buffer_s: int = 60  # Renew token this many seconds before expiry
    default_token_ttl_s: int = 1200  # Fallback if server doesn't return expires_in
    
    # HTTP client settings
    max_keepalive_connections: int = 5
    max_connections: int = 10
    keepalive_expiry_s: float = 30.0
    
    # Retry settings
    retry_attempts: int = 3
    retry_min_wait_s: int = 2
    retry_max_wait_s: int = 10
    
    # Circuit breaker settings
    cb_failure_threshold: int = 5
    cb_reset_timeout_s: float = 30.0
    cb_window_s: float = 60.0


class DelineaVaultProvider:
    """Delinea Secret Server vault provider.
    
    Production-grade provider implementing:
    - ReadableVaultProvider: get_secret, get_credentials, get_secret_or_none
    - WritableVaultProvider: create_or_update_secret, delete_secret
    - EnumerableVaultProvider: list_keys
    
    Delinea Secret Server uses a REST API with OAuth2 authentication.
    Secrets are organized in folders and have typed fields (Username, Password, etc.).
    
    Per Playbook §5: Uses empowernow_common.resilience.CircuitBreaker.
    """
    
    VAULT_TYPE = "delinea"
    CAPABILITIES = {
        Capabilities.LIST_KEYS: True,
        Capabilities.READ_SECRET: True,
        Capabilities.WRITE_SECRET: True,  # Delinea supports full CRUD
        Capabilities.DELETE_SECRET: True,
        Capabilities.METADATA: True,
        Capabilities.READ_METADATA: True,
        Capabilities.UPDATE_METADATA: True,
        Capabilities.VERSIONING: False,  # Secret Server doesn't have KV v2 style versioning
        Capabilities.VERSION_PIN: False,
        Capabilities.SOFT_DELETE: False,
        Capabilities.HARD_DESTROY: True,
        Capabilities.RESPONSE_WRAPPING: False,
        Capabilities.IDENTITY_SCOPING: True,  # Folder-based scoping
        Capabilities.OWNERSHIP_TRACKING: True,  # Secret ownership in Delinea
        Capabilities.AUDIT_METADATA: True,  # Full audit trail
        Capabilities.TAGS: False,
    }
    
    # API endpoints
    _API_TOKEN = "/oauth2/token"
    _API_SECRET = "/api/v2/secrets/{secret_id}"
    _API_SECRET_FIELDS = "/api/v2/secrets/{secret_id}/fields/{field_slug}"
    _API_SECRETS = "/api/v2/secrets"
    _API_SECRETS_LOOKUP = "/api/v1/secrets/lookup"
    _API_FOLDERS = "/api/v1/folders"
    _API_FOLDER = "/api/v1/folders/{folder_id}"
    _API_SECRET_TEMPLATES = "/api/v1/secret-templates"
    _API_VERSION = "/api/v1/version"
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize Delinea Secret Server provider.
        
        Args:
            config: Configuration dictionary with keys:
                - base_url: Secret Server URL
                - grant_type: 'password' or 'client_credentials'
                - username: Username (for password grant)
                - password: Password (for password grant)
                - domain: Domain (optional, for Windows auth)
                - client_id: Client ID (for client_credentials)
                - client_secret: Client secret (for client_credentials)
                - default_folder_id: Default folder ID
                - default_field: Default field name when no fragment (default: 'password')
                - timeout: Request timeout in seconds (default: 30)
                - verify_ssl: Verify TLS certificates (default: true)
                - token_expiry_buffer_s: Seconds before expiry to renew (default: 60)
                - default_token_ttl_s: Fallback TTL if server doesn't specify (default: 1200)
                - max_keepalive_connections: HTTP keepalive connections (default: 5)
                - max_connections: Max HTTP connections (default: 10)
                - retry_attempts: Number of retry attempts (default: 3)
                - retry_min_wait_s: Min retry wait seconds (default: 2)
                - retry_max_wait_s: Max retry wait seconds (default: 10)
                - cb_failure_threshold: Circuit breaker failure threshold (default: 5)
                - cb_reset_timeout_s: Circuit breaker reset timeout (default: 30)
                - cb_window_s: Circuit breaker window seconds (default: 60)
        
        Raises:
            VaultConfigurationError: If required configuration is missing
        """
        # Parse grant type
        grant_type_str = config.get("grant_type", "password").lower()
        try:
            grant_type = GrantType(grant_type_str)
        except ValueError:
            valid_grants = [g.value for g in GrantType if g != GrantType.REFRESH_TOKEN]
            raise VaultConfigurationError(
                f"Invalid grant_type '{grant_type_str}'. Valid: {valid_grants}"
            )
        
        # Parse default folder ID
        default_folder_id = config.get("default_folder_id")
        if default_folder_id is not None:
            try:
                default_folder_id = int(default_folder_id)
            except (ValueError, TypeError):
                default_folder_id = None
        
        self._config = DelineaConfig(
            base_url=config.get("base_url", "").rstrip("/"),
            grant_type=grant_type,
            username=config.get("username"),
            password=config.get("password"),
            domain=config.get("domain"),
            client_id=config.get("client_id"),
            client_secret=config.get("client_secret"),
            default_folder_id=default_folder_id,
            default_field=config.get("default_field", "password"),
            timeout=int(config.get("timeout", 30)),
            verify_ssl=config.get("verify_ssl", True),
            token_expiry_buffer_s=int(config.get("token_expiry_buffer_s", 60)),
            default_token_ttl_s=int(config.get("default_token_ttl_s", 1200)),
            max_keepalive_connections=int(config.get("max_keepalive_connections", 5)),
            max_connections=int(config.get("max_connections", 10)),
            keepalive_expiry_s=float(config.get("keepalive_expiry_s", 30.0)),
            retry_attempts=int(config.get("retry_attempts", 3)),
            retry_min_wait_s=int(config.get("retry_min_wait_s", 2)),
            retry_max_wait_s=int(config.get("retry_max_wait_s", 10)),
            cb_failure_threshold=int(config.get("cb_failure_threshold", 5)),
            cb_reset_timeout_s=float(config.get("cb_reset_timeout_s", 30.0)),
            cb_window_s=float(config.get("cb_window_s", 60.0)),
        )
        
        # Validate required config
        if not self._config.base_url:
            raise VaultConfigurationError("Delinea base_url is required")
        
        if self._config.grant_type == GrantType.PASSWORD:
            if not self._config.username:
                raise VaultConfigurationError("Delinea username is required for password grant")
            if not self._config.password:
                raise VaultConfigurationError("Delinea password is required for password grant")
        elif self._config.grant_type == GrantType.CLIENT_CREDENTIALS:
            if not self._config.client_id:
                raise VaultConfigurationError("Delinea client_id is required for client_credentials grant")
            if not self._config.client_secret:
                raise VaultConfigurationError("Delinea client_secret is required for client_credentials grant")
        
        # Circuit breaker config (lazy initialization)
        self._cb_config = CircuitBreakerConfig(
            threshold=self._config.cb_failure_threshold,
            timeout=self._config.cb_reset_timeout_s,
            window_seconds=self._config.cb_window_s,
        )
        self._breaker: Optional[CircuitBreaker] = None
        
        # Token management
        self._token: Optional[DelineaToken] = None
        self._token_lock = asyncio.Lock()
        
        # HTTP client config
        self._client_limits = httpx.Limits(
            max_keepalive_connections=self._config.max_keepalive_connections,
            max_connections=self._config.max_connections,
            keepalive_expiry=self._config.keepalive_expiry_s,
        )
        
        logger.info(
            "Delinea Secret Server provider initialized: %s",
            self._config.base_url,
            extra={
                "component": "vault_provider",
                "provider_type": "delinea",
                "base_url": self._config.base_url,
                "grant_type": self._config.grant_type.value,
                "default_folder_id": self._config.default_folder_id,
            },
        )
    
    async def _get_circuit_breaker(self) -> CircuitBreaker:
        """Lazily initialize circuit breaker via registry."""
        if self._breaker is None:
            self._breaker = await get_circuit_breaker(
                f"vault_delinea_{self._config.base_url}",
                self._cb_config,
            )
        return self._breaker
    
    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get HTTP headers for API calls."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if include_auth and self._token:
            headers["Authorization"] = f"{self._token.token_type} {self._token.access_token}"
        return headers
    
    # ─────────────────────────────────────────────────────────────
    # Token Management
    # ─────────────────────────────────────────────────────────────
    
    async def _ensure_token(self) -> None:
        """Ensure we have a valid token, authenticating or refreshing if needed."""
        async with self._token_lock:
            if self._token is None:
                await self._authenticate()
            elif self._token.is_expired:
                if self._token.can_refresh:
                    try:
                        await self._refresh_token()
                    except VaultAuthenticationError:
                        # Refresh failed, re-authenticate
                        await self._authenticate()
                else:
                    await self._authenticate()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _authenticate(self) -> None:
        """Authenticate to Delinea and obtain OAuth2 token."""
        with tracer.start_as_current_span("delinea.authenticate") as span:
            span.set_attribute("grant_type", self._config.grant_type.value)
            
            url = f"{self._config.base_url}{self._API_TOKEN}"
            
            # Build request body based on grant type
            if self._config.grant_type == GrantType.PASSWORD:
                body = {
                    "grant_type": "password",
                    "username": self._config.username,
                    "password": self._config.password,
                }
                if self._config.domain:
                    body["domain"] = self._config.domain
            else:  # CLIENT_CREDENTIALS
                body = {
                    "grant_type": "client_credentials",
                    "client_id": self._config.client_id,
                    "client_secret": self._config.client_secret,
                }
            
            try:
                async with httpx.AsyncClient(
                    verify=self._config.verify_ssl,
                    timeout=self._config.timeout,
                    limits=self._client_limits,
                ) as client:
                    response = await client.post(
                        url,
                        data=body,  # OAuth2 uses form-encoded body
                        headers={
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Accept": "application/json",
                        },
                    )
                    
                    if response.status_code == 400:
                        error_data = response.json() if response.content else {}
                        error_msg = error_data.get("error_description", error_data.get("error", "Bad request"))
                        raise VaultAuthenticationError(f"Delinea authentication failed: {error_msg}")
                    elif response.status_code == 401:
                        raise VaultAuthenticationError("Delinea authentication failed: invalid credentials")
                    elif response.status_code == 403:
                        raise VaultAuthorizationError(
                            "Delinea authentication forbidden: account may be disabled",
                            resource="authentication",
                        )
                    
                    response.raise_for_status()
                    token_data = response.json()
                    
                    access_token = token_data.get("access_token")
                    if not access_token:
                        raise VaultAuthenticationError("Delinea authentication failed: no access token")
                    
                    self._token = DelineaToken(
                        access_token=access_token,
                        refresh_token=token_data.get("refresh_token"),
                        token_type=token_data.get("token_type", "Bearer"),
                        expires_in=int(token_data.get("expires_in", self._config.default_token_ttl_s)),
                        created_at=datetime.now(),
                        expiry_buffer_s=self._config.token_expiry_buffer_s,
                    )
                    
                    logger.info(
                        "Delinea token obtained (expires in %ds)",
                        self._token.expires_in,
                        extra={
                            "component": "vault_provider",
                            "grant_type": self._config.grant_type.value,
                        },
                    )
                    
            except (VaultAuthenticationError, VaultAuthorizationError):
                span.set_attribute("error", True)
                raise
            except httpx.TimeoutException as e:
                span.set_attribute("error", True)
                raise VaultTimeoutError(f"Delinea authentication timeout: {e}") from e
            except httpx.ConnectError as e:
                span.set_attribute("error", True)
                raise VaultConnectionError(f"Cannot connect to Delinea: {e}") from e
            except Exception as e:
                span.set_attribute("error", True)
                raise VaultOperationError(f"Delinea authentication error: {e}") from e
    
    async def _refresh_token(self) -> None:
        """Refresh the OAuth2 token using refresh_token grant."""
        if not self._token or not self._token.refresh_token:
            raise VaultAuthenticationError("No refresh token available")
        
        with tracer.start_as_current_span("delinea.refresh_token") as span:
            url = f"{self._config.base_url}{self._API_TOKEN}"
            
            body = {
                "grant_type": "refresh_token",
                "refresh_token": self._token.refresh_token,
            }
            
            try:
                async with httpx.AsyncClient(
                    verify=self._config.verify_ssl,
                    timeout=self._config.timeout,
                    limits=self._client_limits,
                ) as client:
                    response = await client.post(
                        url,
                        data=body,
                        headers={
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Accept": "application/json",
                        },
                    )
                    
                    if response.status_code in (400, 401):
                        raise VaultAuthenticationError("Token refresh failed")
                    
                    response.raise_for_status()
                    token_data = response.json()
                    
                    self._token = DelineaToken(
                        access_token=token_data.get("access_token", ""),
                        refresh_token=token_data.get("refresh_token"),
                        token_type=token_data.get("token_type", "Bearer"),
                        expires_in=int(token_data.get("expires_in", self._config.default_token_ttl_s)),
                        created_at=datetime.now(),
                        expiry_buffer_s=self._config.token_expiry_buffer_s,
                    )
                    
                    logger.debug("Delinea token refreshed")
                    
            except VaultAuthenticationError:
                span.set_attribute("error", True)
                raise
            except Exception as e:
                span.set_attribute("error", True)
                raise VaultAuthenticationError(f"Token refresh failed: {e}") from e
    
    # ─────────────────────────────────────────────────────────────
    # URI Parsing
    # ─────────────────────────────────────────────────────────────
    
    def _parse_reference(self, reference: str) -> Tuple[Optional[int], Optional[str], Optional[str], Optional[str], Dict[str, str]]:
        """Parse a secret reference into components.
        
        Formats supported:
            123                           → Secret ID
            123#password                  → Secret ID with field
            folder/secret-name            → Folder path and name
            folder/secret-name#username   → With field extraction
            delinea://123                 → URI format with ID
            delinea://folder/name         → URI format with path
            delinea://123#field?param=val → Full URI
        
        Args:
            reference: Secret reference string
            
        Returns:
            Tuple of (secret_id, folder_path, secret_name, fragment_key, query_params)
        """
        secret_id: Optional[int] = None
        folder_path: Optional[str] = None
        secret_name: Optional[str] = None
        fragment_key: Optional[str] = None
        query_params: Dict[str, str] = {}
        
        path = reference
        
        # Handle delinea:// or delinea+secret:// URI schemes
        if path.startswith("delinea://"):
            path = path[10:]
        elif path.startswith("delinea+secret://"):
            path = path[17:]
        
        # Extract query params FIRST
        if "?" in path:
            path, query_string = path.split("?", 1)
            for param in query_string.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    query_params[key] = value
        
        # Extract fragment
        if "#" in path:
            path, fragment_key = path.rsplit("#", 1)
        
        # Determine if path is an ID or folder/name
        path = path.strip("/")
        
        if path.isdigit():
            secret_id = int(path)
        elif "/" in path:
            # folder/name format
            parts = path.rsplit("/", 1)
            folder_path = parts[0]
            secret_name = parts[1] if len(parts) > 1 else None
        else:
            # Could be just a name (use default folder) or an ID string
            try:
                secret_id = int(path)
            except ValueError:
                secret_name = path
        
        return secret_id, folder_path, secret_name, fragment_key, query_params
    
    def _extract_field_value(self, secret: Dict[str, Any], field_name: str) -> str:
        """Extract a field value from a secret's items array.
        
        Args:
            secret: Secret data from API
            field_name: Field name to extract (case-insensitive)
            
        Returns:
            Field value
            
        Raises:
            VaultSecretNotFoundError: If field not found
        """
        items = secret.get("items", [])
        field_lower = field_name.lower()
        
        for item in items:
            # Check fieldName and slug
            item_field = item.get("fieldName", "").lower()
            item_slug = item.get("slug", "").lower()
            
            if item_field == field_lower or item_slug == field_lower:
                return str(item.get("itemValue", ""))
        
        # Field not found
        raise VaultSecretNotFoundError(f"Field '{field_name}' not found in secret")
    
    def _secret_to_dict(self, secret: Dict[str, Any]) -> Dict[str, Any]:
        """Convert secret items to a flat dictionary.
        
        Args:
            secret: Secret data from API
            
        Returns:
            Dictionary mapping field names to values
        """
        result: Dict[str, Any] = {
            "id": secret.get("id"),
            "name": secret.get("name"),
            "folderId": secret.get("folderId"),
            "secretTemplateId": secret.get("secretTemplateId"),
            "active": secret.get("active"),
        }
        
        items = secret.get("items", [])
        for item in items:
            field_name = item.get("fieldName", "")
            slug = item.get("slug", field_name.lower().replace(" ", "_"))
            value = item.get("itemValue")
            
            if slug:
                result[slug] = value
            if field_name:
                result[field_name] = value
        
        return result
    
    # ─────────────────────────────────────────────────────────────
    # Secret Operations
    # ─────────────────────────────────────────────────────────────
    
    async def _get_secret_by_id(self, secret_id: int) -> Dict[str, Any]:
        """Get a secret by its ID.
        
        Args:
            secret_id: Delinea secret ID
            
        Returns:
            Secret data dictionary
            
        Raises:
            VaultSecretNotFoundError: If secret not found
        """
        with tracer.start_as_current_span("delinea.get_secret_by_id") as span:
            span.set_attribute("secret_id", secret_id)
            
            await self._ensure_token()
            breaker = await self._get_circuit_breaker()
            
            url = f"{self._config.base_url}{self._API_SECRET.format(secret_id=secret_id)}"
            
            async def _do_get() -> Dict[str, Any]:
                async with httpx.AsyncClient(
                    verify=self._config.verify_ssl,
                    timeout=self._config.timeout,
                    limits=self._client_limits,
                ) as client:
                    response = await client.get(url, headers=self._get_headers())
                    
                    if response.status_code == 401:
                        self._token = None
                        raise VaultAuthenticationError("Token expired")
                    elif response.status_code == 403:
                        raise VaultAuthorizationError(
                            f"Access denied to secret {secret_id}",
                            resource=str(secret_id),
                        )
                    elif response.status_code == 404:
                        raise VaultSecretNotFoundError(str(secret_id))
                    
                    response.raise_for_status()
                    return response.json()
            
            try:
                return await breaker.execute(_do_get)
            except CircuitBreakerOpenError as e:
                span.set_attribute("error", True)
                raise VaultTimeoutError(f"Circuit open: {e}") from e
            except VaultAuthenticationError:
                # Retry once after re-auth
                await self._ensure_token()
                return await breaker.execute(_do_get)
    
    async def _search_secrets(
        self,
        search_text: Optional[str] = None,
        folder_id: Optional[int] = None,
        template_id: Optional[int] = None,
        include_inactive: bool = False,
    ) -> List[Dict[str, Any]]:
        """Search for secrets using lookup endpoint.
        
        Args:
            search_text: Text to search for in secret names
            folder_id: Filter by folder ID
            template_id: Filter by secret template ID
            include_inactive: Include inactive secrets
            
        Returns:
            List of matching secrets (summary info only)
        """
        with tracer.start_as_current_span("delinea.search_secrets") as span:
            await self._ensure_token()
            breaker = await self._get_circuit_breaker()
            
            # Build query params
            params: Dict[str, Any] = {}
            if search_text:
                params["filter.searchText"] = search_text
            if folder_id is not None:
                params["filter.folderId"] = folder_id
            if template_id is not None:
                params["filter.secretTemplateId"] = template_id
            if include_inactive:
                params["filter.includeInactive"] = "true"
            
            url = f"{self._config.base_url}{self._API_SECRETS_LOOKUP}"
            if params:
                url += f"?{urlencode(params)}"
            
            async def _do_search() -> List[Dict[str, Any]]:
                async with httpx.AsyncClient(
                    verify=self._config.verify_ssl,
                    timeout=self._config.timeout,
                    limits=self._client_limits,
                ) as client:
                    response = await client.get(url, headers=self._get_headers())
                    
                    if response.status_code == 401:
                        self._token = None
                        raise VaultAuthenticationError("Token expired")
                    elif response.status_code == 403:
                        raise VaultAuthorizationError(
                            "Access denied to search secrets",
                            resource="search",
                        )
                    
                    response.raise_for_status()
                    result = response.json()
                    return result.get("records", [])
            
            try:
                return await breaker.execute(_do_search)
            except CircuitBreakerOpenError as e:
                span.set_attribute("error", True)
                raise VaultTimeoutError(f"Circuit open: {e}") from e
            except VaultAuthenticationError:
                await self._ensure_token()
                return await breaker.execute(_do_search)
    
    async def _find_folder_by_path(self, folder_path: str) -> Optional[int]:
        """Find folder ID by path.
        
        Args:
            folder_path: Folder path (e.g., "IT/Databases")
            
        Returns:
            Folder ID or None if not found
        """
        with tracer.start_as_current_span("delinea.find_folder") as span:
            await self._ensure_token()
            
            url = f"{self._config.base_url}{self._API_FOLDERS}"
            
            async with httpx.AsyncClient(
                verify=self._config.verify_ssl,
                timeout=self._config.timeout,
                limits=self._client_limits,
            ) as client:
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code != 200:
                    return None
                
                folders = response.json().get("records", [])
                
                # Search for matching folder path
                path_lower = folder_path.lower()
                for folder in folders:
                    folder_full_path = folder.get("folderPath", "")
                    folder_name = folder.get("folderName", "")
                    
                    if folder_full_path.lower() == path_lower or folder_name.lower() == path_lower:
                        return folder.get("id")
                
                return None
    
    # ─────────────────────────────────────────────────────────────
    # ReadableVaultProvider Implementation
    # ─────────────────────────────────────────────────────────────
    
    async def _resolve_secret(self, reference: str) -> Dict[str, Any]:
        """Resolve a secret reference to the full secret data.
        
        This is the core resolution logic used by both get_secret and get_credentials.
        
        Args:
            reference: Secret reference string
            
        Returns:
            Full secret data dictionary from Delinea API
            
        Raises:
            VaultSecretNotFoundError: If secret not found
            VaultOperationError: If reference is invalid
        """
        secret_id, folder_path, secret_name, _, _ = self._parse_reference(reference)
        
        if secret_id is not None:
            return await self._get_secret_by_id(secret_id)
        
        if secret_name:
            # Search for secret
            folder_id = None
            if folder_path:
                folder_id = await self._find_folder_by_path(folder_path)
            elif self._config.default_folder_id:
                folder_id = self._config.default_folder_id
            
            results = await self._search_secrets(
                search_text=secret_name,
                folder_id=folder_id,
            )
            
            if not results:
                raise VaultSecretNotFoundError(reference)
            
            # Find exact match
            resolved_id: Optional[int] = None
            for r in results:
                if r.get("name", "").lower() == secret_name.lower():
                    resolved_id = r.get("id")
                    break
            else:
                resolved_id = results[0].get("id")
            
            if not resolved_id:
                raise VaultSecretNotFoundError(reference)
            
            return await self._get_secret_by_id(resolved_id)
        
        raise VaultOperationError(f"Invalid reference: {reference}")
    
    async def get_secret(self, reference: str) -> str:
        """Get a secret value by reference.
        
        By default returns the configured default_field (default: 'password').
        Use fragment to specify a different field (e.g., #username, #url).
        
        Args:
            reference: Secret reference in formats:
                - "123" → Secret ID, returns default field
                - "123#username" → Secret ID, returns username field
                - "folder/name" → Search by folder/name
                - "delinea://123" → URI format
        
        Returns:
            The secret value (default field or specified field)
            
        Raises:
            VaultSecretNotFoundError: If secret not found
            VaultAuthorizationError: If access denied
        """
        with tracer.start_as_current_span("delinea.get_secret") as span:
            _, _, _, fragment_key, _ = self._parse_reference(reference)
            
            secret = await self._resolve_secret(reference)
            
            # Extract field value
            field = fragment_key or self._config.default_field
            return self._extract_field_value(secret, field)
    
    async def get_credentials(self, reference: str) -> Dict[str, Any]:
        """Get credentials as a dictionary.
        
        Returns all fields from the secret as a dictionary.
        
        Args:
            reference: Secret reference
            
        Returns:
            Dictionary with all secret fields
        """
        with tracer.start_as_current_span("delinea.get_credentials") as span:
            _, _, _, fragment_key, _ = self._parse_reference(reference)
            
            secret = await self._resolve_secret(reference)
            
            # Convert to dictionary
            creds = self._secret_to_dict(secret)
            
            # If fragment specified, return just that key
            if fragment_key:
                field_lower = fragment_key.lower()
                for key, value in creds.items():
                    if key.lower() == field_lower:
                        return {fragment_key: value}
                raise VaultSecretNotFoundError(f"{reference}#{fragment_key}")
            
            return creds
    
    async def get_secret_or_none(self, reference: str) -> Optional[str]:
        """Get secret value or None if not found."""
        try:
            return await self.get_secret(reference)
        except VaultSecretNotFoundError:
            return None
    
    # ─────────────────────────────────────────────────────────────
    # WritableVaultProvider Implementation
    # ─────────────────────────────────────────────────────────────
    
    async def create_or_update_secret(
        self,
        path: str,
        data: Dict[str, Any],
        *,
        custom_metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create or update a secret.
        
        Args:
            path: Secret reference (ID for update, folder/name for create)
            data: Secret data (field values)
            custom_metadata: Not used in Delinea
            
        Returns:
            Dictionary with operation result
        """
        with tracer.start_as_current_span("delinea.create_or_update_secret") as span:
            secret_id, folder_path, secret_name, _, params = self._parse_reference(path)
            
            await self._ensure_token()
            
            if secret_id is not None:
                # Update existing secret
                return await self._update_secret(secret_id, data)
            else:
                # Create new secret
                folder_id = self._config.default_folder_id
                if folder_path:
                    folder_id = await self._find_folder_by_path(folder_path)
                
                if folder_id is None:
                    raise VaultOperationError(
                        "Folder not found or default_folder_id not configured"
                    )
                
                if not secret_name:
                    raise VaultOperationError("Secret name is required for create operation")
                
                return await self._create_secret(
                    name=secret_name,
                    folder_id=folder_id,
                    data=data,
                    template_id=params.get("template_id"),
                )
    
    async def _update_secret(self, secret_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing secret's fields."""
        # Get current secret to find field IDs
        secret = await self._get_secret_by_id(secret_id)
        items = secret.get("items", [])
        
        # Build update payload
        updates = []
        for field_name, value in data.items():
            for item in items:
                if (item.get("fieldName", "").lower() == field_name.lower() or
                    item.get("slug", "").lower() == field_name.lower()):
                    updates.append({
                        "itemId": item.get("itemId"),
                        "itemValue": str(value),
                    })
                    break
        
        if not updates:
            raise VaultOperationError("No matching fields found to update")
        
        url = f"{self._config.base_url}{self._API_SECRET.format(secret_id=secret_id)}"
        
        async with httpx.AsyncClient(
            verify=self._config.verify_ssl,
            timeout=self._config.timeout,
            limits=self._client_limits,
        ) as client:
            response = await client.put(
                url,
                json={"items": updates},
                headers=self._get_headers(),
            )
            
            if response.status_code == 403:
                raise VaultAuthorizationError(
                    f"Access denied to update secret {secret_id}",
                    resource=str(secret_id),
                )
            elif response.status_code == 404:
                raise VaultSecretNotFoundError(str(secret_id))
            
            response.raise_for_status()
            
            return {"id": secret_id, "updated": True}
    
    async def _create_secret(
        self,
        name: str,
        folder_id: int,
        data: Dict[str, Any],
        template_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new secret."""
        url = f"{self._config.base_url}{self._API_SECRETS}"
        
        # Build items from data
        items = []
        for field_name, value in data.items():
            items.append({
                "fieldName": field_name,
                "itemValue": str(value),
            })
        
        body: Dict[str, Any] = {
            "name": name,
            "folderId": folder_id,
            "items": items,
        }
        
        if template_id:
            body["secretTemplateId"] = int(template_id)
        
        async with httpx.AsyncClient(
            verify=self._config.verify_ssl,
            timeout=self._config.timeout,
            limits=self._client_limits,
        ) as client:
            response = await client.post(
                url,
                json=body,
                headers=self._get_headers(),
            )
            
            if response.status_code == 403:
                raise VaultAuthorizationError(
                    f"Access denied to create secret in folder {folder_id}",
                    resource=str(folder_id),
                )
            
            response.raise_for_status()
            result = response.json()
            
            return {"id": result.get("id"), "created": True}
    
    async def delete_secret(self, path: str, *, permanent: bool = False) -> None:
        """Delete a secret.
        
        Args:
            path: Secret reference (ID)
            permanent: Not used (Delinea deletion is permanent)
        """
        with tracer.start_as_current_span("delinea.delete_secret") as span:
            secret_id, _, _, _, _ = self._parse_reference(path)
            
            if secret_id is None:
                raise VaultOperationError("Delete requires a secret ID")
            
            span.set_attribute("secret_id", secret_id)
            
            await self._ensure_token()
            
            url = f"{self._config.base_url}{self._API_SECRET.format(secret_id=secret_id)}"
            
            async with httpx.AsyncClient(
                verify=self._config.verify_ssl,
                timeout=self._config.timeout,
                limits=self._client_limits,
            ) as client:
                response = await client.delete(url, headers=self._get_headers())
                
                if response.status_code == 403:
                    raise VaultAuthorizationError(
                        f"Access denied to delete secret {secret_id}",
                        resource=str(secret_id),
                    )
                elif response.status_code == 404:
                    raise VaultSecretNotFoundError(str(secret_id))
                
                response.raise_for_status()
    
    # ─────────────────────────────────────────────────────────────
    # EnumerableVaultProvider Implementation
    # ─────────────────────────────────────────────────────────────
    
    async def list_keys(self, path: str = "") -> List[str]:
        """List secrets or folders.
        
        Args:
            path: Folder path or ID (empty for root/all folders)
            
        Returns:
            List of secret names or folder names
        """
        with tracer.start_as_current_span("delinea.list_keys") as span:
            await self._ensure_token()
            
            # Handle delinea:// prefix
            if path.startswith("delinea://"):
                path = path[10:]
            
            path = path.strip("/")
            
            if not path:
                # List folders at root
                span.set_attribute("operation", "list_folders")
                return await self._list_folders()
            else:
                # List secrets in folder
                span.set_attribute("operation", "list_secrets")
                
                # Resolve folder ID
                if path.isdigit():
                    folder_id = int(path)
                else:
                    folder_id = await self._find_folder_by_path(path)
                
                if folder_id is None:
                    return []
                
                span.set_attribute("folder_id", folder_id)
                return await self._list_secrets_in_folder(folder_id)
    
    async def _list_folders(self) -> List[str]:
        """List all accessible folders."""
        url = f"{self._config.base_url}{self._API_FOLDERS}"
        
        try:
            async with httpx.AsyncClient(
                verify=self._config.verify_ssl,
                timeout=self._config.timeout,
                limits=self._client_limits,
            ) as client:
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code != 200:
                    logger.warning(
                        "Failed to list folders: HTTP %d",
                        response.status_code,
                        extra={"component": "vault_provider", "status_code": response.status_code},
                    )
                    return []
                
                folders = response.json().get("records", [])
                return [f.get("folderName", "") for f in folders if f.get("folderName")]
        except Exception as e:
            logger.warning(
                "Error listing folders: %s",
                e,
                extra={"component": "vault_provider"},
            )
            return []
    
    async def _list_secrets_in_folder(self, folder_id: int) -> List[str]:
        """List secrets in a specific folder."""
        results = await self._search_secrets(folder_id=folder_id)
        return [r.get("name", "") for r in results if r.get("name")]
    
    # ─────────────────────────────────────────────────────────────
    # Health Check & Lifecycle
    # ─────────────────────────────────────────────────────────────
    
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health.
        
        Returns:
            Health status dictionary including:
            - healthy: Overall health status
            - base_url: Delinea Secret Server URL
            - authenticated: Whether we have a valid token
            - token_remaining_seconds: Time until token expires
            - server_version: Server version (if available)
        """
        with tracer.start_as_current_span("delinea.health_check") as span:
            health: Dict[str, Any] = {
                "healthy": False,
                "base_url": self._config.base_url,
                "grant_type": self._config.grant_type.value,
                "authenticated": False,
                "token_remaining_seconds": 0,
            }
            
            # Check token status
            if self._token and not self._token.is_expired:
                health["authenticated"] = True
                health["token_remaining_seconds"] = self._token.remaining_seconds
            
            # Try to get version info
            try:
                url = f"{self._config.base_url}{self._API_VERSION}"
                
                async with httpx.AsyncClient(
                    verify=self._config.verify_ssl,
                    timeout=self._config.timeout,
                    limits=self._client_limits,
                ) as client:
                    response = await client.get(url, headers=self._get_headers())
                    
                    if response.status_code == 200:
                        version_info = response.json()
                        health["server_version"] = version_info.get("version")
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
        """Close provider and clear token."""
        self._token = None
        logger.info(
            "Delinea provider closed",
            extra={"component": "vault_provider"},
        )
    
    def __repr__(self) -> str:
        return (
            f"DelineaVaultProvider("
            f"base_url={self._config.base_url}, "
            f"grant_type={self._config.grant_type.value}, "
            f"default_folder_id={self._config.default_folder_id})"
        )
