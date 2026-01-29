"""Azure Key Vault provider implementation.

Full-featured provider for Azure Key Vault supporting:
- Managed Identity authentication
- Client credentials (service principal)
- Read/write/delete operations
- Secret versioning
- Circuit breaker protection
- Retry with exponential backoff
- OpenTelemetry tracing

Requires azure-keyvault-secrets and azure-identity packages.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from opentelemetry import trace

from empowernow_common.vault.base import FullVaultProvider, Capabilities
from empowernow_common.vault.uri import parse_secret_uri
from empowernow_common.vault.exceptions import (
    VaultAuthenticationError,
    VaultAuthorizationError,
    VaultConnectionError,
    VaultConfigurationError,
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


class AzureKeyVaultProvider:
    """Azure Key Vault provider implementing FullVaultProvider protocol.
    
    Supports multiple authentication methods:
    - managed_identity: Azure Managed Identity (recommended for Azure VMs/containers)
    - client_credentials: Service principal with client secret
    - default: Uses DefaultAzureCredential (tries multiple methods)
    
    Configuration:
        vault_url: Azure Key Vault URL (e.g., https://my-vault.vault.azure.net/)
        auth:
            method: managed_identity | client_credentials | default
            tenant_id: Azure AD tenant ID (for client_credentials)
            client_id: Service principal client ID (for client_credentials)
            client_secret: Service principal secret (for client_credentials)
    """
    
    VAULT_TYPE = "azure_keyvault"
    CAPABILITIES = Capabilities.full_capabilities()
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize Azure Key Vault provider.
        
        Args:
            config: Configuration dictionary with keys:
                - vault_url: Azure Key Vault URL
                - method: Auth method (managed_identity, client_credentials, default)
                - tenant_id: Azure AD tenant ID
                - client_id: Client/application ID
                - client_secret: Client secret
                - timeout: Request timeout in seconds
                - cb_failure_threshold: Circuit breaker failure threshold
                - cb_reset_timeout_s: Circuit breaker reset timeout
        """
        self._vault_url = config.get("vault_url", "").rstrip("/")
        if not self._vault_url:
            raise VaultConfigurationError("Azure Key Vault URL is required")
        
        self._auth_method = config.get("method", "default")
        self._tenant_id = config.get("tenant_id")
        self._client_id = config.get("client_id")
        self._client_secret = config.get("client_secret")
        self._timeout = int(config.get("timeout", 30))
        
        # Circuit breaker config (lazy initialization)
        self._cb_config = CircuitBreakerConfig(
            threshold=int(config.get("cb_failure_threshold", 5)),
            timeout=float(config.get("cb_reset_timeout_s", 30)),
            window_seconds=60.0,
        )
        self._breaker: Optional[CircuitBreaker] = None
        
        # Lazy initialize client
        self._client: Any = None
        self._credential: Any = None
        
        logger.info(
            "Azure Key Vault provider initialized: %s",
            self._vault_url,
            extra={
                "component": "vault_provider",
                "provider_type": "azure_keyvault",
                "vault_url": self._vault_url,
                "auth_method": self._auth_method,
            },
        )
    
    async def _get_circuit_breaker(self) -> CircuitBreaker:
        """Lazily initialize circuit breaker via registry."""
        if self._breaker is None:
            self._breaker = await get_circuit_breaker(
                f"vault_akv_{self._vault_url}",
                self._cb_config,
            )
        return self._breaker
    
    def _get_credential(self) -> Any:
        """Get Azure credential based on auth method."""
        if self._credential is not None:
            return self._credential
        
        try:
            from azure.identity import (
                DefaultAzureCredential,
                ManagedIdentityCredential,
                ClientSecretCredential,
            )
        except ImportError as e:
            raise VaultConfigurationError(
                "Azure SDK not installed. Install with: pip install azure-keyvault-secrets azure-identity"
            ) from e
        
        if self._auth_method == "managed_identity":
            self._credential = ManagedIdentityCredential(
                client_id=self._client_id,  # Optional for user-assigned MI
            )
        elif self._auth_method == "client_credentials":
            if not all([self._tenant_id, self._client_id, self._client_secret]):
                raise VaultConfigurationError(
                    "client_credentials auth requires tenant_id, client_id, and client_secret"
                )
            self._credential = ClientSecretCredential(
                tenant_id=self._tenant_id,
                client_id=self._client_id,
                client_secret=self._client_secret,
            )
        else:
            # default: try multiple methods
            self._credential = DefaultAzureCredential()
        
        return self._credential
    
    def _get_client(self) -> Any:
        """Get Azure Key Vault client."""
        if self._client is not None:
            return self._client
        
        try:
            from azure.keyvault.secrets import SecretClient
        except ImportError as e:
            raise VaultConfigurationError(
                "Azure SDK not installed. Install with: pip install azure-keyvault-secrets azure-identity"
            ) from e
        
        credential = self._get_credential()
        self._client = SecretClient(
            vault_url=self._vault_url,
            credential=credential,
        )
        
        return self._client
    
    def _handle_azure_error(self, e: Exception, path: str) -> None:
        """Convert Azure errors to vault exceptions."""
        error_msg = str(e).lower()
        
        if "forbidden" in error_msg or "403" in error_msg:
            raise VaultAuthorizationError("Access denied", resource=path) from e
        elif "not found" in error_msg or "404" in error_msg:
            raise VaultSecretNotFoundError(path) from e
        elif "unauthorized" in error_msg or "401" in error_msg:
            raise VaultAuthenticationError("Authentication failed") from e
        else:
            raise VaultOperationError(f"Azure Key Vault error: {e}") from e
    
    # ─────────────────────────────────────────────────────────────
    # ReadableVaultProvider implementation
    # ─────────────────────────────────────────────────────────────
    
    async def get_secret(self, reference: str) -> str:
        """Get a single secret value."""
        creds = await self.get_credentials(reference)
        
        # If reference has a fragment, return that key
        if "://" in reference:
            try:
                uri = parse_secret_uri(reference, allowed_mounts=None)
                if uri.fragment_key and uri.fragment_key in creds:
                    return str(creds[uri.fragment_key])
            except VaultOperationError:
                # URI parsing failed - fall through to return first value
                pass
        
        # Return first value
        if creds:
            return str(next(iter(creds.values())))
        
        raise VaultSecretNotFoundError(reference)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def get_credentials(self, reference: str) -> Dict[str, Any]:
        """Get credentials as dictionary.
        
        Azure Key Vault stores single values per secret, so we return
        a dictionary with the secret name as key.
        """
        with tracer.start_as_current_span("azure_keyvault.get_credentials") as span:
            # Parse URI if provided
            secret_name = reference
            version: Optional[str] = None
            fragment_key: Optional[str] = None
            
            if "://" in reference:
                try:
                    uri = parse_secret_uri(reference, allowed_mounts=None)
                    # Azure Key Vault uses flat namespace, secret name is first path segment
                    secret_name = uri.path_segments[0] if uri.path_segments else uri.mount
                    fragment_key = uri.fragment_key
                    
                    # Extract version from params
                    for k, v in uri.params:
                        if k == "version":
                            version = v
                            break
                except VaultOperationError as e:
                    span.set_attribute("error", True)
                    raise VaultOperationError(f"Invalid URI: {e}") from e
            
            span.set_attribute("secret.name_redacted", secret_name[:10] + "...")
            
            breaker = await self._get_circuit_breaker()
            client = self._get_client()
            
            async def _do_read() -> Dict[str, Any]:
                loop = asyncio.get_running_loop()
                if version:
                    secret = await loop.run_in_executor(
                        None,
                        lambda: client.get_secret(secret_name, version),
                    )
                else:
                    secret = await loop.run_in_executor(
                        None,
                        lambda: client.get_secret(secret_name),
                    )
                
                value = secret.value
                
                # If fragment specified, return just that key
                if fragment_key:
                    return {fragment_key: value}
                
                return {secret_name: value}
            
            try:
                return await breaker.execute(_do_read)
            except CircuitBreakerOpenError as e:
                span.set_attribute("error", True)
                raise VaultTimeoutError(f"Circuit open: {e}") from e
            except (VaultAuthorizationError, VaultSecretNotFoundError):
                span.set_attribute("error", True)
                raise
            except Exception as e:
                span.set_attribute("error", True)
                self._handle_azure_error(e, reference)
                raise  # Never reached, but makes type checker happy
    
    async def get_secret_or_none(self, reference: str) -> Optional[str]:
        """Get secret value or None if not found."""
        try:
            return await self.get_secret(reference)
        except VaultSecretNotFoundError:
            return None
    
    async def close(self) -> None:
        """Close provider resources."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
        self._client = None
        self._credential = None
        logger.info(
            "Azure Key Vault provider closed",
            extra={"component": "vault_provider"},
        )
    
    # ─────────────────────────────────────────────────────────────
    # WritableVaultProvider implementation
    # ─────────────────────────────────────────────────────────────
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def create_or_update_secret(
        self,
        path: str,
        data: Dict[str, Any],
        *,
        custom_metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create or update a secret.
        
        Note: Azure Key Vault stores single values, so we store the first
        value from the data dict, or JSON-encode if multiple keys.
        """
        import json
        
        with tracer.start_as_current_span("azure_keyvault.create_or_update_secret") as span:
            # Determine secret name from path
            secret_name = path.split("/")[-1] if "/" in path else path
            span.set_attribute("secret.name_redacted", secret_name[:10] + "...")
            
            # Determine value to store
            if len(data) == 1:
                value = str(next(iter(data.values())))
            else:
                # Multiple keys - store as JSON
                value = json.dumps(data)
            
            breaker = await self._get_circuit_breaker()
            client = self._get_client()
            
            async def _do_write() -> Dict[str, Any]:
                loop = asyncio.get_running_loop()
                
                # Set secret
                kwargs: Dict[str, Any] = {"tags": custom_metadata} if custom_metadata else {}
                secret = await loop.run_in_executor(
                    None,
                    lambda: client.set_secret(secret_name, value, **kwargs),
                )
                
                return {
                    "path": path,
                    "name": secret.name,
                    "version": secret.properties.version,
                }
            
            try:
                return await breaker.execute(_do_write)
            except CircuitBreakerOpenError as e:
                span.set_attribute("error", True)
                raise VaultTimeoutError(f"Circuit open: {e}") from e
            except Exception as e:
                span.set_attribute("error", True)
                self._handle_azure_error(e, path)
                raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )
    async def delete_secret(
        self,
        path: str,
        *,
        permanent: bool = False,
    ) -> None:
        """Delete a secret."""
        with tracer.start_as_current_span("azure_keyvault.delete_secret") as span:
            secret_name = path.split("/")[-1] if "/" in path else path
            span.set_attribute("secret.name_redacted", secret_name[:10] + "...")
            span.set_attribute("permanent", permanent)
            
            breaker = await self._get_circuit_breaker()
            client = self._get_client()
            
            async def _do_delete() -> None:
                loop = asyncio.get_running_loop()
                
                # Start deletion (soft delete by default in Azure)
                poller = await loop.run_in_executor(
                    None,
                    lambda: client.begin_delete_secret(secret_name),
                )
                
                # Wait for deletion
                await loop.run_in_executor(None, poller.wait)
                
                if permanent:
                    # Purge (permanent delete)
                    await loop.run_in_executor(
                        None,
                        lambda: client.purge_deleted_secret(secret_name),
                    )
            
            try:
                await breaker.execute(_do_delete)
            except CircuitBreakerOpenError as e:
                span.set_attribute("error", True)
                raise VaultTimeoutError(f"Circuit open: {e}") from e
            except Exception as e:
                span.set_attribute("error", True)
                self._handle_azure_error(e, path)
                raise
    
    # ─────────────────────────────────────────────────────────────
    # EnumerableVaultProvider implementation
    # ─────────────────────────────────────────────────────────────
    
    async def list_keys(self, path: str = "") -> List[str]:
        """List secret names."""
        with tracer.start_as_current_span("azure_keyvault.list_keys") as span:
            breaker = await self._get_circuit_breaker()
            client = self._get_client()
            
            async def _do_list() -> List[str]:
                loop = asyncio.get_running_loop()
                
                # List all secrets
                secrets = await loop.run_in_executor(
                    None,
                    lambda: list(client.list_properties_of_secrets()),
                )
                
                return [s.name for s in secrets]
            
            try:
                return await breaker.execute(_do_list)
            except CircuitBreakerOpenError as e:
                span.set_attribute("error", True)
                logger.warning(
                    "Circuit open for list_keys: %s",
                    e,
                    extra={"operation": "list_keys"},
                )
                return []
            except Exception as e:
                span.set_attribute("error", True)
                logger.warning(
                    "Error listing secrets: %s",
                    e,
                    extra={"operation": "list_keys"},
                )
                return []
    
    async def health_check(self) -> None:
        """Verify provider is healthy."""
        with tracer.start_as_current_span("azure_keyvault.health_check") as span:
            client = self._get_client()
            
            try:
                loop = asyncio.get_running_loop()
                
                # Try to list secrets (limited to 1) to verify connectivity
                await loop.run_in_executor(
                    None,
                    lambda: list(client.list_properties_of_secrets(max_page_size=1)),
                )
                
            except Exception as e:
                span.set_attribute("error", True)
                raise VaultConnectionError(f"Azure Key Vault health check failed: {e}") from e
