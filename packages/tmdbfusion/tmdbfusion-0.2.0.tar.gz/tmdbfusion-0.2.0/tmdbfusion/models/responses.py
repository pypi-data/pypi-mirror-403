# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Response models for API endpoints."""

import typing

import msgspec

from tmdbfusion.models.common import Genre
from tmdbfusion.models.common import Image
from tmdbfusion.models.common import Keyword
from tmdbfusion.models.common import Video
from tmdbfusion.models.common import WatchProvider
from tmdbfusion.models.movie import Movie
from tmdbfusion.models.person import CastMember
from tmdbfusion.models.person import CrewMember
from tmdbfusion.models.responses_extra import AggregateCreditsResponse as AggCredResp
from tmdbfusion.models.responses_extra import EpisodeGroupsResponse as EpGrpResp
from tmdbfusion.models.responses_extra import ListDetails as LstDet
from tmdbfusion.models.responses_extra import ListItemStatus as LstItmStat
from tmdbfusion.models.responses_extra import ScreenedTheatricallyResponse as ScrThResp
from tmdbfusion.models.tv import TVSeries


T = typing.TypeVar("T")


class StatusResponse(msgspec.Struct, frozen=True):
    """Generic status response."""

    success: bool
    status_code: int
    status_message: str


class KeywordsResponse(msgspec.Struct, frozen=True):
    """Keywords response."""

    id: int
    keywords: list[Keyword] = []


class TVKeywordsResponse(msgspec.Struct, frozen=True):
    """TV keywords response (uses results instead of keywords)."""

    id: int
    results: list[Keyword] = []


class VideosResponse(msgspec.Struct, frozen=True):
    """Videos response."""

    id: int
    results: list[Video] = []


class ImagesResponse(msgspec.Struct, frozen=True):
    """Images response."""

    id: int
    backdrops: list[Image] = []
    logos: list[Image] = []
    posters: list[Image] = []
    stills: list[Image] = []
    profiles: list[Image] = []


class CreditsResponse(msgspec.Struct, frozen=True):
    """Credits response."""

    id: int
    cast: list[CastMember] = []
    crew: list[CrewMember] = []


class ExternalIdsResponse(msgspec.Struct, frozen=True):
    """External IDs response."""

    id: int
    imdb_id: str | None = None
    facebook_id: str | None = None
    instagram_id: str | None = None
    twitter_id: str | None = None
    wikidata_id: str | None = None
    tvdb_id: int | None = None
    freebase_mid: str | None = None
    freebase_id: str | None = None
    tvrage_id: int | None = None
    tiktok_id: str | None = None
    youtube_id: str | None = None


class TranslationData(msgspec.Struct, frozen=True):
    """Translation data."""

    title: str = ""
    overview: str = ""
    homepage: str = ""
    tagline: str = ""
    name: str = ""
    biography: str = ""


class Translation(msgspec.Struct, frozen=True):
    """Translation."""

    iso_639_1: str
    iso_3166_1: str
    name: str
    english_name: str
    data: TranslationData | None = None


class TranslationsResponse(msgspec.Struct, frozen=True):
    """Translations response."""

    id: int
    translations: list[Translation] = []


class WatchProviderCountry(msgspec.Struct, frozen=True):
    """Watch providers for a country."""

    link: str = ""
    flatrate: list[WatchProvider] = []
    rent: list[WatchProvider] = []
    buy: list[WatchProvider] = []
    ads: list[WatchProvider] = []
    free: list[WatchProvider] = []


class WatchProvidersResponse(msgspec.Struct, frozen=True):
    """Watch providers response."""

    id: int
    results: dict[str, WatchProviderCountry] = {}


class AlternativeTitle(msgspec.Struct, frozen=True):
    """Alternative title."""

    iso_3166_1: str
    title: str
    type: str = ""


class AlternativeTitlesResponse(msgspec.Struct, frozen=True):
    """Alternative titles response."""

    id: int
    titles: list[AlternativeTitle] = []
    results: list[AlternativeTitle] = []


class ReleaseDate(msgspec.Struct, frozen=True):
    """Release date info."""

    certification: str = ""
    iso_639_1: str = ""
    release_date: str = ""
    type: int = 0
    note: str = ""


class ReleaseDatesResult(msgspec.Struct, frozen=True):
    """Release dates by country."""

    iso_3166_1: str
    release_dates: list[ReleaseDate] = []


class ReleaseDatesResponse(msgspec.Struct, frozen=True):
    """Release dates response."""

    id: int
    results: list[ReleaseDatesResult] = []


class ContentRating(msgspec.Struct, frozen=True):
    """Content rating."""

    iso_3166_1: str
    rating: str
    descriptors: list[str] = []


class ContentRatingsResponse(msgspec.Struct, frozen=True):
    """Content ratings response."""

    id: int
    results: list[ContentRating] = []


class Review(msgspec.Struct, frozen=True):
    """Review."""

    id: str
    author: str
    content: str
    created_at: str = ""
    updated_at: str = ""
    url: str = ""


class ReviewsResponse(msgspec.Struct, frozen=True):
    """Reviews response."""

    id: int
    page: int = 1
    results: list[Review] = []
    total_pages: int = 1
    total_results: int = 0


class GenresResponse(msgspec.Struct, frozen=True):
    """Genres list response."""

    genres: list[Genre] = []


class AccountStates(msgspec.Struct, frozen=True):
    """Account states for media."""

    id: int
    favorite: bool = False
    watchlist: bool = False
    rated: bool | dict[str, float] = False


class ChangeItem(msgspec.Struct, frozen=True):
    """Change item."""

    id: str
    action: str
    time: str
    iso_639_1: str = ""
    iso_3166_1: str = ""
    value: typing.Any = None
    original_value: typing.Any = None


