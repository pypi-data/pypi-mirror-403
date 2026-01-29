# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Keywords API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.responses import KeywordDetails
from tmdbfusion.models.search import MoviePaginatedResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class KeywordsAPI(BaseAPI):
    """
    Synchronous Keywords API.

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

    def details(self, keyword_id: int) -> KeywordDetails:
        """
        Get keyword details.

        Parameters
        ----------
        keyword_id : int
            The keyword ID.

        Returns
        -------
        KeywordDetails
            The KeywordDetails response.
        """
        return self._client._get(
            f"/keyword/{keyword_id}",
            KeywordDetails,
        )

    def movies(
        self,
        keyword_id: int,
        *,
        page: int = 1,
        include_adult: bool = False,
    ) -> MoviePaginatedResponse:
        """
        Get movies with keyword.

        Parameters
        ----------
        keyword_id : int
            The keyword ID.
        page : int, optional
            The page number to retrieve.
        include_adult : bool, optional
            Include adult content in results.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return self._client._get(
            f"/keyword/{keyword_id}/movies",
            MoviePaginatedResponse,
            params={"page": page, "include_adult": include_adult},
        )


class AsyncKeywordsAPI(AsyncBaseAPI):
    """
    Asynchronous Keywords API.

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

    async def details(self, keyword_id: int) -> KeywordDetails:
        """
        Get keyword details.

        Parameters
        ----------
        keyword_id : int
            The keyword ID.

        Returns
        -------
        KeywordDetails
            The KeywordDetails response.
        """
        return await self._client._get(
            f"/keyword/{keyword_id}",
            KeywordDetails,
        )

    async def movies(
        self,
        keyword_id: int,
        *,
        page: int = 1,
        include_adult: bool = False,
    ) -> MoviePaginatedResponse:
        """
        Get movies with keyword.

        Parameters
        ----------
        keyword_id : int
            The keyword ID.
        page : int, optional
            The page number to retrieve.
        include_adult : bool, optional
            Include adult content in results.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return await self._client._get(
            f"/keyword/{keyword_id}/movies",
            MoviePaginatedResponse,
            params={"page": page, "include_adult": include_adult},
        )
