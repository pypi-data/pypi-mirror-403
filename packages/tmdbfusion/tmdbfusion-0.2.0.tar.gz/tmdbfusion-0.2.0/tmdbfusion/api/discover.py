# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Discover API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.search import MoviePaginatedResponse
from tmdbfusion.models.search import TVPaginatedResponse
from tmdbfusion.utils import DiscoverBuilder


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


def _build_params(
    base: dict[str, typing.Any],
    **kwargs: str | float | bool | None,
) -> dict[str, typing.Any]:
    """
    Build params dict, filtering None values and mapping keys.

    Parameters
    ----------
    base : dict[str, typing.Any]
        The base parameters dictionary.
    **kwargs : str | float | bool | None
        Additional keyword arguments to add to params.

    Returns
    -------
    dict[str, typing.Any]
        The merged parameters dictionary.
    """
    key_map = {
        "primary_release_date_gte": "primary_release_date.gte",
        "primary_release_date_lte": "primary_release_date.lte",
        "release_date_gte": "release_date.gte",
        "release_date_lte": "release_date.lte",
        "vote_average_gte": "vote_average.gte",
        "vote_average_lte": "vote_average.lte",
        "vote_count_gte": "vote_count.gte",
        "vote_count_lte": "vote_count.lte",
        "with_runtime_gte": "with_runtime.gte",
        "with_runtime_lte": "with_runtime.lte",
        "first_air_date_gte": "first_air_date.gte",
        "first_air_date_lte": "first_air_date.lte",
    }
    result = base.copy()
    for key, value in kwargs.items():
        if value is not None:
            mapped_key = key_map.get(key, key)
            result[mapped_key] = value
    return result


