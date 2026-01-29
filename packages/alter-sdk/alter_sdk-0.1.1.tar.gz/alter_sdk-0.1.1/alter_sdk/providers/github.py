"""
GitHub API client wrapper.

Wraps PyGithub with automatic token injection and audit logging.

NOTE: PyGithub is a synchronous library. This wrapper:
1. Initializes asynchronously (token retrieval)
2. Then proxies to the synchronous PyGithub client
3. Logs API calls in the background (fire-and-forget)
"""

import asyncio
import time
from typing import Any

from alter_sdk.exceptions import ProviderAPIError
from alter_sdk.providers.base import BaseProviderWrapper


class GitHubClientWrapper(BaseProviderWrapper):
    """
    Wrapper for PyGithub client.

    This class wraps the PyGithub library, automatically injecting OAuth
    tokens and logging all API calls.

    IMPORTANT: This wrapper must be initialized before use. The vault.get_client()
    method handles this automatically.

    Example:
        ```python
        github = await vault.get_client("github", {"user_id": "bob"})
        user = github.get_user()  # Synchronous PyGithub call
        repos = user.get_repos()
        ```
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize wrapper."""
        super().__init__(*args, **kwargs)
        self._initialized = False
        self._background_tasks: set[asyncio.Task[None]] = set()

    def _create_client(self, access_token: str) -> Any:
        """
        Create GitHub client.

        Args:
            access_token: OAuth access token

        Returns:
            PyGithub client instance
        """
        try:
            from github import Github
            from github.Auth import Token
        except ImportError as e:
            raise ImportError(
                "GitHub API client requires PyGithub. "
                "Install with: pip install alter-sdk[github]",
            ) from e

        # Create GitHub client with access token using proper Auth object
        return Github(auth=Token(access_token))

    async def initialize(self) -> "GitHubClientWrapper":
        """
        Initialize the wrapper by fetching token and creating client.

        This must be called before using any PyGithub methods.
        vault.get_client() calls this automatically.

        Returns:
            Self for method chaining
        """
        if not self._initialized:
            # Fetch token and create client
            await self._get_client()
            self._initialized = True
        return self

    def _schedule_log(
        self,
        method: str,
        url: str,
        response_status: int,
        latency_ms: int,
    ) -> None:
        """
        Schedule audit log in background (fire-and-forget).

        This handles both sync and async contexts safely.
        """
        try:
            # Try to get the running event loop
            loop = asyncio.get_running_loop()

            # Schedule the coroutine
            task = loop.create_task(
                self._log_api_call(
                    method=method,
                    url=url,
                    response_status=response_status,
                    latency_ms=latency_ms,
                ),
            )

            # Store task reference to prevent premature garbage collection
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        except RuntimeError:
            # No running event loop - we're in a sync context
            # Skip logging (can't run async code without event loop)
            pass

    def __getattr__(self, name: str) -> Any:
        """
        Proxy attribute access to underlying GitHub client.

        This intercepts all method calls to the GitHub client and wraps
        them with audit logging.
        """
        # Check if initialized
        if not self._initialized:
            raise RuntimeError(
                "GitHubClientWrapper not initialized. "
                "Use 'github = await vault.get_client(\"github\", ...)' first.",
            )

        # Get the cached client (already created during initialize())
        if self._client is None:
            raise RuntimeError("GitHub client not available. Token may have expired.")

        # Get the attribute from real client
        attr = getattr(self._client, name)

        # If it's callable, wrap it with audit logging
        if callable(attr):

            def wrapped_method(*args: Any, **kwargs: Any) -> Any:
                """Wrapped method with audit logging."""
                start_time = time.time()

                try:
                    # Call original method
                    result = attr(*args, **kwargs)

                except Exception as e:
                    # Calculate latency
                    latency_ms = int((time.time() - start_time) * 1000)

                    # Log failed API call (fire-and-forget)
                    self._schedule_log(
                        method="GET",
                        url=f"https://api.github.com/{name}",
                        response_status=500,
                        latency_ms=latency_ms,
                    )

                    raise ProviderAPIError(
                        message=f"GitHub API call failed: {e}",
                        status_code=500,
                        response_body=str(e),
                    ) from e
                else:
                    # Calculate latency
                    latency_ms = int((time.time() - start_time) * 1000)

                    # Log API call (fire-and-forget)
                    self._schedule_log(
                        method="GET",  # Most GitHub calls are GET
                        url=f"https://api.github.com/{name}",
                        response_status=200,
                        latency_ms=latency_ms,
                    )

                    return result

            return wrapped_method

        # Return attribute as-is
        return attr
