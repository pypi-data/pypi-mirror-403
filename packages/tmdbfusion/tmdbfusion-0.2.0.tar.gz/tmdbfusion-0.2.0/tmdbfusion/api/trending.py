# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Trending API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.search import MoviePaginatedResponse
from tmdbfusion.models.search import PersonPaginatedResponse
from tmdbfusion.models.search import TVPaginatedResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class TrendingAPI(BaseAPI):
    """
    Synchronous Trending API.

    Parameters
    ----------
    client : TMDBClient
        The TMDB client instance.
    """

    def __init__(self, client: TMDBClient) -> None:
        """
        Initialize the API.

        Parameters
        ----------
        client : TMDBClient
            The TMDB client instance.
        """
        super().__init__(client)

    def movies(
        self,
        time_window: str = "day",
        *,
        page: int = 1,
    ) -> MoviePaginatedResponse:
        """
        Get trending movies.

        Parameters
        ----------
        time_window : str, optional
            The time window (day or week).
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return self._client._get(
            f"/trending/movie/{time_window}",
            MoviePaginatedResponse,
            params={"page": page},
        )

    def tv(
        self,
        time_window: str = "day",
        *,
        page: int = 1,
    ) -> TVPaginatedResponse:
        """
        Get trending TV shows.

        Parameters
        ----------
        time_window : str, optional
            The time window (day or week).
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return self._client._get(
            f"/trending/tv/{time_window}",
            TVPaginatedResponse,
            params={"page": page},
        )

    def people(
        self,
        time_window: str = "day",
        *,
        page: int = 1,
    ) -> PersonPaginatedResponse:
        """
        Get trending people.

        Parameters
        ----------
        time_window : str, optional
            The time window (day or week).
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        PersonPaginatedResponse
            Paginated list of people.
        """
        return self._client._get(
            f"/trending/person/{time_window}",
            PersonPaginatedResponse,
            params={"page": page},
        )

    def all(
        self,
        time_window: str = "day",
        *,
        page: int = 1,
    ) -> MoviePaginatedResponse:
        """
        Get all trending (movies, TV, people).

        Parameters
        ----------
        time_window : str, optional
            The time window (day or week).
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return self._client._get(
            f"/trending/all/{time_window}",
            MoviePaginatedResponse,
            params={"page": page},
        )


class AsyncTrendingAPI(AsyncBaseAPI):
    """
    Asynchronous Trending API.

    Parameters
    ----------
    client : AsyncTMDBClient
        The TMDB client instance.
    """

    def __init__(self, client: AsyncTMDBClient) -> None:
        """
        Initialize the API.

        Parameters
        ----------
        client : TMDBClient
            The TMDB client instance.
        """
        super().__init__(client)

    async def movies(
        self,
        time_window: str = "day",
        *,
        page: int = 1,
    ) -> MoviePaginatedResponse:
        """
        Get trending movies.

        Parameters
        ----------
        time_window : str, optional
            The time window (day or week).
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return await self._client._get(
            f"/trending/movie/{time_window}",
            MoviePaginatedResponse,
            params={"page": page},
        )

    async def tv(
        self,
        time_window: str = "day",
        *,
        page: int = 1,
    ) -> TVPaginatedResponse:
        """
        Get trending TV shows.

        Parameters
        ----------
        time_window : str, optional
            The time window (day or week).
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return await self._client._get(
            f"/trending/tv/{time_window}",
            TVPaginatedResponse,
            params={"page": page},
        )

    async def people(
        self,
        time_window: str = "day",
        *,
        page: int = 1,
    ) -> PersonPaginatedResponse:
        """
        Get trending people.

        Parameters
        ----------
        time_window : str, optional
            The time window (day or week).
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        PersonPaginatedResponse
            Paginated list of people.
        """
        return await self._client._get(
            f"/trending/person/{time_window}",
            PersonPaginatedResponse,
            params={"page": page},
        )

    async def all(
        self,
        time_window: str = "day",
        *,
        page: int = 1,
    ) -> MoviePaginatedResponse:
        """
        Get all trending (movies, TV, people).

        Parameters
        ----------
        time_window : str, optional
            The time window (day or week).
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return await self._client._get(
            f"/trending/all/{time_window}",
            MoviePaginatedResponse,
            params={"page": page},
        )
