"""
Generic HTTP client for unsupported providers.

Provides simple HTTP methods with automatic OAuth token injection and audit logging.

SECURITY: This client uses the vault's _provider_client which does NOT have
x-api-key in headers, preventing credential leakage to external providers.
"""

import time
from typing import TYPE_CHECKING, Any

import httpx

from alter_sdk.exceptions import ProviderAPIError
from alter_sdk.providers.base import BaseProviderWrapper

if TYPE_CHECKING:
    from alter_sdk.client import AlterVault

# HTTP status codes
HTTP_BAD_REQUEST = 400


class GenericHTTPClient(BaseProviderWrapper):
    """
    Generic HTTP client with automatic OAuth token injection.

    This client provides simple HTTP methods (GET, POST, PUT, PATCH, DELETE)
    that automatically inject OAuth tokens in the Authorization header and
    log all requests to the backend.

    Uses the vault's shared _provider_client for:
    - HTTP/2 support
    - Connection pooling
    - Consistent security (no x-api-key leakage)

    Use this for providers that don't have dedicated SDK wrappers.

    Example:
        ```python
        client = await vault.get_generic_client("custom-api", {"user_id": "alice"})

        # GET request
        response = await client.get("https://api.custom.com/v1/users")

        # POST request
        response = await client.post(
            "https://api.custom.com/v1/items",
            json={"name": "New Item"}
        )
        ```
    """

    def __init__(
        self,
        vault: "AlterVault",
        provider_id: str,
        user: dict[str, Any],
        reason: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize generic HTTP client.

        Args:
            vault: AlterVault instance
            provider_id: OAuth provider identifier
            user: User attributes to match connection
            reason: Optional reason for token access
            timeout: Request timeout in seconds (default: 30.0)
        """
        super().__init__(vault, provider_id, user, reason)
        self._timeout = timeout
        # NOTE: We use vault._provider_client instead of creating our own client.
        # This ensures:
        # - HTTP/2 support
        # - Connection pooling (shared with call_api())
        # - NO x-api-key header (security)
        # - Per-request timeout (custom timeout via timeout parameter)

    def _create_client(self, access_token: str) -> Any:
        """
        Generic client just needs the token.

        Args:
            access_token: OAuth access token

        Returns:
            The access token itself (stored for injection)
        """
        return access_token

    async def _request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make HTTP request with automatic token injection and audit logging.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL
            headers: Optional headers dict
            **kwargs: Additional arguments passed to httpx.request()
                     (e.g., json={...}, data={...}, timeout=60.0)

        Returns:
            httpx.Response object

        Raises:
            ProviderAPIError: If API call fails

        Note:
            If timeout is passed in kwargs, it overrides the instance timeout.
        """
        # Ensure we have valid token
        token = await self._ensure_token()

        # Inject Authorization header
        if headers is None:
            headers = {}

        headers["Authorization"] = f"Bearer {token.access_token}"

        # Handle timeout: kwargs timeout overrides instance timeout
        if "timeout" not in kwargs:
            kwargs["timeout"] = self._timeout

        # Track timing
        start_time = time.time()

        try:
            # Make request using vault's shared provider client
            # SECURITY: _provider_client has NO x-api-key header
            response = await self.vault._provider_client.request(  # noqa: SLF001 - Internal SDK use
                method=method,
                url=url,
                headers=headers,
                **kwargs,
            )

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Log API call
            await self._log_api_call(
                method=method,
                url=url,
                request_headers=headers,
                request_body=kwargs.get("json") or kwargs.get("data"),
                response_status=response.status_code,
                response_headers=dict(response.headers),
                response_body=response.text if response.status_code < HTTP_BAD_REQUEST else None,
                latency_ms=latency_ms,
            )

            # Raise for HTTP errors
            response.raise_for_status()

        except httpx.HTTPStatusError as e:
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Log failed call
            await self._log_api_call(
                method=method,
                url=url,
                request_headers=headers,
                response_status=e.response.status_code,
                response_headers=dict(e.response.headers),
                response_body=e.response.text,
                latency_ms=latency_ms,
            )

            raise ProviderAPIError(
                message=f"HTTP {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
                response_body=e.response.text,
            ) from e

        except Exception as e:
            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Log failed call
            await self._log_api_call(
                method=method,
                url=url,
                request_headers=headers,
                response_status=0,
                latency_ms=latency_ms,
            )

            raise ProviderAPIError(
                message=f"Request failed: {e}",
                status_code=0,
                response_body=str(e),
            ) from e
        else:
            return response

    async def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make GET request.

        Args:
            url: Full URL
            headers: Optional headers dict
            **kwargs: Additional arguments passed to httpx.get()

        Returns:
            httpx.Response object
        """
        return await self._request("GET", url, headers=headers, **kwargs)

    async def post(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make POST request.

        Args:
            url: Full URL
            headers: Optional headers dict
            **kwargs: Additional arguments passed to httpx.post()
                     (e.g., json={...}, data={...})

        Returns:
            httpx.Response object
        """
        return await self._request("POST", url, headers=headers, **kwargs)

    async def put(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make PUT request.

        Args:
            url: Full URL
            headers: Optional headers dict
            **kwargs: Additional arguments passed to httpx.put()

        Returns:
            httpx.Response object
        """
        return await self._request("PUT", url, headers=headers, **kwargs)

    async def patch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make PATCH request.

        Args:
            url: Full URL
            headers: Optional headers dict
            **kwargs: Additional arguments passed to httpx.patch()

        Returns:
            httpx.Response object
        """
        return await self._request("PATCH", url, headers=headers, **kwargs)

    async def delete(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make DELETE request.

        Args:
            url: Full URL
            headers: Optional headers dict
            **kwargs: Additional arguments passed to httpx.delete()

        Returns:
            httpx.Response object
        """
        return await self._request("DELETE", url, headers=headers, **kwargs)

    # NOTE: No close() method needed - we use vault's shared _provider_client
    # which is closed when vault.close() is called.
