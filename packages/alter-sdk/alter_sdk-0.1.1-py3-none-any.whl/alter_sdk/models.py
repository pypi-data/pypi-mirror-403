"""
Pydantic models for Alter SDK.

These models provide type-safe data structures with validation.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TokenResponse(BaseModel):
    """
    OAuth token response from Alter Vault.

    This represents an access token retrieved from the backend.
    """

    access_token: str = Field(..., description="OAuth access token")
    token_type: str = Field(default="Bearer", description="Token type (usually Bearer)")
    expires_in: int | None = Field(None, description="Seconds until token expires")
    expires_at: datetime | None = Field(None, description="Absolute expiration time")
    scopes: list[str] = Field(default_factory=list, description="OAuth scopes granted")
    connection_id: UUID = Field(
        ...,
        description="Connection ID that provided this token",
    )

    @field_validator("expires_at", mode="before")
    @classmethod
    def parse_expires_at(cls, v: Any) -> datetime | None:
        """Parse expires_at from ISO string if needed."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Parse ISO format
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            # Ensure timezone aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt
        return v  # type: ignore[return-value]

    def is_expired(self, buffer_seconds: int = 0) -> bool:
        """
        Check if token is expired.

        Args:
            buffer_seconds: Consider token expired N seconds before actual expiry.
                           Useful for preventing race conditions.

        Returns:
            True if token is expired or will expire within buffer_seconds.
        """
        if self.expires_at is None:
            # No expiration time means token doesn't expire
            return False

        now = datetime.now(UTC)
        # Make expires_at timezone-aware if needed
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        # Check if expired with buffer
        from datetime import timedelta

        return expires_at <= now + timedelta(seconds=buffer_seconds)

    def needs_refresh(self, buffer_seconds: int = 300) -> bool:
        """
        Check if token should be refreshed soon.

        Args:
            buffer_seconds: Consider token needing refresh N seconds before expiry.
                           Default 5 minutes (300 seconds).

        Returns:
            True if token will expire within buffer_seconds.
        """
        return self.is_expired(buffer_seconds=buffer_seconds)


class APICallAuditLog(BaseModel):
    """
    Audit log entry for an API call to a provider.

    This is sent to the backend audit endpoint.
    """

    connection_id: UUID
    provider_id: str
    method: str  # GET, POST, PUT, DELETE, etc.
    url: str
    request_headers: dict[str, str] | None = None
    request_body: Any | None = None
    response_status: int
    response_headers: dict[str, str] | None = None
    response_body: Any | None = None
    latency_ms: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reason: str | None = None

    def sanitize(self) -> dict[str, Any]:
        """
        Sanitize sensitive data before sending.

        Removes Authorization headers, cookies, etc.
        """
        sensitive_headers = {
            "authorization",
            "cookie",
            "set-cookie",
            "x-api-key",
            "x-auth-token",
        }

        # Use mode='json' to ensure UUIDs and datetimes are serialized
        sanitized = self.model_dump(mode="json")

        # Sanitize request headers
        if sanitized.get("request_headers"):
            sanitized["request_headers"] = {
                k: v
                for k, v in sanitized["request_headers"].items()
                if k.lower() not in sensitive_headers
            }

        # Sanitize response headers
        if sanitized.get("response_headers"):
            sanitized["response_headers"] = {
                k: v
                for k, v in sanitized["response_headers"].items()
                if k.lower() not in sensitive_headers
            }

        return sanitized
