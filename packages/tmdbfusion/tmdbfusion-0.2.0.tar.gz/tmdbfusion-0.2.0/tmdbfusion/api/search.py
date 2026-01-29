# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Search API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.search import CollectionPaginatedResponse
from tmdbfusion.models.search import CompanyPaginatedResponse
from tmdbfusion.models.search import KeywordPaginatedResponse
from tmdbfusion.models.search import MoviePaginatedResponse
from tmdbfusion.models.search import MultiPaginatedResponse
from tmdbfusion.models.search import PersonPaginatedResponse
from tmdbfusion.models.search import TVPaginatedResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class SearchAPI(BaseAPI):
    """
    Synchronous Search API.

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

    def movie(
        self,
        query: str,
        *,
        page: int = 1,
        include_adult: bool = False,
        year: int | None = None,
        primary_release_year: int | None = None,
        region: str | None = None,
    ) -> MoviePaginatedResponse:
        """
        Search for movies.

        Parameters
        ----------
        query : str
            The search query string.
        page : int, optional
            The page number to retrieve.
        include_adult : bool, optional
            Include adult content in results.
        year : int | None, optional
            Filter by year.
        primary_release_year : int | None, optional
            Filter by primary release year.
        region : str | None, optional
            Filter by region.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        params: dict[str, typing.Any] = {
            "query": query,
            "page": page,
            "include_adult": include_adult,
        }
        if year:
            params["year"] = year
        if primary_release_year:
            params["primary_release_year"] = primary_release_year
        if region:
            params["region"] = region
        return self._client._get(
            "/search/movie",
            MoviePaginatedResponse,
            params=params,
        )

    def tv(
        self,
        query: str,
        *,
        page: int = 1,
        include_adult: bool = False,
        first_air_date_year: int | None = None,
    ) -> TVPaginatedResponse:
        """
        Search for TV shows.

        Parameters
        ----------
        query : str
            The search query string.
        page : int, optional
            The page number to retrieve.
        include_adult : bool, optional
            Include adult content in results.
        first_air_date_year : int | None, optional
            Filter by first air date year.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        params: dict[str, typing.Any] = {
            "query": query,
            "page": page,
            "include_adult": include_adult,
        }
        if first_air_date_year:
            params["first_air_date_year"] = first_air_date_year
        return self._client._get(
            "/search/tv",
            TVPaginatedResponse,
            params=params,
        )

    def person(
        self,
        query: str,
        *,
        page: int = 1,
        include_adult: bool = False,
    ) -> PersonPaginatedResponse:
        """
        Search for people.

        Parameters
        ----------
        query : str
            The search query string.
        page : int, optional
            The page number to retrieve.
        include_adult : bool, optional
            Include adult content in results.

        Returns
        -------
        PersonPaginatedResponse
            Paginated list of people.
        """
        return self._client._get(
            "/search/person",
            PersonPaginatedResponse,
            params={
                "query": query,
                "page": page,
                "include_adult": include_adult,
            },
        )

    def collection(
        self,
        query: str,
        *,
        page: int = 1,
    ) -> CollectionPaginatedResponse:
        """
        Search for collections.

        Parameters
        ----------
        query : str
            The search query string.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        CollectionPaginatedResponse
            The CollectionPaginatedResponse response.
        """
        return self._client._get(
            "/search/collection",
            CollectionPaginatedResponse,
            params={"query": query, "page": page},
        )

    def company(
        self,
        query: str,
        *,
        page: int = 1,
    ) -> CompanyPaginatedResponse:
        """
        Search for companies.

        Parameters
        ----------
        query : str
            The search query string.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        CompanyPaginatedResponse
            The CompanyPaginatedResponse response.
        """
        return self._client._get(
            "/search/company",
            CompanyPaginatedResponse,
            params={"query": query, "page": page},
        )

    def keyword(
        self,
        query: str,
        *,
        page: int = 1,
    ) -> KeywordPaginatedResponse:
        """
        Search for keywords.

        Parameters
        ----------
        query : str
            The search query string.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        KeywordPaginatedResponse
            The KeywordPaginatedResponse response.
        """
        return self._client._get(
            "/search/keyword",
            KeywordPaginatedResponse,
            params={"query": query, "page": page},
        )

    def multi(
        self,
        query: str,
        *,
        page: int = 1,
        include_adult: bool = False,
    ) -> MultiPaginatedResponse:
        """
        Search across movies, TV shows, and people.

        Parameters
        ----------
        query : str
            The search query string.
        page : int, optional
            The page number to retrieve.
        include_adult : bool, optional
            Include adult content in results.

        Returns
        -------
        MultiPaginatedResponse
            The MultiPaginatedResponse response.
        """
        return self._client._get(
            "/search/multi",
            MultiPaginatedResponse,
            params={
                "query": query,
                "page": page,
                "include_adult": include_adult,
            },
        )


class AsyncSearchAPI(AsyncBaseAPI):
    """
    Asynchronous Search API.

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

    async def movie(
        self,
        query: str,
        *,
        page: int = 1,
        include_adult: bool = False,
        year: int | None = None,
        primary_release_year: int | None = None,
        region: str | None = None,
    ) -> MoviePaginatedResponse:
        """
        Search for movies.

        Parameters
        ----------
        query : str
            The search query string.
        page : int, optional
            The page number to retrieve.
        include_adult : bool, optional
            Include adult content in results.
        year : int | None, optional
            Filter by year.
        primary_release_year : int | None, optional
            Filter by primary release year.
        region : str | None, optional
            Filter by region.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        params: dict[str, typing.Any] = {
            "query": query,
            "page": page,
            "include_adult": include_adult,
        }
        if year:
            params["year"] = year
        if primary_release_year:
            params["primary_release_year"] = primary_release_year
        if region:
            params["region"] = region
        return await self._client._get(
            "/search/movie",
            MoviePaginatedResponse,
            params=params,
        )

    async def tv(
        self,
        query: str,
        *,
        page: int = 1,
        include_adult: bool = False,
        first_air_date_year: int | None = None,
    ) -> TVPaginatedResponse:
        """
        Search for TV shows.

        Parameters
        ----------
        query : str
            The search query string.
        page : int, optional
            The page number to retrieve.
        include_adult : bool, optional
            Include adult content in results.
        first_air_date_year : int | None, optional
            Filter by first air date year.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        params: dict[str, typing.Any] = {
            "query": query,
            "page": page,
            "include_adult": include_adult,
        }
        if first_air_date_year:
            params["first_air_date_year"] = first_air_date_year
        return await self._client._get(
            "/search/tv",
            TVPaginatedResponse,
            params=params,
        )

    async def person(
        self,
        query: str,
        *,
        page: int = 1,
        include_adult: bool = False,
    ) -> PersonPaginatedResponse:
        """
        Search for people.

        Parameters
        ----------
        query : str
            The search query string.
        page : int, optional
            The page number to retrieve.
        include_adult : bool, optional
            Include adult content in results.

        Returns
        -------
        PersonPaginatedResponse
            Paginated list of people.
        """
        return await self._client._get(
            "/search/person",
            PersonPaginatedResponse,
            params={
                "query": query,
                "page": page,
                "include_adult": include_adult,
            },
        )

    async def collection(
        self,
        query: str,
        *,
        page: int = 1,
    ) -> CollectionPaginatedResponse:
        """
        Search for collections.

        Parameters
        ----------
        query : str
            The search query string.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        CollectionPaginatedResponse
            The CollectionPaginatedResponse response.
        """
        return await self._client._get(
            "/search/collection",
            CollectionPaginatedResponse,
            params={"query": query, "page": page},
        )

    async def company(
        self,
        query: str,
        *,
        page: int = 1,
    ) -> CompanyPaginatedResponse:
        """
        Search for companies.

        Parameters
        ----------
        query : str
            The search query string.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        CompanyPaginatedResponse
            The CompanyPaginatedResponse response.
        """
        return await self._client._get(
            "/search/company",
            CompanyPaginatedResponse,
            params={"query": query, "page": page},
        )

    async def keyword(
        self,
        query: str,
        *,
        page: int = 1,
    ) -> KeywordPaginatedResponse:
        """
        Search for keywords.

        Parameters
        ----------
        query : str
            The search query string.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        KeywordPaginatedResponse
            The KeywordPaginatedResponse response.
        """
        return await self._client._get(
            "/search/keyword",
            KeywordPaginatedResponse,
            params={"query": query, "page": page},
        )

    async def multi(
        self,
        query: str,
        *,
        page: int = 1,
        include_adult: bool = False,
    ) -> MultiPaginatedResponse:
        """
        Search across movies, TV shows, and people.

        Parameters
        ----------
        query : str
            The search query string.
        page : int, optional
            The page number to retrieve.
        include_adult : bool, optional
            Include adult content in results.

        Returns
        -------
        MultiPaginatedResponse
            The MultiPaginatedResponse response.
        """
        return await self._client._get(
            "/search/multi",
            MultiPaginatedResponse,
            params={
                "query": query,
                "page": page,
                "include_adult": include_adult,
            },
        )
