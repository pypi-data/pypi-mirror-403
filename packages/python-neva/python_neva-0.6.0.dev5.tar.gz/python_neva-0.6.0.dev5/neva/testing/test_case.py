"""Base test case class."""

from collections.abc import AsyncIterator
from pathlib import Path
from typing import TypeVar

import pytest

from neva.arch import Application

T = TypeVar("T")


class TestCase:
    """Base test case with auto-injected app and helper methods.

    Subclasses can override `create_config` to provide custom configuration
    for their tests. The application will be automatically created with this
    configuration and injected into `self.app`.
    """

    app: Application

    def create_config(self, tmp_path: Path) -> Path:
        """Create the configuration directory for tests.

        Override this method to provide custom configuration.

        Args:
            tmp_path: Pytest's temporary directory fixture.

        Returns:
            Path to the configuration directory.
        """
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        _ = (config_dir / "app.py").write_text(
            """config = { "name": "TestApp", "debug": True, "environment": "testing"}"""
        )
        _ = (config_dir / "providers.py").write_text("""config = { "providers": []}""")
        return config_dir

    @pytest.fixture
    def _test_case_config(self, tmp_path: Path) -> Path:
        """Config fixture that uses the create_config method.

        Returns:
            Path to the configuration directory.
        """
        return self.create_config(tmp_path)

    @pytest.fixture
    async def _test_case_application(
        self, _test_case_config: Path
    ) -> AsyncIterator[Application]:
        """Application fixture for TestCase subclasses.

        Yields:
            Application instance with lifespan managed.
        """
        app = Application(config_path=_test_case_config)
        async with app.lifespan():
            yield app

    @pytest.fixture(autouse=True)
    async def _inject_app(self, _test_case_application: Application) -> None:
        """Auto-inject app fixture into self.app."""
        self.app = _test_case_application
