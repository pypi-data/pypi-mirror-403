"""Hashing utility facade."""

from typing import override
from neva.arch import Facade
from neva.security.hashing import HashManager


class Hash(Facade):
    """Hashing utility facade."""

    @classmethod
    @override
    def get_facade_accessor(cls) -> type:
        return HashManager
