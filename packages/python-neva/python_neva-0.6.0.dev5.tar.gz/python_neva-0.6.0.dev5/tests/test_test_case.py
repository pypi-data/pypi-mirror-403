from pathlib import Path
import pytest

from neva import UnwrapError
from neva.arch import Application
from neva.config import ConfigRepository
from neva.testing import TestCase


class TestTestCase(TestCase):
    async def test_app_is_injected(self) -> None:
        assert hasattr(self, "app")
        assert isinstance(self.app, Application)

    async def test_make_resolves_services(self) -> None:
        config = self.app.make(ConfigRepository).unwrap()

        assert config is not None
        assert isinstance(config, ConfigRepository)

    async def test_make_unwraps_result(self) -> None:
        config = self.app.make(ConfigRepository).unwrap()

        name = config.get("app.name").unwrap()
        assert name == "TestApp"

    async def test_make_raises_on_error(self) -> None:
        class NonExistentService:
            pass

        with pytest.raises(UnwrapError):
            _ = self.app.make(NonExistentService).unwrap()

    async def test_app_isolation_between_tests_first(self) -> None:
        self.app.__test_marker = "first"  # type: ignore
        assert self.app.__test_marker == "first"  # type: ignore

    async def test_app_isolation_between_tests_second(self) -> None:
        assert not hasattr(self.app, "__test_marker")


class TestTestCaseWithCustomConfig(TestCase):
    def create_config(self, tmp_path: Path) -> Path:
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        _ = (config_dir / "app.py").write_text(
            """
config = {
    "name": "CustomTestApp",
    "custom_feature": True,
}
"""
        )

        _ = (config_dir / "providers.py").write_text('config = {"providers": []}')

        return config_dir

    async def test_uses_custom_config(self) -> None:
        config = self.app.make(ConfigRepository).unwrap()

        assert config.get("app.name").unwrap() == "CustomTestApp"
        assert config.get("app.custom_feature").unwrap() is True


class TestTestCaseInheritance:
    class CustomTestCase(TestCase):
        def get_app_name(self) -> str:
            config = self.app.make(ConfigRepository).unwrap()
            return config.get("app.name").unwrap()

        def is_debug_mode(self) -> bool:
            config = self.app.make(ConfigRepository).unwrap()
            return config.get("app.debug").unwrap()

    async def test_custom_helpers_work(self) -> None:
        test_case = self.CustomTestCase()

        from neva.arch import Application
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / "config"
            config_dir.mkdir()
            _ = (config_dir / "app.py").write_text(
                """config = {"name": "TestApp", "debug":"""
                + """ True, "environment": "testing"}"""
            )
            _ = (config_dir / "providers.py").write_text('config = {"providers": []}')

            app = Application(config_path=config_dir)
            async with app.lifespan():
                test_case.app = app

                # Use custom helpers
                assert test_case.get_app_name() == "TestApp"
                assert test_case.is_debug_mode() is True
