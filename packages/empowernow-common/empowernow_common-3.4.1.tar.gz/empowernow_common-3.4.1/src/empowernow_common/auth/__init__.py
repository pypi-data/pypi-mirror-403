"""Authentication module for internal service calls.

This module provides cryptographic signing and verification for secure
internal service-to-service (loopback) calls.

⚠️ SECURITY REQUIREMENTS ⚠️
    All loopback calls MUST be signed. Unsigned calls are REJECTED.
    The only exception is development environments with ALLOW_UNSIGNED_LOOPBACK=true.

Security Properties:
    - HMAC-SHA256 signatures
    - 60-second max age
    - Nonce replay protection (Redis-backed)
    - Constant-time comparison
    - Audience binding

Usage:
    from empowernow_common.auth import LoopbackSigner, LoopbackVerifier

    # Signing (client side)
    signer = LoopbackSigner(secret_key=os.getenv("LOOPBACK_SECRET"))
    headers = signer.sign_request(
        method="POST",
        path="/api/v1/execute",
        body=request_body,
        audience="empowernow-crud",
    )

    # Verification (server side)
    verifier = LoopbackVerifier(secret_key=os.getenv("LOOPBACK_SECRET"))
    result = await verifier.verify_request(
        method=request.method,
        path=request.url.path,
        body=await request.body(),
        headers=dict(request.headers),
        audience="empowernow-crud",
        redis=redis_client,
    )
    if not result.valid:
        raise HTTPException(401, result.error)
"""

from .loopback_signer import (
    # Headers
    HEADER_SIGNATURE,
    HEADER_TIMESTAMP,
    HEADER_NONCE,
    HEADER_AUDIENCE,
    # Config
    MAX_AGE_SECONDS,
    NONCE_LENGTH,
    NONCE_TTL_SECONDS,
    # Classes
    CanonicalRequest,
    LoopbackSigner,
    LoopbackVerifier,
    VerificationResult,
    # Functions
    generate_nonce,
    hash_body,
)

from .principal import (
    # Classes
    RequestPrincipal,
    # Functions
    extract_principal,
    extract_principal_safe,
    # Claim keys
    CLAIM_ACCOUNT_ARN,
    CLAIM_IDENTITY_ARN,
    CLAIM_RESOLUTION,
    CLAIM_CONNECTION_ID,
    CLAIM_ORIG_ISS,
    CLAIM_ORIG_SUB,
    CLAIM_ORIG_SUB_HASH,
)


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
    # Identity Resolution v1.1 - Principal extraction
    "RequestPrincipal",
    "extract_principal",
    "extract_principal_safe",
    # Claim keys
    "CLAIM_ACCOUNT_ARN",
    "CLAIM_IDENTITY_ARN",
    "CLAIM_RESOLUTION",
    "CLAIM_CONNECTION_ID",
    "CLAIM_ORIG_ISS",
    "CLAIM_ORIG_SUB",
    "CLAIM_ORIG_SUB_HASH",
]
