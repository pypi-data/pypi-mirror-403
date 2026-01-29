# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
HTTP Transport Layer.

Abstract transport interfaces and httpx implementations.
"""

from __future__ import annotations

import abc
import time
import typing

import httpx
import msgspec


class TransportResponse(msgspec.Struct, frozen=True):
    """Response from transport layer.

    Attributes
    ----------
    status_code : int
        HTTP status code.
    content : bytes
        Response body.
    headers : dict[str, str]
        Response headers.

    """

    status_code: int
    content: bytes
    headers: dict[str, str]


class SyncTransport(abc.ABC):
    """Synchronous transport protocol."""

    @abc.abstractmethod
    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, typing.Any] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        timeout: float | None = None,
    ) -> TransportResponse:
        """Perform HTTP request."""
        ...

    @abc.abstractmethod
    def close(self) -> None:
        """Close the transport."""
        ...


class AsyncTransport(abc.ABC):
    """Asynchronous transport protocol."""

    @abc.abstractmethod
    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, typing.Any] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        timeout: float | None = None,
    ) -> TransportResponse:
        """Perform HTTP request."""
        ...

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the transport."""
        ...


class TransportError(Exception):
    """TMDB API Exceptions."""


class HttpxSyncTransport(SyncTransport):
    """Synchronous httpx transport."""

    def __init__(
        self,
        timeout: float = 30.0,
        retries: int = 3,
        backoff_factor: float = 0.5,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        log_hook: typing.Callable[[str, str, int], None] | None = None,
    ) -> None:
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )
        self._client = httpx.Client(timeout=timeout, limits=limits)
        self._retries = retries
        self._backoff_factor = backoff_factor
        self._log_hook = log_hook

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, typing.Any] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        timeout: float | None = None,
    ) -> TransportResponse:
        """Perform HTTP request with retries."""
        for attempt in range(self._retries + 1):
            try:
                response = self._client.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    content=content,
                    timeout=timeout,
                )
                # Retry on 5xx errors or 429
                if (500 <= response.status_code < 600 or response.status_code == 429) and attempt < self._retries:
                    sleep_time = self._backoff_factor * (2**attempt)
                    if response.status_code == 429:
                        # Respect Retry-After if present
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            sleep_time = max(
                                sleep_time,
                                float(retry_after),
                            )
                    time.sleep(sleep_time)
                    continue

                if self._log_hook:
                    self._log_hook(method, url, response.status_code)

                return TransportResponse(
                    status_code=response.status_code,
                    content=response.content,
                    headers=dict(response.headers),
                )
            except httpx.RequestError:
                if attempt < self._retries:
                    time.sleep(self._backoff_factor * (2**attempt))
                    continue
                raise

        # Should be unreachable if retries are handled correctly or raised
        msg = "Max retries exceeded"
        raise TransportError(msg)

    def close(self) -> None:
        """Close the client."""
        self._client.close()


class HttpxAsyncTransport(AsyncTransport):
    """Asynchronous httpx transport."""

    def __init__(
        self,
        timeout: float = 30.0,
        retries: int = 3,
        backoff_factor: float = 0.5,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        log_hook: typing.Callable[[str, str, int], None] | None = None,
    ) -> None:
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )
        self._client = httpx.AsyncClient(timeout=timeout, limits=limits)
        self._retries = retries
        self._backoff_factor = backoff_factor
        self._log_hook = log_hook

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, typing.Any] | None = None,
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        timeout: float | None = None,
    ) -> TransportResponse:
        """Perform HTTP request with retries."""
        import asyncio

        for attempt in range(self._retries + 1):
            try:
                response = await self._client.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    content=content,
                    timeout=timeout,
                )
                # Retry on 5xx errors or 429
                if (500 <= response.status_code < 600 or response.status_code == 429) and attempt < self._retries:
                    sleep_time = self._backoff_factor * (2**attempt)
                    if response.status_code == 429:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            sleep_time = max(
                                sleep_time,
                                float(retry_after),
                            )
                    await asyncio.sleep(sleep_time)
                    continue

                if self._log_hook:
                    self._log_hook(method, url, response.status_code)

                return TransportResponse(
                    status_code=response.status_code,
                    content=response.content,
                    headers=dict(response.headers),
                )
            except httpx.RequestError:
                if attempt < self._retries:
                    await asyncio.sleep(self._backoff_factor * (2**attempt))
                    continue
                raise

        msg = "Max retries exceeded"
        raise TransportError(msg)

    async def close(self) -> None:
        """Close the client."""
        await self._client.aclose()
