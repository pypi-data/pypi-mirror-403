"""Security service provider."""

from typing import Self, override

from neva import Ok, Result, arch
from neva.security.encryption import AesEncrypter, Encrypter
from neva.security.hashing import HashManager


class SecurityProvider(arch.ServiceProvider):
    """Provider for security features."""

    @override
    def register(self) -> Result[Self, str]:
        self.app.bind(HashManager, interface=HashManager)
        self.app.bind(AesEncrypter, interface=Encrypter)
        return Ok(self)
