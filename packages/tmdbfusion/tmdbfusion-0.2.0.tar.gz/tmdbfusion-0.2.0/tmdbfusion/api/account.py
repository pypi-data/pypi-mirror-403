# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Account API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.account import AccountDetails
from tmdbfusion.models.account import AccountListsResponse
from tmdbfusion.models.account import FavoriteMoviesResponse
from tmdbfusion.models.account import FavoriteTVResponse
from tmdbfusion.models.account import RatedEpisodesResponse
from tmdbfusion.models.account import RatedMoviesResponse
from tmdbfusion.models.account import RatedTVResponse
from tmdbfusion.models.account import WatchlistMoviesResponse
from tmdbfusion.models.account import WatchlistTVResponse
from tmdbfusion.models.responses import StatusResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class AccountAPI(BaseAPI):
    """
    Synchronous Account API.

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

    def details(self, *, session_id: str) -> AccountDetails:
        """
        Get account details.

        Parameters
        ----------
        session_id : str
            The session ID.

        Returns
        -------
        AccountDetails
            The AccountDetails response.
        """
        return self._client._get(
            "/account",
            AccountDetails,
            params={"session_id": session_id},
        )

    def favorite_movies(
        self,
        account_id: int,
        *,
        session_id: str,
        page: int = 1,
        sort_by: str = "created_at.asc",
    ) -> FavoriteMoviesResponse:
        """
        Get favorite movies.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        FavoriteMoviesResponse
            The FavoriteMoviesResponse response.
        """
        return self._client._get(
            f"/account/{account_id}/favorite/movies",
            FavoriteMoviesResponse,
            params={
                "session_id": session_id,
                "page": page,
                "sort_by": sort_by,
            },
        )

    def favorite_tv(
        self,
        account_id: int,
        *,
        session_id: str,
        page: int = 1,
        sort_by: str = "created_at.asc",
    ) -> FavoriteTVResponse:
        """
        Get favorite TV shows.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        FavoriteTVResponse
            The FavoriteTVResponse response.
        """
        return self._client._get(
            f"/account/{account_id}/favorite/tv",
            FavoriteTVResponse,
            params={
                "session_id": session_id,
                "page": page,
                "sort_by": sort_by,
            },
        )

    def add_favorite(
        self,
        account_id: int,
        *,
        session_id: str,
        media_type: str,
        media_id: int,
        favorite: bool,
    ) -> StatusResponse:
        """
        Add/remove from favorites.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        media_type : str
            The media type (movie or tv).
        media_id : int
            The media ID.
        favorite : bool
            Whether to mark as favorite.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return self._client._post(
            f"/account/{account_id}/favorite",
            StatusResponse,
            params={"session_id": session_id},
            body={
                "media_type": media_type,
                "media_id": media_id,
                "favorite": favorite,
            },
        )

    def rated_movies(
        self,
        account_id: int,
        *,
        session_id: str,
        page: int = 1,
        sort_by: str = "created_at.asc",
    ) -> RatedMoviesResponse:
        """
        Get rated movies.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        RatedMoviesResponse
            The RatedMoviesResponse response.
        """
        return self._client._get(
            f"/account/{account_id}/rated/movies",
            RatedMoviesResponse,
            params={
                "session_id": session_id,
                "page": page,
                "sort_by": sort_by,
            },
        )

    def rated_tv(
        self,
        account_id: int,
        *,
        session_id: str,
        page: int = 1,
        sort_by: str = "created_at.asc",
    ) -> RatedTVResponse:
        """
        Get rated TV shows.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        RatedTVResponse
            The RatedTVResponse response.
        """
        return self._client._get(
            f"/account/{account_id}/rated/tv",
            RatedTVResponse,
            params={
                "session_id": session_id,
                "page": page,
                "sort_by": sort_by,
            },
        )

    def rated_episodes(
        self,
        account_id: int,
        *,
        session_id: str,
        page: int = 1,
        sort_by: str = "created_at.asc",
    ) -> RatedEpisodesResponse:
        """
        Get rated TV episodes.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        RatedEpisodesResponse
            The RatedEpisodesResponse response.
        """
        return self._client._get(
            f"/account/{account_id}/rated/tv/episodes",
            RatedEpisodesResponse,
            params={
                "session_id": session_id,
                "page": page,
                "sort_by": sort_by,
            },
        )

    def watchlist_movies(
        self,
        account_id: int,
        *,
        session_id: str,
        page: int = 1,
        sort_by: str = "created_at.asc",
    ) -> WatchlistMoviesResponse:
        """
        Get watchlist movies.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        WatchlistMoviesResponse
            The WatchlistMoviesResponse response.
        """
        return self._client._get(
            f"/account/{account_id}/watchlist/movies",
            WatchlistMoviesResponse,
            params={
                "session_id": session_id,
                "page": page,
                "sort_by": sort_by,
            },
        )

    def watchlist_tv(
        self,
        account_id: int,
        *,
        session_id: str,
        page: int = 1,
        sort_by: str = "created_at.asc",
    ) -> WatchlistTVResponse:
        """
        Get watchlist TV shows.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.

        Returns
        -------
        WatchlistTVResponse
            The WatchlistTVResponse response.
        """
        return self._client._get(
            f"/account/{account_id}/watchlist/tv",
            WatchlistTVResponse,
            params={
                "session_id": session_id,
                "page": page,
                "sort_by": sort_by,
            },
        )

    def add_to_watchlist(
        self,
        account_id: int,
        *,
        session_id: str,
        media_type: str,
        media_id: int,
        watchlist: bool,
    ) -> StatusResponse:
        """
        Add/remove from watchlist.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        media_type : str
            The media type (movie or tv).
        media_id : int
            The media ID.
        watchlist : bool
            Whether to add to watchlist.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return self._client._post(
            f"/account/{account_id}/watchlist",
            StatusResponse,
            params={"session_id": session_id},
            body={
                "media_type": media_type,
                "media_id": media_id,
                "watchlist": watchlist,
            },
        )

    def lists(
        self,
        account_id: int,
        *,
        session_id: str,
        page: int = 1,
    ) -> AccountListsResponse:
        """
        Get account lists.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        AccountListsResponse
            The AccountListsResponse response.
        """
        return self._client._get(
            f"/account/{account_id}/lists",
            AccountListsResponse,
            params={"session_id": session_id, "page": page},
        )


class AsyncAccountAPI(AsyncBaseAPI):
    """
    Asynchronous Account API.

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

    async def details(self, *, session_id: str) -> AccountDetails:
        """
        Get account details.

        Parameters
        ----------
        session_id : str
            The session ID.

        Returns
        -------
        AccountDetails
            The AccountDetails response.
        """
        return await self._client._get(
            "/account",
            AccountDetails,
            params={"session_id": session_id},
        )

    async def favorite_movies(
        self,
        account_id: int,
        *,
        session_id: str,
        page: int = 1,
    ) -> FavoriteMoviesResponse:
        """
        Get favorite movies.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        FavoriteMoviesResponse
            The FavoriteMoviesResponse response.
        """
        return await self._client._get(
            f"/account/{account_id}/favorite/movies",
            FavoriteMoviesResponse,
            params={"session_id": session_id, "page": page},
        )

    async def favorite_tv(
        self,
        account_id: int,
        *,
        session_id: str,
        page: int = 1,
    ) -> FavoriteTVResponse:
        """
        Get favorite TV shows.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        FavoriteTVResponse
            The FavoriteTVResponse response.
        """
        return await self._client._get(
            f"/account/{account_id}/favorite/tv",
            FavoriteTVResponse,
            params={"session_id": session_id, "page": page},
        )

    async def add_favorite(
        self,
        account_id: int,
        *,
        session_id: str,
        media_type: str,
        media_id: int,
        favorite: bool,
    ) -> StatusResponse:
        """
        Add/remove from favorites.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        media_type : str
            The media type (movie or tv).
        media_id : int
            The media ID.
        favorite : bool
            Whether to mark as favorite.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return await self._client._post(
            f"/account/{account_id}/favorite",
            StatusResponse,
            params={"session_id": session_id},
            body={
                "media_type": media_type,
                "media_id": media_id,
                "favorite": favorite,
            },
        )

    async def watchlist_movies(
        self,
        account_id: int,
        *,
        session_id: str,
        page: int = 1,
    ) -> WatchlistMoviesResponse:
        """
        Get watchlist movies.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        WatchlistMoviesResponse
            The WatchlistMoviesResponse response.
        """
        return await self._client._get(
            f"/account/{account_id}/watchlist/movies",
            WatchlistMoviesResponse,
            params={"session_id": session_id, "page": page},
        )

    async def watchlist_tv(
        self,
        account_id: int,
        *,
        session_id: str,
        page: int = 1,
    ) -> WatchlistTVResponse:
        """
        Get watchlist TV shows.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        WatchlistTVResponse
            The WatchlistTVResponse response.
        """
        return await self._client._get(
            f"/account/{account_id}/watchlist/tv",
            WatchlistTVResponse,
            params={"session_id": session_id, "page": page},
        )

    async def add_to_watchlist(
        self,
        account_id: int,
        *,
        session_id: str,
        media_type: str,
        media_id: int,
        watchlist: bool,
    ) -> StatusResponse:
        """
        Add/remove from watchlist.

        Parameters
        ----------
        account_id : int
            The account ID.
        session_id : str
            The session ID.
        media_type : str
            The media type (movie or tv).
        media_id : int
            The media ID.
        watchlist : bool
            Whether to add to watchlist.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return await self._client._post(
            f"/account/{account_id}/watchlist",
            StatusResponse,
            params={"session_id": session_id},
            body={
                "media_type": media_type,
                "media_id": media_id,
                "watchlist": watchlist,
            },
        )
