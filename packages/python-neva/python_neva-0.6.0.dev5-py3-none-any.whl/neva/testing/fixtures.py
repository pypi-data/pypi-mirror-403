"""Fixtures for testing."""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncContextManager

import pytest

from neva.arch import App, Application


@pytest.fixture
def test_config(tmp_path: Path) -> Path:
    """Returns a test config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    _ = (config_dir / "app.py").write_text(
        """config = { "name": "TestApp", "debug": True, "environment": "testing"}"""
    )
    _ = (config_dir / "providers.py").write_text("""config = { "providers": []}""")
    return config_dir


@pytest.fixture
async def application(test_config: Path) -> AsyncIterator[Application]:
    """Pytest fixture for app lifecycle.

    Yields:
        AsyncIterator[Application]: The application instance.
    """
    app = Application(config_path=test_config)
    async with app.lifespan():
        yield app


@pytest.fixture
def webapp(test_config: Path) -> App:
    """Pytest fixture for the HTTP Neva app.

    Returns:
        App: The Neva application instance.
    """
    return App(config_path=test_config)


@pytest.fixture
def app_factory() -> Callable[[Path], AsyncContextManager[Application]]:
    """Factory fixture for creating applications with custom configs.

    Returns:
        A factory function that creates application instances with lifespan managed.
    """

    @asynccontextmanager
    async def _factory(config_path: Path) -> AsyncIterator[Application]:
        app = Application(config_path=config_path)
        async with app.lifespan():
            yield app

    return _factory
