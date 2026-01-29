# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Genres API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.responses import GenresResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class GenresAPI(BaseAPI):
    """
    Synchronous Genres API.

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

    def movie_list(self) -> GenresResponse:
        """
        Get movie genres list.

        Returns
        -------
        GenresResponse
            The GenresResponse response.
        """
        return self._client._get("/genre/movie/list", GenresResponse)

    def tv_list(self) -> GenresResponse:
        """
        Get TV genres list.

        Returns
        -------
        GenresResponse
            The GenresResponse response.
        """
        return self._client._get("/genre/tv/list", GenresResponse)


class AsyncGenresAPI(AsyncBaseAPI):
    """
    Asynchronous Genres API.

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

    async def movie_list(self) -> GenresResponse:
        """
        Get movie genres list.

        Returns
        -------
        GenresResponse
            The GenresResponse response.
        """
        return await self._client._get("/genre/movie/list", GenresResponse)

    async def tv_list(self) -> GenresResponse:
        """
        Get TV genres list.

        Returns
        -------
        GenresResponse
            The GenresResponse response.
        """
        return await self._client._get("/genre/tv/list", GenresResponse)
