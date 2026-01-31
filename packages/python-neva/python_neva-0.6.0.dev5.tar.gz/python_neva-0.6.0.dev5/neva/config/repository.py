"""Configuration repository with dot notation support and immutability.

This module provides the ConfigRepository class which serves as the central
store for all application configuration values. It supports dot notation for
nested access and can be frozen to prevent modifications after initialization.
"""

from typing import Any

from neva import Err, Ok, Result


class ConfigRepository:
    """Central repository for application configuration with dot notation support.

    The configuration repository provides a hierarchical key-value store with
    support for dot notation (e.g., "database.host") and the ability to freeze
    configuration to prevent runtime modifications.

    Attributes:
        _items: Dictionary storing all configuration values.
        _frozen: Whether the configuration is frozen and immutable.

    """

    def __init__(self) -> None:
        """Initialize an empty configuration repository."""
        self._items: dict[str, Any] = {}
        self._frozen: bool = False

    def set(self, key: str, value: object) -> Result[None, str]:
        """Set a configuration value using dot notation.

        Creates nested dictionaries as needed to support dot notation paths.

        Args:
            key: Dot-notated key path (e.g., "database.host").
            value: The value to set.

        Returns:
            Result indicating success or an error if frozen or path conflicts.

        """
        if self._frozen:
            return Err(f"Cannot set config key '{key}': configuration is frozen")

        keys = key.split(".")
        current = self._items

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                return Err(
                    f"Cannot set '{key}': '{k}' is not a dictionary "
                    + f"(found {type(current[k]).__name__})"
                )
            current = current[k]

        current[keys[-1]] = value
        return Ok(None)

    def get(self, key: str, default: object = None) -> Result[Any, str]:
        """Get a configuration value using dot notation.

        Args:
            key: Dot-notated key path (e.g., "database.host").
            default: Default value to return if key is not found.

        Returns:
            Result containing the configuration value or the default.

        """
        keys = key.split(".")
        current = self._items

        try:
            for k in keys:
                if not isinstance(current, dict):
                    if default is not None:
                        return Ok(default)
                    return Err(f"Config key '{key}' not found")
                current = current[k]
            return Ok(current)
        except KeyError:
            if default is not None:
                return Ok(default)
            return Err(f"Config key '{key}' not found")

    def has(self, key: str) -> bool:
        """Check if a configuration key exists.

        Args:
            key: Dot-notated key path to check.

        Returns:
            True if the key exists, False otherwise.

        """
        return self.get(key).is_ok

    def all(self) -> dict[str, Any]:
        """Get all configuration items as a dictionary.

        Returns:
            A copy of the entire configuration dictionary.

        """
        return self._items.copy()

    def freeze(self) -> None:
        """Freeze the configuration to prevent further changes.

        Once frozen, all set and merge operations will fail. This is useful
        to ensure configuration remains immutable after application startup.
        """
        self._frozen = True

    def is_frozen(self) -> bool:
        """Check if configuration is frozen.

        Returns:
            True if the configuration is frozen, False otherwise.

        """
        return self._frozen

    def merge(self, key: str, items: dict[str, Any]) -> Result[None, str]:
        """Merge items into a configuration namespace.

        Updates the dictionary at the given key with the provided items.
        Creates the namespace if it doesn't exist.

        Args:
            key: The namespace key to merge into.
            items: Dictionary of items to merge.

        Returns:
            Result indicating success or an error if frozen or type mismatch.

        """
        if self._frozen:
            return Err(f"Cannot merge into '{key}': configuration is frozen")

        if key not in self._items:
            self._items[key] = {}

        if not isinstance(self._items[key], dict):
            return Err(
                f"Cannot merge into '{key}': "
                f"existing value is {type(self._items[key]).__name__}, not dict"
            )

        self._items[key].update(items)
        return Ok(None)
