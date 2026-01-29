# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Rate Limit Handler.

Utilities for managing TMDB API rate limits with automatic retry and backoff.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
import typing

from tmdbfusion.exceptions import RateLimitError


if typing.TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Callable

T = typing.TypeVar("T")
P = typing.ParamSpec("P")

logger = logging.getLogger("tmdbfusion.rate_limit")


class RateLimitHandler:
    """Handler for rate-limited API calls with automatic retry.

    Examples
    --------
    >>> handler = RateLimitHandler(max_retries=5, backoff_factor=1.0)
    >>> result = handler.execute(client.movies.popular)

    Parameters
    ----------
    max_retries : int
        Maximum number of retries on rate limit (default 3).
    backoff_factor : float
        Base delay multiplier for exponential backoff (default 1.0).
    max_delay : float
        Maximum delay between retries in seconds (default 60.0).
    on_rate_limit : Callable[[int, float], None] | None
        Optional callback called on rate limit. Receives attempt number
        and wait time.

    """

    def __init__(
        self,
        *,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        max_delay: float = 60.0,
        on_rate_limit: Callable[[int, float], None] | None = None,
    ) -> None:
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor
        self._max_delay = max_delay
        self._on_rate_limit = on_rate_limit
        self._stats = RateLimitStats()

    @property
    def stats(self) -> RateLimitStats:
        """Get rate limit statistics.

        Returns
        -------
        RateLimitStats
            Statistics about rate limit handling.

        """
        return self._stats

    def _calculate_delay(
        self,
        attempt: int,
        retry_after: int | None,
    ) -> float:
        """Calculate delay before next retry.

        Parameters
        ----------
        attempt : int
            Current attempt number (0-indexed).
        retry_after : int | None
            Retry-After header value if provided.

        Returns
        -------
        float
            Delay in seconds.

        """
        base_delay = self._backoff_factor * (2**attempt)
        delay = max(base_delay, float(retry_after)) if retry_after else base_delay
        return min(delay, self._max_delay)

    def execute(
        self,
        func: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        """Execute a function with rate limit handling.

        Parameters
        ----------
        func : Callable[P, T]
            Function to execute.
        *args : P.args
            Positional arguments for the function.
        **kwargs : P.kwargs
            Keyword arguments for the function.

        Returns
        -------
        T
            Result of the function.

        Raises
        ------
        RateLimitError
            If max retries exceeded.

        """
        last_error: RateLimitError | None = None

        for attempt in range(self._max_retries + 1):
            try:
                result = func(*args, **kwargs)
                self._stats.add_success()
                return result
            except RateLimitError as e:
                last_error = e
                self._stats.add_rate_limit()

                if attempt >= self._max_retries:
                    logger.warning(
                        "Rate limit max retries (%d) exceeded",
                        self._max_retries,
                    )
                    raise

                delay = self._calculate_delay(attempt, e.retry_after)
                logger.info(
                    "Rate limited, waiting %.2f seconds (attempt %d/%d)",
                    delay,
                    attempt + 1,
                    self._max_retries,
                )

                if self._on_rate_limit:
                    self._on_rate_limit(attempt + 1, delay)

                time.sleep(delay)

        # Should be unreachable
        if last_error:
            raise last_error
        msg = "Unexpected error in rate limit handler"
        raise RuntimeError(msg)

    async def execute_async(
        self,
        func: Callable[P, Awaitable[T]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        """Execute an async function with rate limit handling.

        Parameters
        ----------
        func : Callable[P, Awaitable[T]]
            Async function to execute.
        *args : P.args
            Positional arguments for the function.
        **kwargs : P.kwargs
            Keyword arguments for the function.

        Returns
        -------
        T
            Result of the function.

        Raises
        ------
        RateLimitError
            If max retries exceeded.

        """
        last_error: RateLimitError | None = None

        for attempt in range(self._max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                self._stats.add_success()
                return result
            except RateLimitError as e:
                last_error = e
                self._stats.add_rate_limit()

                if attempt >= self._max_retries:
                    logger.warning(
                        "Rate limit max retries (%d) exceeded",
                        self._max_retries,
                    )
                    raise

                delay = self._calculate_delay(attempt, e.retry_after)
                logger.info(
                    "Rate limited, waiting %.2f seconds (attempt %d/%d)",
                    delay,
                    attempt + 1,
                    self._max_retries,
                )

                if self._on_rate_limit:
                    self._on_rate_limit(attempt + 1, delay)

                await asyncio.sleep(delay)

        if last_error:
            raise last_error
        msg = "Unexpected error in rate limit handler"
        raise RuntimeError(msg)


class RateLimitStats:
    """Statistics for rate limit handling.

    Attributes
    ----------
    total_requests : int
        Total number of requests made.
    rate_limits_hit : int
        Number of times rate limit was hit.
    successful_requests : int
        Number of successful requests.

    """

    def __init__(self) -> None:
        self.total_requests: int = 0
        self.rate_limits_hit: int = 0
        self.successful_requests: int = 0

    def add_success(self) -> None:
        """Record a successful request."""
        self.total_requests += 1
        self.successful_requests += 1

    def add_rate_limit(self) -> None:
        """Record a rate limit hit."""
        self.rate_limits_hit += 1

    def reset(self) -> None:
        """Reset all statistics."""
        self.total_requests = 0
        self.rate_limits_hit = 0
        self.successful_requests = 0

    @property
    def rate_limit_percentage(self) -> float:
        """Get percentage of requests that hit rate limits.

        Returns
        -------
        float
            Percentage of rate-limited requests (0-100).

        """
        if self.total_requests == 0:
            return 0.0
        return (self.rate_limits_hit / self.total_requests) * 100


def with_rate_limit(
    *,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to add rate limit handling to a function.

    Parameters
    ----------
    max_retries : int
        Maximum retries on rate limit.
    backoff_factor : float
        Backoff multiplier.

    Returns
    -------
    Callable[[Callable[P, T]], Callable[P, T]]
        Decorator function.

    Examples
    --------
    >>> @with_rate_limit(max_retries=5)
    ... def fetch_data():
    ...     return client.movies.popular()

    """
    handler = RateLimitHandler(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
    )

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return handler.execute(func, *args, **kwargs)

        return wrapper

    return decorator


def with_rate_limit_async(
    *,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
) -> Callable[
    [Callable[P, Awaitable[T]]],
    Callable[P, Awaitable[T]],
]:
    """Decorator to add rate limit handling to an async function.

    Parameters
    ----------
    max_retries : int
        Maximum retries on rate limit.
    backoff_factor : float
        Backoff multiplier.

    Returns
    -------
    Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]
        Decorator function.

    Examples
    --------
    >>> @with_rate_limit_async(max_retries=5)
    ... async def fetch_data():
    ...     return await client.movies.popular()

    """
    handler = RateLimitHandler(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
    )

    def decorator(
        func: Callable[P, Awaitable[T]],
    ) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return await handler.execute_async(func, *args, **kwargs)

        return wrapper

    return decorator
