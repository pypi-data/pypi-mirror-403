"""Type stub for Config facade."""

from typing import Any, override

from neva import Result
from neva.arch import Facade

class Config(Facade):
    @classmethod
    @override
    def get_facade_accessor(cls) -> type: ...
    @classmethod
    def set(cls, key: str, value: object) -> Result[None, str]:
        """Set a configuration value using dot notation.

        Creates nested dictionaries as needed to support dot notation paths.

        Args:
            key: Dot-notated key path (e.g., "database.host").
            value: The value to set.

        Returns:
            Result indicating success or an error if frozen or path conflicts.

        """
        ...

    @classmethod
    def get(cls, key: str, default: object = None) -> Result[Any, str]:
        """Get a configuration value using dot notation.

        Args:
            key: Dot-notated key path (e.g., "database.host").
            default: Default value to return if key is not found.

        Returns:
            Result containing the configuration value or the default.

        """
        ...

    @classmethod
    def has(cls, key: str) -> bool:
        """Check if a configuration key exists.

        Args:
            key: Dot-notated key path to check.

        Returns:
            True if the key exists, False otherwise.

        """
        ...

    @classmethod
    def all(cls) -> dict[str, Any]:
        """Get all configuration items as a dictionary.

        Returns:
            A copy of the entire configuration dictionary.

        """
        ...

    @classmethod
    def freeze(cls) -> None:
        """Freeze the configuration to prevent further changes.

        Once frozen, all set and merge operations will fail. This is useful
        to ensure configuration remains immutable after application startup.
        """
        ...

    @classmethod
    def is_frozen(cls) -> bool:
        """Check if configuration is frozen.

        Returns:
            True if the configuration is frozen, False otherwise.

        """
        ...

    @classmethod
    def merge(cls, key: str, items: dict[str, Any]) -> Result[None, str]:
        """Merge items into a configuration namespace.

        Updates the dictionary at the given key with the provided items.
        Creates the namespace if it doesn't exist.

        Args:
            key: The namespace key to merge into.
            items: Dictionary of items to merge.

        Returns:
            Result indicating success or an error if frozen or type mismatch.

        """
