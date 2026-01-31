"""HTTP Test helpers."""

from collections.abc import AsyncIterator
from httpx import ASGITransport, AsyncClient
import pytest

from neva.arch import App


@pytest.fixture
async def http_client(webapp: App) -> AsyncIterator[AsyncClient]:
    """An async httpx client to test the application.

    Yields:
        An async httpx client.
    """
    async with AsyncClient(
        transport=ASGITransport(webapp),
        base_url="http://localhost:8000",
    ) as client:
        yield client
