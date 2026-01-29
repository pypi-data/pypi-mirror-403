# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Pagination utilities."""

from __future__ import annotations

import collections.abc
import typing


T = typing.TypeVar("T")


class PaginatedIterator[T]:
    """Iterator for paginated results with take/skip support.

    Examples
    --------
    >>> for movie in client.paginate(client.movies.popular).take(50):
    ...     print(movie.title)

    >>> first_100 = client.paginate(client.movies.popular).take(100).collect()

    """

    def __init__(
        self,
        method: typing.Callable[..., typing.Any],
        *,
        map_response: typing.Callable[[typing.Any], list[T]],
        **kwargs: object,
    ) -> None:
        self._method = method
        self._map_response = map_response
        self._kwargs = kwargs
        self._page = 1
        self._buffer: collections.deque[T] = collections.deque()
        self._total_pages: int | None = None
        self._total_results: int | None = None
        self._items_yielded = 0
        self._take_limit: int | None = None
        self._skip_count: int = 0
        self._skipped: int = 0

    def __iter__(self) -> collections.abc.Iterator[T]:
        """Return self."""
        return self

    def _check_take_limit(self) -> bool:
        """Check if take limit has been reached.

        Returns
        -------
        bool
            True if limit reached, False otherwise.

        """
        return self._take_limit is not None and self._items_yielded >= self._take_limit

    def _update_totals(self, response: typing.Any) -> None:  # noqa: ANN401
        """Update total pages and results from response."""
        if self._total_pages is None:
            if isinstance(response, dict):
                self._total_pages = response.get("total_pages", 1)
            else:
                self._total_pages = getattr(response, "total_pages", 1)

        if self._total_results is None:
            if isinstance(response, dict):
                self._total_results = response.get("total_results")
            else:
                self._total_results = getattr(response, "total_results", None)

    def _fill_buffer(self) -> None:
        """Fetch next page and fill buffer."""
        if self._total_pages is not None and self._page > self._total_pages:
            return

        response = self._method(page=self._page, **self._kwargs)
        self._update_totals(response)

        results = self._map_response(response)
        if results:
            self._buffer.extend(results)
            self._page += 1

    def _should_skip(self) -> bool:
        """Check if current item should be skipped.

        Returns
        -------
        bool
            True if item should be skipped, False otherwise.

        """
        if self._skipped < self._skip_count:
            self._skipped += 1
            return True
        return False

    def _ensure_buffer(self) -> bool:
        """Ensure buffer has items.

        Returns
        -------
        bool
            True if buffer has items, False otherwise.

        """
        if not self._buffer:
            self._fill_buffer()
        return bool(self._buffer)

    def __next__(self) -> T:
        """Get next item."""
        if self._check_take_limit():
            raise StopIteration

        while True:
            if not self._ensure_buffer():
                raise StopIteration

            item = self._buffer.popleft()

            if self._should_skip():
                continue

            self._items_yielded += 1
            return item

    @property
    def total_pages(self) -> int | None:
        """Get total pages if known.

        Returns
        -------
        int | None
            Total pages or None if not yet fetched.

        """
        return self._total_pages

    @property
    def total_results(self) -> int | None:
        """Get total results if known.

        Returns
        -------
        int | None
            Total results or None if not yet fetched.

        """
        return self._total_results

    def take(self, n: int) -> PaginatedIterator[T]:
        """Limit iterator to n items.

        Parameters
        ----------
        n : int
            Maximum items to return.

        Returns
        -------
        PaginatedIterator[T]
            Self for chaining.

        """
        self._take_limit = n
        return self

    def skip(self, n: int) -> PaginatedIterator[T]:
        """Skip first n items.

        Parameters
        ----------
        n : int
            Number of items to skip.

        Returns
        -------
        PaginatedIterator[T]
            Self for chaining.

        """
        self._skip_count = n
        return self

    def collect(self) -> list[T]:
        """Materialize all items into a list.

        Returns
        -------
        list[T]
            List of all items.

        """
        return list(self)


