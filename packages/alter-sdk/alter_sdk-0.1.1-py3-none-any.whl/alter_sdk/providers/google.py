"""
Google API client wrapper.

Wraps google-api-python-client with automatic token injection and audit logging.
"""

import time
from typing import Any

from alter_sdk.exceptions import ProviderAPIError
from alter_sdk.providers.base import BaseProviderWrapper


class GoogleClientWrapper(BaseProviderWrapper):
    """
    Wrapper for Google API Python client.

    This class wraps the google-api-python-client library, automatically
    injecting OAuth tokens and logging all API calls.

    Example:
        ```python
        google = await vault.get_client("google", {"user_id": "alice"})
        calendar = await google.build("calendar", "v3")
        events = calendar.events().list(calendarId="primary").execute()
        ```
    """

    def _create_client(self, access_token: str) -> Any:
        """
        Create Google API credentials.

        Args:
            access_token: OAuth access token

        Returns:
            Google credentials object
        """
        try:
            from google.oauth2.credentials import Credentials
        except ImportError as e:
            raise ImportError(
                "Google API client requires google-auth. "
                "Install with: pip install alter-sdk[google]",
            ) from e

        # Create credentials from access token
        # Note: We don't have refresh token, so token refresh will fail
        # SDK will fetch new token from Alter Vault instead
        return Credentials(token=access_token)

    async def build(self, service_name: str, version: str, **kwargs: Any) -> Any:
        """
        Build a Google API service.

        This wraps googleapiclient.discovery.build() with automatic token
        injection and audit logging.

        Args:
            service_name: Google API service name (e.g., "calendar", "gmail")
            version: API version (e.g., "v3", "v1")
            **kwargs: Additional arguments passed to build()

        Returns:
            Wrapped Google API service object
        """
        try:
            from googleapiclient.discovery import build
        except ImportError as e:
            raise ImportError(
                "Google API client requires google-api-python-client. "
                "Install with: pip install alter-sdk[google]",
            ) from e

        # Get credentials
        credentials = await self._get_client()

        # Build service
        service = build(service_name, version, credentials=credentials, **kwargs)

        # Wrap service to intercept execute() calls
        return GoogleServiceProxy(
            service=service,
            wrapper=self,
        )


class GoogleServiceProxy:
    """
    Proxy for Google API service.

    Intercepts method calls to wrap them with audit logging.
    """

    def __init__(self, service: Any, wrapper: GoogleClientWrapper) -> None:
        """Initialize proxy."""
        self._service = service
        self._wrapper = wrapper

    def __getattr__(self, name: str) -> Any:
        """
        Intercept attribute access.

        Returns wrapped resources/methods for audit logging.
        """
        attr = getattr(self._service, name)

        # If it's a resource, wrap it
        if hasattr(attr, "_baseUrl"):
            return GoogleResourceProxy(resource=attr, wrapper=self._wrapper)

        # Otherwise return as-is
        return attr


class GoogleResourceProxy:
    """
    Proxy for Google API resource.

    Intercepts method calls to wrap them with audit logging.
    """

    def __init__(self, resource: Any, wrapper: GoogleClientWrapper) -> None:
        """Initialize proxy."""
        self._resource = resource
        self._wrapper = wrapper

    def __getattr__(self, name: str) -> Any:
        """
        Intercept method calls.

        Returns wrapped methods for audit logging.
        """
        attr = getattr(self._resource, name)

        # If it's callable, wrap it
        if callable(attr):

            def wrapped_method(*args: Any, **kwargs: Any) -> Any:
                """Wrapped method with audit logging."""
                method = attr(*args, **kwargs)

                # Wrap execute() to log API calls
                if hasattr(method, "execute"):
                    original_execute = method.execute

                    async def wrapped_execute(**exec_kwargs: Any) -> Any:
                        """Wrapped execute with audit logging."""
                        start_time = time.time()

                        try:
                            # Call original execute
                            result = original_execute(**exec_kwargs)

                        except Exception as e:
                            # Calculate latency
                            latency_ms = int((time.time() - start_time) * 1000)

                            # Log failed API call
                            url = getattr(method, "uri", "unknown")
                            http_method = getattr(method, "method", "GET")

                            # Access parent wrapper's log method
                            await self._wrapper._log_api_call(  # noqa: SLF001
                                method=http_method,
                                url=url,
                                response_status=500,
                                latency_ms=latency_ms,
                            )

                            raise ProviderAPIError(
                                message=f"Google API call failed: {e}",
                                status_code=500,
                                response_body=str(e),
                            ) from e
                        else:
                            # Calculate latency
                            latency_ms = int((time.time() - start_time) * 1000)

                            # Log API call (best effort - extract URL from method)
                            url = getattr(method, "uri", "unknown")
                            http_method = getattr(method, "method", "GET")

                            # Access parent wrapper's log method
                            await self._wrapper._log_api_call(  # noqa: SLF001
                                method=http_method,
                                url=url,
                                response_status=200,
                                latency_ms=latency_ms,
                            )

                            return result

                    method.execute = wrapped_execute

                return method

            return wrapped_method

        # If it's another resource, wrap it
        if hasattr(attr, "_baseUrl"):
            return GoogleResourceProxy(resource=attr, wrapper=self._wrapper)

        # Otherwise return as-is
        return attr
