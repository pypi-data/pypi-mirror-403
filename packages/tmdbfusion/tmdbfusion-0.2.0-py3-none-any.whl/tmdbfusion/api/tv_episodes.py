# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""TV Episodes API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.person import Credits
from tmdbfusion.models.responses import AccountStates
from tmdbfusion.models.responses import ChangesResponse
from tmdbfusion.models.responses import ExternalIdsResponse
from tmdbfusion.models.responses import ImagesResponse
from tmdbfusion.models.responses import StatusResponse
from tmdbfusion.models.responses import TranslationsResponse
from tmdbfusion.models.responses import VideosResponse
from tmdbfusion.models.tv import TVEpisode


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class TVEpisodesAPI(BaseAPI):
    """
    Synchronous TV Episodes API.

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
        series_id: int,
        season_number: int,
        episode_number: int,
        *,
        append_to_response: str | None = None,
    ) -> TVEpisode:
        """
        Get TV episode details.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.
        append_to_response : str | None, optional
            Comma-separated list of sub-requests to append.

        Returns
        -------
        TVEpisode
            The TVEpisode response.
        """
        params: dict[str, typing.Any] = {}
        if append_to_response:
            params["append_to_response"] = append_to_response
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}",
            TVEpisode,
            params=params,
        )

    def account_states(
        self,
        series_id: int,
        season_number: int,
        episode_number: int,
        *,
        session_id: str,
    ) -> AccountStates:
        """
        Get account states for episode.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.
        session_id : str
            The session ID.

        Returns
        -------
        AccountStates
            The account states.
        """
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}/account_states",
            AccountStates,
            params={"session_id": session_id},
        )

    def changes(self, episode_id: int) -> ChangesResponse:
        """
        Get episode changes.

        Parameters
        ----------
        episode_id : int
            The episode id.

        Returns
        -------
        ChangesResponse
            The changes.
        """
        return self._client._get(
            f"/tv/episode/{episode_id}/changes",
            ChangesResponse,
        )

    def credits(
        self,
        series_id: int,
        season_number: int,
        episode_number: int,
    ) -> Credits:
        """
        Get episode credits.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.

        Returns
        -------
        Credits
            The credits information.
        """
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}/credits",
            Credits,
        )

    def external_ids(
        self,
        series_id: int,
        season_number: int,
        episode_number: int,
    ) -> ExternalIdsResponse:
        """
        Get episode external IDs.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.

        Returns
        -------
        ExternalIdsResponse
            The external IDs.
        """
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}/external_ids",
            ExternalIdsResponse,
        )

    def images(
        self,
        series_id: int,
        season_number: int,
        episode_number: int,
    ) -> ImagesResponse:
        """
        Get episode images.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.

        Returns
        -------
        ImagesResponse
            The images.
        """
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}/images",
            ImagesResponse,
        )

    def translations(
        self,
        series_id: int,
        season_number: int,
        episode_number: int,
    ) -> TranslationsResponse:
        """
        Get episode translations.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.

        Returns
        -------
        TranslationsResponse
            The translations.
        """
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}/translations",
            TranslationsResponse,
        )

    def videos(
        self,
        series_id: int,
        season_number: int,
        episode_number: int,
    ) -> VideosResponse:
        """
        Get episode videos.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.

        Returns
        -------
        VideosResponse
            The videos.
        """
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}/videos",
            VideosResponse,
        )

    def add_rating(
        self,
        series_id: int,
        season_number: int,
        episode_number: int,
        *,
        rating: float,
        session_id: str | None = None,
        guest_session_id: str | None = None,
    ) -> StatusResponse:
        """
        Rate an episode.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.
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
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}/rating",
            StatusResponse,
            params=params,
            body={"value": rating},
        )

    def delete_rating(
        self,
        series_id: int,
        season_number: int,
        episode_number: int,
        *,
        session_id: str | None = None,
        guest_session_id: str | None = None,
    ) -> StatusResponse:
        """
        Delete episode rating.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.
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
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}/rating",
            StatusResponse,
            params=params,
        )


class AsyncTVEpisodesAPI(AsyncBaseAPI):
    """
    Asynchronous TV Episodes API.

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
        series_id: int,
        season_number: int,
        episode_number: int,
        *,
        append_to_response: str | None = None,
    ) -> TVEpisode:
        """
        Get TV episode details.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.
        append_to_response : str | None, optional
            Comma-separated list of sub-requests to append.

        Returns
        -------
        TVEpisode
            The TVEpisode response.
        """
        params: dict[str, typing.Any] = {}
        if append_to_response:
            params["append_to_response"] = append_to_response
        return await self._client._get(
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}",
            TVEpisode,
            params=params,
        )

    async def credits(
        self,
        series_id: int,
        season_number: int,
        episode_number: int,
    ) -> Credits:
        """
        Get episode credits.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.

        Returns
        -------
        Credits
            The credits information.
        """
        return await self._client._get(
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}/credits",
            Credits,
        )

    async def external_ids(
        self,
        series_id: int,
        season_number: int,
        episode_number: int,
    ) -> ExternalIdsResponse:
        """
        Get episode external IDs.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.

        Returns
        -------
        ExternalIdsResponse
            The external IDs.
        """
        return await self._client._get(
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}/external_ids",
            ExternalIdsResponse,
        )

    async def images(
        self,
        series_id: int,
        season_number: int,
        episode_number: int,
    ) -> ImagesResponse:
        """
        Get episode images.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.

        Returns
        -------
        ImagesResponse
            The images.
        """
        return await self._client._get(
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}/images",
            ImagesResponse,
        )

    async def videos(
        self,
        series_id: int,
        season_number: int,
        episode_number: int,
    ) -> VideosResponse:
        """
        Get episode videos.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.

        Returns
        -------
        VideosResponse
            The videos.
        """
        return await self._client._get(
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}/videos",
            VideosResponse,
        )

    async def add_rating(
        self,
        series_id: int,
        season_number: int,
        episode_number: int,
        *,
        rating: float,
        session_id: str,
    ) -> StatusResponse:
        """
        Rate an episode.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.
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
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}/rating",
            StatusResponse,
            params={"session_id": session_id},
            body={"value": rating},
        )

    async def delete_rating(
        self,
        series_id: int,
        season_number: int,
        episode_number: int,
        *,
        session_id: str,
    ) -> StatusResponse:
        """
        Delete episode rating.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        episode_number : int
            The episode number.
        session_id : str
            The session ID.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return await self._client._delete(
            f"/tv/{series_id}/season/{season_number}/episode/{episode_number}/rating",
            StatusResponse,
            params={"session_id": session_id},
        )
