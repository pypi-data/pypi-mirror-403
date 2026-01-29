"""Unit tests for BaseClient."""

import pytest
import httpx
from tmdbfusion.core.base import BaseClient, RateLimitState
from tmdbfusion.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TMDBError,
)


class TestBaseClient:
    @pytest.fixture
    def client(self):
        return BaseClient(api_key="key", access_token="token")

    def test_build_url_v3(self, client):
        assert (
            client._build_url("/test", version=3) == "https://api.themoviedb.org/3/test"
        )

    def test_build_url_v4(self, client):
        assert (
            client._build_url("/test", version=4) == "https://api.themoviedb.org/4/test"
        )

    def test_build_headers_apikey(self, client):
        headers = client._build_headers(use_bearer=False)
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer key"

    def test_build_headers_bearer(self, client):
        headers = client._build_headers(use_bearer=True)
        assert headers["Authorization"] == "Bearer token"

    def test_build_params(self, client):
        params = client._build_params({"a": 1}, include_language=True)
        assert params == {"a": 1, "language": "en-US"}

        params = client._build_params({"a": 1}, include_language=False)
        assert params == {"a": 1}

    def test_update_rate_limits(self, client):
        # Good headers
        resp = httpx.Response(
            200, headers={"X-RateLimit-Remaining": "10", "X-RateLimit-Reset": "123456"}
        )
        client._update_rate_limits(resp)
        assert client.rate_limit_state.remaining == 10
        assert client.rate_limit_state.reset == 123456

        # Bad/Missing headers (should not crash)
        resp = httpx.Response(200, headers={"X-RateLimit-Remaining": "invalid"})
        client._update_rate_limits(resp)
        # Should remain unchanged (default -1 or previous value)
        assert client.rate_limit_state.remaining == 10

    def test_parse_error_json(self, client):
        resp = httpx.Response(
            400, content=b'{"status_code": 34, "status_message": "Fail"}'
        )
        code, msg = client._parse_error(resp)
        assert code == 34
        assert msg == "Fail"

    def test_parse_error_malformed(self, client):
        resp = httpx.Response(400, content=b"Bad JSON")
        code, msg = client._parse_error(resp)
        assert code == 0
        assert msg == "Bad JSON"

    def test_raise_for_status_ok(self, client):
        resp = httpx.Response(200)
        # Should not raise
        client._raise_for_status(resp)

    def test_raise_for_status_errors(self, client):
        with pytest.raises(AuthenticationError):
            client._raise_for_status(httpx.Response(401, content=b"{}"))

        with pytest.raises(AuthorizationError):
            client._raise_for_status(httpx.Response(403, content=b"{}"))

        with pytest.raises(NotFoundError):
            client._raise_for_status(httpx.Response(404, content=b"{}"))

        with pytest.raises(RateLimitError) as exc:
            client._raise_for_status(
                httpx.Response(429, headers={"Retry-After": "5"}, content=b"{}")
            )
        assert exc.value.retry_after == 5

        with pytest.raises(ServerError):
            client._raise_for_status(httpx.Response(500, content=b"{}"))

        with pytest.raises(TMDBError):
            client._raise_for_status(httpx.Response(418, content=b"{}"))
