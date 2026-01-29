# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Guest Session API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.account import RatedEpisodesResponse
from tmdbfusion.models.account import RatedMoviesResponse
from tmdbfusion.models.account import RatedTVResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class GuestSessionAPI(BaseAPI):
    """
    Synchronous Guest Session API.

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

    def rated_movies(
        self,
        guest_session_id: str,
        *,
        page: int = 1,
        sort_by: str = "created_at.asc",
    ) -> RatedMoviesResponse:
        """
        Get rated movies from guest session.

        Parameters
        ----------
        guest_session_id : str
            The guest session ID.
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
            f"/guest_session/{guest_session_id}/rated/movies",
            RatedMoviesResponse,
            params={"page": page, "sort_by": sort_by},
        )

    def rated_tv(
        self,
        guest_session_id: str,
        *,
        page: int = 1,
        sort_by: str = "created_at.asc",
    ) -> RatedTVResponse:
        """
        Get rated TV shows from guest session.

        Parameters
        ----------
        guest_session_id : str
            The guest session ID.
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
            f"/guest_session/{guest_session_id}/rated/tv",
            RatedTVResponse,
            params={"page": page, "sort_by": sort_by},
        )

    def rated_episodes(
        self,
        guest_session_id: str,
        *,
        page: int = 1,
        sort_by: str = "created_at.asc",
    ) -> RatedEpisodesResponse:
        """
        Get rated TV episodes from guest session.

        Parameters
        ----------
        guest_session_id : str
            The guest session ID.
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
            f"/guest_session/{guest_session_id}/rated/tv/episodes",
            RatedEpisodesResponse,
            params={"page": page, "sort_by": sort_by},
        )


class AsyncGuestSessionAPI(AsyncBaseAPI):
    """
    Asynchronous Guest Session API.

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

    async def rated_movies(
        self,
        guest_session_id: str,
        *,
        page: int = 1,
    ) -> RatedMoviesResponse:
        """
        Get rated movies from guest session.

        Parameters
        ----------
        guest_session_id : str
            The guest session ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        RatedMoviesResponse
            The RatedMoviesResponse response.
        """
        return await self._client._get(
            f"/guest_session/{guest_session_id}/rated/movies",
            RatedMoviesResponse,
            params={"page": page},
        )

    async def rated_tv(
        self,
        guest_session_id: str,
        *,
        page: int = 1,
    ) -> RatedTVResponse:
        """
        Get rated TV shows from guest session.

        Parameters
        ----------
        guest_session_id : str
            The guest session ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        RatedTVResponse
            The RatedTVResponse response.
        """
        return await self._client._get(
            f"/guest_session/{guest_session_id}/rated/tv",
            RatedTVResponse,
            params={"page": page},
        )

    async def rated_episodes(
        self,
        guest_session_id: str,
        *,
        page: int = 1,
    ) -> RatedEpisodesResponse:
        """
        Get rated TV episodes from guest session.

        Parameters
        ----------
        guest_session_id : str
            The guest session ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        RatedEpisodesResponse
            The RatedEpisodesResponse response.
        """
        return await self._client._get(
            f"/guest_session/{guest_session_id}/rated/tv/episodes",
            RatedEpisodesResponse,
            params={"page": page},
        )
