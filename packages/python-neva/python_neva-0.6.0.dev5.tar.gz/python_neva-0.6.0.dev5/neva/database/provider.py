"""Database service provider."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Self, override

from tortoise import Tortoise
from neva import Err, Ok, Result
from neva.arch import ServiceProvider
from neva.database.manager import DatabaseManager
from neva.support.facade import Config, Log


class DatabaseServiceProvider(ServiceProvider):
    """Database service provider."""

    @override
    def register(self) -> Result[Self, str]:
        self.app.bind(DatabaseManager)
        return Ok(self)

    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[None]:
        """Initialize and cleanup database connections."""
        match Config.get("database"):
            case Ok(config):
                await Tortoise.init(config=config, _create_db=True)
                yield
                await Tortoise.close_connections()
            case Err(err):
                Log.error(f"Failed to load database configuration: {err}")
                yield
