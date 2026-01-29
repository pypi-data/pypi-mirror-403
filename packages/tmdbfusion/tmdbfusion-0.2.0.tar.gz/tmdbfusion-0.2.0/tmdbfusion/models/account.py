# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Account models."""

import msgspec

from tmdbfusion.models.movie import Movie
from tmdbfusion.models.tv import TVSeries


class AccountDetails(msgspec.Struct, frozen=True):
    """Account details."""

    id: int
    name: str
    username: str
    include_adult: bool = False
    iso_639_1: str = ""
    iso_3166_1: str = ""
    avatar: dict[str, dict[str, str | None]] = {}


class FavoriteMoviesResponse(msgspec.Struct, frozen=True):
    """Favorite movies response."""

    page: int
    results: list[Movie]
    total_pages: int
    total_results: int


class FavoriteTVResponse(msgspec.Struct, frozen=True):
    """Favorite TV response."""

    page: int
    results: list[TVSeries]
    total_pages: int
    total_results: int


class RatedMovie(msgspec.Struct, frozen=True):
    """Rated movie."""

    id: int
    title: str
    rating: float
    adult: bool = False
    backdrop_path: str | None = None
    genre_ids: list[int] = []
    original_language: str = ""
    original_title: str = ""
    overview: str = ""
    popularity: float = 0.0
    poster_path: str | None = None
    release_date: str = ""
    video: bool = False
    vote_average: float = 0.0
    vote_count: int = 0


class RatedMoviesResponse(msgspec.Struct, frozen=True):
    """Rated movies response."""

    page: int
    results: list[RatedMovie]
    total_pages: int
    total_results: int


class RatedTV(msgspec.Struct, frozen=True):
    """Rated TV show."""

    id: int
    name: str
    rating: float
    adult: bool = False
    backdrop_path: str | None = None
    first_air_date: str = ""
    genre_ids: list[int] = []
    origin_country: list[str] = []
    original_language: str = ""
    original_name: str = ""
    overview: str = ""
    popularity: float = 0.0
    poster_path: str | None = None
    vote_average: float = 0.0
    vote_count: int = 0


class RatedTVResponse(msgspec.Struct, frozen=True):
    """Rated TV response."""

    page: int
    results: list[RatedTV]
    total_pages: int
    total_results: int


class RatedEpisode(msgspec.Struct, frozen=True):
    """Rated episode."""

    id: int
    name: str
    rating: float
    air_date: str = ""
    episode_number: int = 0
    overview: str = ""
    production_code: str = ""
    runtime: int | None = None
    season_number: int = 0
    show_id: int = 0
    still_path: str | None = None
    vote_average: float = 0.0
    vote_count: int = 0


class RatedEpisodesResponse(msgspec.Struct, frozen=True):
    """Rated episodes response."""

    page: int
    results: list[RatedEpisode]
    total_pages: int
    total_results: int


class WatchlistMoviesResponse(msgspec.Struct, frozen=True):
    """Watchlist movies response."""

    page: int
    results: list[Movie]
    total_pages: int
    total_results: int


class WatchlistTVResponse(msgspec.Struct, frozen=True):
    """Watchlist TV response."""

    page: int
    results: list[TVSeries]
    total_pages: int
    total_results: int


class AccountListsResponse(msgspec.Struct, frozen=True):
    """Account lists response."""

    page: int
    results: list[dict[str, object]]
    total_pages: int
    total_results: int
