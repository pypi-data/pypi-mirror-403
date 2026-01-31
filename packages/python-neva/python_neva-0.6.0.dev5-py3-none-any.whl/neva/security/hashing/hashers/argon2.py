"""Argon2 hasher."""

from typing import override

import argon2
from pwdlib.hashers.argon2 import Argon2Hasher as PwdLibArgon2Hasher

from neva.security.hashing.hashers.protocol import Hasher


class Argon2Hasher(Hasher):
    """Argon2 hasher."""

    def __init__(
        self,
        time_cost: int = argon2.DEFAULT_TIME_COST,
        memory_cost: int = argon2.DEFAULT_MEMORY_COST,
        parallelism: int = argon2.DEFAULT_PARALLELISM,
        hash_len: int = argon2.DEFAULT_HASH_LENGTH,
        salt_len: int = argon2.DEFAULT_RANDOM_SALT_LENGTH,
    ) -> None:
        """Initialize the hasher."""
        self._hasher: PwdLibArgon2Hasher = PwdLibArgon2Hasher(
            time_cost,
            memory_cost,
            parallelism,
            hash_len,
            salt_len,
        )

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
