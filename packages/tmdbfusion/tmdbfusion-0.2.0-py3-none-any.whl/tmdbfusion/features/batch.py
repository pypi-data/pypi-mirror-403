# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Batch Context Manager.

Execute multiple API calls with concurrency control using a Pythonic
context manager interface.
"""

from __future__ import annotations

import asyncio
import typing
from dataclasses import dataclass
from dataclasses import field


if typing.TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Callable

T = typing.TypeVar("T")


@dataclass
class BatchResult:
    """Result from batch execution.

    Attributes
    ----------
    results : list[object]
        Successful results in queue order (None for failed items).
    errors : list[tuple[int, Exception]]
        List of (index, exception) for failed operations.

    """

    results: list[object] = field(default_factory=list)
    errors: list[tuple[int, Exception]] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        """Get number of successful operations.

        Returns
        -------
        int
            Number of successes.

        """
        return sum(1 for r in self.results if r is not None)

    @property
    def failure_count(self) -> int:
        """Get number of failed operations.

        Returns
        -------
        int
            Number of failures.

        """
        return len(self.errors)

    @property
    def all_succeeded(self) -> bool:
        """Check if all operations succeeded.

        Returns
        -------
        bool
            True if no errors occurred.

        """
        return len(self.errors) == 0


class BatchContext:
    """Sync batch context for queuing and executing operations.

    Examples
    --------
    >>> with client.batch(concurrency=5) as batch:
    ...     batch.queue(client.movies.details, 550)
    ...     batch.queue(client.movies.details, 551)
    >>> print(batch.result.results)

    Parameters
    ----------
    concurrency : int
        Maximum concurrent operations (for async execution).

    """

    def __init__(self, concurrency: int = 10) -> None:
        self._concurrency = concurrency
        self._queue: list[tuple[Callable[..., object], tuple[object, ...]]] = []
        self._result: BatchResult = BatchResult()

    def queue(
        self,
        func: Callable[..., T],
        *args: object,
    ) -> None:
        """Queue a function call for batch execution.

        Parameters
        ----------
        func : Callable[..., T]
            Function to call.
        *args : object
            Arguments for the function.

        """
        self._queue.append((func, args))

    @property
    def result(self) -> BatchResult:
        """Get batch execution result.

        Returns
        -------
        BatchResult
            Result containing successes and errors.

        """
        return self._result

    def __enter__(self) -> typing.Self:
        """Enter context manager.

        Returns
        -------
        BatchContext
            Self.

        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Execute all queued operations on exit.

        Parameters
        ----------
        exc_type : type[BaseException] | None
            Exception type if raised.
        exc_val : BaseException | None
            Exception value if raised.
        exc_tb : object
            Traceback if raised.

        """
        if exc_type is not None:
            return

        results: list[object] = []
        errors: list[tuple[int, Exception]] = []

        for idx, (func, args) in enumerate(self._queue):
            try:
                result = func(*args)
                results.append(result)
            except Exception as e:  # noqa: BLE001
                results.append(None)
                errors.append((idx, e))

        self._result = BatchResult(results=results, errors=errors)


class AsyncBatchContext:
    """Async batch context for queuing and executing operations.

    Examples
    --------
    >>> async with client.batch(concurrency=5) as batch:
    ...     batch.queue(client.movies.details, 550)
    ...     batch.queue(client.movies.details, 551)
    >>> print(batch.result.results)

    Parameters
    ----------
    concurrency : int
        Maximum concurrent operations.

    """

    def __init__(self, concurrency: int = 10) -> None:
        self._concurrency = concurrency
        self._queue: list[tuple[Callable[..., Awaitable[object]], tuple[object, ...]]] = []
        self._result: BatchResult = BatchResult()

    def queue(
        self,
        func: Callable[..., Awaitable[T]],
        *args: object,
    ) -> None:
        """Queue an async function call for batch execution.

        Parameters
        ----------
        func : Callable[..., Awaitable[T]]
            Async function to call.
        *args : object
            Arguments for the function.

        """
        self._queue.append((func, args))

    @property
    def result(self) -> BatchResult:
        """Get batch execution result.

        Returns
        -------
        BatchResult
            Result containing successes and errors.

        """
        return self._result

    async def __aenter__(self) -> typing.Self:
        """Enter async context manager.

        Returns
        -------
        AsyncBatchContext
            Self.

        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Execute all queued operations on exit.

        Parameters
        ----------
        exc_type : type[BaseException] | None
            Exception type if raised.
        exc_val : BaseException | None
            Exception value if raised.
        exc_tb : object
            Traceback if raised.

        """
        if exc_type is not None:
            return

        semaphore = asyncio.Semaphore(self._concurrency)
        results: list[object] = [None] * len(self._queue)
        errors: list[tuple[int, Exception]] = []

        async def run_one(
            idx: int,
            func: Callable[..., Awaitable[object]],
            args: tuple[object, ...],
        ) -> None:
            async with semaphore:
                try:
                    results[idx] = await func(*args)
                except Exception as e:  # noqa: BLE001
                    errors.append((idx, e))

        tasks = [run_one(idx, func, args) for idx, (func, args) in enumerate(self._queue)]
        await asyncio.gather(*tasks)

        self._result = BatchResult(results=results, errors=errors)
