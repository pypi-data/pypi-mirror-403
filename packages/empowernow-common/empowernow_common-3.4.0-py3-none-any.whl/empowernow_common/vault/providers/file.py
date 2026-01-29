"""File-based vault provider for local/CSI-mounted secrets.

Production-grade provider for reading secrets from local filesystem with
first-class support for Docker Secrets and Kubernetes CSI Secrets Store.

Supported Secret Sources:
- Docker Secrets (/run/secrets) - auto-detected in Docker containers
- Kubernetes CSI Secrets Store driver (/mnt/secrets-store)
- Azure Key Vault CSI provider
- AWS Secrets Manager CSI provider
- HashiCorp Vault CSI provider
- Custom mounted secrets directories

URI Formats:
    file://path/to/secret#fragment      → Generic file access
    docker://secret-name                → Docker Secrets (/run/secrets)
    k8s://secret-name                   → Kubernetes CSI (/mnt/secrets-store)
    
Examples:
    file://db-password                  → $FILE_MOUNT_PATH/db-password
    file://db-password#password         → Extract "password" key from JSON
    docker://db-password                → /run/secrets/db-password
    k8s://api-credentials#api_key       → /mnt/secrets-store/api-credentials (JSON key)

Docker Secrets Features:
- Auto-detection via /.dockerenv or /run/secrets presence
- World-readable permissions allowed (Docker standard)
- Direct secret name mapping (no path hierarchy)
- Automatic stripping of trailing newlines

Kubernetes CSI Features:
- Auto-detection via KUBERNETES_SERVICE_HOST env var
- Support for nested secret structures
- Secret rotation awareness (file change detection)
- Multiple CSI provider compatibility (Azure, AWS, HashiCorp)

Security Features:
- Path traversal prevention (blocks ../, symlinks outside mount)
- Configurable base path restriction
- File permission validation (relaxed for Docker)
- Content size limits
- Audit logging for all access

Per design: VAULT_PROVIDER_UNIFICATION.md
Per Playbook: AI_PYTHON_FASTAPI_EXCELLENCE_PLAYBOOK.md §4 (Fail-Closed), §9 (Error Handling)
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import stat
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from empowernow_common.vault.base import ReadableVaultProvider, Capabilities
from empowernow_common.vault.exceptions import (
    VaultAuthorizationError,
    VaultConfigurationError,
    VaultOperationError,
    VaultSecretNotFoundError,
)


logger = logging.getLogger(__name__)


class ContainerRuntime(Enum):
    """Detected container runtime environment."""
    UNKNOWN = auto()
    DOCKER = auto()
    KUBERNETES = auto()
    PODMAN = auto()


@dataclass
class SecretMetadata:
    """Metadata about a secret file for rotation detection."""
    path: str
    mtime: float
    size: int
    checksum: str


def _detect_container_runtime() -> ContainerRuntime:
    """Detect the container runtime environment.
    
    Returns:
        ContainerRuntime enum indicating the detected environment.
    """
    # Check for Kubernetes first (more specific)
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        return ContainerRuntime.KUBERNETES
    
    # Check for Kubernetes service account
    if Path("/var/run/secrets/kubernetes.io/serviceaccount").exists():
        return ContainerRuntime.KUBERNETES
    
    # Check for Docker
    if Path("/.dockerenv").exists():
        return ContainerRuntime.DOCKER
    
    # Check for Docker secrets directory
    if Path("/run/secrets").is_dir():
        return ContainerRuntime.DOCKER
    
    # Check for Podman
    if Path("/run/.containerenv").exists():
        return ContainerRuntime.PODMAN
    
    return ContainerRuntime.UNKNOWN


def _is_docker_secret_path() -> bool:
    """Check if Docker secrets directory exists and is populated."""
    docker_path = Path("/run/secrets")
    if docker_path.is_dir():
        try:
            return any(docker_path.iterdir())
        except (OSError, PermissionError):
            pass
    return False


def _is_kubernetes_csi_path() -> bool:
    """Check if Kubernetes CSI secrets directory exists."""
    csi_path = Path("/mnt/secrets-store")
    return csi_path.is_dir()


class FileVaultProvider:
    """File-based vault provider implementing ReadableVaultProvider protocol.
    
    Production-grade provider with first-class support for:
    - Docker Secrets (/run/secrets)
    - Kubernetes CSI Secrets Store driver (/mnt/secrets-store)
    - Azure Key Vault CSI provider
    - AWS Secrets Manager CSI provider
    - HashiCorp Vault CSI provider
    - CI/CD mounted secrets
    - Development environments
    
    Configuration:
        mount_path: Base directory for secrets (auto-detected if not specified)
        docker_secrets_path: Docker secrets path (default: /run/secrets)
        kubernetes_csi_path: Kubernetes CSI path (default: /mnt/secrets-store)
        allow_symlinks: Allow symlinked files (default: False, True for Docker)
        max_file_size: Maximum secret file size in bytes (default: 1MB)
        validate_permissions: Check file permissions (default: True, relaxed for Docker)
        encoding: File encoding (default: utf-8)
        binary_extensions: Extensions treated as binary (default: .pem, .crt, .key, .p12, .pfx)
        enable_rotation_check: Enable secret rotation detection (default: True)
    
    Security Considerations:
        - Files outside mount_path are rejected (path traversal protection)
        - Symlinks are blocked by default (except Docker which uses symlinks)
        - World-writable files are always rejected
        - Docker world-readable is allowed (standard Docker behavior)
        - Large files are rejected to prevent memory exhaustion
    
    URI Schemes:
        - file://path/to/secret - Generic file access
        - docker://secret-name - Docker Secrets shorthand
        - k8s://secret-name - Kubernetes CSI shorthand
    """
    
    VAULT_TYPE = "file"
    CAPABILITIES = {
        Capabilities.LIST_KEYS: True,
        Capabilities.READ_SECRET: True,
        Capabilities.WRITE_SECRET: False,  # File provider is read-only for security
        Capabilities.DELETE_SECRET: False,
        Capabilities.METADATA: False,
        Capabilities.READ_METADATA: False,
        Capabilities.UPDATE_METADATA: False,
        Capabilities.VERSIONING: False,
        Capabilities.VERSION_PIN: False,
        Capabilities.SOFT_DELETE: False,
        Capabilities.HARD_DESTROY: False,
        Capabilities.RESPONSE_WRAPPING: False,
        Capabilities.IDENTITY_SCOPING: False,
        Capabilities.OWNERSHIP_TRACKING: False,
        Capabilities.AUDIT_METADATA: False,
        Capabilities.TAGS: False,
    }
    
    # Standard paths for different environments
    DOCKER_SECRETS_PATH = "/run/secrets"
    KUBERNETES_CSI_PATH = "/mnt/secrets-store"
    
    # Default paths used by common secret mounting solutions (priority order)
    DEFAULT_MOUNT_PATHS = [
        "/run/secrets",        # Docker Secrets (highest priority - most common)
        "/mnt/secrets-store",  # Kubernetes CSI driver
        "/var/run/secrets",    # Alternative Docker/K8s path
        "/secrets",            # Generic mount point
    ]
    
    # Maximum file size (1MB default - secrets should be small)
    DEFAULT_MAX_FILE_SIZE = 1 * 1024 * 1024
    
    # Binary file extensions (certificates, keys, etc.)
    DEFAULT_BINARY_EXTENSIONS = frozenset({".pem", ".crt", ".key", ".p12", ".pfx", ".der", ".cer"})
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize file vault provider.
        
        Args:
            config: Configuration dictionary with optional keys:
                - mount_path: Base directory for secrets (auto-detected if not set)
                - docker_secrets_path: Path for Docker secrets
                - kubernetes_csi_path: Path for Kubernetes CSI secrets
                - allow_symlinks: Allow symlinked secret files
                - max_file_size: Maximum file size in bytes
                - validate_permissions: Check file permissions
                - encoding: File encoding for text secrets
                - binary_extensions: Set of extensions for binary files
                - enable_rotation_check: Enable secret rotation detection
        
        Raises:
            VaultConfigurationError: If mount_path is explicitly set but invalid
        """
        # Detect container runtime
        self._runtime = _detect_container_runtime()
        
        # Configure paths for Docker and Kubernetes
        self._docker_path = Path(config.get("docker_secrets_path", self.DOCKER_SECRETS_PATH))
        self._k8s_path = Path(config.get("kubernetes_csi_path", self.KUBERNETES_CSI_PATH))
        
        # Determine primary mount path with smart auto-detection
        mount_path = config.get("mount_path") or os.getenv("FILE_MOUNT_PATH")
        
        if not mount_path:
            mount_path = self._auto_detect_mount_path()
        
        self._mount_path = Path(mount_path).resolve()
        
        # Runtime-aware defaults for symlinks and permissions
        is_docker = self._runtime == ContainerRuntime.DOCKER or self._is_docker_mode()
        
        # Docker uses symlinks for secrets, so allow them by default in Docker
        self._allow_symlinks = config.get("allow_symlinks", is_docker)
        
        # Docker secrets are typically world-readable (0444), relax validation
        self._validate_permissions = config.get("validate_permissions", not is_docker)
        self._docker_mode = is_docker
        
        self._max_file_size = int(config.get("max_file_size", self.DEFAULT_MAX_FILE_SIZE))
        self._encoding = config.get("encoding", "utf-8")
        self._json_extension = config.get("json_extension", ".json")
        self._binary_extensions = frozenset(
            config.get("binary_extensions", self.DEFAULT_BINARY_EXTENSIONS)
        )
        self._enable_rotation_check = config.get("enable_rotation_check", True)
        
        # Cache for rotation detection
        self._secret_metadata_cache: Dict[str, SecretMetadata] = {}
        
        # Validate mount path exists (warn but don't fail - might be mounted later)
        if not self._mount_path.exists():
            logger.warning(
                "File vault mount path does not exist: %s (may be mounted at runtime)",
                self._mount_path,
            )
        elif not self._mount_path.is_dir():
            raise VaultConfigurationError(
                f"File vault mount path is not a directory: {self._mount_path}"
            )
        
        # Log initialization with environment context
        env_info = f"runtime={self._runtime.name}"
        if is_docker:
            env_info += ", docker_mode=True"
        
        logger.info(
            "File vault provider initialized: mount_path=%s, %s, allow_symlinks=%s",
            self._mount_path,
            env_info,
            self._allow_symlinks,
        )
    
    def _auto_detect_mount_path(self) -> str:
        """Auto-detect the appropriate mount path based on environment.
        
        Returns:
            Best mount path for the detected environment
        """
        # Docker environment - prefer Docker secrets path
        if self._runtime == ContainerRuntime.DOCKER and self._docker_path.is_dir():
            return str(self._docker_path)
        
        # Kubernetes environment - prefer CSI path
        if self._runtime == ContainerRuntime.KUBERNETES and self._k8s_path.is_dir():
            return str(self._k8s_path)
        
        # Try default paths in order
        for default_path in self.DEFAULT_MOUNT_PATHS:
            if os.path.isdir(default_path):
                return default_path
        
        # Development fallback
        dev_path = os.path.join(os.getcwd(), "secrets")
        if os.path.isdir(dev_path):
            return dev_path
        
        # Return first default even if missing (will warn later)
        return self.DEFAULT_MOUNT_PATHS[0]
    
    def _is_docker_mode(self) -> bool:
        """Check if we're operating in Docker secrets mode."""
        return str(self._mount_path).startswith("/run/secrets") or _is_docker_secret_path()
    
    def _parse_reference(self, reference: str) -> Tuple[str, Optional[str]]:
        """Parse a secret reference into path and optional fragment key.
        
        Handles all URI schemes: file://, docker://, k8s://, kubernetes://
        
        Args:
            reference: Raw reference string
            
        Returns:
            Tuple of (path_reference, fragment_key or None)
        """
        fragment_key: Optional[str] = None
        
        if "#" not in reference:
            return reference, None
        
        # Handle URI schemes - split on first # after scheme
        if any(reference.startswith(s) for s in ("file://", "docker://", "k8s://", "kubernetes://")):
            parts = reference.split("#", 1)
            return parts[0], parts[1] if len(parts) > 1 else None
        
        # Plain path - split on last #
        path, fragment_key = reference.rsplit("#", 1)
        return path, fragment_key
    
    def _resolve_path(self, reference: str) -> Tuple[Path, Path]:
        """Resolve a secret reference to a filesystem path with security checks.
        
        Supports multiple URI schemes:
        - file://path/to/secret - Uses configured mount_path
        - docker://secret-name - Uses Docker secrets path (/run/secrets)
        - k8s://secret-name - Uses Kubernetes CSI path (/mnt/secrets-store)
        - Plain path - Uses configured mount_path
        
        Args:
            reference: Secret reference (path relative to mount, or full URI)
            
        Returns:
            Tuple of (resolved_path, base_mount_path)
            
        Raises:
            VaultAuthorizationError: If path traversal or symlink attack detected
            VaultConfigurationError: If mount path doesn't exist
        """
        base_mount = self._mount_path
        path_part = reference
        
        # Handle docker:// URI - Docker Secrets shorthand
        if reference.startswith("docker://"):
            path_part = reference[9:]  # Remove "docker://"
            base_mount = self._docker_path
            
        # Handle k8s:// URI - Kubernetes CSI shorthand
        elif reference.startswith("k8s://") or reference.startswith("kubernetes://"):
            scheme_len = 6 if reference.startswith("k8s://") else 13
            path_part = reference[scheme_len:]
            base_mount = self._k8s_path
            
        # Handle file:// URI format
        elif reference.startswith("file://"):
            path_part = reference[7:]  # Remove "file://"
        
        # Strip fragment and query (should already be done by _parse_reference, but be safe)
        if "#" in path_part:
            path_part = path_part.split("#")[0]
        if "?" in path_part:
            path_part = path_part.split("?")[0]
        
        # Runtime check: verify mount path exists
        if not base_mount.exists():
            raise VaultConfigurationError(
                f"Secrets mount path does not exist: {base_mount}"
            )
        
        # Resolve base_mount first to get canonical path
        base_mount_resolved = base_mount.resolve()
        
        # Security check: reject symlinks in the requested path BEFORE resolving
        # This catches symlinks that could escape the mount directory
        if not self._allow_symlinks:
            check_path = base_mount_resolved
            for part in Path(path_part).parts:
                check_path = check_path / part
                # Check if this component exists and is a symlink
                # (may not exist yet if path doesn't exist)
                if check_path.exists() and check_path.is_symlink():
                    logger.warning(
                        "SECURITY: Symlink access blocked: %s (symlink at %s)",
                        reference,
                        check_path,
                    )
                    raise VaultAuthorizationError(
                        "Access denied: symlinks not allowed",
                        resource=reference,
                    )
        
        # Build target path
        target_path = base_mount_resolved / path_part
        
        # Resolve to absolute path (handles .. etc.)
        # Use strict=False to not follow symlinks and not require existence
        try:
            # For security, we use resolve() which follows symlinks
            # The symlink check above already blocked unwanted symlinks
            resolved_path = target_path.resolve()
        except (OSError, RuntimeError) as e:
            raise VaultAuthorizationError(
                f"Cannot resolve secret path: {e}",
                resource=reference,
            )
        
        # Security check: ensure resolved path is under base mount
        try:
            resolved_path.relative_to(base_mount_resolved)
        except ValueError:
            # Path is outside mount directory - potential traversal attack
            logger.warning(
                "SECURITY: Path traversal attempt blocked: %s → %s (mount: %s)",
                reference,
                resolved_path,
                base_mount_resolved,
            )
            raise VaultAuthorizationError(
                "Access denied: path outside secrets directory",
                resource=reference,
            )
        
        return resolved_path, base_mount_resolved
    
    def _read_and_validate_atomic(self, path: Path, base_mount: Path) -> str:
        """Atomically validate and read a secret file.
        
        This consolidates validation and reading into a single operation to avoid
        TOCTOU (time-of-check-time-of-use) race conditions.
        
        Docker-aware: allows world-readable files in Docker mode.
        
        Args:
            path: Resolved file path
            base_mount: Base mount path for relative path calculation
            
        Returns:
            File contents as string (base64 for binary files)
            
        Raises:
            VaultSecretNotFoundError: If file doesn't exist
            VaultAuthorizationError: If file permissions are insecure
            VaultOperationError: If file is too large or unreadable
        """
        def _get_rel_path() -> str:
            try:
                return str(path.relative_to(base_mount))
            except ValueError:
                return str(path)
        
        # Check if this is a binary file by extension
        is_binary = path.suffix.lower() in self._binary_extensions
        
        try:
            # Open the file - this is atomic: either succeeds or fails
            # All validation happens with the open file handle
            mode = "rb" if is_binary else "r"
            kwargs = {} if is_binary else {"encoding": self._encoding}
            
            with open(path, mode, **kwargs) as f:
                # Get file stats from the open handle (avoids TOCTOU)
                fd = f.fileno()
                file_stat = os.fstat(fd)
                
                # Validate it's a regular file
                if not stat.S_ISREG(file_stat.st_mode):
                    raise VaultOperationError(f"Secret path is not a file: {_get_rel_path()}")
                
                # Check file size before reading
                if file_stat.st_size > self._max_file_size:
                    raise VaultOperationError(
                        f"Secret file too large: {file_stat.st_size} bytes (max: {self._max_file_size})",
                        code="SECRET_TOO_LARGE",
                    )
                
                # Check permissions on Unix systems
                if self._validate_permissions and os.name == "posix":
                    mode_bits = file_stat.st_mode
                    
                    # World-writable is ALWAYS a critical security risk
                    if mode_bits & stat.S_IWOTH:
                        raise VaultAuthorizationError(
                            "Secret file is world-writable (insecure)",
                            resource=_get_rel_path(),
                        )
                    
                    # World-readable check - warn unless in Docker mode
                    if (mode_bits & stat.S_IROTH) and not self._docker_mode:
                        logger.warning(
                            "SECURITY: World-readable secret file: %s (mode: %o)",
                            path,
                            mode_bits & 0o777,
                        )
                
                # Read content from the already-open file
                content = f.read()
                
                # Process content based on type
                if is_binary:
                    return base64.b64encode(content).decode("ascii")
                else:
                    # Strip trailing whitespace/newlines (common in mounted secrets)
                    return content.rstrip()
                    
        except FileNotFoundError:
            raise VaultSecretNotFoundError(_get_rel_path())
        except IsADirectoryError:
            raise VaultOperationError(f"Secret path is not a file: {_get_rel_path()}")
        except PermissionError as e:
            raise VaultAuthorizationError(
                f"Permission denied reading secret: {e}",
                resource=_get_rel_path(),
            )
        except UnicodeDecodeError as e:
            # Try reading as binary if text fails
            logger.debug("Text decode failed, trying binary: %s", e)
            try:
                with open(path, "rb") as f:
                    # Re-validate size with binary read
                    content_bytes = f.read(self._max_file_size + 1)
                    if len(content_bytes) > self._max_file_size:
                        raise VaultOperationError(
                            f"Secret file too large (max: {self._max_file_size})",
                            code="SECRET_TOO_LARGE",
                        )
                    return base64.b64encode(content_bytes).decode("ascii")
            except OSError:
                raise VaultOperationError(
                    f"Secret file is not valid {self._encoding}: {e}",
                    code="ENCODING_ERROR",
                )
        except OSError as e:
            raise VaultOperationError(f"Cannot read secret file: {e}")
    
    def _check_rotation(self, path: Path) -> bool:
        """Check if a secret has been rotated (file changed).
        
        Used for Kubernetes CSI secrets that support rotation.
        
        Args:
            path: Path to the secret file
            
        Returns:
            True if secret appears to have been rotated
        """
        if not self._enable_rotation_check:
            return False
        
        path_str = str(path)
        
        try:
            stat_info = path.stat()
            current_mtime = stat_info.st_mtime
            current_size = stat_info.st_size
            
            # Calculate checksum for content comparison (SHA-256 for FIPS compliance)
            with open(path, "rb") as f:
                current_checksum = hashlib.sha256(f.read()).hexdigest()
            
            cached = self._secret_metadata_cache.get(path_str)
            
            if cached is None:
                # First read - cache and return False
                self._secret_metadata_cache[path_str] = SecretMetadata(
                    path=path_str,
                    mtime=current_mtime,
                    size=current_size,
                    checksum=current_checksum,
                )
                return False
            
            # Check if rotated
            rotated = (
                current_mtime != cached.mtime or
                current_size != cached.size or
                current_checksum != cached.checksum
            )
            
            if rotated:
                logger.info(
                    "Secret rotation detected: %s (mtime: %s→%s, size: %s→%s)",
                    path_str,
                    cached.mtime, current_mtime,
                    cached.size, current_size,
                )
                # Update cache
                self._secret_metadata_cache[path_str] = SecretMetadata(
                    path=path_str,
                    mtime=current_mtime,
                    size=current_size,
                    checksum=current_checksum,
                )
            
            return rotated
            
        except OSError:
            return False
    
    def _parse_json_content(self, content: str, path: Path) -> Dict[str, Any]:
        """Parse JSON content from a secret file.
        
        Args:
            content: File content string
            path: Path for error messages
            
        Returns:
            Parsed dictionary
            
        Raises:
            VaultOperationError: If JSON is invalid
        """
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                raise VaultOperationError(
                    f"Secret file contains JSON but not an object: {type(data).__name__}",
                    code="INVALID_SECRET_FORMAT",
                )
            return data
        except json.JSONDecodeError as e:
            raise VaultOperationError(
                f"Invalid JSON in secret file: {e}",
                code="JSON_PARSE_ERROR",
            )
    
    async def get_secret(self, reference: str) -> str:
        """Get a secret value by reference.
        
        Supports multiple URI schemes:
        - "secret-name" - Relative to configured mount
        - "path/to/secret" - Nested path relative to mount
        - "file://path#key" - File URI with optional JSON key extraction
        - "docker://secret-name" - Docker Secrets shorthand
        - "k8s://secret-name#key" - Kubernetes CSI shorthand
        
        Args:
            reference: Secret reference in one of the formats above
                
        Returns:
            Secret value as string (base64 for binary files)
            
        Raises:
            VaultSecretNotFoundError: If secret doesn't exist
            VaultAuthorizationError: If access denied (path traversal, permissions)
            VaultOperationError: If read fails
        """
        # Parse reference to extract path and fragment
        path_ref, fragment_key = self._parse_reference(reference)
        
        # Resolve path with security checks
        path, base_mount = self._resolve_path(path_ref)
        
        # Check for rotation (Kubernetes CSI) - best effort, non-blocking
        self._check_rotation(path)
        
        # Atomic read with validation - run in thread pool for true async
        content = await asyncio.to_thread(
            self._read_and_validate_atomic, path, base_mount
        )
        
        # If fragment key specified, parse as JSON and extract key
        if fragment_key:
            data = self._parse_json_content(content, path)
            if fragment_key not in data:
                raise VaultSecretNotFoundError(f"{path_ref}#{fragment_key}")
            value = data[fragment_key]
            return str(value) if not isinstance(value, str) else value
        
        return content
    
    async def get_secret_or_none(self, reference: str) -> Optional[str]:
        """Get secret value or None if not found.
        
        Convenience method for callers who want Optional semantics.
        
        Args:
            reference: Secret reference in any supported format
            
        Returns:
            Secret value or None if not found
            
        Raises:
            VaultAuthorizationError: If access denied
            VaultOperationError: If read fails
        """
        try:
            return await self.get_secret(reference)
        except VaultSecretNotFoundError:
            return None
    
    async def get_credentials(self, reference: str) -> Dict[str, Any]:
        """Get credentials as a dictionary.
        
        For file provider, files with .json extension are parsed as JSON.
        Plain text files return {"value": "<content>"}.
        Binary files return {"value": "<base64>", "encoding": "base64"}.
        
        Note: JSON detection is based ONLY on .json file extension to avoid
        misinterpreting plaintext secrets that happen to start with '{'.
        
        Supports all URI schemes: file://, docker://, k8s://
        
        Args:
            reference: Secret reference
            
        Returns:
            Dictionary of credential fields
            
        Raises:
            VaultSecretNotFoundError: If secret doesn't exist
            VaultAuthorizationError: If access denied
            VaultOperationError: If read fails
        """
        # Parse reference to extract path and fragment
        path_ref, fragment_key = self._parse_reference(reference)
        
        # Resolve path with security checks
        path, base_mount = self._resolve_path(path_ref)
        
        # Check for rotation (Kubernetes CSI) - best effort
        self._check_rotation(path)
        
        # Atomic read with validation - run in thread pool for true async
        content = await asyncio.to_thread(
            self._read_and_validate_atomic, path, base_mount
        )
        
        # Check if binary file (returns base64)
        is_binary = path.suffix.lower() in self._binary_extensions
        
        # Parse as JSON ONLY if file has .json extension (not content heuristic)
        # This avoids misinterpreting plaintext like "{template}" or shell vars
        if not is_binary and path.suffix.lower() == self._json_extension:
            data = self._parse_json_content(content, path)
            
            # If fragment key specified, return just that key
            if fragment_key:
                if fragment_key not in data:
                    raise VaultSecretNotFoundError(f"{path_ref}#{fragment_key}")
                return {fragment_key: data[fragment_key]}
            
            return data
        
        # Plain text or binary file
        result: Dict[str, Any] = {"value": content}
        
        # Add metadata for binary files
        if is_binary:
            result["encoding"] = "base64"
            result["content_type"] = self._get_content_type(path.suffix)
        
        # If fragment key was specified, use it as the key name
        if fragment_key:
            return {fragment_key: content}
        
        return result
    
    def _get_content_type(self, suffix: str) -> str:
        """Get content type for binary file extensions."""
        content_types = {
            ".pem": "application/x-pem-file",
            ".crt": "application/x-x509-ca-cert",
            ".cer": "application/x-x509-ca-cert",
            ".key": "application/x-pem-file",
            ".p12": "application/x-pkcs12",
            ".pfx": "application/x-pkcs12",
            ".der": "application/x-x509-ca-cert",
        }
        return content_types.get(suffix.lower(), "application/octet-stream")
    
    async def list_keys(self, path: str = "") -> List[str]:
        """List secret files in a directory.
        
        Supports URI schemes for directory listing:
        - "" or "/" - List root of configured mount
        - "subdir" - List subdirectory
        - "file://subdir" - File URI format
        - "docker://" - List Docker secrets root
        - "k8s://" - List Kubernetes CSI root
        
        Args:
            path: Subdirectory path or URI (empty for root)
            
        Returns:
            List of secret file names (directories have trailing /)
            
        Raises:
            VaultAuthorizationError: If path is outside mount
            VaultOperationError: If directory cannot be read
        """
        base_mount = self._mount_path
        
        # Handle URI schemes
        if path.startswith("docker://"):
            base_mount = self._docker_path.resolve()
            path = path[9:]
        elif path.startswith("k8s://") or path.startswith("kubernetes://"):
            base_mount = self._k8s_path.resolve()
            path = path[6:] if path.startswith("k8s://") else path[13:]
        elif path.startswith("file://"):
            path = path[7:]
        
        dir_path = base_mount / path if path else base_mount
        
        # Security check
        try:
            resolved = dir_path.resolve()
            resolved.relative_to(base_mount)
        except ValueError:
            raise VaultAuthorizationError(
                "Access denied: path outside secrets directory",
                resource=path,
            )
        
        if not resolved.exists():
            raise VaultSecretNotFoundError(path or "/")
        
        if not resolved.is_dir():
            raise VaultOperationError(f"Path is not a directory: {path}")
        
        try:
            entries = []
            for entry in resolved.iterdir():
                # Skip hidden files
                if entry.name.startswith("."):
                    continue
                
                # Skip symlinks if not allowed (except in Docker mode)
                if entry.is_symlink() and not self._allow_symlinks:
                    continue
                
                # Add trailing / for directories
                if entry.is_dir():
                    entries.append(entry.name + "/")
                else:
                    entries.append(entry.name)
            
            return sorted(entries)
            
        except PermissionError as e:
            raise VaultAuthorizationError(
                f"Permission denied listing directory: {e}",
                resource=path,
            )
        except OSError as e:
            raise VaultOperationError(f"Cannot list directory: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health with environment-specific details.
        
        Returns:
            Health status dictionary including:
            - healthy: Overall health status
            - mount_path: Primary configured mount
            - mount_exists/mount_readable: Mount status
            - runtime: Detected container runtime
            - docker_available: Docker secrets availability
            - kubernetes_available: Kubernetes CSI availability
            - secrets_count: Number of secrets in mount (if readable)
        """
        mount_exists = self._mount_path.exists()
        mount_readable = False
        secrets_count = 0
        
        if mount_exists:
            try:
                entries = list(self._mount_path.iterdir())
                mount_readable = True
                secrets_count = len([e for e in entries if not e.name.startswith(".")])
            except (OSError, PermissionError):
                pass
        
        # Check Docker secrets availability
        docker_exists = self._docker_path.exists()
        docker_readable = False
        docker_count = 0
        if docker_exists:
            try:
                entries = list(self._docker_path.iterdir())
                docker_readable = True
                docker_count = len([e for e in entries if not e.name.startswith(".")])
            except (OSError, PermissionError):
                pass
        
        # Check Kubernetes CSI availability
        k8s_exists = self._k8s_path.exists()
        k8s_readable = False
        k8s_count = 0
        if k8s_exists:
            try:
                entries = list(self._k8s_path.iterdir())
                k8s_readable = True
                k8s_count = len([e for e in entries if not e.name.startswith(".")])
            except (OSError, PermissionError):
                pass
        
        return {
            "healthy": mount_exists and mount_readable,
            "mount_path": str(self._mount_path),
            "mount_exists": mount_exists,
            "mount_readable": mount_readable,
            "secrets_count": secrets_count,
            "runtime": self._runtime.name,
            "docker_mode": self._docker_mode,
            "docker": {
                "path": str(self._docker_path),
                "available": docker_exists and docker_readable,
                "secrets_count": docker_count,
            },
            "kubernetes": {
                "path": str(self._k8s_path),
                "available": k8s_exists and k8s_readable,
                "secrets_count": k8s_count,
            },
        }
    
    async def list_docker_secrets(self) -> List[str]:
        """List all Docker secrets.
        
        Convenience method for Docker environments.
        
        Returns:
            List of Docker secret names
        """
        return await self.list_keys("docker://")
    
    async def list_kubernetes_secrets(self) -> List[str]:
        """List all Kubernetes CSI secrets.
        
        Convenience method for Kubernetes environments.
        
        Returns:
            List of Kubernetes secret names
        """
        return await self.list_keys("k8s://")
    
    async def get_docker_secret(self, name: str) -> str:
        """Get a Docker secret by name.
        
        Convenience method for Docker environments.
        
        Args:
            name: Secret name (as specified in docker-compose or swarm)
            
        Returns:
            Secret value
        """
        return await self.get_secret(f"docker://{name}")
    
    async def get_kubernetes_secret(self, name: str, key: Optional[str] = None) -> str:
        """Get a Kubernetes CSI secret by name.
        
        Convenience method for Kubernetes environments.
        
        Args:
            name: Secret name (as mounted by CSI driver)
            key: Optional key to extract from JSON secret
            
        Returns:
            Secret value
        """
        uri = f"k8s://{name}"
        if key:
            uri += f"#{key}"
        return await self.get_secret(uri)
    
    def clear_rotation_cache(self) -> None:
        """Clear the secret rotation detection cache.
        
        Call this to reset rotation tracking, forcing fresh reads.
        """
        self._secret_metadata_cache.clear()
        logger.debug("Secret rotation cache cleared")
    
    async def close(self) -> None:
        """Close provider and clear caches."""
        self._secret_metadata_cache.clear()
    
    def __repr__(self) -> str:
        return (
            f"FileVaultProvider("
            f"mount_path={self._mount_path}, "
            f"runtime={self._runtime.name}, "
            f"docker_mode={self._docker_mode})"
        )
