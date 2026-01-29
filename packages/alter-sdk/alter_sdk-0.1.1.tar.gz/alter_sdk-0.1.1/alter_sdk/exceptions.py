"""
Exception hierarchy for Alter SDK.

All exceptions inherit from AlterSDKError for easy catching.
"""

from typing import Any


class AlterSDKError(Exception):
    """Base exception for all Alter SDK errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize exception with message and optional details."""
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation."""
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class TokenRetrievalError(AlterSDKError):
    """Raised when token retrieval fails."""


class PolicyViolationError(TokenRetrievalError):
    """
    Raised when token access is denied by policy enforcement.

    This indicates the connection exists but access was denied by Cerbos policy
    (e.g., unauthorized scopes, outside business hours, rate limit exceeded).
    """

    def __init__(
        self,
        message: str,
        policy_error: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize with policy violation details."""
        super().__init__(message, details)
        self.policy_error = policy_error


class ConnectionNotFoundError(TokenRetrievalError):
    """
    Raised when OAuth connection not found.

    This indicates no connection exists for the given provider and attributes.
    """


class TokenExpiredError(TokenRetrievalError):
    """
    Raised when token refresh fails.

    This indicates the connection exists but token refresh failed (e.g., refresh
    token revoked, provider API error).
    """

    def __init__(
        self,
        message: str,
        connection_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize with connection ID."""
        super().__init__(message, details)
        self.connection_id = connection_id


class ProviderAPIError(AlterSDKError):
    """
    Raised when provider API call fails.

    This is raised by wrapper classes when the actual provider API returns an error.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: Any | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize with provider API error details."""
        super().__init__(message, details)
        self.status_code = status_code
        self.response_body = response_body


class NetworkError(AlterSDKError):
    """
    Raised when network operations fail.

    This includes connection errors, timeouts, and DNS failures when communicating
    with Alter Vault backend.
    """


class UnsupportedProviderError(AlterSDKError):
    """
    Raised when provider is not supported.

    This is raised when get_client() is called with an unsupported provider
    and no fallback is available.
    """
