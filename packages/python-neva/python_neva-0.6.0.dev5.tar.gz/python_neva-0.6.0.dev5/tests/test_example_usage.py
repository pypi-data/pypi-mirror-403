from pathlib import Path

from neva.arch import Application
from neva.config import ConfigRepository
from neva.testing import TestCase


class TestBasicUsage(TestCase):
    async def test_simple_config_access(self) -> None:
        config = self.app.make(ConfigRepository).unwrap()

        app_name = config.get("app.name").unwrap()
        assert app_name == "TestApp"

        is_debug = config.get("app.debug").unwrap()
        assert is_debug is True

    async def test_config_with_default(self) -> None:
        config = self.app.make(ConfigRepository).unwrap()

        missing = config.get("app.missing_key", "default_value").unwrap()
        assert missing == "default_value"

    async def test_multiple_config_keys(self) -> None:
        config = self.app.make(ConfigRepository).unwrap()

        assert config.get("app.name").unwrap() == "TestApp"
        assert config.get("app.debug").unwrap() is True
        assert config.get("app.environment").unwrap() == "testing"


class TestCustomConfig(TestCase):
    def create_config(self, tmp_path: Path) -> Path:
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        _ = (config_dir / "app.py").write_text(
            """
config = {
    "name": "CustomApp",
    "debug": False,
    "environment": "custom",
    "custom_feature": True,
}
"""
        )

        _ = (config_dir / "providers.py").write_text("""config = {"providers": []}""")

        return config_dir

    async def test_uses_custom_config(self) -> None:
        config = self.app.make(ConfigRepository).unwrap()

        assert config.get("app.name").unwrap() == "CustomApp"
        assert config.get("app.debug").unwrap() is False
        assert config.get("app.environment").unwrap() == "custom"
        assert config.get("app.custom_feature").unwrap() is True


class TestConfigManipulation:
    async def test_add_database_config(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        _ = (config_dir / "app.py").write_text(
            """config = { "name": "TestApp", "debug": True, "environment": "testing"}"""
        )
        _ = (config_dir / "providers.py").write_text("""config = { "providers": []}""")

        _ = (config_dir / "database.py").write_text(
            """
config = {
    "default": "sqlite",
    "connections": {
        "sqlite": {
            "driver": "sqlite",
            "database": ":memory:",
        }
    }
}
"""
        )

        app = Application(config_path=config_dir)

        async with app.lifespan():
            config = app.make(ConfigRepository).unwrap()

            # Verify database config is loaded
            assert config.get("database.default").unwrap() == "sqlite"
            assert config.get("database.connections.sqlite.driver").unwrap() == "sqlite"
            assert (
                config.get("database.connections.sqlite.database").unwrap()
                == ":memory:"
            )

    async def test_add_multiple_config_files(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        _ = (config_dir / "app.py").write_text(
            """config = { "name": "TestApp", "debug": True, "environment": "testing"}"""
        )
        _ = (config_dir / "providers.py").write_text("""config = { "providers": []}""")

        _ = (config_dir / "cache.py").write_text(
            """config = {"driver": "memory", "ttl": 3600}"""
        )

        _ = (config_dir / "logging.py").write_text(
            """config = {"level": "DEBUG", "format": "json"}"""
        )

        app = Application(config_path=config_dir)

        async with app.lifespan():
            config = app.make(ConfigRepository).unwrap()

            # Verify both configs are loaded
            assert config.get("cache.driver").unwrap() == "memory"
            assert config.get("cache.ttl").unwrap() == 3600
            assert config.get("logging.level").unwrap() == "DEBUG"
            assert config.get("logging.format").unwrap() == "json"


class TestAppLifecycle:
    async def test_manual_app_creation(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        _ = (config_dir / "app.py").write_text(
            """config = { "name": "TestApp", "debug": True, "environment": "testing"}"""
        )
        _ = (config_dir / "providers.py").write_text("""config = { "providers": []}""")

        app = Application(config_path=config_dir)

        async with app.lifespan():
            config = app.make(ConfigRepository).unwrap()
            assert config.get("app.name").unwrap() == "TestApp"

    async def test_multiple_apps_in_one_test(self, tmp_path: Path) -> None:
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        _ = (config_dir / "app.py").write_text(
            """config = { "name": "TestApp", "debug": True, "environment": "testing"}"""
        )
        _ = (config_dir / "providers.py").write_text("""config = { "providers": []}""")

        app1 = Application(config_path=config_dir)
        async with app1.lifespan():
            config1 = app1.make(ConfigRepository).unwrap()
            assert config1.get("app.name").unwrap() == "TestApp"

        app2 = Application(config_path=config_dir)
        async with app2.lifespan():
            config2 = app2.make(ConfigRepository).unwrap()
            assert config2.get("app.name").unwrap() == "TestApp"

        assert app1 is not app2


class TestIsolation(TestCase):
    async def test_isolation_test_one(self) -> None:
        config = self.app.make(ConfigRepository).unwrap()

        original_name = config.get("app.name").unwrap()
        assert original_name == "TestApp"

    async def test_isolation_test_two(self) -> None:
        config = self.app.make(ConfigRepository).unwrap()

        assert config.get("app.name").unwrap() == "TestApp"
