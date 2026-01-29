# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Common models shared across endpoints."""

import msgspec


class Genre(msgspec.Struct, frozen=True):
    """Genre."""

    id: int
    name: str


class ProductionCompany(msgspec.Struct, frozen=True):
    """Production company."""

    id: int
    name: str
    logo_path: str | None = None
    origin_country: str = ""


class ProductionCountry(msgspec.Struct, frozen=True):
    """Production country."""

    iso_3166_1: str
    name: str


class SpokenLanguage(msgspec.Struct, frozen=True):
    """Spoken language."""

    iso_639_1: str
    name: str
    english_name: str = ""


class Keyword(msgspec.Struct, frozen=True):
    """Keyword."""

    id: int
    name: str


class Video(msgspec.Struct, frozen=True):
    """Video (trailer, teaser, etc.)."""

    id: str
    iso_639_1: str
    iso_3166_1: str
    key: str
    name: str
    site: str
    size: int
    type: str
    official: bool = True
    published_at: str = ""


class Image(msgspec.Struct, frozen=True):
    """Image (poster, backdrop, etc.)."""

    file_path: str
    aspect_ratio: float
    height: int
    width: int
    vote_average: float = 0.0
    vote_count: int = 0
    iso_639_1: str | None = None


class WatchProvider(msgspec.Struct, frozen=True):
    """Watch provider."""

    provider_id: int
    provider_name: str
    logo_path: str
    display_priority: int = 0


class Translation(msgspec.Struct, frozen=True):
    """Translation."""

    iso_639_1: str
    iso_3166_1: str
    name: str
    english_name: str
    data: dict[str, str] = {}


class ExternalIds(msgspec.Struct, frozen=True):
    """External IDs."""

    imdb_id: str | None = None
    facebook_id: str | None = None
    instagram_id: str | None = None
    twitter_id: str | None = None
    wikidata_id: str | None = None
    tvdb_id: int | None = None
    freebase_mid: str | None = None
    freebase_id: str | None = None
