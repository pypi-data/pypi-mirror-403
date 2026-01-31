"""Hasher protocol."""

from typing import Protocol


class Hasher(Protocol):
    """Wrapper hasher class."""

    def make(
        self,
        plaintext: str | bytes,
        *,
        salt: bytes | None = None,
    ) -> str:
        """Hash a plaintext password."""
        ...

    def check(
        self,
        plaintext: str | bytes,
        hashed: str | bytes,
    ) -> bool:
        """Verify a password against a hashed value."""
        ...

    def needs_rehash(
        self,
        hashed: str | bytes,
    ) -> bool:
        """Check if a hashed value needs to be rehashed."""
        ...
