"""OpenBao/HashiCorp Vault provider implementation.

Full-featured provider supporting KV v2 secrets engine with:
- Read/write/delete operations
- Version management (soft delete, undelete, destroy)
- Custom metadata
- Response wrapping
- Circuit breaker protection

Per design §D: OpenBao KV v2 versioning operations preserved as extension methods.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)
from opentelemetry import trace

from empowernow_common.vault.base import FullVaultProvider, Capabilities
from empowernow_common.vault.uri import parse_secret_uri
from empowernow_common.vault.exceptions import (
    VaultAuthenticationError,
    VaultAuthorizationError,
    VaultConnectionError,
    VaultOperationError,
    VaultSecretNotFoundError,
    VaultSecretVersionDeletedError,
    VaultSecretVersionDestroyedError,
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


@dataclass
class OpenBaoConfig:
    """Configuration for OpenBao provider."""
    
    url: str
    token: Optional[str] = None
    role_id: Optional[str] = None
    secret_id: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = True
    pool_size: int = 10
    token_renewal_threshold: int = 600
    max_concurrent_operations: int = 50


class OpenBaoVaultProvider:
    """OpenBao/HashiCorp Vault provider implementing FullVaultProvider protocol.
    
    Pure async implementation using httpx HTTP client.
    Supports all KV v2 operations including versioning.
    
    Per Playbook §5: Uses empowernow_common.resilience.CircuitBreaker.
    """
    
    VAULT_TYPE = "openbao"
    CAPABILITIES = Capabilities.full_capabilities()
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize provider from configuration dict.
        
        Args:
            config: Configuration dictionary with keys:
                - url: Vault URL
                - token: Auth token (or use role_id/secret_id for AppRole)
                - role_id: AppRole role ID
                - secret_id: AppRole secret ID
                - timeout: Request timeout in seconds
                - verify_ssl: Verify TLS certificates
                - pool_size: HTTP connection pool size
                - token_renewal_threshold: Seconds before expiry to renew
                - cb_failure_threshold: Circuit breaker failure threshold
                - cb_reset_timeout_s: Circuit breaker reset timeout
        """
        self._config = OpenBaoConfig(
            url=config.get("url", "").rstrip("/"),
            token=config.get("token"),
            role_id=config.get("role_id"),
            secret_id=config.get("secret_id"),
            timeout=int(config.get("timeout", 30)),
            verify_ssl=config.get("verify_ssl", True),
            pool_size=int(config.get("pool_size", 10)),
            token_renewal_threshold=int(config.get("token_renewal_threshold", 600)),
            max_concurrent_operations=int(config.get("max_concurrent_operations", 50)),
        )
        
        # Circuit breaker config (lazy initialization)
        self._cb_config = CircuitBreakerConfig(
            threshold=int(config.get("cb_failure_threshold", 5)),
            timeout=float(config.get("cb_reset_timeout_s", 30)),
            window_seconds=60.0,
        )
        self._breaker: Optional[CircuitBreaker] = None
        
        # HTTP client limits
        self._client_limits = httpx.Limits(
            max_keepalive_connections=self._config.pool_size,
            max_connections=self._config.pool_size * 2,
            keepalive_expiry=30.0,
        )
        
        # Token management
        self._last_token_renewal = datetime.now()
        self._last_token_check = datetime.now()
        self._token_renewal_lock = asyncio.Lock()
        
        # Validate authentication at init
        self._setup_auth()
        
        logger.info(
            "OpenBao provider initialized: %s",
            self._config.url,
            extra={
                "component": "vault_provider",
                "provider_type": "openbao",
                "url": self._config.url,
            },
        )
    
    def _setup_auth(self) -> None:
        """Validate and setup authentication."""
        if not self._config.url:
            raise VaultConnectionError("OpenBao URL is required")
        
        if not self._config.token:
            if not (self._config.role_id and self._config.secret_id):
                raise VaultAuthenticationError(
                    "OpenBao authentication requires either:\n"
                    "  - A token, OR\n"
                    "  - AppRole credentials (role_id + secret_id)"
                )
            
            # Perform AppRole login
            self._approle_login_sync()
        
        # Validate token
        self._validate_token_sync()
    
    def _approle_login_sync(self) -> None:
        """Perform synchronous AppRole login (for init only)."""
        try:
            with httpx.Client(
                verify=self._config.verify_ssl,
                timeout=self._config.timeout,
            ) as client:
                response = client.post(
                    f"{self._config.url}/v1/auth/approle/login",
                    json={
                        "role_id": self._config.role_id,
                        "secret_id": self._config.secret_id,
                    },
                )
                response.raise_for_status()
                self._config.token = response.json()["auth"]["client_token"]
        except Exception as e:
            raise VaultAuthenticationError(
                f"AppRole login failed: {e}"
            ) from e
    
    def _validate_token_sync(self) -> None:
        """Validate token synchronously (for init only)."""
        try:
            with httpx.Client(
                verify=self._config.verify_ssl,
                timeout=self._config.timeout,
            ) as client:
                response = client.get(
                    f"{self._config.url}/v1/auth/token/lookup-self",
                    headers=self._get_headers(),
                )
                if response.status_code == 403:
                    raise VaultAuthenticationError("Invalid or expired token")
                response.raise_for_status()
        except VaultAuthenticationError:
            raise
        except Exception as e:
            raise VaultConnectionError(
                f"Failed to validate token: {e}"
            ) from e
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API calls."""
        return {
            "X-Vault-Token": self._config.token or "",
            "Content-Type": "application/json",
        }
    
    async def _get_circuit_breaker(self) -> CircuitBreaker:
        """Lazily initialize circuit breaker via registry."""
        if self._breaker is None:
            self._breaker = await get_circuit_breaker(
                f"vault_{self._config.url}",
                self._cb_config,
            )
        return self._breaker
    
    async def _check_token_renewal(self) -> None:
        """Check and renew token if needed."""
        now = datetime.now()
        
        # Rate limit: only check every 60 seconds
        if (now - self._last_token_check).total_seconds() < 60:
            return
        
        self._last_token_check = now
        
        try:
            async with httpx.AsyncClient(
                verify=self._config.verify_ssl,
                timeout=self._config.timeout,
                limits=self._client_limits,
            ) as client:
                response = await client.get(
                    f"{self._config.url}/v1/auth/token/lookup-self",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                token_info = response.json()
                ttl = token_info["data"]["ttl"]
                
                if ttl <= self._config.token_renewal_threshold:
                    async with self._token_renewal_lock:
                        if (datetime.now() - self._last_token_renewal).total_seconds() > 60:
                            response = await client.post(
                                f"{self._config.url}/v1/auth/token/renew-self",
                                headers=self._get_headers(),
                            )
                            response.raise_for_status()
                            self._last_token_renewal = datetime.now()
                            logger.info("Token renewed successfully")
        except Exception as e:
            logger.warning(
                "Token renewal check failed: %s",
                e,
                extra={"component": "vault_provider"},
            )
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path (strip leading 'secret/' if present)."""
        if path.startswith("secret/"):
            return path.split("/", 1)[1]
        return path
    
    # ─────────────────────────────────────────────────────────────
    # ReadableVaultProvider implementation
    # ─────────────────────────────────────────────────────────────
    
    async def get_secret(self, reference: str) -> str:
        """Get a single secret value.
        
        Per design Decision 3: Raises VaultSecretNotFoundError if not found.
        """
        creds = await self.get_credentials(reference)
        
        # If reference has a fragment, return that key
        if "://" in reference:
            uri = parse_secret_uri(reference, allowed_mounts=None)
            if uri.fragment_key and uri.fragment_key in creds:
                return str(creds[uri.fragment_key])
        
        # Return first value
        if creds:
            return str(next(iter(creds.values())))
        
        raise VaultSecretNotFoundError(reference)
    
    async def get_credentials(self, reference: str) -> Dict[str, Any]:
        """Get credentials as dictionary."""
        await self._check_token_renewal()
        
        # Parse URI if provided
        version: Optional[int] = None
        fragment_key: Optional[str] = None
        path = reference
        
        if "://" in reference:
            try:
                uri = parse_secret_uri(reference, allowed_mounts=None)
                path = "/".join(uri.path_segments)
                fragment_key = uri.fragment_key
                
                # Extract version from params
                for k, v in uri.params:
                    if k == "version":
                        version = int(v)
                        break
            except Exception as e:
                raise VaultOperationError(f"Invalid URI: {e}") from e
        
        # Read secret
        result = await self._read_secret(path, version=version)
        
        # Extract data
        inner = result.get("data", {})
        metadata = inner.get("metadata", {})
        
        # Check version status
        if version is not None:
            if metadata.get("destroyed") is True:
                raise VaultSecretVersionDestroyedError(path, version)
            deletion_time = metadata.get("deletion_time")
            if deletion_time and str(deletion_time).strip():
                raise VaultSecretVersionDeletedError(path, version)
        
        payload = inner.get("data")
        if payload is None:
            raise VaultOperationError("Malformed response from OpenBao")
        
        # Filter by fragment if specified
        if fragment_key:
            return {fragment_key: payload.get(fragment_key)} if isinstance(payload, dict) else {fragment_key: None}
        
        return payload
    
    async def get_secret_or_none(self, reference: str) -> Optional[str]:
        """Get secret value or None if not found."""
        try:
            return await self.get_secret(reference)
        except VaultSecretNotFoundError:
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _read_secret(
        self,
        path: str,
        version: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Read a secret from KV v2."""
        with tracer.start_as_current_span("openbao.read_secret") as span:
            norm_path = self._normalize_path(path)
            span.set_attribute("secret.path_redacted", norm_path[:20] + "...")
            
            breaker = await self._get_circuit_breaker()
            
            async def _do_read() -> Dict[str, Any]:
                async with httpx.AsyncClient(
                    verify=self._config.verify_ssl,
                    timeout=self._config.timeout,
                    limits=self._client_limits,
                ) as client:
                    url = f"{self._config.url}/v1/secret/data/{norm_path}"
                    if version is not None:
                        url += f"?version={version}"
                    
                    response = await client.get(url, headers=self._get_headers())
                    
                    if response.status_code == 403:
                        raise VaultAuthorizationError(f"Access denied", resource=path)
                    elif response.status_code == 404:
                        raise VaultSecretNotFoundError(path)
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    if not result or "data" not in result:
                        raise VaultOperationError("Invalid response format")
                    
                    return result
            
            try:
                return await breaker.execute(_do_read)
            except CircuitBreakerOpenError as e:
                span.set_attribute("error", True)
                raise VaultTimeoutError(f"Circuit open: {e}") from e
            except (VaultAuthorizationError, VaultSecretNotFoundError):
                span.set_attribute("error", True)
                raise
            except Exception as e:
                logger.error(
                    "Error reading secret: %s",
                    e,
                    extra={"operation": "read_secret"},
                )
                raise VaultOperationError(f"Failed to read secret: {e}") from e
    
    async def close(self) -> None:
        """Close provider resources."""
        logger.info(
            "OpenBao provider closed",
            extra={"component": "vault_provider"},
        )
    
    # ─────────────────────────────────────────────────────────────
    # WritableVaultProvider implementation
    # ─────────────────────────────────────────────────────────────
    
    async def create_or_update_secret(
        self,
        path: str,
        data: Dict[str, Any],
        *,
        custom_metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create or update a secret."""
        await self._check_token_renewal()
        norm_path = self._normalize_path(path)
        
        with tracer.start_as_current_span("openbao.write_secret") as span:
            span.set_attribute("secret.path_redacted", norm_path[:20] + "...")
            
            try:
                async with httpx.AsyncClient(
                    verify=self._config.verify_ssl,
                    timeout=self._config.timeout,
                    limits=self._client_limits,
                ) as client:
                    response = await client.post(
                        f"{self._config.url}/v1/secret/data/{norm_path}",
                        json={"data": data},
                        headers=self._get_headers(),
                    )
                    
                    if response.status_code == 403:
                        raise VaultAuthorizationError("Access denied", resource=path)
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    # Update custom metadata if provided
                    if custom_metadata:
                        await self._update_custom_metadata(norm_path, custom_metadata)
                    
                    return {
                        "path": path,
                        "version": result.get("data", {}).get("version"),
                    }
            except VaultAuthorizationError:
                raise
            except Exception as e:
                logger.error(
                    "Error writing secret: %s",
                    e,
                    extra={"operation": "write_secret"},
                )
                raise VaultOperationError(f"Failed to write secret: {e}") from e
    
    async def delete_secret(
        self,
        path: str,
        *,
        permanent: bool = False,
    ) -> None:
        """Delete a secret (soft or permanent)."""
        await self._check_token_renewal()
        norm_path = self._normalize_path(path)
        
        with tracer.start_as_current_span("openbao.delete_secret") as span:
            span.set_attribute("secret.path_redacted", norm_path[:20] + "...")
            span.set_attribute("permanent", permanent)
            
            try:
                async with httpx.AsyncClient(
                    verify=self._config.verify_ssl,
                    timeout=self._config.timeout,
                    limits=self._client_limits,
                ) as client:
                    if permanent:
                        # Destroy all versions
                        response = await client.delete(
                            f"{self._config.url}/v1/secret/metadata/{norm_path}",
                            headers=self._get_headers(),
                        )
                    else:
                        # Soft delete latest
                        response = await client.delete(
                            f"{self._config.url}/v1/secret/data/{norm_path}",
                            headers=self._get_headers(),
                        )
                    
                    if response.status_code == 403:
                        raise VaultAuthorizationError("Access denied", resource=path)
                    elif response.status_code == 404:
                        raise VaultSecretNotFoundError(path)
                    
                    response.raise_for_status()
                    
            except (VaultAuthorizationError, VaultSecretNotFoundError):
                raise
            except Exception as e:
                logger.error(
                    "Error deleting secret: %s",
                    e,
                    extra={"operation": "delete_secret"},
                )
                raise VaultOperationError(f"Failed to delete secret: {e}") from e
    
    # ─────────────────────────────────────────────────────────────
    # EnumerableVaultProvider implementation
    # ─────────────────────────────────────────────────────────────
    
    async def list_keys(self, path: str = "") -> List[str]:
        """List keys at path."""
        await self._check_token_renewal()
        norm_path = self._normalize_path(path) if path else ""
        
        try:
            async with httpx.AsyncClient(
                verify=self._config.verify_ssl,
                timeout=self._config.timeout,
                limits=self._client_limits,
            ) as client:
                response = await client.request(
                    "LIST",
                    f"{self._config.url}/v1/secret/metadata/{norm_path}",
                    headers=self._get_headers(),
                )
                
                if response.status_code == 404:
                    return []  # Empty directory
                
                response.raise_for_status()
                return response.json().get("data", {}).get("keys", [])
                
        except Exception as e:
            logger.warning(
                "Error listing keys: %s",
                e,
                extra={"operation": "list_keys"},
            )
            return []
    
    # ─────────────────────────────────────────────────────────────
    # KV v2 Extension Methods (per design §D)
    # ─────────────────────────────────────────────────────────────
    
    async def get_secret_version(self, path: str, version: int) -> str:
        """Get specific version of secret."""
        return await self.get_secret(f"{path}?version={version}")
    
    async def soft_delete_versions(self, path: str, versions: List[int]) -> None:
        """Soft-delete specific versions (recoverable)."""
        norm_path = self._normalize_path(path)
        
        async with httpx.AsyncClient(
            verify=self._config.verify_ssl,
            timeout=self._config.timeout,
            limits=self._client_limits,
        ) as client:
            response = await client.post(
                f"{self._config.url}/v1/secret/delete/{norm_path}",
                json={"versions": versions},
                headers=self._get_headers(),
            )
            response.raise_for_status()
    
    async def undelete_versions(self, path: str, versions: List[int]) -> None:
        """Recover soft-deleted versions."""
        norm_path = self._normalize_path(path)
        
        async with httpx.AsyncClient(
            verify=self._config.verify_ssl,
            timeout=self._config.timeout,
            limits=self._client_limits,
        ) as client:
            response = await client.post(
                f"{self._config.url}/v1/secret/undelete/{norm_path}",
                json={"versions": versions},
                headers=self._get_headers(),
            )
            
            if response.status_code == 403:
                raise VaultAuthorizationError("Access denied", resource=path)
            elif response.status_code == 404:
                raise VaultSecretNotFoundError(path)
            
            response.raise_for_status()
    
    async def destroy_versions(self, path: str, versions: List[int]) -> None:
        """Permanently destroy specific versions."""
        norm_path = self._normalize_path(path)
        
        async with httpx.AsyncClient(
            verify=self._config.verify_ssl,
            timeout=self._config.timeout,
            limits=self._client_limits,
        ) as client:
            response = await client.post(
                f"{self._config.url}/v1/secret/destroy/{norm_path}",
                json={"versions": versions},
                headers=self._get_headers(),
            )
            
            if response.status_code == 403:
                raise VaultAuthorizationError("Access denied", resource=path)
            elif response.status_code == 404:
                raise VaultSecretNotFoundError(path)
            
            response.raise_for_status()
    
    async def destroy_all_versions(self, path: str) -> None:
        """Permanently destroy all versions."""
        await self.delete_secret(path, permanent=True)
    
    async def read_secret_metadata(self, path: str) -> Dict[str, Any]:
        """Read secret metadata (versions, deletion status, etc.)."""
        norm_path = self._normalize_path(path)
        await self._check_token_renewal()
        
        try:
            async with httpx.AsyncClient(
                verify=self._config.verify_ssl,
                timeout=self._config.timeout,
                limits=self._client_limits,
            ) as client:
                response = await client.get(
                    f"{self._config.url}/v1/secret/metadata/{norm_path}",
                    headers=self._get_headers(),
                )
                
                if response.status_code == 404:
                    raise VaultSecretNotFoundError(path)
                
                response.raise_for_status()
                resp = response.json()
            
            meta = resp.get("data", {})
            versions_map = meta.get("versions", {}) or {}
            
            versions = []
            for ver_str, vinfo in versions_map.items():
                try:
                    ver = int(ver_str)
                except Exception:
                    continue
                versions.append({
                    "version": ver,
                    "created_time": vinfo.get("created_time"),
                    "deletion_time": vinfo.get("deletion_time"),
                    "destroyed": bool(vinfo.get("destroyed")),
                })
            
            versions.sort(key=lambda x: x["version"], reverse=True)
            
            return {
                "current_version": meta.get("current_version"),
                "oldest_version": meta.get("oldest_version"),
                "max_versions": meta.get("max_versions"),
                "versions": versions,
                "custom_metadata": meta.get("custom_metadata", {}) or {},
            }
            
        except VaultSecretNotFoundError:
            raise
        except Exception as e:
            raise VaultOperationError(f"Failed to read metadata: {e}") from e
    
    async def _update_custom_metadata(
        self,
        path: str,
        custom: Dict[str, str],
        merge: bool = True,
    ) -> None:
        """Update custom metadata on a secret."""
        existing: Dict[str, str] = {}
        
        if merge:
            try:
                meta = await self.read_secret_metadata(path)
                existing = meta.get("custom_metadata", {})
            except VaultSecretNotFoundError:
                pass
        
        new_meta = {**existing, **custom} if merge else custom
        
        # Sanitize: Vault requires string values
        sanitized = {str(k): str(v) for k, v in new_meta.items() if v is not None}
        
        async with httpx.AsyncClient(
            verify=self._config.verify_ssl,
            timeout=self._config.timeout,
            limits=self._client_limits,
        ) as client:
            response = await client.post(
                f"{self._config.url}/v1/secret/metadata/{path}",
                json={"custom_metadata": sanitized},
                headers=self._get_headers(),
            )
            response.raise_for_status()
    
    async def health_check(self) -> None:
        """Verify provider is healthy."""
        async with httpx.AsyncClient(
            verify=self._config.verify_ssl,
            timeout=5.0,
            limits=self._client_limits,
        ) as client:
            response = await client.get(
                f"{self._config.url}/v1/sys/health",
                headers=self._get_headers(),
            )
            # Health endpoint returns 200/429/472/473/501/503
            # 200 = initialized, unsealed, active
            if response.status_code not in (200, 429):
                raise VaultConnectionError(
                    f"Vault unhealthy: status {response.status_code}"
                )
