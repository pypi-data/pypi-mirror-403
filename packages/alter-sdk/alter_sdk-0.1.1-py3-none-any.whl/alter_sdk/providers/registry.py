"""
Provider registry for Alter SDK.

This registry tracks which OAuth providers have dedicated SDK wrappers vs
which should use the generic HTTP client.

For scalability with 100+ providers:
- Only popular providers get dedicated wrappers (better DX)
- All other providers automatically use generic HTTP client
- Registry stays in sync with backend via API
"""

from typing import Any

# Static registry: Providers with dedicated Python SDK wrappers
# Only add providers here if they have a popular, well-maintained Python SDK
WRAPPER_REGISTRY: dict[str, dict[str, Any]] = {
    "google": {
        "name": "Google",
        "wrapper_class": "GoogleClientWrapper",
        "module_path": "alter_sdk.providers.google",
        "dependencies": ["google-api-python-client", "google-auth"],
        "sdk_url": "https://github.com/googleapis/google-api-python-client",
        "description": "Wrapper for Google APIs (Calendar, Gmail, Drive, etc.)",
    },
    "github": {
        "name": "GitHub",
        "wrapper_class": "GitHubClientWrapper",
        "module_path": "alter_sdk.providers.github",
        "dependencies": ["PyGithub"],
        "sdk_url": "https://github.com/PyGithub/PyGithub",
        "description": "Wrapper for GitHub API v3",
    },
    # Add more only if they have popular Python SDKs:
}


class ProviderRegistry:
    """
    Provider registry with backend sync capability.

    This class manages the list of available providers and determines
    whether to use a dedicated wrapper or generic HTTP client.
    """

    def __init__(self) -> None:
        """Initialize registry."""
        self._backend_providers: list[str] | None = None

    def has_wrapper(self, provider_id: str) -> bool:
        """
        Check if provider has a dedicated SDK wrapper.

        Args:
            provider_id: OAuth provider identifier

        Returns:
            True if provider has dedicated wrapper, False otherwise
        """
        return provider_id in WRAPPER_REGISTRY

    def get_wrapper_info(self, provider_id: str) -> dict[str, Any] | None:
        """
        Get wrapper information for a provider.

        Args:
            provider_id: OAuth provider identifier

        Returns:
            Wrapper info dict, or None if no wrapper exists
        """
        return WRAPPER_REGISTRY.get(provider_id)

    def list_providers_with_wrappers(self) -> list[str]:
        """
        List all providers that have dedicated SDK wrappers.

        Returns:
            List of provider IDs with wrappers
        """
        return list(WRAPPER_REGISTRY.keys())

    async def sync_with_backend(self, vault: Any) -> list[str]:
        """
        Fetch list of all available providers from backend.

        This allows SDK to know about all 100+ providers supported by backend,
        even if they don't have dedicated wrappers.

        Args:
            vault: AlterVault instance

        Returns:
            List of all provider IDs from backend

        Note:
            This is optional - SDK will work without calling this.
            Useful for showing users "available providers" in your app.
        """
        try:
            # Call backend API to get all providers
            # Access private client to make API call
            response = await vault._alter_client.get("/oauth/providers")  # noqa: SLF001
            response.raise_for_status()

        except Exception:
            # If sync fails, fall back to wrapper registry only
            return list(WRAPPER_REGISTRY.keys())
        else:
            providers_data = response.json()
            self._backend_providers = [p["provider_id"] for p in providers_data]
            return self._backend_providers

    def list_all_providers(self) -> list[str]:
        """
        List all available providers (from backend if synced).

        Returns:
            List of all provider IDs. If backend sync was called, returns
            all providers from backend. Otherwise returns only providers
            with wrappers.
        """
        if self._backend_providers:
            return self._backend_providers
        return list(WRAPPER_REGISTRY.keys())

    def uses_generic_client(self, provider_id: str) -> bool:
        """
        Check if provider will use generic HTTP client.

        Args:
            provider_id: OAuth provider identifier

        Returns:
            True if provider uses generic client, False if it has wrapper
        """
        return not self.has_wrapper(provider_id)


# Singleton instance
_registry_instance: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    """
    Get singleton provider registry instance.

    Returns:
        ProviderRegistry instance
    """
    global _registry_instance  # noqa: PLW0603
    if _registry_instance is None:
        _registry_instance = ProviderRegistry()
    return _registry_instance
