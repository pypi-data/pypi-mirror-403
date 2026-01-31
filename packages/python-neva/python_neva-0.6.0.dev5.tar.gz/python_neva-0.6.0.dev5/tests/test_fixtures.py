from pathlib import Path


from neva.arch import Application
from neva.config import ConfigRepository


class TestTestConfig:
    def test_creates_config_directory(
        self,
        test_config: Path,
    ) -> None:
        assert test_config.exists()
        assert test_config.is_dir()
        assert test_config.name == "config"

    def test_creates_app_config_file(
        self,
        test_config: Path,
    ) -> None:
        app_config = test_config / "app.py"
        assert app_config.exists()
        assert app_config.is_file()

        content = app_config.read_text()
        assert "TestApp" in content
        assert "debug" in content
        assert "testing" in content

    def test_creates_providers_config_file(
        self,
        test_config: Path,
    ) -> None:
        providers_config = test_config / "providers.py"
        assert providers_config.exists()
        assert providers_config.is_file()

        content = providers_config.read_text()
        assert "providers" in content


class TestAppFixture:
    async def test_app_is_application_instance(
        self,
        application: Application,
    ) -> None:
        assert isinstance(application, Application)

    async def test_app_config_is_loaded(
        self,
        application: Application,
    ) -> None:
        config_result = application.make(ConfigRepository)
        assert config_result.is_ok

        config = config_result.unwrap()
        assert config is not None

        assert config.get("app.name").unwrap() == "TestApp"
        assert config.get("app.debug").unwrap() is True
        assert config.get("app.environment").unwrap() == "testing"

    async def test_app_is_fresh_per_test_first(
        self,
        application: Application,
    ) -> None:
        type(application).__test_marker = "first_test"  # type: ignore[unresolved-attribute]
        assert type(application).__test_marker == "first_test"  # type: ignore[unresolved-attribute]

    async def test_app_is_fresh_per_test_second(
        self,
        application: Application,
    ) -> None:
        assert not hasattr(type(application), "__test_marker")

    async def test_app_can_resolve_services(
        self,
        application: Application,
    ) -> None:
        config_result = application.make(ConfigRepository)
        assert config_result.is_ok

        config = config_result.unwrap()
        assert config is not None
        assert isinstance(config, ConfigRepository)

    async def test_multiple_resolutions_return_same_instance(
        self,
        application: Application,
    ) -> None:
        config1 = application.make(ConfigRepository).unwrap()
        config2 = application.make(ConfigRepository).unwrap()

        assert config1 is config2


class TestFixtureIntegration:
    async def test_test_config_and_app_work_together(
        self,
        test_config: Path,
        application: Application,
    ) -> None:
        config = application.make(ConfigRepository).unwrap()

        assert config.get("app.name").unwrap() == "TestApp"

        app_config_file = test_config / "app.py"
        assert app_config_file.exists()

    async def test_can_customize_config_in_test(self, test_config: Path) -> None:
        _ = (test_config / "custom.py").write_text(
            """config = {"custom_key": "custom_value"}"""
        )

        app = Application(config_path=test_config)

        async with app.lifespan():
            config = app.make(ConfigRepository).unwrap()
            assert config.get("custom.custom_key").unwrap() == "custom_value"
