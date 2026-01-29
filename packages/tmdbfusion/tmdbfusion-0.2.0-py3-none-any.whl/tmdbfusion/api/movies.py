# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Movies API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.movie import MovieDetails
from tmdbfusion.models.person import Credits
from tmdbfusion.models.responses import AccountStates
from tmdbfusion.models.responses import AlternativeTitlesResponse
from tmdbfusion.models.responses import ChangesResponse
from tmdbfusion.models.responses import ExternalIdsResponse
from tmdbfusion.models.responses import ImagesResponse
from tmdbfusion.models.responses import KeywordsResponse
from tmdbfusion.models.responses import ListsResponse
from tmdbfusion.models.responses import ReleaseDatesResponse
from tmdbfusion.models.responses import ReviewsResponse
from tmdbfusion.models.responses import StatusResponse
from tmdbfusion.models.responses import TranslationsResponse
from tmdbfusion.models.responses import VideosResponse
from tmdbfusion.models.responses import WatchProvidersResponse
from tmdbfusion.models.search import MoviePaginatedResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class MoviesAPI(BaseAPI):
    """
    Synchronous Movies API.

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

    def details(
        self,
        movie_id: int,
        *,
        append_to_response: str | None = None,
    ) -> MovieDetails:
        """
        Get movie details.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        append_to_response : str | None, optional
            Comma-separated list of sub-requests to append.

        Returns
        -------
        MovieDetails
            The movie details.
        """
        params: dict[str, typing.Any] = {}
        if append_to_response:
            params["append_to_response"] = append_to_response
        return self._client._get(
            f"/movie/{movie_id}",
            MovieDetails,
            params=params,
        )

    def popular(self, *, page: int = 1) -> MoviePaginatedResponse:
        """
        Get popular movies.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return self._client._get(
            "/movie/popular",
            MoviePaginatedResponse,
            params={"page": page},
        )

    def top_rated(self, *, page: int = 1) -> MoviePaginatedResponse:
        """
        Get top rated movies.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return self._client._get(
            "/movie/top_rated",
            MoviePaginatedResponse,
            params={"page": page},
        )

    def now_playing(self, *, page: int = 1) -> MoviePaginatedResponse:
        """
        Get now playing movies.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return self._client._get(
            "/movie/now_playing",
            MoviePaginatedResponse,
            params={"page": page},
        )

    def upcoming(self, *, page: int = 1) -> MoviePaginatedResponse:
        """
        Get upcoming movies.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return self._client._get(
            "/movie/upcoming",
            MoviePaginatedResponse,
            params={"page": page},
        )

    def credits(self, movie_id: int) -> Credits:
        """
        Get movie credits.

        Parameters
        ----------
        movie_id : int
            The movie ID.

        Returns
        -------
        Credits
            The credits information.
        """
        return self._client._get(f"/movie/{movie_id}/credits", Credits)

    def recommendations(
        self,
        movie_id: int,
        *,
        page: int = 1,
    ) -> MoviePaginatedResponse:
        """
        Get movie recommendations.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return self._client._get(
            f"/movie/{movie_id}/recommendations",
            MoviePaginatedResponse,
            params={"page": page},
        )

    def similar(
        self,
        movie_id: int,
        *,
        page: int = 1,
    ) -> MoviePaginatedResponse:
        """
        Get similar movies.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return self._client._get(
            f"/movie/{movie_id}/similar",
            MoviePaginatedResponse,
            params={"page": page},
        )

    def account_states(
        self,
        movie_id: int,
        *,
        session_id: str,
    ) -> AccountStates:
        """
        Get account states for movie.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        session_id : str
            The session ID.

        Returns
        -------
        AccountStates
            The account states.
        """
        return self._client._get(
            f"/movie/{movie_id}/account_states",
            AccountStates,
            params={"session_id": session_id},
        )

    def alternative_titles(
        self,
        movie_id: int,
        *,
        country: str | None = None,
    ) -> AlternativeTitlesResponse:
        """
        Get movie alternative titles.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        country : str | None, optional
            Filter by country code.

        Returns
        -------
        AlternativeTitlesResponse
            The alternative titles.
        """
        params: dict[str, typing.Any] = {}
        if country:
            params["country"] = country
        return self._client._get(
            f"/movie/{movie_id}/alternative_titles",
            AlternativeTitlesResponse,
            params=params,
        )

    def changes(
        self,
        movie_id: int,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> ChangesResponse:
        """
        Get movie changes.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        start_date : str | None, optional
            Filter changes from this date.
        end_date : str | None, optional
            Filter changes until this date.

        Returns
        -------
        ChangesResponse
            The changes.
        """
        params: dict[str, typing.Any] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._client._get(
            f"/movie/{movie_id}/changes",
            ChangesResponse,
            params=params,
        )

    def external_ids(self, movie_id: int) -> ExternalIdsResponse:
        """
        Get movie external IDs.

        Parameters
        ----------
        movie_id : int
            The movie ID.

        Returns
        -------
        ExternalIdsResponse
            The external IDs.
        """
        return self._client._get(
            f"/movie/{movie_id}/external_ids",
            ExternalIdsResponse,
        )

    def images(
        self,
        movie_id: int,
        *,
        include_image_language: str | None = None,
    ) -> ImagesResponse:
        """
        Get movie images.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        include_image_language : str | None, optional
            Languages to include for images.

        Returns
        -------
        ImagesResponse
            The images.
        """
        params: dict[str, typing.Any] = {}
        if include_image_language:
            params["include_image_language"] = include_image_language
        return self._client._get(
            f"/movie/{movie_id}/images",
            ImagesResponse,
            params=params,
        )

    def keywords(self, movie_id: int) -> KeywordsResponse:
        """
        Get movie keywords.

        Parameters
        ----------
        movie_id : int
            The movie ID.

        Returns
        -------
        KeywordsResponse
            The keywords.
        """
        return self._client._get(
            f"/movie/{movie_id}/keywords",
            KeywordsResponse,
        )

    def latest(self) -> MovieDetails:
        """
        Get latest movie.

        Returns
        -------
        MovieDetails
            The movie details.
        """
        return self._client._get(
            "/movie/latest",
            MovieDetails,
            include_language=False,
        )

    def lists(self, movie_id: int, *, page: int = 1) -> ListsResponse:
        """
        Get lists containing movie.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        ListsResponse
            Lists containing the item.
        """
        return self._client._get(
            f"/movie/{movie_id}/lists",
            ListsResponse,
            params={"page": page},
        )

    def release_dates(self, movie_id: int) -> ReleaseDatesResponse:
        """
        Get movie release dates.

        Parameters
        ----------
        movie_id : int
            The movie ID.

        Returns
        -------
        ReleaseDatesResponse
            The release dates.
        """
        return self._client._get(
            f"/movie/{movie_id}/release_dates",
            ReleaseDatesResponse,
        )

    def reviews(self, movie_id: int, *, page: int = 1) -> ReviewsResponse:
        """
        Get movie reviews.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        ReviewsResponse
            The reviews.
        """
        return self._client._get(
            f"/movie/{movie_id}/reviews",
            ReviewsResponse,
            params={"page": page},
        )

    def translations(self, movie_id: int) -> TranslationsResponse:
        """
        Get movie translations.

        Parameters
        ----------
        movie_id : int
            The movie ID.

        Returns
        -------
        TranslationsResponse
            The translations.
        """
        return self._client._get(
            f"/movie/{movie_id}/translations",
            TranslationsResponse,
        )

    def videos(
        self,
        movie_id: int,
        *,
        include_video_language: str | None = None,
    ) -> VideosResponse:
        """
        Get movie videos.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        include_video_language : str | None, optional
            Languages to include for videos.

        Returns
        -------
        VideosResponse
            The videos.
        """
        params: dict[str, typing.Any] = {}
        if include_video_language:
            params["include_video_language"] = include_video_language
        return self._client._get(
            f"/movie/{movie_id}/videos",
            VideosResponse,
            params=params,
        )

    def watch_providers(self, movie_id: int) -> WatchProvidersResponse:
        """
        Get movie watch providers.

        Parameters
        ----------
        movie_id : int
            The movie ID.

        Returns
        -------
        WatchProvidersResponse
            The watch providers.
        """
        return self._client._get(
            f"/movie/{movie_id}/watch/providers",
            WatchProvidersResponse,
        )

    def add_rating(
        self,
        movie_id: int,
        *,
        rating: float,
        session_id: str | None = None,
        guest_session_id: str | None = None,
    ) -> StatusResponse:
        """
        Rate a movie.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        rating : float
            The rating value (0.5-10.0).
        session_id : str | None, optional
            The session ID.
        guest_session_id : str | None, optional
            The guest session ID.

        Returns
        -------
        StatusResponse
            The status response.
        """
        params: dict[str, typing.Any] = {}
        if session_id:
            params["session_id"] = session_id
        if guest_session_id:
            params["guest_session_id"] = guest_session_id
        return self._client._post(
            f"/movie/{movie_id}/rating",
            StatusResponse,
            params=params,
            body={"value": rating},
        )

    def delete_rating(
        self,
        movie_id: int,
        *,
        session_id: str | None = None,
        guest_session_id: str | None = None,
    ) -> StatusResponse:
        """
        Delete movie rating.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        session_id : str | None, optional
            The session ID.
        guest_session_id : str | None, optional
            The guest session ID.

        Returns
        -------
        StatusResponse
            The status response.
        """
        params: dict[str, typing.Any] = {}
        if session_id:
            params["session_id"] = session_id
        if guest_session_id:
            params["guest_session_id"] = guest_session_id
        return self._client._delete(
            f"/movie/{movie_id}/rating",
            StatusResponse,
            params=params,
        )


class AsyncMoviesAPI(AsyncBaseAPI):
    """
    Asynchronous Movies API.

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

    async def details(
        self,
        movie_id: int,
        *,
        append_to_response: str | None = None,
    ) -> MovieDetails:
        """
        Get movie details.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        append_to_response : str | None, optional
            Comma-separated list of sub-requests to append.

        Returns
        -------
        MovieDetails
            The movie details.
        """
        params: dict[str, typing.Any] = {}
        if append_to_response:
            params["append_to_response"] = append_to_response
        return await self._client._get(
            f"/movie/{movie_id}",
            MovieDetails,
            params=params,
        )

    async def popular(self, *, page: int = 1) -> MoviePaginatedResponse:
        """
        Get popular movies.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return await self._client._get(
            "/movie/popular",
            MoviePaginatedResponse,
            params={"page": page},
        )

    async def top_rated(self, *, page: int = 1) -> MoviePaginatedResponse:
        """
        Get top rated movies.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return await self._client._get(
            "/movie/top_rated",
            MoviePaginatedResponse,
            params={"page": page},
        )

    async def now_playing(self, *, page: int = 1) -> MoviePaginatedResponse:
        """
        Get now playing movies.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return await self._client._get(
            "/movie/now_playing",
            MoviePaginatedResponse,
            params={"page": page},
        )

    async def upcoming(self, *, page: int = 1) -> MoviePaginatedResponse:
        """
        Get upcoming movies.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return await self._client._get(
            "/movie/upcoming",
            MoviePaginatedResponse,
            params={"page": page},
        )

    async def credits(self, movie_id: int) -> Credits:
        """
        Get movie credits.

        Parameters
        ----------
        movie_id : int
            The movie ID.

        Returns
        -------
        Credits
            The credits information.
        """
        return await self._client._get(f"/movie/{movie_id}/credits", Credits)

    async def recommendations(
        self,
        movie_id: int,
        *,
        page: int = 1,
    ) -> MoviePaginatedResponse:
        """
        Get movie recommendations.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return await self._client._get(
            f"/movie/{movie_id}/recommendations",
            MoviePaginatedResponse,
            params={"page": page},
        )

    async def similar(
        self,
        movie_id: int,
        *,
        page: int = 1,
    ) -> MoviePaginatedResponse:
        """
        Get similar movies.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        MoviePaginatedResponse
            Paginated list of movies.
        """
        return await self._client._get(
            f"/movie/{movie_id}/similar",
            MoviePaginatedResponse,
            params={"page": page},
        )

    async def external_ids(self, movie_id: int) -> ExternalIdsResponse:
        """
        Get movie external IDs.

        Parameters
        ----------
        movie_id : int
            The movie ID.

        Returns
        -------
        ExternalIdsResponse
            The external IDs.
        """
        return await self._client._get(
            f"/movie/{movie_id}/external_ids",
            ExternalIdsResponse,
        )

    async def images(self, movie_id: int) -> ImagesResponse:
        """
        Get movie images.

        Parameters
        ----------
        movie_id : int
            The movie ID.

        Returns
        -------
        ImagesResponse
            The images.
        """
        return await self._client._get(
            f"/movie/{movie_id}/images",
            ImagesResponse,
        )

    async def keywords(self, movie_id: int) -> KeywordsResponse:
        """
        Get movie keywords.

        Parameters
        ----------
        movie_id : int
            The movie ID.

        Returns
        -------
        KeywordsResponse
            The keywords.
        """
        return await self._client._get(
            f"/movie/{movie_id}/keywords",
            KeywordsResponse,
        )

    async def videos(self, movie_id: int) -> VideosResponse:
        """
        Get movie videos.

        Parameters
        ----------
        movie_id : int
            The movie ID.

        Returns
        -------
        VideosResponse
            The videos.
        """
        return await self._client._get(
            f"/movie/{movie_id}/videos",
            VideosResponse,
        )

    async def watch_providers(self, movie_id: int) -> WatchProvidersResponse:
        """
        Get movie watch providers.

        Parameters
        ----------
        movie_id : int
            The movie ID.

        Returns
        -------
        WatchProvidersResponse
            The watch providers.
        """
        return await self._client._get(
            f"/movie/{movie_id}/watch/providers",
            WatchProvidersResponse,
        )

    async def reviews(
        self,
        movie_id: int,
        *,
        page: int = 1,
    ) -> ReviewsResponse:
        """
        Get movie reviews.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        ReviewsResponse
            The reviews.
        """
        return await self._client._get(
            f"/movie/{movie_id}/reviews",
            ReviewsResponse,
            params={"page": page},
        )

    async def translations(self, movie_id: int) -> TranslationsResponse:
        """
        Get movie translations.

        Parameters
        ----------
        movie_id : int
            The movie ID.

        Returns
        -------
        TranslationsResponse
            The translations.
        """
        return await self._client._get(
            f"/movie/{movie_id}/translations",
            TranslationsResponse,
        )

    async def add_rating(
        self,
        movie_id: int,
        *,
        rating: float,
        session_id: str,
    ) -> StatusResponse:
        """
        Rate a movie.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        rating : float
            The rating value (0.5-10.0).
        session_id : str
            The session ID.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return await self._client._post(
            f"/movie/{movie_id}/rating",
            StatusResponse,
            params={"session_id": session_id},
            body={"value": rating},
        )

    async def delete_rating(
        self,
        movie_id: int,
        *,
        session_id: str,
    ) -> StatusResponse:
        """
        Delete movie rating.

        Parameters
        ----------
        movie_id : int
            The movie ID.
        session_id : str
            The session ID.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return await self._client._delete(
            f"/movie/{movie_id}/rating",
            StatusResponse,
            params={"session_id": session_id},
        )
