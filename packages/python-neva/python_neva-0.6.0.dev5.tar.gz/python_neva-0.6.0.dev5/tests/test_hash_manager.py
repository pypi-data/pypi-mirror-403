from pathlib import Path

from neva.security import HashManager
from neva.support.facade import Hash
from neva.testing import TestCase


class TestHashManager(TestCase):
    def create_config(self, tmp_path: Path) -> Path:
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        _ = (config_dir / "app.py").write_text(
            """
config = {
    "name": "TestApp",
    "debug": True,
}
"""
        )

        _ = (config_dir / "providers.py").write_text(
            """
from neva.security import SecurityProvider

config = {"providers": [SecurityProvider]}
"""
        )

        _ = (config_dir / "hashing.py").write_text(
            """
config = {
    "driver": "bcrypt",
    "bcrypt": {
        "rounds": 10,
        "prefix": "2b",
    },
    "argon": {
        "time_cost": 2,
        "memory_cost": 65536,
        "parallelism": 4,
        "hash_len": 16,
        "salt_len": 16,
    },
}
"""
        )

        return config_dir

    async def test_hash_manager_creates_with_default_driver(self) -> None:
        password = "secret_password"  # noqa: S105
        hashed = Hash.make(password)

        assert hashed.startswith("$2b$")
        assert Hash.check(password, hashed)

    async def test_hash_manager_can_use_specific_hasher(self) -> None:
        password = "another_password"  # noqa: S105
        hashed = Hash.make(password, hasher="argon2")

        assert hashed.startswith("$argon2")
        assert Hash.check(password, hashed, hasher="argon2")

    async def test_hash_manager_check_password(self) -> None:
        password = "test_password"  # noqa: S105
        wrong_password = "wrong_password"  # noqa: S105

        hashed = Hash.make(password)

        assert Hash.check(password, hashed)
        assert not Hash.check(wrong_password, hashed)

    async def test_hash_manager_needs_rehash(self) -> None:
        password = "test_password"  # noqa: S105
        hashed = Hash.make(password)

        assert not Hash.needs_rehash(hashed)

    async def test_hash_manager_uses_strategy_pattern(self) -> None:
        hash_manager = self.app.make(HashManager).unwrap()

        bcrypt_hasher = hash_manager.use().unwrap()
        assert bcrypt_hasher is not None

        argon2_hasher = hash_manager.use("argon2").unwrap()
        assert argon2_hasher is not None

        assert bcrypt_hasher is not argon2_hasher

        bcrypt_hasher_again = hash_manager.use().unwrap()
        assert bcrypt_hasher is bcrypt_hasher_again
