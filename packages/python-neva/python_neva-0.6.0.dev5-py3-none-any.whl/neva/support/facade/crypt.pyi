"""Type stub for Crypt facade."""

from typing import override

from neva import Result
from neva.arch import Facade
from neva.security.encryption.protocol import JsonValue

class Crypt(Facade):
    @classmethod
    @override
    def get_facade_accessor(cls) -> type: ...
    @classmethod
    def encrypt(cls, value: JsonValue) -> Result[str, str]:
        """Encrypt a value.

        Args:
            value: The value to encrypt. Non-string values are JSON serialized.

        Returns:
            Ok with base64-encoded encrypted payload, or Err with message.
        """

    @classmethod
    def decrypt(cls, payload: str) -> Result[JsonValue, str]:
        """Decrypt a payload.

        Args:
            payload: Base64-encoded encrypted payload.

        Returns:
            Ok with the decrypted value, or Err with message.
        """
