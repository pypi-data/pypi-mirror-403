# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""TV API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.person import Credits
from tmdbfusion.models.responses import AccountStates
from tmdbfusion.models.responses import AlternativeTitlesResponse
from tmdbfusion.models.responses import ChangesResponse
from tmdbfusion.models.responses import ContentRatingsResponse
from tmdbfusion.models.responses import ExternalIdsResponse
from tmdbfusion.models.responses import ImagesResponse
from tmdbfusion.models.responses import ListsResponse
from tmdbfusion.models.responses import ReviewsResponse
from tmdbfusion.models.responses import StatusResponse
from tmdbfusion.models.responses import TranslationsResponse
from tmdbfusion.models.responses import TVKeywordsResponse
from tmdbfusion.models.responses import VideosResponse
from tmdbfusion.models.responses import WatchProvidersResponse
from tmdbfusion.models.responses_extra import AggregateCreditsResponse
from tmdbfusion.models.responses_extra import EpisodeGroupsResponse
from tmdbfusion.models.responses_extra import ScreenedTheatricallyResponse
from tmdbfusion.models.search import TVPaginatedResponse
from tmdbfusion.models.tv import TVSeriesDetails


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class TVAPI(BaseAPI):
    """
    Synchronous TV API.

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
        series_id: int,
        *,
        append_to_response: str | None = None,
    ) -> TVSeriesDetails:
        """
        Get TV series details.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        append_to_response : str | None, optional
            Comma-separated list of sub-requests to append.

        Returns
        -------
        TVSeriesDetails
            The TV series details.
        """
        params: dict[str, typing.Any] = {}
        if append_to_response:
            params["append_to_response"] = append_to_response
        return self._client._get(
            f"/tv/{series_id}",
            TVSeriesDetails,
            params=params,
        )

    def popular(self, *, page: int = 1) -> TVPaginatedResponse:
        """
        Get popular TV shows.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return self._client._get(
            "/tv/popular",
            TVPaginatedResponse,
            params={"page": page},
        )

    def top_rated(self, *, page: int = 1) -> TVPaginatedResponse:
        """
        Get top rated TV shows.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return self._client._get(
            "/tv/top_rated",
            TVPaginatedResponse,
            params={"page": page},
        )

    def airing_today(self, *, page: int = 1) -> TVPaginatedResponse:
        """
        Get TV shows airing today.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return self._client._get(
            "/tv/airing_today",
            TVPaginatedResponse,
            params={"page": page},
        )

    def on_the_air(self, *, page: int = 1) -> TVPaginatedResponse:
        """
        Get TV shows on the air.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return self._client._get(
            "/tv/on_the_air",
            TVPaginatedResponse,
            params={"page": page},
        )

    def account_states(
        self,
        series_id: int,
        *,
        session_id: str,
    ) -> AccountStates:
        """
        Get account states for series.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        session_id : str
            The session ID.

        Returns
        -------
        AccountStates
            The account states.
        """
        return self._client._get(
            f"/tv/{series_id}/account_states",
            AccountStates,
            params={"session_id": session_id},
        )

    def aggregate_credits(self, series_id: int) -> AggregateCreditsResponse:
        """
        Get aggregate credits.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        AggregateCreditsResponse
            The aggregate credits.
        """
        return self._client._get(
            f"/tv/{series_id}/aggregate_credits",
            AggregateCreditsResponse,
        )

    def alternative_titles(self, series_id: int) -> AlternativeTitlesResponse:
        """
        Get alternative titles.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        AlternativeTitlesResponse
            The alternative titles.
        """
        return self._client._get(
            f"/tv/{series_id}/alternative_titles",
            AlternativeTitlesResponse,
        )

    def changes(
        self,
        series_id: int,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> ChangesResponse:
        """
        Get series changes.

        Parameters
        ----------
        series_id : int
            The TV series ID.
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
            f"/tv/{series_id}/changes",
            ChangesResponse,
            params=params,
        )

    def content_ratings(self, series_id: int) -> ContentRatingsResponse:
        """
        Get content ratings.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        ContentRatingsResponse
            The content ratings.
        """
        return self._client._get(
            f"/tv/{series_id}/content_ratings",
            ContentRatingsResponse,
        )

    def credits(self, series_id: int) -> Credits:
        """
        Get credits.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        Credits
            The credits information.
        """
        return self._client._get(f"/tv/{series_id}/credits", Credits)

    def episode_groups(self, series_id: int) -> EpisodeGroupsResponse:
        """
        Get episode groups.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        EpisodeGroupsResponse
            The episode groups.
        """
        return self._client._get(
            f"/tv/{series_id}/episode_groups",
            EpisodeGroupsResponse,
        )

    def external_ids(self, series_id: int) -> ExternalIdsResponse:
        """
        Get external IDs.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        ExternalIdsResponse
            The external IDs.
        """
        return self._client._get(
            f"/tv/{series_id}/external_ids",
            ExternalIdsResponse,
        )

    def images(self, series_id: int) -> ImagesResponse:
        """
        Get images.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        ImagesResponse
            The images.
        """
        return self._client._get(f"/tv/{series_id}/images", ImagesResponse)

    def keywords(self, series_id: int) -> TVKeywordsResponse:
        """
        Get keywords.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        TVKeywordsResponse
            The keywords.
        """
        return self._client._get(
            f"/tv/{series_id}/keywords",
            TVKeywordsResponse,
        )

    def latest(self) -> TVSeriesDetails:
        """
        Get latest TV show.

        Returns
        -------
        TVSeriesDetails
            The TV series details.
        """
        return self._client._get(
            "/tv/latest",
            TVSeriesDetails,
            include_language=False,
        )

    def lists(self, series_id: int, *, page: int = 1) -> ListsResponse:
        """
        Get lists containing series.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        ListsResponse
            Lists containing the item.
        """
        return self._client._get(
            f"/tv/{series_id}/lists",
            ListsResponse,
            params={"page": page},
        )

    def recommendations(
        self,
        series_id: int,
        *,
        page: int = 1,
    ) -> TVPaginatedResponse:
        """
        Get TV recommendations.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return self._client._get(
            f"/tv/{series_id}/recommendations",
            TVPaginatedResponse,
            params={"page": page},
        )

    def reviews(self, series_id: int, *, page: int = 1) -> ReviewsResponse:
        """
        Get reviews.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        ReviewsResponse
            The reviews.
        """
        return self._client._get(
            f"/tv/{series_id}/reviews",
            ReviewsResponse,
            params={"page": page},
        )

    def screened_theatrically(
        self,
        series_id: int,
    ) -> ScreenedTheatricallyResponse:
        """
        Get screened theatrically info.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        ScreenedTheatricallyResponse
            Episodes screened theatrically.
        """
        return self._client._get(
            f"/tv/{series_id}/screened_theatrically",
            ScreenedTheatricallyResponse,
        )

    def similar(self, series_id: int, *, page: int = 1) -> TVPaginatedResponse:
        """
        Get similar TV shows.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return self._client._get(
            f"/tv/{series_id}/similar",
            TVPaginatedResponse,
            params={"page": page},
        )

    def translations(self, series_id: int) -> TranslationsResponse:
        """
        Get translations.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        TranslationsResponse
            The translations.
        """
        return self._client._get(
            f"/tv/{series_id}/translations",
            TranslationsResponse,
        )

    def videos(self, series_id: int) -> VideosResponse:
        """
        Get videos.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        VideosResponse
            The videos.
        """
        return self._client._get(f"/tv/{series_id}/videos", VideosResponse)

    def watch_providers(self, series_id: int) -> WatchProvidersResponse:
        """
        Get watch providers.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        WatchProvidersResponse
            The watch providers.
        """
        return self._client._get(
            f"/tv/{series_id}/watch/providers",
            WatchProvidersResponse,
        )

    def add_rating(
        self,
        series_id: int,
        *,
        rating: float,
        session_id: str | None = None,
        guest_session_id: str | None = None,
    ) -> StatusResponse:
        """
        Rate a TV series.

        Parameters
        ----------
        series_id : int
            The TV series ID.
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
            f"/tv/{series_id}/rating",
            StatusResponse,
            params=params,
            body={"value": rating},
        )

    def delete_rating(
        self,
        series_id: int,
        *,
        session_id: str | None = None,
        guest_session_id: str | None = None,
    ) -> StatusResponse:
        """
        Delete TV series rating.

        Parameters
        ----------
        series_id : int
            The TV series ID.
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
            f"/tv/{series_id}/rating",
            StatusResponse,
            params=params,
        )


