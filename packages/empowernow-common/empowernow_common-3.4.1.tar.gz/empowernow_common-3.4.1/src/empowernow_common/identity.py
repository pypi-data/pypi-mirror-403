"""Identity helpers (UniqueIdentity).

A compact, deterministic string that uniquely identifies a principal within
an IdP namespace. Prevents subject collision between IdPs by including the
IdP name. Optimised for audit-logs, cache keys and resource ACLs.

Format (canonical):

    auth:{entity_type}:{idp_name}:{encoded_subject}

Subject Encoding:
    Colons in the subject are percent-encoded (%3A) to ensure the ARN
    always has exactly 4 colon-separated segments. This prevents parsing
    ambiguity for subjects like "local:username" or "tenant:user:id".

Examples::

    >>> uid = UniqueIdentity(issuer="https://login.microsoftonline.com/contoso", subject="123")
    >>> str(uid)
    'auth:account:login.microsoftonline.com:123'

    >>> uid = UniqueIdentity(issuer="https://idp.example.com", subject="tenant:user:123")
    >>> str(uid)
    'auth:account:idp.example.com:tenant%3Auser%3A123'

The helper supports three creation paths:

* direct construction ``UniqueIdentity(issuer, subject)``
* parsing a canonical UID string via :py:meth:`parse`
* deriving from a JWT claims payload via :py:meth:`from_claims`
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, Literal
from urllib.parse import quote, unquote, urlparse

__all__ = ["UniqueIdentity", "VALID_ENTITY_TYPES"]

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

VALID_ENTITY_TYPES: Final[frozenset[str]] = frozenset(
    {"account", "identity", "service", "agent"}
)
"""Valid entity types for ARN construction."""

EntityType = Literal["account", "identity", "service", "agent"]
"""Type alias for valid entity types."""

# Characters safe in ARN subject segment (everything except colon)
_ARN_SAFE_CHARS: Final[str] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~@/"


# ─────────────────────────────────────────────────────────────────────────────
# UniqueIdentity
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(slots=True, frozen=True)
class UniqueIdentity:
    """Immutable identity representation with canonical ARN serialization.

    Attributes:
        issuer: Original issuer URL or identifier (preserved for roundtrip)
        subject: Original subject identifier (unencoded)
        idp_name: Normalized IdP name extracted from issuer
        entity_type: Type of entity (account, identity, service, agent)
    """

    issuer: str
    subject: str
    idp_name: str
    entity_type: EntityType = "account"

    def __post_init__(self) -> None:
        """Validate fields after dataclass initialization."""
        # Validate entity_type
        if self.entity_type not in VALID_ENTITY_TYPES:
            raise ValueError(
                f"entity_type must be one of {sorted(VALID_ENTITY_TYPES)}, "
                f"got '{self.entity_type}'"
            )

        # Validate subject is not empty
        if not self.subject or not self.subject.strip():
            raise ValueError("subject cannot be empty or whitespace-only")

        # Validate idp_name is not empty
        if not self.idp_name or not self.idp_name.strip():
            raise ValueError("idp_name cannot be empty or whitespace-only")

        # Check if subject is already a canonical ARN (pass-through case)
        if self.subject.startswith("auth:"):
            parts = self.subject.split(":", 3)
            if len(parts) == 4 and parts[1] in VALID_ENTITY_TYPES:
                # Subject is already a canonical ARN - this is valid
                return

        # Validate idp_name doesn't contain colons (would break ARN format)
        if ":" in self.idp_name:
            raise ValueError(
                f"idp_name cannot contain colons, got '{self.idp_name}'. "
                "Colons should be replaced with underscores."
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Derived Properties
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def value(self) -> str:
        """Return canonical ARN identifier.

        If subject is already a valid canonical ARN, returns it as-is to avoid
        double-encoding. Otherwise, constructs ARN with encoded subject.

        Returns:
            Canonical ARN string in format auth:{type}:{idp}:{encoded_subject}
        """
        # Pass-through: if subject is already a canonical ARN, return as-is
        if self.subject.startswith("auth:"):
            parts = self.subject.split(":", 3)
            if len(parts) == 4 and parts[1] in VALID_ENTITY_TYPES:
                return self.subject

        # Encode colons in subject to prevent parsing ambiguity
        encoded_subject = encode_arn_segment(self.subject)
        safe_idp = self.idp_name.replace(":", "_").lower()

        return f"auth:{self.entity_type}:{safe_idp}:{encoded_subject}"

    def __str__(self) -> str:
        """Return canonical ARN string representation."""
        return self.value

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return (
            f"UniqueIdentity(issuer={self.issuer!r}, subject={self.subject!r}, "
            f"idp_name={self.idp_name!r}, entity_type={self.entity_type!r})"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Constructors
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def from_claims(cls, claims: dict[str, str]) -> UniqueIdentity:
        """Create from JWT claims.

        Args:
            claims: JWT claims dictionary (requires 'iss' and 'sub')

        Returns:
            UniqueIdentity instance

        Raises:
            ValueError: If required claims are missing
        """
        if "iss" not in claims:
            raise ValueError("claims missing required 'iss' (issuer)")
        if "sub" not in claims:
            raise ValueError("claims missing required 'sub' (subject)")

        issuer = claims["iss"]
        subject = claims["sub"]

        if not issuer:
            raise ValueError("'iss' claim cannot be empty")
        if not subject:
            raise ValueError("'sub' claim cannot be empty")

        return cls(
            issuer=issuer,
            subject=subject,
            idp_name=_idp_from_issuer(issuer),
        )

    @classmethod
    def parse(cls, arn: str) -> UniqueIdentity:
        """Parse a canonical ARN string.

        Args:
            arn: Canonical ARN string (auth:{type}:{idp}:{subject})

        Returns:
            UniqueIdentity instance with decoded subject

        Raises:
            ValueError: If ARN format is invalid
        """
        if not arn:
            raise ValueError("ARN cannot be empty")

        if not arn.startswith("auth:"):
            raise ValueError(f"ARN must start with 'auth:', got '{arn[:20]}...'")

        parts = arn.split(":", 3)
        if len(parts) != 4:
            raise ValueError(
                f"ARN must have exactly 4 colon-separated segments, "
                f"got {len(parts)}: '{arn}'"
            )

        _, entity_type, idp_name, encoded_subject = parts

        if entity_type not in VALID_ENTITY_TYPES:
            raise ValueError(
                f"Invalid entity type '{entity_type}', "
                f"must be one of {sorted(VALID_ENTITY_TYPES)}"
            )

        if not idp_name:
            raise ValueError("IdP name segment cannot be empty")

        if not encoded_subject:
            raise ValueError("Subject segment cannot be empty")

        # Decode percent-encoded subject
        subject = decode_arn_segment(encoded_subject)

        # Reconstruct issuer URL from idp_name
        # Note: This is lossy - we default to https and lose path/port info
        issuer = f"https://{idp_name}"

        return cls(
            issuer=issuer,
            subject=subject,
            idp_name=idp_name,
            entity_type=entity_type,  # type: ignore[arg-type]
        )


# ─────────────────────────────────────────────────────────────────────────────
# Encoding/Decoding Helpers
# ─────────────────────────────────────────────────────────────────────────────


def encode_arn_segment(segment: str) -> str:
    """Encode a string for safe inclusion in an ARN segment.

    Colons are percent-encoded to %3A to ensure ARN always has exactly
    4 colon-separated segments.

    Args:
        segment: Raw string to encode

    Returns:
        Encoded string safe for ARN segment
    """
    # Use percent-encoding, keeping most characters readable
    return quote(segment, safe=_ARN_SAFE_CHARS)


def decode_arn_segment(segment: str) -> str:
    """Decode a percent-encoded ARN segment.

    Args:
        segment: Percent-encoded string from ARN

    Returns:
        Decoded original string
    """
    return unquote(segment)


# ─────────────────────────────────────────────────────────────────────────────
# Internal Helpers
# ─────────────────────────────────────────────────────────────────────────────

_IDP_HOST_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<host>[a-zA-Z0-9][a-zA-Z0-9.\-]*[a-zA-Z0-9])(/|$)"
)


def _idp_from_issuer(issuer: str) -> str:
    """Extract normalized IdP name from issuer URL.

    Args:
        issuer: Issuer URL or ARN

    Returns:
        Normalized IdP name (lowercase, no colons)
    """
    if not issuer:
        raise ValueError("issuer cannot be empty")

    # URL issuer (most common)
    if "://" in issuer:
        parsed = urlparse(issuer)
        host = parsed.netloc
        if host:
            # Replace port separator colon with underscore to avoid ARN parsing issues
            return host.replace(":", "_").lower()

    # AWS ARN style: "arn:aws:cognito-idp:region:account:userpool/id"
    if issuer.startswith("arn:"):
        parts = issuer.split(":")
        if len(parts) >= 6:
            # Extract the resource type (e.g., "userpool")
            resource = parts[5].split("/")[0]
            if resource:
                return resource.lower()

    # Fallback: extract host-like pattern from start
    match = _IDP_HOST_RE.match(issuer)
    if match:
        return match.group("host").lower()

    # Last resort: use issuer as-is, replacing colons
    return issuer.replace(":", "_").lower()
