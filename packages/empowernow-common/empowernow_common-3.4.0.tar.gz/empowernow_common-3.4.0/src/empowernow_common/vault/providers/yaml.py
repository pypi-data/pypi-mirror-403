"""YAML file-based vault provider (development only).

Simple provider for local development that reads secrets from a YAML file.
NOT for production use - provides no encryption or access control.

Supports hot-reload of secrets file for rapid development iteration.
"""
from __future__ import annotations

import io
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml

from empowernow_common.vault.base import EnumerableVaultProvider, Capabilities
from empowernow_common.vault.uri import parse_secret_uri
from empowernow_common.vault.exceptions import (
    VaultSecretNotFoundError,
    VaultOperationError,
)


logger = logging.getLogger(__name__)


@dataclass
class YAMLCache:
    """Cache entry for loaded YAML data."""
    
    mtime: float
    data: Dict[str, Any]


class YAMLVaultProvider:
    """YAML file-based vault provider for development.
    
    Implements EnumerableVaultProvider (read + list, no write/delete).
    
    Configuration:
        - path: Path to YAML secrets file
        - reload_interval_s: Minimum seconds between file reloads
    
    YAML Format:
        mount_name:
          path:
            to:
              secret:
                key1: value1
                key2: value2
    
    Usage:
        provider = YAMLVaultProvider({
            "path": "/app/dev_secrets.yaml",
            "reload_interval_s": 2,
        })
        
        creds = await provider.get_credentials("yaml://secret/app#token")
    """
    
    VAULT_TYPE = "yaml"
    CAPABILITIES = Capabilities.yaml_capabilities()
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize YAML provider.
        
        Args:
            config: Configuration dictionary with keys:
                - path: Path to YAML file (default: YAML_VAULT_PATH env or ./dev_secrets.yaml)
                - reload_interval_s: Reload interval (default: 2)
        """
        self._yaml_path: str = (
            config.get("path")
            or os.getenv("YAML_VAULT_PATH", "./dev_secrets.yaml")
        )
        self._reload_interval_s: float = float(
            config.get("reload_interval_s")
            or os.getenv("YAML_VAULT_RELOAD_INTERVAL_S", "2")
        )
        self._cache: Optional[YAMLCache] = None
        
        logger.info(
            "YAML provider initialized: %s (dev only)",
            self._yaml_path,
            extra={
                "component": "vault_provider",
                "provider_type": "yaml",
                "path": self._yaml_path,
            },
        )
    
    def _load_yaml(self) -> Dict[str, Any]:
        """Load YAML file with caching."""
        path = self._yaml_path
        
        if not os.path.isfile(path):
            logger.warning("YAML secrets file not found: %s", path)
            return {}
        
        stat = os.stat(path)
        
        # Return cached data if file hasn't changed
        if self._cache and self._cache.mtime == stat.st_mtime:
            return self._cache.data
        
        with io.open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                data = {}
        
        self._cache = YAMLCache(mtime=stat.st_mtime, data=data)
        return data
    
    def _resolve_path(self, segments: List[str], data: Dict[str, Any]) -> Any:
        """Resolve a path through nested dictionaries."""
        node: Any = data
        
        for seg in segments:
            if not isinstance(node, dict):
                return {}
            node = node.get(seg, {})
        
        return node
    
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
    
    async def get_credentials(self, reference: str) -> Dict[str, Any]:
        """Get credentials as dictionary."""
        # Parse URI format: yaml://mount/path/to/secret#fragment
        if reference.startswith("yaml://"):
            path_part = reference.split("://", 1)[1]
            path_and_frag = path_part.split("#", 1)
            path = path_and_frag[0]
            frag = path_and_frag[1] if len(path_and_frag) > 1 else None
            
            segments = [seg for seg in path.split("/") if seg]
            if not segments:
                raise VaultOperationError("Invalid YAML credential path")
            
            data = self._load_yaml()
            node = self._resolve_path(segments, data)
            
            if not isinstance(node, dict):
                if node is not None and frag:
                    return {frag: node}
                return {}
            
            if frag:
                val = node.get(frag)
                if val is None:
                    raise VaultSecretNotFoundError(reference)
                if isinstance(val, dict):
                    return val
                return {frag: val}
            
            return node if isinstance(node, dict) else {}
        
        # Try JSON pointer format
        try:
            obj = json.loads(reference)
        except Exception:
            obj = None
        
        if isinstance(obj, dict) and obj.get("vault_type") == "yaml":
            mount = obj.get("mount") or "secrets"
            full_path = [mount] + [seg for seg in (obj.get("path") or "").split("/") if seg]
            frag = obj.get("fragment")
            
            data = self._load_yaml()
            node = self._resolve_path(full_path, data)
            
            if not isinstance(node, dict):
                node = {}
            
            if frag:
                val = node.get(frag)
                if val is None:
                    raise VaultSecretNotFoundError(reference)
                if isinstance(val, dict):
                    return val
                return {frag: val}
            
            return node if isinstance(node, dict) else {}
        
        raise VaultOperationError("Unsupported YAML credential reference format")
    
    async def get_secret_or_none(self, reference: str) -> Optional[str]:
        """Get secret value or None if not found."""
        try:
            return await self.get_secret(reference)
        except VaultSecretNotFoundError:
            return None
    
    async def close(self) -> None:
        """Close provider resources."""
        self._cache = None
        logger.info(
            "YAML provider closed",
            extra={"component": "vault_provider"},
        )
    
    # ─────────────────────────────────────────────────────────────
    # EnumerableVaultProvider implementation
    # ─────────────────────────────────────────────────────────────
    
    async def list_keys(self, path: str = "") -> List[str]:
        """List keys at path."""
        data = self._load_yaml()
        results: List[str] = []
        
        def _walk(prefix: str, node: Any) -> None:
            if isinstance(node, dict):
                for k, v in node.items():
                    new_prefix = f"{prefix}/{k}" if prefix else k
                    results.append(new_prefix)
                    _walk(new_prefix, v)
        
        if path:
            segments = [seg for seg in path.split("/") if seg]
            node = self._resolve_path(segments, data)
            if isinstance(node, dict):
                _walk(path.rstrip("/"), node)
        else:
            _walk("", data)
        
        return results
    
    async def health_check(self) -> None:
        """Verify provider is healthy (file exists)."""
        if not os.path.isfile(self._yaml_path):
            raise VaultOperationError(f"YAML file not found: {self._yaml_path}")
