"""Database manager."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from tortoise.transactions import in_transaction


class DatabaseManager:
    """Dtabase manager."""

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        """Initiate a transaction."""
        async with in_transaction():
            yield
