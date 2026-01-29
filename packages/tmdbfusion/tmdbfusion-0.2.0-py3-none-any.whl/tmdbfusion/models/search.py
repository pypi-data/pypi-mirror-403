# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Search result models."""

from __future__ import annotations

import typing

import msgspec


class MovieSearchResult(msgspec.Struct, frozen=True):
    """Movie search result."""

    id: int
    title: str
    media_type: str = "movie"
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


class TVSearchResult(msgspec.Struct, frozen=True):
    """TV search result."""

    id: int
    name: str
    media_type: str = "tv"
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


class PersonSearchResult(msgspec.Struct, frozen=True):
    """Person search result."""

    id: int
    name: str
    media_type: str = "person"
    adult: bool = False
    gender: int = 0
    known_for_department: str = ""
    original_name: str = ""
    popularity: float = 0.0
    profile_path: str | None = None


class CollectionSearchResult(msgspec.Struct, frozen=True):
    """Collection search result."""

    id: int
    name: str
    backdrop_path: str | None = None
    poster_path: str | None = None
    adult: bool = False
    original_language: str = ""
    original_name: str = ""
    overview: str = ""


class CompanySearchResult(msgspec.Struct, frozen=True):
    """Company search result."""

    id: int
    name: str
    logo_path: str | None = None
    origin_country: str = ""


class KeywordSearchResult(msgspec.Struct, frozen=True):
    """Keyword search result."""

    id: int
    name: str


MultiSearchResult = MovieSearchResult | TVSearchResult | PersonSearchResult


class PaginatedResponse(msgspec.Struct, frozen=True, kw_only=True):
    """Base paginated response."""

    page: int
    total_pages: int
    total_results: int


class MoviePaginatedResponse(PaginatedResponse, frozen=True, kw_only=True):
    """Paginated movie response."""

    results: list[MovieSearchResult]


class TVPaginatedResponse(PaginatedResponse, frozen=True, kw_only=True):
    """Paginated TV response."""

    results: list[TVSearchResult]


class PersonPaginatedResponse(PaginatedResponse, frozen=True, kw_only=True):
    """Paginated person response."""

    results: list[PersonSearchResult]


class CollectionPaginatedResponse(
    PaginatedResponse,
    frozen=True,
    kw_only=True,
):
    """Paginated collection response."""

    results: list[CollectionSearchResult]


class CompanyPaginatedResponse(PaginatedResponse, frozen=True, kw_only=True):
    """Paginated company response."""

    results: list[CompanySearchResult]


class KeywordPaginatedResponse(PaginatedResponse, frozen=True, kw_only=True):
    """Paginated keyword response."""

    results: list[KeywordSearchResult]


class MultiPaginatedResponse(PaginatedResponse, frozen=True, kw_only=True):
    """Paginated multi-search response."""

    results: list[dict[str, typing.Any]]
