"""Global test configuration."""

import typing
import pytest
import respx
import pytest_asyncio
from httpx import Response
from tmdbfusion import TMDBClient
from tmdbfusion import AsyncTMDBClient


@pytest.fixture
def respx_mock() -> typing.Generator[respx.MockRouter, None, None]:
    """Mock HTTP requests."""
    with respx.mock(assert_all_called=False) as mock:
        yield mock


@pytest.fixture
def tmdb_client() -> TMDBClient:
    """Return a synchronous TMDB client."""
    return TMDBClient(api_key="fake-key")


@pytest_asyncio.fixture
async def async_tmdb_client() -> AsyncTMDBClient:
    """Return an asynchronous TMDB client."""
    return AsyncTMDBClient(api_key="fake-key")


@pytest.fixture
def mock_response_factory() -> typing.Callable[[int, typing.Any], Response]:
    """Factory to create mock responses."""

    def _create(status_code: int = 200, json_data: typing.Any = None) -> Response:
        import msgspec

        content = msgspec.json.encode(json_data) if json_data is not None else b""
        return Response(status_code, content=content)

    return _create
