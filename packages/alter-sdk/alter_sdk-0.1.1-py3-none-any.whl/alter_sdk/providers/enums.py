"""
Provider enum system for type-safe provider identifiers.

This module provides a dynamic Provider enum that syncs with the backend
to provide IDE autocomplete and type safety for provider IDs.
"""

from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from alter_sdk.client import AlterVault


class ProviderMeta(type(Enum)):  # type: ignore
    """Metaclass for Provider enum to enable dynamic member creation."""

    def __contains__(cls, item: Any) -> bool:
        """Check if provider exists in enum."""
        try:
            cls(item)
        except ValueError:
            return False
        else:
            return True


class Provider(str, Enum, metaclass=ProviderMeta):
    """
    Dynamic enum of OAuth provider identifiers.

    This enum is populated dynamically by syncing with the backend's
    list of active providers. It provides:
    - Type safety for provider IDs
    - IDE autocomplete
    - Runtime validation

    Example:
        ```python
        from alter_sdk import AlterVault, Provider

        vault = AlterVault(api_key="...", app_id="...")

        # Type-safe with autocomplete
        google = await vault.get_client(Provider.GOOGLE, user={"user_id": "alice"})

        # String also works (backward compatible)
        google = await vault.get_client("google", user={"user_id": "alice"})
        ```

    The enum syncs automatically on first use via `sync_with_backend()`.
    """

    # Placeholder member (will be replaced during sync)
    __UNSYNCED__ = "__UNSYNCED__"

    # Track sync status (class variables)
    _synced: ClassVar[bool] = False  # type: ignore[misc]
    _provider_ids: ClassVar[list[str]] = []  # type: ignore[misc]

    @classmethod
    async def sync_with_backend(cls, vault: "AlterVault") -> None:
        """
        Sync Provider enum with backend's active providers.

        This fetches the list of active provider IDs from the backend
        and dynamically creates enum members for each.

        Args:
            vault: AlterVault instance to use for API calls

        Raises:
            NetworkError: If backend is unreachable
            Exception: If sync fails
        """
        # Fetch provider IDs from backend (internal access for enum sync)
        response = await vault._alter_client.get("/oauth/providers/ids")  # noqa: SLF001 - Enum sync needs HTTP client
        response.raise_for_status()

        data = response.json()
        provider_ids = data.get("provider_ids", [])

        # Clear existing provider members but keep special members
        for member_name in list(cls.__members__.keys()):
            if member_name not in (
                "_synced",
                "_provider_ids",
            ) and not member_name.startswith("_"):
                # Remove from both internal maps
                if member_name in cls._member_map_:
                    del cls._member_map_[member_name]
                if member_name in cls.__members__:
                    member_value = cls.__members__[member_name].value
                    if member_value in cls._value2member_map_:
                        del cls._value2member_map_[member_value]
                # Remove attribute
                delattr(cls, member_name)

        # Add new members dynamically
        for provider_id in provider_ids:
            # Convert to enum member name (e.g., "google" -> "GOOGLE")
            member_name = provider_id.upper().replace("-", "_")

            # Create enum member
            # We use str.__new__ since Provider inherits from str (Python 3.14+)
            if not hasattr(cls, member_name):
                new_member = str.__new__(cls, provider_id)
                new_member._name_ = member_name
                new_member._value_ = provider_id
                # Use type.__setattr__ for class attributes
                type.__setattr__(cls, member_name, new_member)
                cls._member_map_[member_name] = new_member  # type: ignore
                cls._value2member_map_[provider_id] = new_member  # type: ignore

        # Update state (use type.__setattr__ to bypass enum immutability)
        type.__setattr__(cls, "_synced", True)  # type: ignore[misc]
        type.__setattr__(cls, "_provider_ids", provider_ids)  # type: ignore[misc]

    @classmethod
    def list_all(cls) -> list[str]:
        """
        Get list of all provider IDs.

        Returns:
            List of provider ID strings (e.g., ["google", "github", "slack"])

        Note:
            Returns empty list if not synced yet.
        """
        return cls._provider_ids.copy()

    @classmethod
    def has_provider(cls, provider_id: str) -> bool:
        """
        Check if a provider ID exists.

        Args:
            provider_id: Provider identifier to check

        Returns:
            True if provider exists, False otherwise

        Note:
            Returns False if not synced yet.
        """
        return provider_id in cls._provider_ids

    @classmethod
    def is_synced(cls) -> bool:
        """
        Check if the enum has been synced with backend.

        Returns:
            True if synced, False otherwise
        """
        return cls._synced

    def __str__(self) -> str:
        """Return the provider ID string value."""
        return self.value
