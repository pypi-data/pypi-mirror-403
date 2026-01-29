# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""TV models."""

import msgspec

from tmdbfusion.models.common import Genre
from tmdbfusion.models.common import ProductionCompany
from tmdbfusion.models.common import ProductionCountry
from tmdbfusion.models.common import SpokenLanguage


class Creator(msgspec.Struct, frozen=True):
    """TV series creator."""

    id: int
    name: str
    credit_id: str = ""
    gender: int = 0
    profile_path: str | None = None


class Network(msgspec.Struct, frozen=True):
    """TV network."""

    id: int
    name: str
    logo_path: str | None = None
    origin_country: str = ""


class TVSeries(msgspec.Struct, frozen=True):
    """TV series summary (from lists/search)."""

    id: int
    name: str
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


class SeasonSummary(msgspec.Struct, frozen=True):
    """Season summary for TVSeriesDetails."""

    id: int
    name: str
    air_date: str | None = None
    episode_count: int = 0
    overview: str = ""
    poster_path: str | None = None
    season_number: int = 0
    vote_average: float = 0.0


class TVSeriesDetails(msgspec.Struct, frozen=True):
    """Full TV series details."""

    id: int
    name: str
    adult: bool = False
    backdrop_path: str | None = None
    created_by: list[Creator] = []
    episode_run_time: list[int] = []
    first_air_date: str = ""
    genres: list[Genre] = []
    homepage: str = ""
    in_production: bool = False
    languages: list[str] = []
    last_air_date: str = ""
    networks: list[Network] = []
    number_of_episodes: int = 0
    number_of_seasons: int = 0
    origin_country: list[str] = []
    original_language: str = ""
    original_name: str = ""
    overview: str = ""
    popularity: float = 0.0
    poster_path: str | None = None
    production_companies: list[ProductionCompany] = []
    production_countries: list[ProductionCountry] = []
    seasons: list[SeasonSummary] = []
    spoken_languages: list[SpokenLanguage] = []
    status: str = ""
    tagline: str = ""
    type: str = ""
    vote_average: float = 0.0
    vote_count: int = 0


class TVSeason(msgspec.Struct, frozen=True):
    """TV season details."""

    id: int
    name: str
    air_date: str | None = None
    episode_count: int = 0
    overview: str = ""
    poster_path: str | None = None
    season_number: int = 0
    vote_average: float = 0.0


class GuestStar(msgspec.Struct, frozen=True):
    """Guest star in episode."""

    id: int
    name: str
    character: str = ""
    credit_id: str = ""
    order: int = 0
    adult: bool = False
    gender: int = 0
    known_for_department: str = ""
    original_name: str = ""
    popularity: float = 0.0
    profile_path: str | None = None


class TVEpisode(msgspec.Struct, frozen=True):
    """TV episode details."""

    id: int
    name: str
    air_date: str | None = None
    episode_number: int = 0
    episode_type: str = ""
    overview: str = ""
    production_code: str = ""
    runtime: int | None = None
    season_number: int = 0
    show_id: int = 0
    still_path: str | None = None
    vote_average: float = 0.0
    vote_count: int = 0
    guest_stars: list[GuestStar] = []
