"""Bcrypt hasher."""

from typing import Literal, override

from pwdlib.hashers.bcrypt import BcryptHasher as PwdLibBcryptHasher

from neva.security.hashing.hashers.protocol import Hasher


class BcryptHasher(Hasher):
    """Bcrypt hasher."""

    def __init__(
        self,
        rounds: int = 12,
        prefix: Literal["2a", "2b"] = "2a",
    ) -> None:
        """Initialize the hasher."""
        self._hasher: PwdLibBcryptHasher = PwdLibBcryptHasher(rounds, prefix)

    @override
    def make(
        self,
        plaintext: str | bytes,
        *,
        salt: bytes | None = None,
    ) -> str:
        return self._hasher.hash(
            password=plaintext,
            salt=salt,
        )

    @override
    def check(
        self,
        plaintext: str | bytes,
        hashed: str | bytes,
    ) -> bool:
        return self._hasher.verify(
            password=plaintext,
            hash=hashed,
        )

    @override
    def needs_rehash(
        self,
        hashed: str | bytes,
    ) -> bool:
        return self._hasher.check_needs_rehash(hashed)
