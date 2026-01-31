"""Type stop for Hash facade."""

from typing import override
from neva.arch import Facade

class Hash(Facade):
    @classmethod
    @override
    def get_facade_accessor(cls) -> type: ...
    @classmethod
    def make(
        cls,
        plaintext: str | bytes,
        *,
        salt: bytes | None = None,
        hasher: str | None = None,
    ) -> str:
        """Hash a plaintext password using the specified or default hasher.

        Args:
            plaintext: The password to hash.
            salt: Optional salt for the hash.
            hasher: Name of the hasher to use (defaults to configured hasher).

        Returns:
            The hashed password string.
        """

    @classmethod
    def check(
        cls,
        plaintext: str | bytes,
        hashed: str | bytes,
        *,
        hasher: str | None = None,
    ) -> bool:
        """Verify a password against a hashed value.

        Args:
            plaintext: The plaintext password to verify.
            hashed: The hashed password to verify against.
            hasher: Name of the hasher to use (defaults to configured hasher).

        Returns:
            True if the password matches, False otherwise.
        """

    @classmethod
    def needs_rehash(
        cls,
        hashed: str | bytes,
        *,
        hasher: str | None = None,
    ) -> bool:
        """Check if a hashed password needs to be rehashed.

        Args:
            hashed: The hashed password to check.
            hasher: Name of the hasher to use (defaults to configured hasher).

        Returns:
            True if the password needs rehashing, False otherwise.
        """