class DiscoverAPI(BaseAPI):
    """
    Synchronous Discover API.

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

    def build(self) -> DiscoverBuilder:
        """
        Create a query builder.

        Returns
        -------
        DiscoverBuilder
            The DiscoverBuilder response.
        """
        return DiscoverBuilder()

    def movie(
        self,
        *,
        page: int = 1,
        sort_by: str = "popularity.desc",
        include_adult: bool = False,
        include_video: bool = False,
        primary_release_year: int | None = None,
        primary_release_date_gte: str | None = None,
        primary_release_date_lte: str | None = None,
        release_date_gte: str | None = None,
        release_date_lte: str | None = None,
        vote_average_gte: float | None = None,
        vote_average_lte: float | None = None,
        vote_count_gte: int | None = None,
        vote_count_lte: int | None = None,
        with_genres: str | None = None,
        without_genres: str | None = None,
        with_keywords: str | None = None,
        without_keywords: str | None = None,
        with_cast: str | None = None,
        with_crew: str | None = None,
        with_companies: str | None = None,
        with_people: str | None = None,
        with_watch_providers: str | None = None,
        watch_region: str | None = None,
        with_runtime_gte: int | None = None,
        with_runtime_lte: int | None = None,
        with_original_language: str | None = None,
        year: int | None = None,
    ) -> MoviePaginatedResponse:
        """
        Discover movies.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.
        include_adult : bool, optional
            Include adult content in results.
        include_video : bool, optional
            The include video.
        primary_release_year : int | None, optional
            Filter by primary release year.
        primary_release_date_gte : str | None, optional
            The primary release date gte.
        primary_release_date_lte : str | None, optional
            The primary release date lte.
        release_date_gte : str | None, optional
            The release date gte.
        release_date_lte : str | None, optional
            The release date lte.
        vote_average_gte : float | None, optional
            The vote average gte.
        vote_average_lte : float | None, optional
            The vote average lte.
        vote_count_gte : int | None, optional
            The vote count gte.
        vote_count_lte : int | None, optional
            The vote count lte.
        with_genres : str | None, optional
            The with genres.
        without_genres : str | None, optional
            The without genres.
        with_keywords : str | None, optional
            The with keywords.
        without_keywords : str | None, optional
            The without keywords.
        with_cast : str | None, optional
            The with cast.
        with_crew : str | None, optional
            The with crew.
        with_companies : str | None, optional
            The with companies.
        with_people : str | None, optional
            The with people.
        with_watch_providers : str | None, optional
            The with watch providers.
        watch_region : str | None, optional
            Filter by watch region.
        with_runtime_gte : int | None, optional
            The with runtime gte.
        with_runtime_lte : int | None, optional
            The with runtime lte.
        with_original_language : str | None, optional
            The with original language.
        year : int | None, optional
            Filter by year.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        base = {
            "page": page,
            "sort_by": sort_by,
            "include_adult": include_adult,
            "include_video": include_video,
        }
        params = _build_params(
            base,
            primary_release_year=primary_release_year,
            primary_release_date_gte=primary_release_date_gte,
            primary_release_date_lte=primary_release_date_lte,
            release_date_gte=release_date_gte,
            release_date_lte=release_date_lte,
            vote_average_gte=vote_average_gte,
            vote_average_lte=vote_average_lte,
            vote_count_gte=vote_count_gte,
            vote_count_lte=vote_count_lte,
            with_genres=with_genres,
            without_genres=without_genres,
            with_keywords=with_keywords,
            without_keywords=without_keywords,
            with_cast=with_cast,
            with_crew=with_crew,
            with_companies=with_companies,
            with_people=with_people,
            with_watch_providers=with_watch_providers,
            watch_region=watch_region,
            with_runtime_gte=with_runtime_gte,
            with_runtime_lte=with_runtime_lte,
            with_original_language=with_original_language,
            year=year,
        )
        return self._client._get(
            "/discover/movie",
            MoviePaginatedResponse,
            params=params,
        )

    def tv(
        self,
        *,
        page: int = 1,
        sort_by: str = "popularity.desc",
        include_adult: bool = False,
        include_null_first_air_dates: bool = False,
        first_air_date_year: int | None = None,
        first_air_date_gte: str | None = None,
        first_air_date_lte: str | None = None,
        vote_average_gte: float | None = None,
        vote_average_lte: float | None = None,
        vote_count_gte: int | None = None,
        with_genres: str | None = None,
        without_genres: str | None = None,
        with_keywords: str | None = None,
        without_keywords: str | None = None,
        with_companies: str | None = None,
        with_networks: str | None = None,
        with_watch_providers: str | None = None,
        watch_region: str | None = None,
        with_runtime_gte: int | None = None,
        with_runtime_lte: int | None = None,
        with_original_language: str | None = None,
        with_status: str | None = None,
        with_type: str | None = None,
        screened_theatrically: bool | None = None,
        timezone: str | None = None,
    ) -> TVPaginatedResponse:
        """
        Discover TV shows.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.
        include_adult : bool, optional
            Include adult content in results.
        include_null_first_air_dates : bool, optional
            The include null first air dates.
        first_air_date_year : int | None, optional
            Filter by first air date year.
        first_air_date_gte : str | None, optional
            The first air date gte.
        first_air_date_lte : str | None, optional
            The first air date lte.
        vote_average_gte : float | None, optional
            The vote average gte.
        vote_average_lte : float | None, optional
            The vote average lte.
        vote_count_gte : int | None, optional
            The vote count gte.
        with_genres : str | None, optional
            The with genres.
        without_genres : str | None, optional
            The without genres.
        with_keywords : str | None, optional
            The with keywords.
        without_keywords : str | None, optional
            The without keywords.
        with_companies : str | None, optional
            The with companies.
        with_networks : str | None, optional
            The with networks.
        with_watch_providers : str | None, optional
            The with watch providers.
        watch_region : str | None, optional
            Filter by watch region.
        with_runtime_gte : int | None, optional
            The with runtime gte.
        with_runtime_lte : int | None, optional
            The with runtime lte.
        with_original_language : str | None, optional
            The with original language.
        with_status : str | None, optional
            The with status.
        with_type : str | None, optional
            The with type.
        screened_theatrically : bool | None, optional
            The screened theatrically.
        timezone : str | None, optional
            The timezone.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        base = {
            "page": page,
            "sort_by": sort_by,
            "include_adult": include_adult,
            "include_null_first_air_dates": include_null_first_air_dates,
        }
        params = _build_params(
            base,
            first_air_date_year=first_air_date_year,
            first_air_date_gte=first_air_date_gte,
            first_air_date_lte=first_air_date_lte,
            vote_average_gte=vote_average_gte,
            vote_average_lte=vote_average_lte,
            vote_count_gte=vote_count_gte,
            with_genres=with_genres,
            without_genres=without_genres,
            with_keywords=with_keywords,
            without_keywords=without_keywords,
            with_companies=with_companies,
            with_networks=with_networks,
            with_watch_providers=with_watch_providers,
            watch_region=watch_region,
            with_runtime_gte=with_runtime_gte,
            with_runtime_lte=with_runtime_lte,
            with_original_language=with_original_language,
            with_status=with_status,
            with_type=with_type,
            screened_theatrically=screened_theatrically,
            timezone=timezone,
        )
        return self._client._get(
            "/discover/tv",
            TVPaginatedResponse,
            params=params,
        )


class AsyncDiscoverAPI(AsyncBaseAPI):
    """
    Asynchronous Discover API.

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

    def build(self) -> DiscoverBuilder:
        """
        Create a query builder.

        Returns
        -------
        DiscoverBuilder
            The DiscoverBuilder response.
        """
        return DiscoverBuilder()

    async def movie(
        self,
        *,
        page: int = 1,
        sort_by: str = "popularity.desc",
        include_adult: bool = False,
        include_video: bool = False,
        primary_release_year: int | None = None,
        with_genres: str | None = None,
        without_genres: str | None = None,
        with_keywords: str | None = None,
        with_companies: str | None = None,
        with_original_language: str | None = None,
        year: int | None = None,
    ) -> MoviePaginatedResponse:
        """
        Discover movies.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.
        include_adult : bool, optional
            Include adult content in results.
        include_video : bool, optional
            The include video.
        primary_release_year : int | None, optional
            Filter by primary release year.
        with_genres : str | None, optional
            The with genres.
        without_genres : str | None, optional
            The without genres.
        with_keywords : str | None, optional
            The with keywords.
        with_companies : str | None, optional
            The with companies.
        with_original_language : str | None, optional
            The with original language.
        year : int | None, optional
            Filter by year.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        base = {
            "page": page,
            "sort_by": sort_by,
            "include_adult": include_adult,
            "include_video": include_video,
        }
        params = _build_params(
            base,
            primary_release_year=primary_release_year,
            with_genres=with_genres,
            without_genres=without_genres,
            with_keywords=with_keywords,
            with_companies=with_companies,
            with_original_language=with_original_language,
            year=year,
        )
        return await self._client._get(
            "/discover/movie",
            MoviePaginatedResponse,
            params=params,
        )

    async def tv(
        self,
        *,
        page: int = 1,
        sort_by: str = "popularity.desc",
        include_adult: bool = False,
        first_air_date_year: int | None = None,
        with_genres: str | None = None,
        without_genres: str | None = None,
        with_keywords: str | None = None,
        with_companies: str | None = None,
        with_networks: str | None = None,
        with_original_language: str | None = None,
    ) -> TVPaginatedResponse:
        """
        Discover TV shows.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.
        sort_by : str, optional
            Sort order for results.
        include_adult : bool, optional
            Include adult content in results.
        first_air_date_year : int | None, optional
            Filter by first air date year.
        with_genres : str | None, optional
            The with genres.
        without_genres : str | None, optional
            The without genres.
        with_keywords : str | None, optional
            The with keywords.
        with_companies : str | None, optional
            The with companies.
        with_networks : str | None, optional
            The with networks.
        with_original_language : str | None, optional
            The with original language.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        base = {
            "page": page,
            "sort_by": sort_by,
            "include_adult": include_adult,
        }
        params = _build_params(
            base,
            first_air_date_year=first_air_date_year,
            with_genres=with_genres,
            without_genres=without_genres,
            with_keywords=with_keywords,
            with_companies=with_companies,
            with_networks=with_networks,
            with_original_language=with_original_language,
        )
        return await self._client._get(
            "/discover/tv",
            TVPaginatedResponse,
            params=params,
        )
