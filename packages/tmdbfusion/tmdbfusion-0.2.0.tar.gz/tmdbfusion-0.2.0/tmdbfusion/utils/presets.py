# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Discover Query Presets.

Pre-built, documented discovery queries for common use cases.
"""

from __future__ import annotations

import typing
from dataclasses import dataclass
from datetime import date
from datetime import timedelta


if typing.TYPE_CHECKING:
    from tmdbfusion.core.sync_client import TMDBClient
    from tmdbfusion.models.responses import PaginatedMovieResults
    from tmdbfusion.models.responses import PaginatedTVResults


@dataclass
class GenreIds:
    """Common TMDB genre IDs.

    Attributes
    ----------
    ACTION : int
        Action genre ID.
    COMEDY : int
        Comedy genre ID.
    DRAMA : int
        Drama genre ID.
    HORROR : int
        Horror genre ID.
    SCIFI : int
        Science Fiction genre ID.
    ANIMATION : int
        Animation genre ID.
    DOCUMENTARY : int
        Documentary genre ID.
    ROMANCE : int
        Romance genre ID.
    THRILLER : int
        Thriller genre ID.

    """

    # Movie genres
    ACTION: int = 28
    COMEDY: int = 35
    DRAMA: int = 18
    HORROR: int = 27
    SCIFI: int = 878
    ANIMATION: int = 16
    DOCUMENTARY: int = 99
    ROMANCE: int = 10749
    THRILLER: int = 53

    # TV genres (some differ)
    TV_ACTION: int = 10759
    TV_ANIMATION: int = 16
    TV_COMEDY: int = 35
    TV_DRAMA: int = 18
    TV_SCIFI: int = 10765


class DiscoverPresets:
    """Pre-built discovery queries.

    Examples
    --------
    >>> presets = DiscoverPresets(client)
    >>> movies = presets.top_rated_movies(min_votes=1000)
    >>> hidden = presets.hidden_gems(min_rating=7.5)

    Parameters
    ----------
    client : TMDBClient
        TMDB client instance.

    """

    def __init__(self, client: TMDBClient) -> None:
        self._client = client

    def top_rated_movies(
        self,
        *,
        min_votes: int = 500,
        page: int = 1,
    ) -> PaginatedMovieResults:
        """Get top-rated movies with significant vote counts.

        Parameters
        ----------
        min_votes : int
            Minimum vote count threshold.
        page : int
            Page number.

        Returns
        -------
        PaginatedMovieResults
            Paginated results.

        """
        return self._client.discover.movie(
            sort_by="vote_average.desc",
            vote_count_gte=min_votes,
            page=page,
        )

    def hidden_gems(
        self,
        *,
        min_rating: float = 7.0,
        max_votes: int = 500,
        page: int = 1,
    ) -> PaginatedMovieResults:
        """Find highly-rated movies with low vote counts.

        Parameters
        ----------
        min_rating : float
            Minimum vote average.
        max_votes : int
            Maximum vote count (to find lesser-known films).
        page : int
            Page number.

        Returns
        -------
        PaginatedMovieResults
            Paginated results.

        """
        return self._client.discover.movie(
            sort_by="vote_average.desc",
            vote_average_gte=min_rating,
            vote_count_lte=max_votes,
            vote_count_gte=50,  # At least some votes
            page=page,
        )

    def new_releases(
        self,
        *,
        days: int = 30,
        region: str = "US",
        page: int = 1,
    ) -> PaginatedMovieResults:
        """Get recent theatrical releases.

        Parameters
        ----------
        days : int
            Number of days back to look.
        region : str
            Release region code.
        page : int
            Page number.

        Returns
        -------
        PaginatedMovieResults
            Paginated results.

        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        return self._client.discover.movie(
            sort_by="release_date.desc",
            primary_release_date_gte=start_date.isoformat(),
            primary_release_date_lte=end_date.isoformat(),
            region=region,
            with_release_type=3,  # Theatrical
            page=page,
        )

    def upcoming_movies(
        self,
        *,
        days_ahead: int = 90,
        region: str = "US",
        page: int = 1,
    ) -> PaginatedMovieResults:
        """Get upcoming movie releases.

        Parameters
        ----------
        days_ahead : int
            Days into the future to look.
        region : str
            Release region code.
        page : int
            Page number.

        Returns
        -------
        PaginatedMovieResults
            Paginated results.

        """
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)

        return self._client.discover.movie(
            sort_by="primary_release_date.asc",
            primary_release_date_gte=start_date.isoformat(),
            primary_release_date_lte=end_date.isoformat(),
            region=region,
            page=page,
        )

    def by_genre(
        self,
        genre_id: int,
        *,
        min_rating: float = 6.0,
        page: int = 1,
    ) -> PaginatedMovieResults:
        """Get movies by genre with quality filter.

        Parameters
        ----------
        genre_id : int
            Genre ID (use GenreIds constants).
        min_rating : float
            Minimum vote average.
        page : int
            Page number.

        Returns
        -------
        PaginatedMovieResults
            Paginated results.

        """
        return self._client.discover.movie(
            with_genres=str(genre_id),
            sort_by="popularity.desc",
            vote_average_gte=min_rating,
            vote_count_gte=100,
            page=page,
        )

    def anime_series(
        self,
        *,
        sort: str = "popularity",
        page: int = 1,
    ) -> PaginatedTVResults:
        """Get anime TV series.

        Parameters
        ----------
        sort : str
            Sort field: "popularity", "rating", "date".
        page : int
            Page number.

        Returns
        -------
        PaginatedTVResults
            Paginated results.

        """
        sort_map = {
            "popularity": "popularity.desc",
            "rating": "vote_average.desc",
            "date": "first_air_date.desc",
        }
        sort_by = sort_map.get(sort, "popularity.desc")

        return self._client.discover.tv(
            with_genres=str(GenreIds.TV_ANIMATION),
            with_keywords="210024",  # Anime keyword
            sort_by=sort_by,
            vote_count_gte=50,
            page=page,
        )

    def documentary_films(
        self,
        *,
        min_rating: float = 7.0,
        page: int = 1,
    ) -> PaginatedMovieResults:
        """Get highly-rated documentaries.

        Parameters
        ----------
        min_rating : float
            Minimum vote average.
        page : int
            Page number.

        Returns
        -------
        PaginatedMovieResults
            Paginated results.

        """
        return self._client.discover.movie(
            with_genres=str(GenreIds.DOCUMENTARY),
            sort_by="vote_average.desc",
            vote_average_gte=min_rating,
            vote_count_gte=100,
            page=page,
        )

    def classic_movies(
        self,
        *,
        before_year: int = 1980,
        min_rating: float = 7.5,
        page: int = 1,
    ) -> PaginatedMovieResults:
        """Get classic films from before a cutoff year.

        Parameters
        ----------
        before_year : int
            Movies released before this year.
        min_rating : float
            Minimum vote average.
        page : int
            Page number.

        Returns
        -------
        PaginatedMovieResults
            Paginated results.

        """
        return self._client.discover.movie(
            sort_by="vote_average.desc",
            primary_release_date_lte=f"{before_year}-01-01",
            vote_average_gte=min_rating,
            vote_count_gte=500,
            page=page,
        )

    def streaming_on(
        self,
        provider_id: int,
        *,
        region: str = "US",
        page: int = 1,
    ) -> PaginatedMovieResults:
        """Get movies available on a streaming provider.

        Parameters
        ----------
        provider_id : int
            Watch provider ID (e.g., 8 for Netflix, 9 for Amazon).
        region : str
            Region code.
        page : int
            Page number.

        Returns
        -------
        PaginatedMovieResults
            Paginated results.

        """
        return self._client.discover.movie(
            with_watch_providers=str(provider_id),
            watch_region=region,
            sort_by="popularity.desc",
            page=page,
        )
