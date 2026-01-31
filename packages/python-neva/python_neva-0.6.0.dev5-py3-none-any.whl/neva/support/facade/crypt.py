"""Encryption utility facade."""

from typing import override

from neva.arch import Facade
from neva.security.encryption import Encrypter


class Crypt(Facade):
    """Encryption utility facade."""

    @classmethod
    @override
    def get_facade_accessor(cls) -> type:
        return Encrypter
