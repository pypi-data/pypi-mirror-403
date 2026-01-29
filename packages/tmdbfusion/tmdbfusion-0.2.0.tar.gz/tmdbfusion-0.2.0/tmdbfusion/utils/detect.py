# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Media Type Detector.

Utilities for detecting media types from TMDB IDs and performing
universal lookups.
"""

from __future__ import annotations

import enum
import typing
from dataclasses import dataclass

import msgspec


if typing.TYPE_CHECKING:
    from tmdbfusion.core.async_client import AsyncTMDBClient
    from tmdbfusion.core.sync_client import TMDBClient
    from tmdbfusion.models.responses import FindResults


class MediaType(enum.Enum):
    """Media type enumeration.

    Attributes
    ----------
    MOVIE : str
        Movie media type.
    TV : str
        TV series media type.
    PERSON : str
        Person media type.
    UNKNOWN : str
        Unknown media type.

    """

    MOVIE = "movie"
    TV = "tv"
    PERSON = "person"
    UNKNOWN = "unknown"


class ExternalSource(enum.Enum):
    """External source for Find API.

    Attributes
    ----------
    IMDB : str
        IMDb ID source.
    TVDB : str
        TheTVDB ID source.
    FREEBASE_MID : str
        Freebase MID source.
    FREEBASE_ID : str
        Freebase ID source.
    FACEBOOK : str
        Facebook ID source.
    TWITTER : str
        Twitter ID source.
    INSTAGRAM : str
        Instagram ID source.
    WIKIDATA : str
        Wikidata ID source.

    """

    IMDB = "imdb_id"
    TVDB = "tvdb_id"
    FREEBASE_MID = "freebase_mid"
    FREEBASE_ID = "freebase_id"
    FACEBOOK = "facebook_id"
    TWITTER = "twitter_id"
    INSTAGRAM = "instagram_id"
    WIKIDATA = "wikidata_id"


class MediaInfo(msgspec.Struct, frozen=True):
    """Detected media information.

    Attributes
    ----------
    media_type : MediaType
        Type of media (movie, tv, person).
    tmdb_id : int | None
        TMDB ID if found.
    title : str
        Title or name of the media.
    original_data : object
        Original response data.

    """

    media_type: MediaType
    tmdb_id: int | None
    title: str
    original_data: object


@dataclass
class DetectionResult:
    """Result from media detection.

    Attributes
    ----------
    found : bool
        Whether any media was found.
    media : list[MediaInfo]
        List of detected media items.
    source_id : str
        Original ID used for lookup.

    """

    found: bool
    media: list[MediaInfo]
    source_id: str

    @property
    def first(self) -> MediaInfo | None:
        """Get first detected media.

        Returns
        -------
        MediaInfo | None
            First media item or None if not found.

        """
        return self.media[0] if self.media else None

    @property
    def movies(self) -> list[MediaInfo]:
        """Get all detected movies.

        Returns
        -------
        list[MediaInfo]
            List of movie results.

        """
        return [m for m in self.media if m.media_type == MediaType.MOVIE]

    @property
    def tv_shows(self) -> list[MediaInfo]:
        """Get all detected TV shows.

        Returns
        -------
        list[MediaInfo]
            List of TV results.

        """
        return [m for m in self.media if m.media_type == MediaType.TV]

    @property
    def people(self) -> list[MediaInfo]:
        """Get all detected people.

        Returns
        -------
        list[MediaInfo]
            List of person results.

        """
        return [m for m in self.media if m.media_type == MediaType.PERSON]


class MediaDetector:
    """Detect media type from external IDs.

    Examples
    --------
    >>> detector = MediaDetector(client)
    >>> result = detector.by_imdb("tt0111161")
    >>> if result.found:
    ...     print(result.first.media_type)
    MediaType.MOVIE

    Parameters
    ----------
    client : TMDBClient
        Synchronous TMDB client.

    """

    def __init__(self, client: TMDBClient) -> None:
        self._client = client

    def _parse_find_results(
        self,
        results: FindResults,
        source_id: str,
    ) -> DetectionResult:
        """Parse FindResults into DetectionResult.

        Parameters
        ----------
        results : FindResults
            Results from Find API.
        source_id : str
            Original ID used for lookup.

        Returns
        -------
        DetectionResult
            Parsed detection result.

        """

        # Movies
        media: list[MediaInfo] = [
            MediaInfo(
                media_type=MediaType.MOVIE,
                tmdb_id=movie.id,
                title=movie.title,
                original_data=movie,
            )
            for movie in results.movie_results
        ]

        # TV Shows
        media.extend(
            MediaInfo(
                media_type=MediaType.TV,
                tmdb_id=tv.id,
                title=tv.name,
                original_data=tv,
            )
            for tv in results.tv_results
        )

        # People
        media.extend(
            MediaInfo(
                media_type=MediaType.PERSON,
                tmdb_id=person.id,
                title=person.name,
                original_data=person,
            )
            for person in results.person_results
        )

        return DetectionResult(
            found=len(media) > 0,
            media=media,
            source_id=source_id,
        )

    def by_external_id(
        self,
        external_id: str,
        source: ExternalSource,
    ) -> DetectionResult:
        """Detect media by external ID.

        Parameters
        ----------
        external_id : str
            External ID to look up.
        source : ExternalSource
            Source of the external ID.

        Returns
        -------
        DetectionResult
            Detection result with media info.

        """
        results = self._client.find.by_id(
            external_id,
            external_source=source.value,
        )
        return self._parse_find_results(results, external_id)

    def by_imdb(self, imdb_id: str) -> DetectionResult:
        """Detect media by IMDb ID.

        Parameters
        ----------
        imdb_id : str
            IMDb ID (e.g., "tt0111161").

        Returns
        -------
        DetectionResult
            Detection result with media info.

        Examples
        --------
        >>> result = detector.by_imdb("tt0111161")
        >>> print(result.first.title)
        The Shawshank Redemption

        """
        return self.by_external_id(imdb_id, ExternalSource.IMDB)

    def by_tvdb(self, tvdb_id: str) -> DetectionResult:
        """Detect media by TVDB ID.

        Parameters
        ----------
        tvdb_id : str
            TheTVDB ID.

        Returns
        -------
        DetectionResult
            Detection result with media info.

        """
        return self.by_external_id(tvdb_id, ExternalSource.TVDB)


class AsyncMediaDetector:
    """Async detect media type from external IDs.

    Examples
    --------
    >>> detector = AsyncMediaDetector(client)
    >>> result = await detector.by_imdb("tt0111161")
    >>> if result.found:
    ...     print(result.first.media_type)
    MediaType.MOVIE

    Parameters
    ----------
    client : AsyncTMDBClient
        Asynchronous TMDB client.

    """

    def __init__(self, client: AsyncTMDBClient) -> None:
        self._client = client

    def _parse_find_results(
        self,
        results: FindResults,
        source_id: str,
    ) -> DetectionResult:
        """Parse FindResults into DetectionResult.

        Parameters
        ----------
        results : FindResults
            Results from Find API.
        source_id : str
            Original ID used for lookup.

        Returns
        -------
        DetectionResult
            Parsed detection result.

        """

        media: list[MediaInfo] = [
            MediaInfo(
                media_type=MediaType.MOVIE,
                tmdb_id=movie.id,
                title=movie.title,
                original_data=movie,
            )
            for movie in results.movie_results
        ]

        media.extend(
            MediaInfo(
                media_type=MediaType.TV,
                tmdb_id=tv.id,
                title=tv.name,
                original_data=tv,
            )
            for tv in results.tv_results
        )

        media.extend(
            MediaInfo(
                media_type=MediaType.PERSON,
                tmdb_id=person.id,
                title=person.name,
                original_data=person,
            )
            for person in results.person_results
        )

        return DetectionResult(
            found=len(media) > 0,
            media=media,
            source_id=source_id,
        )

    async def by_external_id(
        self,
        external_id: str,
        source: ExternalSource,
    ) -> DetectionResult:
        """Detect media by external ID.

        Parameters
        ----------
        external_id : str
            External ID to look up.
        source : ExternalSource
            Source of the external ID.

        Returns
        -------
        DetectionResult
            Detection result with media info.

        """
        results = await self._client.find.by_id(
            external_id,
            external_source=source.value,
        )
        return self._parse_find_results(results, external_id)

    async def by_imdb(self, imdb_id: str) -> DetectionResult:
        """Detect media by IMDb ID.

        Parameters
        ----------
        imdb_id : str
            IMDb ID (e.g., "tt0111161").

        Returns
        -------
        DetectionResult
            Detection result with media info.

        """
        return await self.by_external_id(imdb_id, ExternalSource.IMDB)

    async def by_tvdb(self, tvdb_id: str) -> DetectionResult:
        """Detect media by TVDB ID.

        Parameters
        ----------
        tvdb_id : str
            TheTVDB ID.

        Returns
        -------
        DetectionResult
            Detection result with media info.

        """
        return await self.by_external_id(tvdb_id, ExternalSource.TVDB)
