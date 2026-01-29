"""
Performant HTTP client utilities for Alter SDK.

This module provides HTTP client factory functions with connection pooling,
HTTP/2 support, and optimized settings for both Alter backend and provider APIs.

Key Features:
- Connection pooling (reuses TCP connections, avoids 3-way handshake)
- TLS session reuse (avoids handshake overhead)
- HTTP/2 multiplexing for better performance
- Reduces latency by 200-500ms per request

Security:
- Alter client: Includes x-api-key for backend authentication
- Provider client: NO x-api-key (prevents credential leakage to third parties)
"""

import httpx

# SDK version for User-Agent header
SDK_VERSION = "0.1.0"
SDK_USER_AGENT = f"alter-sdk-python/{SDK_VERSION}"

# Default timeout for HTTP requests
DEFAULT_TIMEOUT = 30.0

# Connection pool limits (optimized for SDK usage patterns)
DEFAULT_LIMITS = httpx.Limits(
    max_keepalive_connections=20,  # Keep idle connections warm
    max_connections=100,  # Max concurrent connections
    keepalive_expiry=30.0,  # Keep connections alive for 30 seconds
)

# httpx requires the optional 'h2' dependency when http2=True.
# Keep SDK default install lightweight by enabling HTTP/2 only when available.
try:
    import h2  # type: ignore  # noqa: F401

    _HTTP2_ENABLED = True
except Exception:
    _HTTP2_ENABLED = False


def create_alter_client(
    base_url: str,
    api_key: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> httpx.AsyncClient:
    """
    Create HTTP client for Alter backend API calls.

    This client includes x-api-key header for authentication with Alter backend.
    Should ONLY be used for calls to Alter's API (token retrieval, audit logging).

    Args:
        base_url: Alter backend base URL (e.g., "https://api.alter.com")
        api_key: Alter API key (starts with "alter_key_")
        timeout: Request timeout in seconds

    Returns:
        Configured AsyncClient for Alter backend
    """
    return httpx.AsyncClient(
        base_url=base_url,
        headers={
            "x-api-key": api_key,
            "User-Agent": SDK_USER_AGENT,
        },
        timeout=timeout,
        limits=DEFAULT_LIMITS,
        http2=_HTTP2_ENABLED,
    )


def create_provider_client(
    timeout: float = DEFAULT_TIMEOUT,
) -> httpx.AsyncClient:
    """
    Create HTTP client for external provider API calls.

    SECURITY: This client does NOT include x-api-key header.
    This prevents leaking Alter credentials to third-party providers
    like Google, Stripe, GitHub, etc.

    The OAuth Bearer token is added per-request by call_api().

    Args:
        timeout: Request timeout in seconds

    Returns:
        Configured AsyncClient for provider APIs (no x-api-key!)
    """
    return httpx.AsyncClient(
        headers={
            "User-Agent": SDK_USER_AGENT,
            # NO x-api-key! OAuth token added per-request
        },
        timeout=timeout,
        limits=DEFAULT_LIMITS,
        http2=_HTTP2_ENABLED,
    )
