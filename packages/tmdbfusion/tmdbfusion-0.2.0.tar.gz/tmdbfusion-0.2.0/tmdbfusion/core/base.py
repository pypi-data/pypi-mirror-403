# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT


"""
Base client functionality.

Shared logic for sync and async clients.
"""

from __future__ import annotations

import typing

import msgspec

from tmdbfusion.exceptions import AuthenticationError
from tmdbfusion.exceptions import AuthorizationError
from tmdbfusion.exceptions import NotFoundError
from tmdbfusion.exceptions import RateLimitError
from tmdbfusion.exceptions import ServerError
from tmdbfusion.exceptions import TMDBError


if typing.TYPE_CHECKING:
    from tmdbfusion.core.http import TransportResponse

# API URLs
API_V3_BASE = "https://api.themoviedb.org/3"
API_V4_BASE = "https://api.themoviedb.org/4"

# HTTP Status Codes
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_RATE_LIMITED = 429
HTTP_SERVER_ERROR = 500

T = typing.TypeVar("T")


class RateLimitState(msgspec.Struct):
    """Rate limit state."""

    remaining: int = -1
    reset: int = -1


class BaseClient:
    """
    Base client with shared functionality.

    Parameters
    ----------
    api_key : str
        TMDB API key.
    access_token : str | None
        TMDB v4 access token.
    language : str
        Default language.

    """

    def __init__(
        self,
        api_key: str,
        *,
        access_token: str | None = None,
        language: str = "en-US",
    ) -> None:
        self._api_key = api_key
        self._access_token = access_token
        self._language = language
        self.rate_limit_state = RateLimitState()

    def _build_url(self, path: str, *, version: int = 3) -> str:
        """Build full API URL.

        Parameters
        ----------
        path : str
            API path.
        version : int
            API version.

        Returns
        -------
        str
            Full API URL.

        """
        base = API_V4_BASE if version == 4 else API_V3_BASE
        return f"{base}{path}"

    def _build_headers(self, *, use_bearer: bool = False) -> dict[str, str]:
        """Build request headers.

        Parameters
        ----------
        use_bearer : bool
            Whether to use Bearer token (v4) or API Key (v3).

        Returns
        -------
        dict[str, str]
            Request headers.

        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        token = self._access_token if use_bearer else self._api_key
        headers["Authorization"] = f"Bearer {token}"
        return headers

    def _build_params(
        self,
        params: dict[str, typing.Any] | None = None,
        *,
        include_language: bool = True,
    ) -> dict[str, typing.Any]:
        """Build query parameters.

        Parameters
        ----------
        params : dict[str, typing.Any] | None
            Query parameters.
        include_language : bool
            Whether to include default language.

        Returns
        -------
        dict[str, typing.Any]
            Query parameters.

        """
        result: dict[str, typing.Any] = {}
        if include_language:
            result["language"] = self._language
        if params:
            result.update(params)
        return result

    def _update_rate_limits(self, response: TransportResponse) -> None:
        """Update rate limit state from response headers.

        Parameters
        ----------
        response : TransportResponse
            API response.

        Returns
        -------
        None

        """
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset = response.headers.get("X-RateLimit-Reset")

        if remaining and remaining.isdigit():
            self.rate_limit_state.remaining = int(remaining)
        if reset and reset.isdigit():
            self.rate_limit_state.reset = int(reset)

    def _parse_error(self, response: TransportResponse) -> tuple[int, str]:
        """Parse error response.

        Parameters
        ----------
        response : TransportResponse
            API response.

        Returns
        -------
        tuple[int, str]
            Error code and message.

        """
        try:
            data: dict[str, object] = msgspec.json.decode(response.content)
            code = int(data.get("status_code", 0))  # type: ignore[arg-type]
            msg = str(data.get("status_message", "Unknown error"))
            return code, msg
        except (ValueError, TypeError, msgspec.DecodeError):
            return 0, response.content.decode("utf-8", errors="replace")

    def _raise_for_status(self, response: TransportResponse) -> None:
        """Raise exception for error status codes."""
        if response.status_code < HTTP_BAD_REQUEST:
            return

        code, msg = self._parse_error(response)

        if response.status_code == HTTP_UNAUTHORIZED:
            raise AuthenticationError(code, msg, response.status_code)
        if response.status_code == HTTP_FORBIDDEN:
            raise AuthorizationError(code, msg, response.status_code)
        if response.status_code == HTTP_NOT_FOUND:
            raise NotFoundError(code, msg, response.status_code)
        if response.status_code == HTTP_RATE_LIMITED:
            retry = response.headers.get("Retry-After")
            raise RateLimitError(
                code,
                msg,
                response.status_code,
                int(retry) if retry else None,
            )
        if response.status_code >= HTTP_SERVER_ERROR:
            raise ServerError(code, msg, response.status_code)

        raise TMDBError(code, msg, response.status_code)

    def _decode(self, response: TransportResponse, typ: type[T]) -> T:
        """Decode response to type.

        Parameters
        ----------
        response : TransportResponse
            API response.
        typ : type[T]
            Target type.

        Returns
        -------
        T
            Decoded response object.

        """
        self._raise_for_status(response)
        return msgspec.json.decode(response.content, type=typ)
