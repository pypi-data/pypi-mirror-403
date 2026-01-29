"""Delegation error hierarchy.

This module defines the exception hierarchy for delegation-related errors.
All exceptions inherit from EmpowerNowError to integrate with the SDK's
unified error handling.

Exception Hierarchy:
    EmpowerNowError
    └── DelegationError
        ├── DelegationNotFoundError
        ├── DelegationExpiredError
        ├── DelegationRevokedError
        ├── DelegationSuspendedError
        ├── CapabilityNotAllowedError
        ├── ProtocolVersionError
        └── DelegationVerificationError
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, Optional

from ..exceptions import EmpowerNowError


class DelegationError(EmpowerNowError):
    """Base class for delegation-related errors.

    All delegation exceptions carry structured context for:
    - Machine-readable error codes (reason_code)
    - Human-readable messages
    - Audit-trail context (delegator, delegate, etc.)

    Attributes:
        message: Human-readable error message.
        delegator_arn: ARN of the delegating user (if applicable).
        delegate_arn: ARN of the delegate agent (if applicable).
        reason_code: Machine-readable error code for programmatic handling.
        context: Additional context for debugging/audit.
    """

    def __init__(
        self,
        message: str,
        *,
        delegator_arn: Optional[str] = None,
        delegate_arn: Optional[str] = None,
        reason_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a delegation error.

        Args:
            message: Human-readable error message.
            delegator_arn: ARN of the delegating user.
            delegate_arn: ARN of the delegate agent.
            reason_code: Machine-readable error code.
            context: Additional context dictionary.
        """
        super().__init__(message)
        self.message = message
        self.delegator_arn = delegator_arn
        self.delegate_arn = delegate_arn
        self.reason_code = reason_code or "DELEGATION_ERROR"
        self.context: Dict[str, Any] = context.copy() if context else {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize error to dictionary for API responses.

        Returns:
            Dictionary with error details safe for external exposure.
        """
        return {
            "error_type": type(self).__name__,
            "reason_code": self.reason_code,
            "message": self.message,
            "delegator_arn": self.delegator_arn,
            "delegate_arn": self.delegate_arn,
            "context": self.context,
        }

    def __str__(self) -> str:
        """Return string representation with context."""
        parts = [self.message]
        if self.delegator_arn:
            parts.append(f"delegator={self.delegator_arn}")
        if self.delegate_arn:
            parts.append(f"delegate={self.delegate_arn}")
        if self.reason_code != "DELEGATION_ERROR":
            parts.append(f"reason={self.reason_code}")
        return " | ".join(parts)


class DelegationNotFoundError(DelegationError):
    """No delegation exists between delegator and delegate.

    Raised when attempting to verify a delegation that does not exist
    in the system. This is a common case and should be handled gracefully.
    """

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Initialize with DELEGATION_NOT_FOUND reason code."""
        super().__init__(message, reason_code="DELEGATION_NOT_FOUND", **kwargs)


class DelegationExpiredError(DelegationError):
    """Delegation has expired based on its expires_at timestamp.

    This error indicates the delegation was once valid but has passed
    its expiration time. The delegation record still exists but is no
    longer active.

    Attributes:
        delegation_id: ID of the expired delegation.
        expired_at: When the delegation expired.
    """

    def __init__(
        self,
        message: str,
        *,
        delegation_id: str,
        expired_at: str,
        **kwargs: Any,
    ) -> None:
        """Initialize with expiration details.

        Args:
            message: Human-readable message.
            delegation_id: ID of the expired delegation.
            expired_at: ISO timestamp when delegation expired.
            **kwargs: Additional DelegationError arguments.
        """
        super().__init__(message, reason_code="DELEGATION_EXPIRED", **kwargs)
        self.delegation_id = delegation_id
        self.expired_at = expired_at
        self.context["delegation_id"] = delegation_id
        self.context["expired_at"] = expired_at


class DelegationRevokedError(DelegationError):
    """Delegation has been explicitly revoked.

    This error indicates the delegation was revoked by the delegator
    or an administrator. Unlike expiration, revocation is an explicit
    action that may warrant different handling (e.g., security audit).

    Attributes:
        delegation_id: ID of the revoked delegation.
        revoked_at: When the delegation was revoked.
        revoked_by: Who revoked the delegation.
    """

    def __init__(
        self,
        message: str,
        *,
        delegation_id: str,
        revoked_at: Optional[str] = None,
        revoked_by: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with revocation details.

        Args:
            message: Human-readable message.
            delegation_id: ID of the revoked delegation.
            revoked_at: ISO timestamp when delegation was revoked.
            revoked_by: Identity ARN of who revoked it.
            **kwargs: Additional DelegationError arguments.
        """
        super().__init__(message, reason_code="DELEGATION_REVOKED", **kwargs)
        self.delegation_id = delegation_id
        self.context["delegation_id"] = delegation_id
        if revoked_at:
            self.revoked_at = revoked_at
            self.context["revoked_at"] = revoked_at
        if revoked_by:
            self.revoked_by = revoked_by
            self.context["revoked_by"] = revoked_by


class DelegationSuspendedError(DelegationError):
    """Delegation is temporarily suspended.

    Suspension is a temporary state that can be lifted. This differs from
    revocation which is typically permanent. Common reasons include:
    - Security investigation
    - User request for temporary pause
    - Administrative action

    Attributes:
        delegation_id: ID of the suspended delegation.
        suspended_reason: Why the delegation was suspended.
    """

    def __init__(
        self,
        message: str,
        *,
        delegation_id: str,
        suspended_reason: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with suspension details.

        Args:
            message: Human-readable message.
            delegation_id: ID of the suspended delegation.
            suspended_reason: Why the delegation was suspended.
            **kwargs: Additional DelegationError arguments.
        """
        super().__init__(message, reason_code="DELEGATION_SUSPENDED", **kwargs)
        self.delegation_id = delegation_id
        self.context["delegation_id"] = delegation_id
        if suspended_reason:
            self.suspended_reason = suspended_reason
            self.context["suspended_reason"] = suspended_reason


class CapabilityNotAllowedError(DelegationError):
    """Requested tool is not in the delegation's capability list.

    The delegation exists and is active, but the specific tool/capability
    being accessed is not authorized. This helps distinguish between
    "no delegation at all" vs "delegation exists but doesn't cover this action".

    Attributes:
        tool_id: The tool ID that was denied.
        delegation_id: ID of the delegation (if available).
    """

    def __init__(
        self,
        message: str,
        *,
        tool_id: str,
        capability_ids: Optional[list] = None,
        delegation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with capability details.

        Args:
            message: Human-readable message.
            tool_id: The tool ID that was denied.
            capability_ids: List of allowed capabilities (count only, for privacy).
            delegation_id: ID of the delegation.
            **kwargs: Additional DelegationError arguments.
        """
        super().__init__(message, reason_code="CAPABILITY_NOT_ALLOWED", **kwargs)
        self.tool_id = tool_id
        self.context["tool_id"] = tool_id
        # Don't expose full capability list - just the count for debugging
        if capability_ids is not None:
            self.context["allowed_capability_count"] = len(capability_ids)
        if delegation_id:
            self.delegation_id = delegation_id
            self.context["delegation_id"] = delegation_id


class ProtocolVersionError(DelegationError):
    """Protocol version mismatch between client and server.

    The delegation protocol uses semantic versioning. This error is raised
    when the client sends a version that the server cannot support.

    Attributes:
        expected_versions: Set of supported versions.
        received_version: The version that was received.
    """

    def __init__(
        self,
        message: str,
        *,
        expected_versions: FrozenSet[str],
        received_version: str,
        **kwargs: Any,
    ) -> None:
        """Initialize with version details.

        Args:
            message: Human-readable message.
            expected_versions: Set of supported protocol versions.
            received_version: The protocol version that was received.
            **kwargs: Additional DelegationError arguments.
        """
        super().__init__(message, reason_code="PROTOCOL_VERSION_MISMATCH", **kwargs)
        self.expected_versions = expected_versions
        self.received_version = received_version
        self.context["expected_versions"] = list(expected_versions)
        self.context["received_version"] = received_version


class DelegationVerificationError(DelegationError):
    """Generic verification error when a more specific error doesn't apply.

    This is a catch-all for unexpected errors during verification, such as:
    - Network failures when contacting membership service
    - Serialization errors
    - Unexpected response formats

    Attributes:
        cause: The underlying exception that caused this error.
    """

    def __init__(
        self,
        message: str,
        *,
        cause: Optional[Exception] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize with cause details.

        Args:
            message: Human-readable message.
            cause: The underlying exception.
            **kwargs: Additional DelegationError arguments.
        """
        super().__init__(message, reason_code="VERIFICATION_ERROR", **kwargs)
        self.cause = cause
        if cause:
            self.context["cause_type"] = type(cause).__name__
            # Don't include full exception message - might contain sensitive data
            self.context["cause_message"] = str(cause)[:200]

    def __cause__(self) -> Optional[Exception]:
        """Return the underlying cause for exception chaining."""
        return self.cause


__all__ = [
    "DelegationError",
    "DelegationNotFoundError",
    "DelegationExpiredError",
    "DelegationRevokedError",
    "DelegationSuspendedError",
    "CapabilityNotAllowedError",
    "ProtocolVersionError",
    "DelegationVerificationError",
]
