"""Unit tests for the HTTP transport layer."""

import pytest
import respx
import httpx
from unittest import mock
from tmdbfusion.core.http import HttpxSyncTransport, HttpxAsyncTransport, TransportError
import pytest_asyncio

API_URL = "https://api.themoviedb.org/3/movie/550"


class TestSyncTransport:
    @pytest.fixture
    def transport(self) -> HttpxSyncTransport:
        return HttpxSyncTransport(retries=2, backoff_factor=0.1)

    def test_successful_request(
        self, transport: HttpxSyncTransport, respx_mock: respx.MockRouter
    ) -> None:
        """Test a successful request."""
        respx_mock.get(API_URL).mock(
            return_value=httpx.Response(200, json={"title": "Fight Club"})
        )

        response = transport.request("GET", API_URL)

        assert response.status_code == 200
        assert b"Fight Club" in response.content

    def test_retry_on_500(
        self, transport: HttpxSyncTransport, respx_mock: respx.MockRouter
    ) -> None:
        """Test retries on 500 error."""
        route = respx_mock.get(API_URL).mock(
            side_effect=[
                httpx.Response(500),
                httpx.Response(500),
                httpx.Response(200, json={"ok": True}),
            ]
        )

        with mock.patch("time.sleep") as mock_sleep:
            response = transport.request("GET", API_URL)

        assert response.status_code == 200
        # Called 3 times: 500, 500, 200
        assert route.call_count == 3
        # Should sleep twice (after 1st and 2nd failure)
        assert mock_sleep.call_count == 2

    def test_max_retries_exceeded(
        self, transport: HttpxSyncTransport, respx_mock: respx.MockRouter
    ) -> None:
        """Test max retries exceeded behavior."""
        respx_mock.get(API_URL).mock(return_value=httpx.Response(500))

        with mock.patch("time.sleep"):
            response = transport.request("GET", API_URL)
            assert response.status_code == 500

    def test_retry_after_header(
        self, transport: HttpxSyncTransport, respx_mock: respx.MockRouter
    ) -> None:
        """Test respect for Retry-After header."""
        respx_mock.get(API_URL).mock(
            side_effect=[
                httpx.Response(429, headers={"Retry-After": "2.5"}),
                httpx.Response(200),
            ]
        )

        with mock.patch("time.sleep") as mock_sleep:
            transport.request("GET", API_URL)

        # Ensure it slept for at least the Retry-After value
        mock_sleep.assert_called_with(2.5)


@pytest.mark.asyncio
class TestAsyncTransport:
    @pytest_asyncio.fixture
    async def transport(self) -> HttpxAsyncTransport:
        t = HttpxAsyncTransport(retries=2, backoff_factor=0.1)
        yield t
        await t.close()

    async def test_async_successful_request(
        self, transport: HttpxAsyncTransport, respx_mock: respx.MockRouter
    ) -> None:
        """Test async successful request."""
        respx_mock.get(API_URL).mock(
            return_value=httpx.Response(200, json={"title": "Fight Club"})
        )

        response = await transport.request("GET", API_URL)
        assert response.status_code == 200

    async def test_async_retry_logic(
        self, transport: HttpxAsyncTransport, respx_mock: respx.MockRouter
    ) -> None:
        """Test async retry logic."""
        route = respx_mock.get(API_URL).mock(
            side_effect=[httpx.Response(503), httpx.Response(200)]
        )

        with mock.patch("asyncio.sleep", new_callable=mock.AsyncMock) as mock_sleep:
            response = await transport.request("GET", API_URL)

        assert response.status_code == 200
        assert route.call_count == 2
        assert mock_sleep.call_count == 1
