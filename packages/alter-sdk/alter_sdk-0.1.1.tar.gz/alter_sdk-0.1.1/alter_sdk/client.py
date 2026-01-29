"""
Main Alter Vault SDK client.

This module provides the primary AlterVault class for interacting with
the Alter Vault OAuth token management system.
"""

import logging
from typing import TYPE_CHECKING, Any, Union
from uuid import UUID

import httpx

from alter_sdk.exceptions import (
    ConnectionNotFoundError,
    NetworkError,
    PolicyViolationError,
    TokenExpiredError,
    TokenRetrievalError,
)
from alter_sdk.models import APICallAuditLog, TokenResponse

if TYPE_CHECKING:
    from alter_sdk.providers.enums import Provider

logger = logging.getLogger(__name__)

# HTTP status codes as constants
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_BAD_REQUEST = 400
HTTP_BAD_GATEWAY = 502

# Request/Response size limits
MAX_BODY_SIZE_BYTES = 10000  # 10KB max for audit log bodies
HTTP_CLIENT_ERROR_START = 400  # HTTP status codes >= 400 are errors


class AlterVault:
    """
    Main SDK class for Alter Vault OAuth token management.

    This class handles:
    - Token retrieval from Alter Vault backend (tokens never exposed)
    - Audit logging of API calls
    - Provider client creation

    Zero Token Exposure:
    - Tokens are retrieved internally but NEVER exposed to developers
    - All API calls inject tokens automatically behind the scenes
    - Developers only see API results, never authentication credentials

    HTTP Client Architecture (Security):
        This SDK uses TWO separate HTTP clients to prevent credential leakage:

        1. _alter_client (for Alter backend):
           - Communicates with api.alter.com
           - Includes x-api-key header for authentication
           - Used by: _get_token(), log_api_call()

        2. _provider_client (for external APIs):
           - Calls Google, Stripe, GitHub, etc.
           - NO x-api-key header (prevents leakage!)
           - OAuth token added per-request
           - Used by: call_api()

        ⚠️ SECURITY: The _alter_client must NEVER be used for external API calls,
           as it would leak the Alter API key to third-party providers.

    Example:
        ```python
        vault = AlterVault(
            api_key="alter_key_...",
            app_id="123e4567-e89b-12d3-a456-426614174000"
        )

        # Get provider client (wrapper) - tokens hidden
        google = await vault.get_client("google", user={"user_id": "alice"})
        calendar = await google.build("calendar", "v3")
        events = calendar.events().list(calendarId="primary").execute()

        # Clean up
        await vault.close()
        ```
    """

    def __init__(
        self,
        api_key: str,
        app_id: str,
        base_url: str = "https://api.alter.com",
        enable_audit_logging: bool = True,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize Alter Vault client.

        Args:
            api_key: Alter Vault API key (starts with "alter_key_")
            app_id: Application ID (UUID string)
            base_url: Base URL for Alter Vault API
            enable_audit_logging: Whether to send audit logs to backend
            timeout: HTTP request timeout in seconds

        Raises:
            ValueError: If api_key or app_id is invalid

        Note:
            Token caching is handled by the backend for performance and security.
            SDK always calls backend, but backend returns cached tokens (fast, <10ms).
        """
        # Validate inputs
        if not api_key:
            raise ValueError("api_key is required")
        if not api_key.startswith("alter_key_"):
            raise ValueError("api_key must start with 'alter_key_'")
        if not app_id:
            raise ValueError("app_id is required")

        # Validate app_id is valid UUID
        try:
            UUID(app_id)
        except ValueError as e:
            raise ValueError(f"app_id must be valid UUID: {e}") from e

        self.api_key = api_key
        self.app_id = app_id
        self.base_url = base_url.rstrip("/")
        self.enable_audit_logging = enable_audit_logging

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # HTTP CLIENT ARCHITECTURE - TWO SEPARATE CLIENTS FOR SECURITY
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        #
        # We maintain TWO separate HTTP clients to prevent credential leakage:
        #
        # ┌─────────────────────────────────────────────────────────────────────┐
        # │ _alter_client                                                       │
        # │ ├── Purpose: Communicate with Alter Vault backend                   │
        # │ ├── Headers: x-api-key (Alter API key for authentication)          │
        # │ ├── Base URL: https://api.alter.com (Alter backend)                │
        # │ └── Used by: _get_token(), log_api_call()                          │
        # └─────────────────────────────────────────────────────────────────────┘
        #
        # ┌─────────────────────────────────────────────────────────────────────┐
        # │ _provider_client                                                    │
        # │ ├── Purpose: Call external provider APIs (Google, Stripe, etc.)    │
        # │ ├── Headers: NO x-api-key (prevents credential leakage!)           │
        # │ ├── Base URL: None (varies per provider)                           │
        # │ └── Used by: call_api()                                            │
        # └─────────────────────────────────────────────────────────────────────┘
        #
        # SECURITY: Never use _alter_client for external API calls!
        #           The x-api-key would be leaked to third parties.
        #
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        # Shared connection pool settings for performance
        # Both clients use connection pooling. HTTP/2 is enabled only if the optional
        # 'h2' dependency is installed (httpx requires it for http2=True).
        #
        # We intentionally do NOT force-install httpx[http2] for the SDK, to keep the
        # default install lightweight. If 'h2' isn't present, we fall back to HTTP/1.1.
        try:
            import h2  # type: ignore  # noqa: F401

            _http2_enabled = True
        except Exception:
            _http2_enabled = False

        _shared_limits = httpx.Limits(
            max_keepalive_connections=20,  # Reuse TCP connections
            max_connections=100,  # Handle concurrent requests
            keepalive_expiry=30.0,  # 30s idle timeout
        )

        # ──────────────────────────────────────────────────────────────────────
        # CLIENT 1: Alter Backend Client (_alter_client)
        # ──────────────────────────────────────────────────────────────────────
        # Used for: Token retrieval, audit logging
        # Auth: x-api-key header (Alter API key)
        # Target: Alter Vault backend only (api.alter.com)
        self._alter_client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,  # ✅ Sent to Alter backend
                "User-Agent": "alter-sdk-python/0.1.0",
            },
            timeout=timeout,
            limits=_shared_limits,
            http2=_http2_enabled,
        )

        # ──────────────────────────────────────────────────────────────────────
        # CLIENT 2: Provider API Client (_provider_client)
        # ──────────────────────────────────────────────────────────────────────
        # Used for: Calling external provider APIs (Google, Stripe, GitHub, etc.)
        # Auth: OAuth Bearer token (added per-request, NOT in default headers)
        # Target: External APIs (api.stripe.com, googleapis.com, etc.)
        #
        # ⚠️  SECURITY CRITICAL: NO x-api-key header!
        #     This prevents leaking Alter credentials to third parties.
        self._provider_client = httpx.AsyncClient(
            # NO base_url - varies per provider
            headers={
                "User-Agent": "alter-sdk-python/0.1.0",
                # ❌ NO x-api-key here - would leak to external providers!
            },
            timeout=timeout,
            limits=_shared_limits,
            http2=_http2_enabled,
        )

        # Cache for provider client wrapper instances (GoogleClientWrapper, etc.)
        self._provider_clients: dict[str, Any] = {}

        # Track Provider enum sync status
        self._providers_synced: bool = False

    def _raise_policy_violation(self, error_data: dict[str, Any]) -> None:
        """Raise PolicyViolationError from error data."""
        raise PolicyViolationError(
            message=error_data.get("message", "Access denied by policy"),
            policy_error=error_data.get("error"),
            details=error_data.get("details", {}),
        )

    def _raise_connection_not_found(self, error_data: dict[str, Any]) -> None:
        """Raise ConnectionNotFoundError from error data."""
        raise ConnectionNotFoundError(
            message=error_data.get(
                "message",
                "OAuth connection not found for these attributes",
            ),
            details=error_data,
        )

    def _raise_token_expired(self, error_data: dict[str, Any]) -> None:
        """Raise TokenExpiredError from error data."""
        raise TokenExpiredError(
            message=error_data.get(
                "message",
                "Token expired and refresh failed",
            ),
            connection_id=error_data.get("connection_id"),
            details=error_data,
        )

    def _handle_error_response(self, response: httpx.Response) -> None:
        """
        Handle HTTP error responses from backend.

        Raises appropriate exceptions based on status code.
        """
        if response.status_code == HTTP_FORBIDDEN:
            # Policy violation
            error_data = response.json()
            self._raise_policy_violation(error_data)

        if response.status_code == HTTP_NOT_FOUND:
            # Connection not found
            error_data = response.json()
            self._raise_connection_not_found(error_data)

        if response.status_code in (HTTP_BAD_REQUEST, HTTP_BAD_GATEWAY):
            # Token expired / refresh failed
            error_data = response.json()
            if "token_expired" in str(error_data).lower():
                self._raise_token_expired(error_data)

        # Raise for other HTTP errors
        response.raise_for_status()

    async def _get_token(
        self,
        provider_id: str,
        attributes: dict[str, Any],
        reason: str | None = None,
    ) -> TokenResponse:
        """
        Retrieve OAuth access token for a provider and user (INTERNAL USE ONLY).

        This is a private method used internally by SDK wrappers and call_api().
        Tokens should NEVER be exposed to developers. Use get_client() or call_api()
        instead, which handle tokens internally.

        This method:
        1. Fetches token from backend (backend handles caching)
        2. Returns TokenResponse

        Args:
            provider_id: OAuth provider identifier (e.g., "google", "github")
            attributes: User attributes to match connection (e.g., {"user_id": "alice"})
            reason: Optional reason for token access (for audit)

        Returns:
            TokenResponse with access token and metadata (for internal use only)

        Raises:
            PolicyViolationError: If access denied by policy (403)
            ConnectionNotFoundError: If no connection found (404)
            TokenExpiredError: If token refresh failed (400/502)
            NetworkError: If backend unreachable
            TokenRetrievalError: For other errors

        Note:
            Backend handles token caching for performance (<10ms response time).
            SDK always calls backend to ensure real-time policy enforcement.
        """
        # Fetch token from backend (no SDK-side caching)
        try:
            response = await self._alter_client.post(
                "/oauth/token",
                json={
                    "provider_id": provider_id,
                    "attributes": attributes,
                    "reason": reason,
                },
            )

            # Handle error responses
            self._handle_error_response(response)

        except httpx.ConnectError as e:
            raise NetworkError(
                message=f"Failed to connect to Alter Vault backend: {e}",
                details={"base_url": self.base_url},
            ) from e

        except httpx.TimeoutException as e:
            raise NetworkError(
                message=f"Request to Alter Vault backend timed out: {e}",
                details={"base_url": self.base_url},
            ) from e

        except (PolicyViolationError, ConnectionNotFoundError, TokenExpiredError):
            # Re-raise our custom exceptions
            raise

        except Exception as e:
            # Catch-all for unexpected errors
            raise TokenRetrievalError(
                message=f"Failed to retrieve token: {e}",
                details={"provider_id": provider_id, "error": str(e)},
            ) from e
        else:
            # Parse successful response
            token_data = response.json()
            token = TokenResponse(**token_data)

            logger.debug("Retrieved token for %s", provider_id)
            return token

    async def log_api_call(
        self,
        connection_id: UUID,
        provider_id: str,
        method: str,
        url: str,
        request_headers: dict[str, str] | None = None,
        request_body: Any | None = None,
        response_status: int = 0,
        response_headers: dict[str, str] | None = None,
        response_body: Any | None = None,
        latency_ms: int = 0,
        reason: str | None = None,
    ) -> None:
        """
        Log an API call to the backend audit endpoint.

        This method runs in the background and NEVER raises exceptions to avoid
        crashing the application if audit logging fails.

        Args:
            connection_id: OAuth connection ID
            provider_id: OAuth provider identifier
            method: HTTP method (GET, POST, etc.)
            url: Full API URL
            request_headers: Request headers dict
            request_body: Request body (any JSON-serializable type)
            response_status: HTTP response status code
            response_headers: Response headers dict
            response_body: Response body (any JSON-serializable type)
            latency_ms: Request latency in milliseconds
            reason: Optional reason for API call
        """
        # Check if audit logging is enabled
        if not self.enable_audit_logging:
            return

        try:
            # Create audit log entry
            audit_log = APICallAuditLog(
                connection_id=connection_id,
                provider_id=provider_id,
                method=method,
                url=url,
                request_headers=request_headers,
                request_body=request_body,
                response_status=response_status,
                response_headers=response_headers,
                response_body=response_body,
                latency_ms=latency_ms,
                reason=reason,
            )

            # Sanitize sensitive data
            sanitized = audit_log.sanitize()

            # Send to backend (fire-and-forget)
            response = await self._alter_client.post(
                "/oauth/audit/api-call",
                json=sanitized,
            )
            response.raise_for_status()

            logger.debug("Logged API call to %s", url)

        except Exception as e:
            # NEVER raise - log warning and continue
            logger.warning("Failed to log API call (non-fatal): %s", e)

    async def get_client(
        self,
        provider_id: Union["Provider", str],
        user: dict[str, Any],
        reason: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Get provider-specific client wrapper.

        This method returns a wrapper around the provider's official SDK
        (e.g., google-api-python-client, PyGithub) with automatic token
        injection and audit logging.

        Zero Token Exposure:
        - Tokens retrieved internally but NEVER exposed to developer
        - Wrapper automatically injects tokens in API calls
        - Developer only sees API results, never credentials

        Args:
            provider_id: OAuth provider identifier (Provider enum OR string)
                        - Type-safe: Provider.GOOGLE, Provider.GITHUB
                        - String: "google", "github" (backward compatible)
            user: User attributes to match connection (e.g., {"user_id": "alice"})
            reason: Optional reason for token access
            **kwargs: Additional arguments passed to wrapper constructor

        Returns:
            Provider-specific wrapper instance

        Raises:
            UnsupportedProviderError: If provider is not supported
            (All other exceptions from _get_token())

        Example:
            ```python
            # Type-safe with enum (recommended)
            google = await vault.get_client(Provider.GOOGLE, user={"user_id": "alice"})

            # String-based (backward compatible)
            google = await vault.get_client("google", user={"user_id": "alice"})
            ```
        """
        # Auto-sync providers enum on first use
        await self._ensure_providers_synced()

        # Convert Provider enum to string if needed
        from alter_sdk.providers.enums import Provider

        provider_str = provider_id.value if isinstance(provider_id, Provider) else str(provider_id)

        from alter_sdk.exceptions import UnsupportedProviderError

        # Import provider wrappers dynamically
        try:
            if provider_str == "google":
                from alter_sdk.providers.google import GoogleClientWrapper

                return GoogleClientWrapper(
                    vault=self,
                    provider_id=provider_str,
                    user=user,
                    reason=reason,
                    **kwargs,
                )

            if provider_str == "github":
                from alter_sdk.providers.github import GitHubClientWrapper

                wrapper = GitHubClientWrapper(
                    vault=self,
                    provider_id=provider_str,
                    user=user,
                    reason=reason,
                    **kwargs,
                )
                # Initialize the wrapper (fetches token, creates PyGithub client)
                # This must be done before returning since PyGithub is synchronous
                await wrapper.initialize()
                return wrapper

            raise UnsupportedProviderError(
                message=f"Provider '{provider_str}' is not supported. "
                "Use get_generic_client() or call_api() instead.",
                details={"provider_id": provider_str},
            )

        except ImportError as e:
            raise UnsupportedProviderError(
                message=f"Provider '{provider_str}' requires additional dependencies. "
                f"Install with: pip install alter-sdk[{provider_str}]",
                details={"provider_id": provider_str, "error": str(e)},
            ) from e

    async def get_generic_client(
        self,
        provider_id: str,
        user: dict[str, Any],
        reason: str | None = None,
    ) -> Any:
        """
        Get generic HTTP client for unsupported providers.

        This returns a simple HTTP client that automatically injects
        OAuth tokens in Authorization headers and logs all requests.

        Args:
            provider_id: OAuth provider identifier
            user: User attributes to match connection (e.g., {"user_id": "alice"})
            reason: Optional reason for token access

        Returns:
            GenericHTTPClient instance

        Raises:
            (All exceptions from _get_token())
        """
        from alter_sdk.providers.generic import GenericHTTPClient

        return GenericHTTPClient(
            vault=self,
            provider_id=provider_id,
            user=user,
            reason=reason,
        )

    async def call_api(
        self,
        provider: Union["Provider", str],
        method: str,
        endpoint: str,
        user: dict[str, Any],
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        reason: str | None = None,
    ) -> httpx.Response:
        """
        Execute generic HTTP request to any provider API with automatic token injection.

        This method provides a simple way to call any provider's API without needing
        a dedicated SDK wrapper. Tokens are retrieved and injected automatically -
        NEVER exposed to the developer.

        Zero Token Exposure:
        - Tokens retrieved internally via _get_token() (private method)
        - Authorization header injected automatically
        - Developer only sees API response, never tokens

        Args:
            provider: OAuth provider identifier (Provider enum OR string)
                     - Type-safe: Provider.STRIPE, Provider.SHOPIFY
                     - String: "stripe", "shopify" (backward compatible)
            method: HTTP method ("GET", "POST", "PUT", "DELETE", "PATCH")
            endpoint: API endpoint path (e.g., "/v1/customers")
            user: User attributes to match connection (e.g., {"user_id": "alice"})
            body: Optional request body (dict, will be JSON serialized)
            headers: Optional additional headers (Authorization header auto-injected)
            params: Optional query parameters
            reason: Optional reason for API call (for audit)

        Returns:
            httpx.Response object with:
            - .status_code: HTTP status code
            - .json(): Parse JSON response
            - .text: Raw text response
            - .headers: Response headers

        Raises:
            PolicyViolationError: If access denied by policy (403)
            ConnectionNotFoundError: If no connection found (404)
            TokenExpiredError: If token refresh failed (400/502)
            NetworkError: If API or backend unreachable
            ProviderAPIError: If provider API returns error

        Example:
            ```python
            # Type-safe with enum (recommended)
            response = await vault.call_api(
                provider=Provider.STRIPE,
                method="GET",
                endpoint="/v1/customers",
                user={"org_id": "acme"},
                params={"limit": 10}
            )
            customers = response.json()["data"]

            # String-based (backward compatible)
            response = await vault.call_api(
                provider="shopify",
                method="POST",
                endpoint="/admin/api/2024-01/products.json",
                user={"store_id": "my-store"},
                body={"product": {"title": "New Product", "price": "29.99"}}
            )
            product = response.json()["product"]
            ```

        Note:
            - Developer NEVER sees OAuth token at any point
            - Token injection happens internally
            - All API calls are audited automatically
        """
        # Auto-sync providers enum on first use
        await self._ensure_providers_synced()

        # Convert Provider enum to string if needed
        from alter_sdk.providers.enums import Provider

        provider_str = provider.value if isinstance(provider, Provider) else str(provider)

        import time

        from alter_sdk.exceptions import ProviderAPIError

        # Get token internally (NEVER exposed to developer)
        token_response = await self._get_token(
            provider_id=provider_str,
            attributes=user,  # Internal method still uses 'attributes' parameter name
            reason=reason,
        )

        # Build headers with automatic token injection
        request_headers = headers.copy() if headers else {}
        request_headers["Authorization"] = f"Bearer {token_response.access_token}"
        request_headers.setdefault("User-Agent", "alter-sdk-python/0.1.0")

        # Determine base URL (would need provider-specific configuration)
        # For now, endpoint should be full URL or we need provider base URLs
        url = endpoint if endpoint.startswith("http") else endpoint

        # Execute request using provider client (NO x-api-key!)
        # SECURITY: _provider_client does not include x-api-key header,
        # preventing Alter credentials from leaking to third-party providers.
        start_time = time.time()
        try:
            response = await self._provider_client.request(
                method=method.upper(),
                url=url,
                json=body,
                headers=request_headers,
                params=params,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            # Log API call (fire-and-forget)
            await self.log_api_call(
                connection_id=token_response.connection_id,
                provider_id=provider_str,
                method=method.upper(),
                url=url,
                request_headers=request_headers,
                request_body=body,
                response_status=response.status_code,
                response_headers=dict(response.headers),
                response_body=response.text[:10000]
                if len(response.text) < MAX_BODY_SIZE_BYTES
                else response.text[:MAX_BODY_SIZE_BYTES] + "...",
                latency_ms=latency_ms,
                reason=reason,
            )

            # Check for HTTP errors and raise if needed
            if response.status_code >= HTTP_CLIENT_ERROR_START:
                raise ProviderAPIError(  # noqa: TRY301 - Clear error handling
                    message=f"Provider API returned error {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text,
                    details={
                        "provider": provider_str,
                        "method": method,
                        "endpoint": endpoint,
                    },
                )

            return response  # noqa: TRY300 - Return after conditional raise is clear

        except ProviderAPIError:
            # Re-raise provider API errors
            raise
        except httpx.HTTPError as e:
            raise NetworkError(
                message=f"Failed to call provider API: {e}",
                details={
                    "provider": provider_str,
                    "method": method,
                    "endpoint": endpoint,
                    "error": str(e),
                },
            ) from e

    async def _ensure_providers_synced(self) -> None:
        """
        Ensure Provider enum is synced with backend (INTERNAL USE ONLY).

        This is called automatically on first use of get_client() or call_api()
        to populate the Provider enum with active providers from backend.
        """
        if not self._providers_synced:
            from alter_sdk.providers.enums import Provider

            await Provider.sync_with_backend(self)
            self._providers_synced = True

    async def close(self) -> None:
        """
        Close HTTP clients and release resources.

        This should be called when done using the SDK, or use the SDK
        as an async context manager.
        """
        await self._alter_client.aclose()
        await self._provider_client.aclose()

    async def __aenter__(self) -> "AlterVault":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Async context manager exit."""
        await self.close()
