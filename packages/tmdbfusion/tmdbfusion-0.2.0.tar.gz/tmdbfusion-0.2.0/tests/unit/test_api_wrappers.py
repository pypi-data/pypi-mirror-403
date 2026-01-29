"""Parametric unit tests for API wrappers."""

import pytest
import respx
import httpx
import inspect
import typing
from tmdbfusion import TMDBClient, AsyncTMDBClient
from tmdbfusion.api._base import BaseAPI, AsyncBaseAPI

# --- Helper Functions ---


def get_all_client_methods(client_cls) -> list[tuple[str, str]]:
    """Return a list of (namespace, method_name) tuples for all API methods."""
    methods = []
    # Create a dummy instance just to inspect structure (no network needed)
    if client_cls == TMDBClient:
        dummy = TMDBClient("key")
    else:
        dummy = AsyncTMDBClient("key")

    # Manually initialize images API
    if not hasattr(dummy, "images"):
        from tmdbfusion.utils.images import ImagesAPI

        dummy.images = ImagesAPI(dummy)

    for attr_name in dir(dummy):
        if attr_name.startswith("_"):
            continue

        attr = getattr(dummy, attr_name)
        # Check if it looks like an API namespace
        if isinstance(attr, (BaseAPI, AsyncBaseAPI)) or attr_name == "images":
            for method_name in dir(attr):
                if method_name.startswith("_"):
                    continue

                method = getattr(attr, method_name)
                if callable(method):
                    methods.append((attr_name, method_name))
    return sorted(list(set(methods)))


SYNC_METHODS = get_all_client_methods(TMDBClient)
ASYNC_METHODS = get_all_client_methods(AsyncTMDBClient)

# --- Fixtures ---


@pytest.fixture
def mock_generic_response(respx_mock):
    """Mock ANY request to return a generic success structure."""
    # This covers both paginated and non-paginated expectations loosely
    respx_mock.route().mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 1,
                "results": [],
                "page": 1,
                "total_pages": 1,
                "total_results": 0,
                "success": True,
                "status_code": 200,
                "status_message": "Success",
                "guest_session_id": "guest_session_id",
                "expires_at": "2026-01-01 00:00:00 UTC",
                "request_token": "request_token",
                "session_id": "session_id",
            },
        )
    )


# --- Parametric Tests ---


@pytest.mark.parametrize("namespace, method_name", SYNC_METHODS)
def test_sync_api_method_coverage(tmdb_client, namespace, method_name):
    """Call every sync API method with minimal arguments to trigger coverage."""
    api_instance = getattr(tmdb_client, namespace)
    method = getattr(api_instance, method_name)

    # Mock the client's _request method to return a dummy TransportResponse
    # checking that it was called is enough for coverage of the wrapper
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            tmdb_client,
            "_request",
            lambda *args, **kwargs: httpx.Response(200, content=b"{}"),
        )
        # We also need to mock _decode because it will try to parse the empty JSON into a strict model
        # We can just return a dummy object that has all attributes (MagicMock)
        from unittest.mock import MagicMock

        mp.setattr(tmdb_client, "_decode", lambda *args, **kwargs: MagicMock())

        # Inspect signature to provide required arguments
        sig = inspect.signature(method)
        args = {}
        for name, param in sig.parameters.items():
            if param.default == inspect.Parameter.empty and name != "self":
                # Provide dummy values based on type annotation if possible
                annotation = param.annotation
                if (
                    annotation == int
                    or "id" in name
                    or "year" in name
                    or "page" in name
                ):
                    args[name] = 1
                elif annotation == str or "query" in name or "token" in name:
                    args[name] = "dummy_str"
                elif annotation == bool:
                    args[name] = True
                elif "body" in name:
                    args[name] = {"key": "value"}
                else:
                    args[name] = "dummy"

        # Call the method
        try:
            method(**args)
        except Exception as e:
            pytest.fail(
                f"Failed to call {namespace}.{method_name} with args {args}: {e}"
            )


@pytest.mark.asyncio
@pytest.mark.parametrize("namespace, method_name", ASYNC_METHODS)
async def test_async_api_method_coverage(async_tmdb_client, namespace, method_name):
    """Call every async API method with minimal arguments."""
    api_instance = getattr(async_tmdb_client, namespace)
    method = getattr(api_instance, method_name)

    # Mocking internal methods to bypass network and schema validation
    from unittest.mock import AsyncMock, MagicMock

    # _request is async
    async_tmdb_client._request = AsyncMock(
        return_value=httpx.Response(200, content=b"{}")
    )
    # _decode is NOT async in the code (it just returns the object),
    # BUT wait, commonly _decode might be sync. Let's check the code.
    # Looking at _base.py: _decode is sync.
    async_tmdb_client._decode = MagicMock(return_value=MagicMock())

    sig = inspect.signature(method)
    args = {}
    for name, param in sig.parameters.items():
        if param.default == inspect.Parameter.empty and name != "self":
            annotation = param.annotation
            if annotation == int or "id" in name or "year" in name or "page" in name:
                args[name] = 1
            elif annotation == str or "query" in name or "token" in name:
                args[name] = "dummy_str"
            elif annotation == bool:
                args[name] = True
            elif "body" in name:
                args[name] = {"key": "value"}
            else:
                args[name] = "dummy"

    try:
        if inspect.iscoroutinefunction(method):
            await method(**args)
        else:
            method(**args)
    except Exception as e:
        pytest.fail(f"Failed to call {namespace}.{method_name}: {e}")
