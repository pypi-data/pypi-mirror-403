# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Movie models."""

import msgspec

from tmdbfusion.models.common import Genre
from tmdbfusion.models.common import ProductionCompany
from tmdbfusion.models.common import ProductionCountry
from tmdbfusion.models.common import SpokenLanguage


class Movie(msgspec.Struct, frozen=True):
    """Movie summary (from lists/search)."""

    id: int
    title: str
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


class BelongsToCollection(msgspec.Struct, frozen=True):
    """Collection reference."""

    id: int
    name: str
    poster_path: str | None = None
    backdrop_path: str | None = None


class MovieDetails(msgspec.Struct, frozen=True):
    """Full movie details."""

    id: int
    title: str
    adult: bool = False
    backdrop_path: str | None = None
    belongs_to_collection: BelongsToCollection | None = None
    budget: int = 0
    genres: list[Genre] = []
    homepage: str = ""
    imdb_id: str | None = None
    origin_country: list[str] = []
    original_language: str = ""
    original_title: str = ""
    overview: str = ""
    popularity: float = 0.0
    poster_path: str | None = None
    production_companies: list[ProductionCompany] = []
    production_countries: list[ProductionCountry] = []
    release_date: str = ""
    revenue: int = 0
    runtime: int | None = None
    spoken_languages: list[SpokenLanguage] = []
    status: str = ""
    tagline: str = ""
    video: bool = False
    vote_average: float = 0.0
    vote_count: int = 0