class AsyncPaginatedIterator[T]:
    """Async iterator for paginated results with take/skip support.

    Examples
    --------
    >>> async for movie in client.paginate(client.movies.popular).take(50):
    ...     print(movie.title)

    >>> first_100 = await client.paginate(client.movies.popular).take(100).collect()

    """

    def __init__(
        self,
        method: typing.Callable[..., typing.Awaitable[typing.Any]],
        *,
        map_response: typing.Callable[[typing.Any], list[T]],
        **kwargs: object,
    ) -> None:
        self._method = method
        self._map_response = map_response
        self._kwargs = kwargs
        self._page = 1
        self._buffer: collections.deque[T] = collections.deque()
        self._total_pages: int | None = None
        self._total_results: int | None = None
        self._items_yielded = 0
        self._take_limit: int | None = None
        self._skip_count: int = 0
        self._skipped: int = 0

    def __aiter__(self) -> collections.abc.AsyncIterator[T]:
        """Return self."""
        return self

    def _check_take_limit(self) -> bool:
        """Check if take limit has been reached.

        Returns
        -------
        bool
            True if limit reached, False otherwise.

        """
        return bool(self._take_limit is not None and self._items_yielded >= self._take_limit)

    async def _ensure_buffer(self) -> bool:
        """Ensure buffer has items.

        Returns
        -------
        bool
            True if buffer has items, False otherwise.

        """
        if not self._buffer:
            await self._fill_buffer()
        return bool(self._buffer)

    def _update_totals(self, response: typing.Any) -> None:  # noqa: ANN401
        """Update total pages and results from response."""
        if self._total_pages is None:
            if isinstance(response, dict):
                self._total_pages = response.get("total_pages", 1)
            else:
                self._total_pages = getattr(response, "total_pages", 1)

        if self._total_results is None:
            if isinstance(response, dict):
                self._total_results = response.get("total_results")
            else:
                self._total_results = getattr(response, "total_results", None)

    async def _fill_buffer(self) -> None:
        """Fetch next page and fill buffer."""
        if self._total_pages is not None and self._page > self._total_pages:
            return

        response = await self._method(page=self._page, **self._kwargs)
        self._update_totals(response)

        results = self._map_response(response)
        if results:
            self._buffer.extend(results)
            self._page += 1

    def _should_skip(self) -> bool:
        """Check if current item should be skipped.

        Returns
        -------
        bool
            True if item should be skipped, False otherwise.

        """
        if self._skipped < self._skip_count:
            self._skipped += 1
            return True
        return False

    async def __anext__(self) -> T:
        """Get next item."""
        if self._check_take_limit():
            raise StopAsyncIteration

        while True:
            if not await self._ensure_buffer():
                raise StopAsyncIteration

            item = self._buffer.popleft()

            if self._should_skip():
                continue

            self._items_yielded += 1
            return item

    @property
    def total_pages(self) -> int | None:
        """Get total pages if known.

        Returns
        -------
        int | None
            Total pages or None if not yet fetched.

        """
        return self._total_pages

    @property
    def total_results(self) -> int | None:
        """Get total results if known.

        Returns
        -------
        int | None
            Total results or None if not yet fetched.

        """
        return self._total_results

    def take(self, n: int) -> AsyncPaginatedIterator[T]:
        """Limit iterator to n items.

        Parameters
        ----------
        n : int
            Maximum items to return.

        Returns
        -------
        AsyncPaginatedIterator[T]
            Self for chaining.

        """
        self._take_limit = n
        return self

    def skip(self, n: int) -> AsyncPaginatedIterator[T]:
        """Skip first n items.

        Parameters
        ----------
        n : int
            Number of items to skip.

        Returns
        -------
        AsyncPaginatedIterator[T]
            Self for chaining.

        """
        self._skip_count = n
        return self

    async def collect(self) -> list[T]:
        """Materialize all items into a list.

        Returns
        -------
        list[T]
            List of all items.

        """
        return [item async for item in self]