class AsyncTVAPI(AsyncBaseAPI):
    """
    Asynchronous TV API.

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
        series_id: int,
        *,
        append_to_response: str | None = None,
    ) -> TVSeriesDetails:
        """
        Get TV series details.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        append_to_response : str | None, optional
            Comma-separated list of sub-requests to append.

        Returns
        -------
        TVSeriesDetails
            The TV series details.
        """
        params: dict[str, typing.Any] = {}
        if append_to_response:
            params["append_to_response"] = append_to_response
        return await self._client._get(
            f"/tv/{series_id}",
            TVSeriesDetails,
            params=params,
        )

    async def popular(self, *, page: int = 1) -> TVPaginatedResponse:
        """
        Get popular TV shows.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return await self._client._get(
            "/tv/popular",
            TVPaginatedResponse,
            params={"page": page},
        )

    async def top_rated(self, *, page: int = 1) -> TVPaginatedResponse:
        """
        Get top rated TV shows.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return await self._client._get(
            "/tv/top_rated",
            TVPaginatedResponse,
            params={"page": page},
        )

    async def airing_today(self, *, page: int = 1) -> TVPaginatedResponse:
        """
        Get TV shows airing today.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return await self._client._get(
            "/tv/airing_today",
            TVPaginatedResponse,
            params={"page": page},
        )

    async def on_the_air(self, *, page: int = 1) -> TVPaginatedResponse:
        """
        Get TV shows on the air.

        Parameters
        ----------
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return await self._client._get(
            "/tv/on_the_air",
            TVPaginatedResponse,
            params={"page": page},
        )

    async def aggregate_credits(
        self,
        series_id: int,
    ) -> AggregateCreditsResponse:
        """
        Get aggregate credits.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        AggregateCreditsResponse
            The aggregate credits.
        """
        return await self._client._get(
            f"/tv/{series_id}/aggregate_credits",
            AggregateCreditsResponse,
        )

    async def credits(self, series_id: int) -> Credits:
        """
        Get credits.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        Credits
            The credits information.
        """
        return await self._client._get(f"/tv/{series_id}/credits", Credits)

    async def external_ids(self, series_id: int) -> ExternalIdsResponse:
        """
        Get external IDs.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        ExternalIdsResponse
            The external IDs.
        """
        return await self._client._get(
            f"/tv/{series_id}/external_ids",
            ExternalIdsResponse,
        )

    async def images(self, series_id: int) -> ImagesResponse:
        """
        Get images.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        ImagesResponse
            The images.
        """
        return await self._client._get(
            f"/tv/{series_id}/images",
            ImagesResponse,
        )

    async def keywords(self, series_id: int) -> TVKeywordsResponse:
        """
        Get keywords.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        TVKeywordsResponse
            The keywords.
        """
        return await self._client._get(
            f"/tv/{series_id}/keywords",
            TVKeywordsResponse,
        )

    async def recommendations(
        self,
        series_id: int,
        *,
        page: int = 1,
    ) -> TVPaginatedResponse:
        """
        Get TV recommendations.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return await self._client._get(
            f"/tv/{series_id}/recommendations",
            TVPaginatedResponse,
            params={"page": page},
        )

    async def similar(
        self,
        series_id: int,
        *,
        page: int = 1,
    ) -> TVPaginatedResponse:
        """
        Get similar TV shows.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        TVPaginatedResponse
            Paginated list of TV shows.
        """
        return await self._client._get(
            f"/tv/{series_id}/similar",
            TVPaginatedResponse,
            params={"page": page},
        )

    async def videos(self, series_id: int) -> VideosResponse:
        """
        Get videos.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        VideosResponse
            The videos.
        """
        return await self._client._get(
            f"/tv/{series_id}/videos",
            VideosResponse,
        )

    async def watch_providers(self, series_id: int) -> WatchProvidersResponse:
        """
        Get watch providers.

        Parameters
        ----------
        series_id : int
            The TV series ID.

        Returns
        -------
        WatchProvidersResponse
            The watch providers.
        """
        return await self._client._get(
            f"/tv/{series_id}/watch/providers",
            WatchProvidersResponse,
        )

    async def add_rating(
        self,
        series_id: int,
        *,
        rating: float,
        session_id: str,
    ) -> StatusResponse:
        """
        Rate a TV series.

        Parameters
        ----------
        series_id : int
            The TV series ID.
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
            f"/tv/{series_id}/rating",
            StatusResponse,
            params={"session_id": session_id},
            body={"value": rating},
        )

    async def delete_rating(
        self,
        series_id: int,
        *,
        session_id: str,
    ) -> StatusResponse:
        """
        Delete TV series rating.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        session_id : str
            The session ID.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return await self._client._delete(
            f"/tv/{series_id}/rating",
            StatusResponse,
            params={"session_id": session_id},
        )
