"""HMAC signing for secure internal loopback calls.

This module provides cryptographic signing and verification for internal
service-to-service calls (loopback). All loopback calls MUST be signed
to prevent unauthorized access.

Security Properties:
    - HMAC-SHA256 signatures
    - 60-second max age (prevents replay of old requests)
    - Nonce replay protection (Redis-backed)
    - Constant-time comparison (timing attack resistant)
    - Audience binding (prevents cross-service replay)

Headers:
    X-Loopback-Signature: <HMAC-SHA256 hex>
    X-Loopback-Timestamp: <unix_timestamp>
    X-Loopback-Nonce: <random_32_hex>
    X-Loopback-Audience: <target_service_id>

Canonical Signing Input:
    CANONICAL_INPUT = join("\\n", [
        METHOD,              # HTTP method, uppercase
        PATH,                # Request path
        CANONICAL_QUERY,     # Query string, sorted by key
        CONTENT_TYPE,        # Content-Type header
        BODY_HASH,           # SHA-256 of request body
        TIMESTAMP,           # Unix timestamp
        NONCE,               # Random 32-char hex
        AUDIENCE,            # Target service ID
    ])

Usage:
    # Signing a request
    signer = LoopbackSigner(secret_key=os.getenv("LOOPBACK_SECRET"))
    headers = signer.sign_request(
        method="POST",
        path="/api/v1/execute",
        body=b'{"tool_id": "..."}',
        audience="empowernow-crud",
    )

    # Verifying a request
    verifier = LoopbackVerifier(secret_key=os.getenv("LOOPBACK_SECRET"))
    is_valid = await verifier.verify_request(
        method="POST",
        path="/api/v1/execute",
        body=b'{"tool_id": "..."}',
        headers=request.headers,
        audience="empowernow-crud",
        redis=redis_client,  # For nonce replay protection
    )
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlencode

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# Header names
HEADER_SIGNATURE = "X-Loopback-Signature"
HEADER_TIMESTAMP = "X-Loopback-Timestamp"
HEADER_NONCE = "X-Loopback-Nonce"
HEADER_AUDIENCE = "X-Loopback-Audience"

# Security parameters
MAX_AGE_SECONDS = 60
"""Maximum age for valid signatures (prevents replay of old requests)."""

MAX_FUTURE_SKEW_SECONDS = 5
"""Maximum allowed future timestamp (for clock skew tolerance)."""

NONCE_LENGTH = 32
"""Length of nonce in hex characters (16 bytes = 32 hex chars)."""

NONCE_TTL_SECONDS = 65
"""TTL for nonce in Redis (slightly > MAX_AGE for clock skew)."""


# =============================================================================
# Canonical Request
# =============================================================================


@dataclass(frozen=True)
class CanonicalRequest:
    """Canonical representation of a request for signing.

    All components are normalized to ensure consistent signatures.

    Attributes:
        method: HTTP method (uppercase).
        path: Request path (exact, no normalization).
        query_string: Query string (sorted by key).
        content_type: Content-Type header (lowercase).
        body_hash: SHA-256 hex of request body.
        timestamp: Unix timestamp (integer seconds).
        nonce: Random 32-char hex string.
        audience: Target service identifier.
    """

    method: str
    path: str
    query_string: str
    content_type: str
    body_hash: str
    timestamp: int
    nonce: str
    audience: str

    def to_signing_string(self) -> str:
        """Convert to canonical signing string.

        Returns:
            Newline-separated canonical string for HMAC input.
        """
        return "\n".join(
            [
                self.method,
                self.path,
                self.query_string,
                self.content_type,
                self.body_hash,
                str(self.timestamp),
                self.nonce,
                self.audience,
            ]
        )

    @classmethod
    def from_request(
        cls,
        method: str,
        path: str,
        query_string: str = "",
        content_type: str = "",
        body: bytes = b"",
        timestamp: Optional[int] = None,
        nonce: Optional[str] = None,
        audience: str = "",
    ) -> "CanonicalRequest":
        """Create canonical request from request components.

        Args:
            method: HTTP method.
            path: Request path.
            query_string: Raw query string.
            content_type: Content-Type header value.
            body: Request body bytes.
            timestamp: Unix timestamp (uses current time if None).
            nonce: Random nonce (generates new if None).
            audience: Target service identifier.

        Returns:
            Normalized CanonicalRequest.
        """
        # Normalize method
        method = method.upper().strip()

        # Normalize path (preserve exact encoding)
        path = path.strip() or "/"

        # Normalize query string (sort by key, then value)
        canonical_query = _canonicalize_query(query_string)

        # Normalize content type
        content_type = content_type.lower().strip() if content_type else ""

        # Hash body
        body_hash = hashlib.sha256(body).hexdigest()

        # Generate timestamp if not provided
        if timestamp is None:
            timestamp = int(time.time())

        # Generate nonce if not provided
        if nonce is None:
            nonce = secrets.token_hex(NONCE_LENGTH // 2)

        # Normalize audience
        audience = audience.lower().strip()

        return cls(
            method=method,
            path=path,
            query_string=canonical_query,
            content_type=content_type,
            body_hash=body_hash,
            timestamp=timestamp,
            nonce=nonce,
            audience=audience,
        )


def _canonicalize_query(query_string: str) -> str:
    """Canonicalize query string by sorting parameters.

    Args:
        query_string: Raw query string (without leading ?).

    Returns:
        Canonicalized query string (sorted by key, then value).
    """
    if not query_string:
        return ""

    # Parse and sort
    params = parse_qs(query_string, keep_blank_values=True)
    sorted_params = []
    for key in sorted(params.keys()):
        values = sorted(params[key])
        for value in values:
            sorted_params.append((key, value))

    return urlencode(sorted_params)


# =============================================================================
# Signer
# =============================================================================


class LoopbackSigner:
    """Signs requests for secure loopback calls.

    Uses HMAC-SHA256 with a shared secret key to sign requests.
    The signature covers all security-relevant request components.

    Example:
        signer = LoopbackSigner(secret_key=os.getenv("LOOPBACK_SECRET"))
        headers = signer.sign_request(
            method="POST",
            path="/api/v1/execute",
            body=b'{"data": "value"}',
            audience="empowernow-crud",
        )
        # headers now contains X-Loopback-* headers
    """

    def __init__(self, secret_key: str) -> None:
        """Initialize signer with secret key.

        Args:
            secret_key: Shared secret for HMAC signing.
                Must be at least 32 characters for security.

        Raises:
            ValueError: If secret_key is too short.
        """
        if not secret_key or len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        self._secret_key = secret_key.encode("utf-8")

    def sign_request(
        self,
        method: str,
        path: str,
        body: bytes = b"",
        audience: str = "",
        query_string: str = "",
        content_type: str = "application/json",
    ) -> Dict[str, str]:
        """Sign a request and return headers.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: Request path.
            body: Request body bytes.
            audience: Target service identifier.
            query_string: Query string (without leading ?).
            content_type: Content-Type header value.

        Returns:
            Dictionary of X-Loopback-* headers to add to request.
        """
        canonical = CanonicalRequest.from_request(
            method=method,
            path=path,
            query_string=query_string,
            content_type=content_type,
            body=body,
            audience=audience,
        )

        signature = self._compute_signature(canonical)

        return {
            HEADER_SIGNATURE: signature,
            HEADER_TIMESTAMP: str(canonical.timestamp),
            HEADER_NONCE: canonical.nonce,
            HEADER_AUDIENCE: canonical.audience,
        }

    def _compute_signature(self, canonical: CanonicalRequest) -> str:
        """Compute HMAC-SHA256 signature.

        Args:
            canonical: Canonical request to sign.

        Returns:
            Hex-encoded signature string.
        """
        signing_string = canonical.to_signing_string()
        signature = hmac.new(
            self._secret_key,
            signing_string.encode("utf-8"),
            hashlib.sha256,
        )
        return signature.hexdigest()


# =============================================================================
# Verifier
# =============================================================================


@dataclass
class VerificationResult:
    """Result of signature verification.

    Attributes:
        valid: Whether the signature is valid.
        error: Error message if invalid, None if valid.
        canonical: The canonical request (for debugging).
    """

    valid: bool
    error: Optional[str] = None
    canonical: Optional[CanonicalRequest] = None


class LoopbackVerifier:
    """Verifies signatures on loopback requests.

    Performs comprehensive verification including:
    - Signature validation (HMAC-SHA256)
    - Timestamp freshness (max 60 seconds)
    - Nonce replay protection (via Redis)
    - Audience matching

    Example:
        verifier = LoopbackVerifier(secret_key=os.getenv("LOOPBACK_SECRET"))
        result = await verifier.verify_request(
            method="POST",
            path="/api/v1/execute",
            body=b'{"data": "value"}',
            headers=request.headers,
            audience="empowernow-crud",
            redis=redis_client,
        )
        if not result.valid:
            raise HTTPException(401, result.error)
    """

    def __init__(
        self,
        secret_key: str,
        max_age_seconds: int = MAX_AGE_SECONDS,
        allow_degraded: bool = False,
    ) -> None:
        """Initialize verifier.

        Args:
            secret_key: Shared secret for HMAC verification.
            max_age_seconds: Maximum age for valid signatures.
            allow_degraded: If True, allow verification without Redis
                (timestamp-only). NEVER enable in production.

        Raises:
            ValueError: If secret_key is too short.
        """
        if not secret_key or len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        self._secret_key = secret_key.encode("utf-8")
        self._max_age = max_age_seconds
        self._allow_degraded = allow_degraded

    async def verify_request(
        self,
        method: str,
        path: str,
        body: bytes,
        headers: Dict[str, str],
        audience: str,
        redis: Optional[Any] = None,
        query_string: str = "",
        content_type: str = "",
    ) -> VerificationResult:
        """Verify a signed request.

        Args:
            method: HTTP method.
            path: Request path.
            body: Request body bytes.
            headers: Request headers (must include X-Loopback-* headers).
            audience: Expected audience (target service).
            redis: Redis client for nonce replay protection.
            query_string: Query string (without leading ?).
            content_type: Content-Type header value.

        Returns:
            VerificationResult indicating validity and any errors.
        """
        # Extract headers (case-insensitive)
        header_map = {k.lower(): v for k, v in headers.items()}

        signature = header_map.get(HEADER_SIGNATURE.lower())
        timestamp_str = header_map.get(HEADER_TIMESTAMP.lower())
        nonce = header_map.get(HEADER_NONCE.lower())
        header_audience = header_map.get(HEADER_AUDIENCE.lower())

        # Check required headers
        if not signature:
            return VerificationResult(valid=False, error="Missing signature header")
        if not timestamp_str:
            return VerificationResult(valid=False, error="Missing timestamp header")
        if not nonce:
            return VerificationResult(valid=False, error="Missing nonce header")
        if not header_audience:
            return VerificationResult(valid=False, error="Missing audience header")

        # Parse timestamp
        try:
            timestamp = int(timestamp_str)
        except ValueError:
            return VerificationResult(valid=False, error="Invalid timestamp format")

        # Check timestamp freshness (bounded skew, not abs)
        # Security: Using abs() would extend replay window for future-dated requests
        now = int(time.time())
        if timestamp > now + MAX_FUTURE_SKEW_SECONDS:
            return VerificationResult(
                valid=False,
                error=f"Timestamp in future: {timestamp} > {now} + {MAX_FUTURE_SKEW_SECONDS}s",
            )
        age = now - timestamp
        if age > self._max_age:
            return VerificationResult(
                valid=False,
                error=f"Signature too old: {age}s > {self._max_age}s",
            )

        # Check audience
        if header_audience.lower() != audience.lower():
            return VerificationResult(
                valid=False,
                error=f"Audience mismatch: {header_audience} != {audience}",
            )

        # Check nonce replay
        if redis:
            is_new = await self._check_nonce(nonce, redis)
            if not is_new:
                return VerificationResult(valid=False, error="Nonce replay detected")
        elif not self._allow_degraded:
            return VerificationResult(
                valid=False,
                error="Redis required for nonce verification (fail-closed)",
            )
        else:
            logger.warning("Degraded mode: skipping nonce verification")

        # Build canonical request
        canonical = CanonicalRequest.from_request(
            method=method,
            path=path,
            query_string=query_string,
            content_type=content_type,
            body=body,
            timestamp=timestamp,
            nonce=nonce,
            audience=audience,
        )

        # Verify signature (constant-time comparison)
        expected = self._compute_signature(canonical)
        if not hmac.compare_digest(signature.lower(), expected.lower()):
            return VerificationResult(
                valid=False,
                error="Invalid signature",
                canonical=canonical,
            )

        return VerificationResult(valid=True, canonical=canonical)

    async def _check_nonce(self, nonce: str, redis: Any) -> bool:
        """Check and record nonce for replay protection.

        Args:
            nonce: The nonce to check.
            redis: Async Redis client.

        Returns:
            True if nonce is new (valid), False if replay.
        """
        key = f"loopback:nonce:{nonce}"
        try:
            # Atomic SET NX EX - sets key only if it doesn't exist, with TTL
            # This is safer than setnx + expire (which is non-atomic)
            is_new = await redis.set(key, "1", nx=True, ex=NONCE_TTL_SECONDS)
            return bool(is_new)
        except Exception as e:
            logger.error("Redis nonce check failed: %s", e)
            if self._allow_degraded:
                logger.warning("Degraded mode: allowing request despite Redis failure")
                return True
            return False

    def _compute_signature(self, canonical: CanonicalRequest) -> str:
        """Compute expected signature."""
        signing_string = canonical.to_signing_string()
        signature = hmac.new(
            self._secret_key,
            signing_string.encode("utf-8"),
            hashlib.sha256,
        )
        return signature.hexdigest()


# =============================================================================
# Utility Functions
# =============================================================================


def generate_nonce() -> str:
    """Generate a random nonce for signing.

    Returns:
        32-character hex string.
    """
    return secrets.token_hex(NONCE_LENGTH // 2)


def hash_body(body: bytes) -> str:
    """Compute SHA-256 hash of request body.

    Args:
        body: Request body bytes.

    Returns:
        Hex-encoded hash string.
    """
    return hashlib.sha256(body).hexdigest()


__all__ = [
    # Headers
    "HEADER_SIGNATURE",
    "HEADER_TIMESTAMP",
    "HEADER_NONCE",
    "HEADER_AUDIENCE",
    # Config
    "MAX_AGE_SECONDS",
    "NONCE_LENGTH",
    "NONCE_TTL_SECONDS",
    # Classes
    "CanonicalRequest",
    "LoopbackSigner",
    "LoopbackVerifier",
    "VerificationResult",
    # Functions
    "generate_nonce",
    "hash_body",
]
