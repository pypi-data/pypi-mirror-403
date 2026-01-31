"""Encrypter protocol."""

from typing import Any, Protocol, runtime_checkable

from neva import Result

JsonValue = str | int | float | bool | list[Any] | dict[str, Any] | None


@runtime_checkable
class Encrypter(Protocol):
    """Symmetric encryption interface."""

    def encrypt(self, value: JsonValue) -> Result[str, str]:
        """Encrypt a value.

        Args:
            value: The value to encrypt. Non-string values are JSON serialized.

        Returns:
            Ok with base64-encoded encrypted payload, or Err with message.
        """
        ...

    def decrypt(self, payload: str) -> Result[JsonValue, str]:
        """Decrypt a payload.

        Args:
            payload: Base64-encoded encrypted payload.

        Returns:
            Ok with the decrypted value, or Err with message.
        """
        ...
