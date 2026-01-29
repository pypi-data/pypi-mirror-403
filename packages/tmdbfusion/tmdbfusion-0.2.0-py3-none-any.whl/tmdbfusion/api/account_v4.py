# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""V4 Account API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.search import MoviePaginatedResponse
from tmdbfusion.models.search import TVPaginatedResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class AccountV4API(BaseAPI):
    """
    Synchronous V4 Account API.

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

    def lists(
        self,
        account_id: str,
        *,
        page: int = 1,
    ) -> dict[str, typing.Any]:
        """
        Get lists from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return self._client._get(
            f"/account/{account_id}/lists",
            dict[str, typing.Any],
            params={"page": page},
            version=4,
        )

    def favorite_movies(
        self,
        account_id: str,
        *,
        page: int = 1,
        sort_by: str = "created_at.desc",
    ) -> MoviePaginatedResponse:
        """
        Get favorite movies from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return self._client._get(
            f"/account/{account_id}/movie/favorites",
            MoviePaginatedResponse,
            params={"page": page, "sort_by": sort_by},
            version=4,
        )

    def favorite_tv(
        self,
        account_id: str,
        *,
        page: int = 1,
        sort_by: str = "created_at.desc",
    ) -> TVPaginatedResponse:
        """
        Get favorite TV shows from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return self._client._get(
            f"/account/{account_id}/tv/favorites",
            TVPaginatedResponse,
            params={"page": page, "sort_by": sort_by},
            version=4,
        )

    def rated_movies(
        self,
        account_id: str,
        *,
        page: int = 1,
        sort_by: str = "created_at.desc",
    ) -> MoviePaginatedResponse:
        """
        Get rated movies from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return self._client._get(
            f"/account/{account_id}/movie/rated",
            MoviePaginatedResponse,
            params={"page": page, "sort_by": sort_by},
            version=4,
        )

    def rated_tv(
        self,
        account_id: str,
        *,
        page: int = 1,
        sort_by: str = "created_at.desc",
    ) -> TVPaginatedResponse:
        """
        Get rated TV shows from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return self._client._get(
            f"/account/{account_id}/tv/rated",
            TVPaginatedResponse,
            params={"page": page, "sort_by": sort_by},
            version=4,
        )

    def movie_recommendations(
        self,
        account_id: str,
        *,
        page: int = 1,
        sort_by: str = "created_at.desc",
    ) -> MoviePaginatedResponse:
        """
        Get movie recommendations from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return self._client._get(
            f"/account/{account_id}/movie/recommendations",
            MoviePaginatedResponse,
            params={"page": page, "sort_by": sort_by},
            version=4,
        )

    def tv_recommendations(
        self,
        account_id: str,
        *,
        page: int = 1,
        sort_by: str = "created_at.desc",
    ) -> TVPaginatedResponse:
        """
        Get TV recommendations from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return self._client._get(
            f"/account/{account_id}/tv/recommendations",
            TVPaginatedResponse,
            params={"page": page, "sort_by": sort_by},
            version=4,
        )

    def movie_watchlist(
        self,
        account_id: str,
        *,
        page: int = 1,
        sort_by: str = "created_at.desc",
    ) -> MoviePaginatedResponse:
        """
        Get movie watchlist from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return self._client._get(
            f"/account/{account_id}/movie/watchlist",
            MoviePaginatedResponse,
            params={"page": page, "sort_by": sort_by},
            version=4,
        )

    def tv_watchlist(
        self,
        account_id: str,
        *,
        page: int = 1,
        sort_by: str = "created_at.desc",
    ) -> TVPaginatedResponse:
        """
        Get TV watchlist from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return self._client._get(
            f"/account/{account_id}/tv/watchlist",
            TVPaginatedResponse,
            params={"page": page, "sort_by": sort_by},
            version=4,
        )


class AsyncAccountV4API(AsyncBaseAPI):
    """
    Asynchronous V4 Account API.

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

    async def lists(
        self,
        account_id: str,
        *,
        page: int = 1,
    ) -> dict[str, typing.Any]:
        """
        Get lists from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return await self._client._get(
            f"/account/{account_id}/lists",
            dict[str, typing.Any],
            params={"page": page},
            version=4,
        )

    async def favorite_movies(
        self,
        account_id: str,
        *,
        page: int = 1,
    ) -> MoviePaginatedResponse:
        """
        Get favorite movies from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return await self._client._get(
            f"/account/{account_id}/movie/favorites",
            MoviePaginatedResponse,
            params={"page": page},
            version=4,
        )

    async def favorite_tv(
        self,
        account_id: str,
        *,
        page: int = 1,
    ) -> TVPaginatedResponse:
        """
        Get favorite TV shows from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return await self._client._get(
            f"/account/{account_id}/tv/favorites",
            TVPaginatedResponse,
            params={"page": page},
            version=4,
        )

    async def rated_movies(
        self,
        account_id: str,
        *,
        page: int = 1,
    ) -> MoviePaginatedResponse:
        """
        Get rated movies from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return await self._client._get(
            f"/account/{account_id}/movie/rated",
            MoviePaginatedResponse,
            params={"page": page},
            version=4,
        )

    async def rated_tv(
        self,
        account_id: str,
        *,
        page: int = 1,
    ) -> TVPaginatedResponse:
        """
        Get rated TV shows from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return await self._client._get(
            f"/account/{account_id}/tv/rated",
            TVPaginatedResponse,
            params={"page": page},
            version=4,
        )

    async def movie_recommendations(
        self,
        account_id: str,
        *,
        page: int = 1,
    ) -> MoviePaginatedResponse:
        """
        Get movie recommendations from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return await self._client._get(
            f"/account/{account_id}/movie/recommendations",
            MoviePaginatedResponse,
            params={"page": page},
            version=4,
        )

    async def tv_recommendations(
        self,
        account_id: str,
        *,
        page: int = 1,
    ) -> TVPaginatedResponse:
        """
        Get TV recommendations from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return await self._client._get(
            f"/account/{account_id}/tv/recommendations",
            TVPaginatedResponse,
            params={"page": page},
            version=4,
        )

    async def movie_watchlist(
        self,
        account_id: str,
        *,
        page: int = 1,
    ) -> MoviePaginatedResponse:
        """
        Get movie watchlist from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return await self._client._get(
            f"/account/{account_id}/movie/watchlist",
            MoviePaginatedResponse,
            params={"page": page},
            version=4,
        )

    async def tv_watchlist(
        self,
        account_id: str,
        *,
        page: int = 1,
    ) -> TVPaginatedResponse:
        """
        Get TV watchlist from V4 account.

        Parameters
        ----------
        account_id : str
            The account ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return await self._client._get(
            f"/account/{account_id}/tv/watchlist",
            TVPaginatedResponse,
            params={"page": page},
            version=4,
        )