class Change(msgspec.Struct, frozen=True):
    """Change."""

    key: str
    items: list[ChangeItem] = []


class ChangesResponse(msgspec.Struct, frozen=True):
    """Changes response."""

    changes: list[Change] = []


class ListItem(msgspec.Struct, frozen=True):
    """List summary."""

    id: int
    name: str
    description: str = ""
    favorite_count: int = 0
    item_count: int = 0
    iso_639_1: str = ""
    list_type: str = ""
    poster_path: str | None = None


class ListsResponse(msgspec.Struct, frozen=True):
    """Lists response for media."""

    id: int
    page: int = 1
    results: list[ListItem] = []
    total_pages: int = 1
    total_results: int = 0


class FindResults(msgspec.Struct, frozen=True):
    """Find by external ID results."""

    movie_results: list[Movie] = []
    tv_results: list[TVSeries] = []
    person_results: list[typing.Any] = []
    tv_episode_results: list[typing.Any] = []
    tv_season_results: list[typing.Any] = []


class ImagesConfiguration(msgspec.Struct, frozen=True):
    """Images configuration."""

    base_url: str
    secure_base_url: str
    backdrop_sizes: list[str] = []
    logo_sizes: list[str] = []
    poster_sizes: list[str] = []
    profile_sizes: list[str] = []
    still_sizes: list[str] = []


class ConfigurationDetails(msgspec.Struct, frozen=True):
    """API configuration."""

    images: ImagesConfiguration
    change_keys: list[str] = []


class Country(msgspec.Struct, frozen=True):
    """Country."""

    iso_3166_1: str
    english_name: str
    native_name: str = ""


class Language(msgspec.Struct, frozen=True):
    """Language."""

    iso_639_1: str
    english_name: str
    name: str = ""


class Job(msgspec.Struct, frozen=True):
    """Job/department."""

    department: str
    jobs: list[str] = []


class Timezone(msgspec.Struct, frozen=True):
    """Timezone."""

    iso_3166_1: str
    zones: list[str] = []


class CertificationItem(msgspec.Struct, frozen=True):
    """Certification."""

    certification: str
    meaning: str
    order: int


class CertificationsResponse(msgspec.Struct, frozen=True):
    """Certifications response."""

    certifications: dict[str, list[CertificationItem]] = {}


class ChangesListItem(msgspec.Struct, frozen=True):
    """Item in changes list."""

    id: int
    adult: bool | None = None


class ChangesListResponse(msgspec.Struct, frozen=True):
    """Changes list response."""

    results: list[ChangesListItem] = []
    page: int = 1
    total_pages: int = 1
    total_results: int = 0


class RequestToken(msgspec.Struct, frozen=True):
    """Request token response."""

    success: bool
    expires_at: str = ""
    request_token: str = ""


class Session(msgspec.Struct, frozen=True):
    """Session response."""

    success: bool
    session_id: str = ""
    guest_session_id: str = ""
    expires_at: str = ""


class AvailableRegion(msgspec.Struct, frozen=True):
    """Available region for watch providers."""

    iso_3166_1: str
    english_name: str
    native_name: str = ""


class AvailableRegionsResponse(msgspec.Struct, frozen=True):
    """Available regions response."""

    results: list[AvailableRegion] = []


class WatchProviderItem(msgspec.Struct, frozen=True):
    """Watch provider item."""

    provider_id: int
    provider_name: str
    logo_path: str = ""
    display_priority: int = 0
    display_priorities: dict[str, int] = {}


class WatchProviderListResponse(msgspec.Struct, frozen=True):
    """Watch provider list response."""

    results: list[WatchProviderItem] = []


class CollectionDetails(msgspec.Struct, frozen=True):
    """Collection details."""

    id: int
    name: str
    overview: str = ""
    poster_path: str | None = None
    backdrop_path: str | None = None
    parts: list[Movie] = []


class CompanyDetails(msgspec.Struct, frozen=True):
    """Company details."""

    id: int
    name: str
    description: str = ""
    headquarters: str = ""
    homepage: str = ""
    logo_path: str | None = None
    origin_country: str = ""
    parent_company: typing.Any = None


class CompanyAlternativeName(msgspec.Struct, frozen=True):
    """Company alternative name."""

    name: str
    type: str = ""


class CompanyAlternativeNamesResponse(msgspec.Struct, frozen=True):
    """Company alternative names response."""

    id: int
    results: list[CompanyAlternativeName] = []


class CompanyImagesResponse(msgspec.Struct, frozen=True):
    """Company images response."""

    id: int
    logos: list[Image] = []


class NetworkDetails(msgspec.Struct, frozen=True):
    """Network details."""

    id: int
    name: str
    headquarters: str = ""
    homepage: str = ""
    logo_path: str | None = None
    origin_country: str = ""


class CreditDetails(msgspec.Struct, frozen=True):
    """Credit details."""

    id: str
    credit_type: str = ""
    department: str = ""
    job: str = ""
    media_type: str = ""
    media: typing.Any = None
    person: typing.Any = None


class KeywordDetails(msgspec.Struct, frozen=True):
    """Keyword details."""

    id: int
    name: str


class ReviewDetails(msgspec.Struct, frozen=True):
    """Review details."""

    id: str
    author: str
    content: str
    created_at: str = ""
    iso_639_1: str = ""
    media_id: int = 0
    media_title: str = ""
    media_type: str = ""
    updated_at: str = ""
    url: str = ""


# Re-export from responses_extra


AggregateCreditsResponse = AggCredResp
EpisodeGroupsResponse = EpGrpResp
ListDetails = LstDet
ListItemStatus = LstItmStat
ScreenedTheatricallyResponse = ScrThResp
