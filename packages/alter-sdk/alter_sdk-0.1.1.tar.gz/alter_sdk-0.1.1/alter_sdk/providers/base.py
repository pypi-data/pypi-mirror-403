"""
Base provider wrapper class.

All provider-specific wrappers inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from alter_sdk.models import TokenResponse

if TYPE_CHECKING:
    from uuid import UUID

    from alter_sdk.client import AlterVault


class BaseProviderWrapper(ABC):
    """
    Abstract base class for provider-specific wrappers.

    Subclasses should implement:
    - _create_client(): Create the provider's SDK client with token
    """

    def __init__(
        self,
        vault: "AlterVault",
        provider_id: str,
        user: dict[str, Any],
        reason: str | None = None,
    ) -> None:
        """
        Initialize provider wrapper.

        Args:
            vault: AlterVault instance
            provider_id: OAuth provider identifier
            user: User attributes to match connection (e.g., {"user_id": "alice"})
            reason: Optional reason for token access
        """
        self.vault = vault
        self.provider_id = provider_id
        self.user = user
        self.reason = reason

        # Current token and client (fetched fresh from backend on each call)
        self._token: TokenResponse | None = None
        self._connection_id: UUID | None = None
        self._client: Any | None = None

    async def _ensure_token(self, _force_refresh: bool = False) -> TokenResponse:
        """
        Fetch token from backend (INTERNAL USE ONLY).

        NO CLIENT-SIDE CACHING: Always calls backend to ensure real-time policy
        enforcement. Backend handles caching via Redis for performance (<10ms).

        Args:
            _force_refresh: Ignored (kept for API compatibility, always fetches from backend)

        Returns:
            TokenResponse (for internal use only - never exposed to developer)

        Note:
            - Every call ensures real-time policy checks
            - Backend Redis cache provides performance (5-15min TTL)
            - Complete audit trail (backend logs every token access)
            - Instant revocation (no SDK-side cache delays)
        """
        # ALWAYS fetch from backend - no SDK-side caching
        # Backend handles caching efficiently via Redis
        self._token = await self.vault._get_token(  # noqa: SLF001 - Internal use by wrappers
            provider_id=self.provider_id,
            attributes=self.user,  # Internal _get_token still uses 'attributes' parameter
            reason=self.reason,
        )
        self._connection_id = self._token.connection_id

        # Recreate client with new token
        self._client = None

        return self._token

    async def _log_api_call(
        self,
        method: str,
        url: str,
        request_headers: dict[str, str] | None = None,
        request_body: Any | None = None,
        response_status: int = 0,
        response_headers: dict[str, str] | None = None,
        response_body: Any | None = None,
        latency_ms: int = 0,
    ) -> None:
        """
        Log API call to backend audit endpoint.

        This is a convenience wrapper around vault.log_api_call().

        Args:
            method: HTTP method
            url: Full API URL
            request_headers: Request headers
            request_body: Request body
            response_status: HTTP status code
            response_headers: Response headers
            response_body: Response body
            latency_ms: Latency in milliseconds
        """
        if self._connection_id is None:
            # Can't log without connection ID
            return

        await self.vault.log_api_call(
            connection_id=self._connection_id,
            provider_id=self.provider_id,
            method=method,
            url=url,
            request_headers=request_headers,
            request_body=request_body,
            response_status=response_status,
            response_headers=response_headers,
            response_body=response_body,
            latency_ms=latency_ms,
            reason=self.reason,
        )

    @abstractmethod
    def _create_client(self, access_token: str) -> Any:
        """
        Create provider-specific SDK client.

        Subclasses must implement this to create the actual provider client
        (e.g., Google API client, GitHub client, etc.)

        Args:
            access_token: OAuth access token

        Returns:
            Provider-specific client instance
        """
        raise NotImplementedError("Subclasses must implement _create_client()")

    async def _get_client(self) -> Any:
        """
        Get or create provider client.

        Returns:
            Provider-specific client instance
        """
        # Ensure token is valid
        token = await self._ensure_token()

        # Create client if needed
        if self._client is None:
            self._client = self._create_client(token.access_token)

        return self._client
