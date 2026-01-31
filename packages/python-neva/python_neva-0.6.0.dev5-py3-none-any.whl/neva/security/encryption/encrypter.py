"""Encryption service using AES-256-GCM."""

import base64
import binascii
import json
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from neva import Err, Ok, Result
from neva.arch import Application
from neva.config import ConfigRepository
from neva.security.encryption.protocol import JsonValue


class DecryptionError(Exception):
    """Raised when decryption fails."""


class AesEncrypter:
    """Encryption service using AES-256-GCM."""

    def __init__(self, app: Application) -> None:
        """Initialize the encrypter.

        Keys are loaded lazily on first encrypt/decrypt call to avoid
        re-entering the DI container during construction.

        Args:
            app: The application instance for configuration access.
        """
        self._app: Application = app
        self._ciphers: list[AESGCM] | None = None

    @staticmethod
    def generate_key() -> str:
        """Generate a 32-bytes encryption key.

        Returns:
            A base64-encoded 32-byte key suitable for AES-256.
        """
        return base64.b64encode(os.urandom(32)).decode()

    def encrypt(self, value: JsonValue) -> Result[str, str]:
        """Encrypt a value.

        Args:
            value: The value to encrypt. Non-string values are JSON serialized.

        Returns:
            Ok with base64-encoded encrypted payload, or Err with message.
        """
        if isinstance(value, str):
            wrapper = {"__str__": value}
        else:
            wrapper = {"__json__": value}

        try:
            payload = json.dumps(wrapper)
        except (TypeError, ValueError) as e:
            return Err(f"Failed to serialize value: {e}")

        plaintext = payload.encode("utf-8")
        iv = os.urandom(12)

        ciphers = self._get_ciphers()
        ciphertext = ciphers[0].encrypt(iv, plaintext, None)

        encrypted_payload = json.dumps(
            {
                "iv": base64.b64encode(iv).decode("ascii"),
                "value": base64.b64encode(ciphertext).decode("ascii"),
            }
        )

        return Ok(base64.b64encode(encrypted_payload.encode("utf-8")).decode("ascii"))

    def decrypt(self, payload: str) -> Result[JsonValue, str]:
        """Decrypt a payload.

        Args:
            payload: Base64-encoded encrypted payload.

        Returns:
            Ok with the decrypted value, or Err with message.
        """
        try:
            encrypted_data = json.loads(base64.b64decode(payload))
            iv = base64.b64decode(encrypted_data["iv"])
            ciphertext = base64.b64decode(encrypted_data["value"])
        except (json.JSONDecodeError, KeyError, binascii.Error) as e:
            return Err(f"Invalid encrypted payload format: {e}")

        for cipher in self._get_ciphers():
            try:
                plaintext = cipher.decrypt(iv, ciphertext, None)
                break
            except InvalidTag:
                continue
        else:
            return Err("Decryption failed: invalid key or corrupted data")

        try:
            data = json.loads(plaintext.decode("utf-8"))
            if "__str__" in data:
                return Ok(data["__str__"])
            return Ok(data["__json__"])
        except (json.JSONDecodeError, KeyError) as e:
            return Err(f"Decryption failed: invalid payload structure: {e}")

    def _get_ciphers(self) -> list[AESGCM]:
        """Return cached ciphers, loading keys on first access.

        Returns:
            List of AESGCM cipher instances.
        """
        if self._ciphers is None:
            self._ciphers = self._load_keys()
        return self._ciphers

    def _load_keys(self) -> list[AESGCM]:
        """Load encryption keys from configuration.

        Returns:
            List of AESGCM cipher instances.

        Raises:
            ValueError: If no encryption key is configured.
        """
        config = self._app.make(ConfigRepository).expect(
            "ConfigRepository not found in container"
        )

        key = config.get("app.key", default=None).unwrap_or(None)
        previous_keys = config.get("app.previous_keys", default=[]).unwrap_or([])

        if key is None:
            msg = "No encryption key configured. Set 'app.key' in configuration."
            raise ValueError(msg)

        ciphers = [AESGCM(self._parse_key(key))]

        for prev_key in previous_keys:
            ciphers.append(AESGCM(self._parse_key(prev_key)))

        return ciphers

    def _parse_key(self, key: str) -> bytes:
        """Parse a base64-encoded key into bytes.

        Args:
            key: Base64-encoded 32-byte key.

        Returns:
            The decoded key bytes.

        Raises:
            ValueError: If key is not valid base64 or not 32 bytes.
        """
        try:
            key_bytes = base64.b64decode(key)
        except binascii.Error as e:
            msg = "Invalid encryption key: must be valid base64"
            raise ValueError(msg) from e

        if len(key_bytes) != 32:
            msg = f"Invalid encryption key: must be 32 bytes, got {len(key_bytes)}"
            raise ValueError(msg)

        return key_bytes
