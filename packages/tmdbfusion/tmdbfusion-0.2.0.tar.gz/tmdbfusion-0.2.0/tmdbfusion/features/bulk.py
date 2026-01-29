# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Bulk Fetcher.

Utilities for fetching multiple items efficiently with batching and
concurrency control.
"""

from __future__ import annotations

import asyncio
import logging
import typing
from dataclasses import dataclass
from dataclasses import field


if typing.TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Callable
    from collections.abc import Iterable

T = typing.TypeVar("T")
R = typing.TypeVar("R")

logger = logging.getLogger("tmdbfusion.bulk")


@dataclass
class BulkResult[T, R]:
    """Result from bulk fetch operation.

    Attributes
    ----------
    successful : list[tuple[T, R]]
        List of (id, result) tuples for successful fetches.
    failed : list[tuple[T, Exception]]
        List of (id, error) tuples for failed fetches.

    """

    successful: list[tuple[T, R]] = field(default_factory=list)
    failed: list[tuple[T, Exception]] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        """Get number of successful fetches.

        Returns
        -------
        int
            Number of successful items.

        """
        return len(self.successful)

    @property
    def failure_count(self) -> int:
        """Get number of failed fetches.

        Returns
        -------
        int
            Number of failed items.

        """
        return len(self.failed)

    @property
    def total_count(self) -> int:
        """Get total number of items processed.

        Returns
        -------
        int
            Total items.

        """
        return self.success_count + self.failure_count

    def get_results(self) -> list[R]:
        """Get list of successful results only.

        Returns
        -------
        list[R]
            List of results in order of success.

        """
        return [result for _, result in self.successful]

    def get_results_by_id(self) -> dict[T, R]:
        """Get dictionary mapping IDs to results.

        Returns
        -------
        dict[T, R]
            Mapping of ID to result.

        """
        return dict(self.successful)


class BulkFetcher[T, R]:
    """Fetch multiple items with concurrency control.

    Examples
    --------
    >>> fetcher = BulkFetcher(max_concurrency=5)
    >>> ids = [550, 551, 552, 553]
    >>> result = await fetcher.fetch_async(
    ...     ids,
    ...     lambda id: client.movies.details(id),
    ... )
    >>> print(result.success_count)
    4

    Parameters
    ----------
    max_concurrency : int
        Maximum concurrent requests (default 10).
    delay_between_batches : float
        Delay between batch executions in seconds (default 0.0).
    continue_on_error : bool
        Whether to continue fetching on individual errors (default True).

    """

    def __init__(
        self,
        *,
        max_concurrency: int = 10,
        delay_between_batches: float = 0.0,
        continue_on_error: bool = True,
    ) -> None:
        self._max_concurrency = max_concurrency
        self._delay_between_batches = delay_between_batches
        self._continue_on_error = continue_on_error

    def fetch(
        self,
        ids: Iterable[T],
        fetcher: Callable[[T], R],
    ) -> BulkResult[T, R]:
        """Fetch multiple items synchronously.

        Parameters
        ----------
        ids : Iterable[T]
            IDs to fetch.
        fetcher : Callable[[T], R]
            Function that fetches a single item by ID.

        Returns
        -------
        BulkResult[T, R]
            Results with successful and failed fetches.

        Raises
        ------
        Exception
            If continue_on_error is False and any fetch fails.

        """
        result: BulkResult[T, R] = BulkResult()
        id_list = list(ids)

        for item_id in id_list:
            try:
                data = fetcher(item_id)
                result.successful.append((item_id, data))
                logger.debug("Fetched ID %s successfully", item_id)
            except Exception as e:
                logger.warning("Failed to fetch ID %s: %s", item_id, e)
                if not self._continue_on_error:
                    raise
                result.failed.append((item_id, e))

        return result

    async def fetch_async(
        self,
        ids: Iterable[T],
        fetcher: Callable[[T], Awaitable[R]],
    ) -> BulkResult[T, R]:
        """Fetch multiple items asynchronously with concurrency control.

        Parameters
        ----------
        ids : Iterable[T]
            IDs to fetch.
        fetcher : Callable[[T], Awaitable[R]]
            Async function that fetches a single item by ID.

        Returns
        -------
        BulkResult[T, R]
            Results with successful and failed fetches.

        Raises
        ------
        Exception
            If continue_on_error is False and any fetch fails.

        """
        result: BulkResult[T, R] = BulkResult()
        id_list = list(ids)
        semaphore = asyncio.Semaphore(self._max_concurrency)

        async def fetch_one(item_id: T) -> tuple[T, R | Exception]:
            async with semaphore:
                try:
                    data = await fetcher(item_id)
                    logger.debug("Fetched ID %s successfully", item_id)
                    return (item_id, data)
                except Exception as e:
                    logger.warning("Failed to fetch ID %s: %s", item_id, e)
                    if not self._continue_on_error:
                        raise
                    return (item_id, e)

        # Process in batches for delay support
        batches = [id_list[i : i + self._max_concurrency] for i in range(0, len(id_list), self._max_concurrency)]

        for batch_idx, batch in enumerate(batches):
            tasks = [fetch_one(item_id) for item_id in batch]
            results = await asyncio.gather(*tasks, return_exceptions=False)

            for item_id, data in results:
                if isinstance(data, Exception):
                    result.failed.append((item_id, data))
                else:
                    result.successful.append((item_id, data))

            # Delay between batches (except after last)
            if self._delay_between_batches > 0 and batch_idx < len(batches) - 1:
                await asyncio.sleep(self._delay_between_batches)

        return result

    async def fetch_ordered_async(
        self,
        ids: Iterable[T],
        fetcher: Callable[[T], Awaitable[R]],
    ) -> list[R | None]:
        """Fetch items and return results in original order.

        Parameters
        ----------
        ids : Iterable[T]
            IDs to fetch.
        fetcher : Callable[[T], Awaitable[R]]
            Async function that fetches a single item by ID.

        Returns
        -------
        list[R | None]
            Results in same order as input IDs. None for failed fetches.

        """
        id_list = list(ids)
        result = await self.fetch_async(id_list, fetcher)
        result_map = result.get_results_by_id()

        return [result_map.get(item_id) for item_id in id_list]


async def bulk_fetch_async(
    ids: Iterable[T],
    fetcher: Callable[[T], Awaitable[R]],
    *,
    max_concurrency: int = 10,
    continue_on_error: bool = True,
) -> BulkResult[T, R]:
    """Convenience function for async bulk fetching.

    Parameters
    ----------
    ids : Iterable[T]
        IDs to fetch.
    fetcher : Callable[[T], Awaitable[R]]
        Async function that fetches a single item by ID.
    max_concurrency : int
        Maximum concurrent requests.
    continue_on_error : bool
        Whether to continue on individual errors.

    Returns
    -------
    BulkResult[T, R]
        Results with successful and failed fetches.

    Examples
    --------
    >>> result = await bulk_fetch_async(
    ...     [550, 551, 552],
    ...     client.movies.details,
    ...     max_concurrency=5,
    ... )

    """
    fetcher_instance = BulkFetcher[T, R](
        max_concurrency=max_concurrency,
        continue_on_error=continue_on_error,
    )
    return await fetcher_instance.fetch_async(ids, fetcher)


def bulk_fetch(
    ids: Iterable[T],
    fetcher: Callable[[T], R],
    *,
    continue_on_error: bool = True,
) -> BulkResult[T, R]:
    """Convenience function for sync bulk fetching.

    Parameters
    ----------
    ids : Iterable[T]
        IDs to fetch.
    fetcher : Callable[[T], R]
        Function that fetches a single item by ID.
    continue_on_error : bool
        Whether to continue on individual errors.

    Returns
    -------
    BulkResult[T, R]
        Results with successful and failed fetches.

    Examples
    --------
    >>> result = bulk_fetch(
    ...     [550, 551, 552],
    ...     client.movies.details,
    ... )

    """
    fetcher_instance = BulkFetcher[T, R](continue_on_error=continue_on_error)
    return fetcher_instance.fetch(ids, fetcher)
