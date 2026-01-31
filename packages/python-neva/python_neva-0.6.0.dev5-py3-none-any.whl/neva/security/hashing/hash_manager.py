"""Hash manager for managing password hashing strategies."""

from typing import override

from neva import Option, from_optional
from neva.arch import Application
from neva.config import ConfigRepository
from neva.security.hashing.hashers.argon2 import Argon2Hasher
from neva.security.hashing.hashers.bcrypt import BcryptHasher
from neva.security.hashing.hashers.protocol import Hasher
from neva.support.strategy import StrategyResolver


class HashManager(StrategyResolver[Hasher]):
    """Manager for password hashing strategies."""

    def __init__(self, app: Application) -> None:
        """Initialize the hash manager and register available hashers.

        Args:
            app: The application instance for configuration access.
        """
        super().__init__(app)

        _ = self.register("argon2", self._create_argon2_hasher)
        _ = self.register("bcrypt", self._create_bcrypt_hasher)

    @override
    def default(self) -> Option[str]:
        """Get the default hasher from configuration.

        Returns:
            Option containing the default hasher name.
        """
        config_result = self.app.make(ConfigRepository)
        if config_result.is_err:
            return from_optional(None)

        config = config_result.unwrap()
        driver = config.get("hashing.driver", default=None).unwrap_or(None)
        return from_optional(driver)

    def make(
        self,
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
        hasher_instance = self.use(hasher).expect(
            f"Failed to resolve hasher '{hasher or 'default'}'"
        )
        return hasher_instance.make(plaintext, salt=salt)

    def check(
        self,
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
        hasher_instance = self.use(hasher).expect(
            f"Failed to resolve hasher '{hasher or 'default'}'"
        )
        return hasher_instance.check(plaintext, hashed)

    def needs_rehash(
        self,
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
        hasher_instance = self.use(hasher).expect(
            f"Failed to resolve hasher '{hasher or 'default'}'"
        )
        return hasher_instance.needs_rehash(hashed)

    def _create_argon2_hasher(self, manager: StrategyResolver[Hasher]) -> Argon2Hasher:
        """Create an instance of the Argon2 hash strategy.

        Args:
            manager: The strategy resolver instance.

        Returns:
            Configured Argon2Hasher instance.
        """
        config = manager.app.make(ConfigRepository).unwrap()
        argon_config = config.get("hashing.argon", default={}).unwrap()

        if isinstance(argon_config, dict):
            return Argon2Hasher(
                time_cost=argon_config.get("time_cost", 2),
                memory_cost=argon_config.get("memory_cost", 102400),
                parallelism=argon_config.get("parallelism", 8),
                hash_len=argon_config.get("hash_len", 16),
                salt_len=argon_config.get("salt_len", 16),
            )
        return Argon2Hasher()

    def _create_bcrypt_hasher(self, manager: StrategyResolver[Hasher]) -> BcryptHasher:
        """Create an instance of the Bcrypt hash strategy.

        Args:
            manager: The strategy resolver instance.

        Returns:
            Configured BcryptHasher instance.
        """
        config = manager.app.make(ConfigRepository).unwrap()
        bcrypt_config = config.get("hashing.bcrypt", default={}).unwrap()

        if isinstance(bcrypt_config, dict):
            return BcryptHasher(
                rounds=bcrypt_config.get("rounds", 12),
                prefix=bcrypt_config.get("prefix", "2b"),
            )
        return BcryptHasher()
