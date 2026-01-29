# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""TV Seasons API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.person import Credits
from tmdbfusion.models.responses import AccountStates
from tmdbfusion.models.responses import ChangesResponse
from tmdbfusion.models.responses import ExternalIdsResponse
from tmdbfusion.models.responses import ImagesResponse
from tmdbfusion.models.responses import TranslationsResponse
from tmdbfusion.models.responses import VideosResponse
from tmdbfusion.models.responses import WatchProvidersResponse
from tmdbfusion.models.responses_extra import AggregateCreditsResponse
from tmdbfusion.models.tv import TVSeason


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class TVSeasonsAPI(BaseAPI):
    """
    Synchronous TV Seasons API.

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
        *,
        append_to_response: str | None = None,
    ) -> TVSeason:
        """
        Get TV season details.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        append_to_response : str | None, optional
            Comma-separated list of sub-requests to append.

        Returns
        -------
        TVSeason
            The TVSeason response.
        """
        params: dict[str, typing.Any] = {}
        if append_to_response:
            params["append_to_response"] = append_to_response
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}",
            TVSeason,
            params=params,
        )

    def account_states(
        self,
        series_id: int,
        season_number: int,
        *,
        session_id: str,
    ) -> AccountStates:
        """
        Get account states for season.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        session_id : str
            The session ID.

        Returns
        -------
        AccountStates
            The account states.
        """
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/account_states",
            AccountStates,
            params={"session_id": session_id},
        )

    def aggregate_credits(
        self,
        series_id: int,
        season_number: int,
    ) -> AggregateCreditsResponse:
        """
        Get aggregate credits for season.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.

        Returns
        -------
        AggregateCreditsResponse
            The aggregate credits.
        """
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/aggregate_credits",
            AggregateCreditsResponse,
        )

    def changes(self, season_id: int) -> ChangesResponse:
        """
        Get season changes.

        Parameters
        ----------
        season_id : int
            The season ID.

        Returns
        -------
        ChangesResponse
            The changes.
        """
        return self._client._get(
            f"/tv/season/{season_id}/changes",
            ChangesResponse,
        )

    def credits(self, series_id: int, season_number: int) -> Credits:
        """
        Get season credits.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.

        Returns
        -------
        Credits
            The credits information.
        """
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/credits",
            Credits,
        )

    def external_ids(
        self,
        series_id: int,
        season_number: int,
    ) -> ExternalIdsResponse:
        """
        Get season external IDs.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.

        Returns
        -------
        ExternalIdsResponse
            The external IDs.
        """
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/external_ids",
            ExternalIdsResponse,
        )

    def images(self, series_id: int, season_number: int) -> ImagesResponse:
        """
        Get season images.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.

        Returns
        -------
        ImagesResponse
            The images.
        """
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/images",
            ImagesResponse,
        )

    def translations(
        self,
        series_id: int,
        season_number: int,
    ) -> TranslationsResponse:
        """
        Get season translations.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.

        Returns
        -------
        TranslationsResponse
            The translations.
        """
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/translations",
            TranslationsResponse,
        )

    def videos(self, series_id: int, season_number: int) -> VideosResponse:
        """
        Get season videos.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.

        Returns
        -------
        VideosResponse
            The videos.
        """
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/videos",
            VideosResponse,
        )

    def watch_providers(
        self,
        series_id: int,
        season_number: int,
    ) -> WatchProvidersResponse:
        """
        Get season watch providers.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.

        Returns
        -------
        WatchProvidersResponse
            The watch providers.
        """
        return self._client._get(
            f"/tv/{series_id}/season/{season_number}/watch/providers",
            WatchProvidersResponse,
        )


class AsyncTVSeasonsAPI(AsyncBaseAPI):
    """
    Asynchronous TV Seasons API.

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
        *,
        append_to_response: str | None = None,
    ) -> TVSeason:
        """
        Get TV season details.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.
        append_to_response : str | None, optional
            Comma-separated list of sub-requests to append.

        Returns
        -------
        TVSeason
            The TVSeason response.
        """
        params: dict[str, typing.Any] = {}
        if append_to_response:
            params["append_to_response"] = append_to_response
        return await self._client._get(
            f"/tv/{series_id}/season/{season_number}",
            TVSeason,
            params=params,
        )

    async def aggregate_credits(
        self,
        series_id: int,
        season_number: int,
    ) -> AggregateCreditsResponse:
        """
        Get aggregate credits for season.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.

        Returns
        -------
        AggregateCreditsResponse
            The aggregate credits.
        """
        return await self._client._get(
            f"/tv/{series_id}/season/{season_number}/aggregate_credits",
            AggregateCreditsResponse,
        )

    async def credits(self, series_id: int, season_number: int) -> Credits:
        """
        Get season credits.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.

        Returns
        -------
        Credits
            The credits information.
        """
        return await self._client._get(
            f"/tv/{series_id}/season/{season_number}/credits",
            Credits,
        )

    async def external_ids(
        self,
        series_id: int,
        season_number: int,
    ) -> ExternalIdsResponse:
        """
        Get season external IDs.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.

        Returns
        -------
        ExternalIdsResponse
            The external IDs.
        """
        return await self._client._get(
            f"/tv/{series_id}/season/{season_number}/external_ids",
            ExternalIdsResponse,
        )

    async def images(
        self,
        series_id: int,
        season_number: int,
    ) -> ImagesResponse:
        """
        Get season images.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.

        Returns
        -------
        ImagesResponse
            The images.
        """
        return await self._client._get(
            f"/tv/{series_id}/season/{season_number}/images",
            ImagesResponse,
        )

    async def videos(
        self,
        series_id: int,
        season_number: int,
    ) -> VideosResponse:
        """
        Get season videos.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.

        Returns
        -------
        VideosResponse
            The videos.
        """
        return await self._client._get(
            f"/tv/{series_id}/season/{season_number}/videos",
            VideosResponse,
        )

    async def watch_providers(
        self,
        series_id: int,
        season_number: int,
    ) -> WatchProvidersResponse:
        """
        Get season watch providers.

        Parameters
        ----------
        series_id : int
            The TV series ID.
        season_number : int
            The season number.

        Returns
        -------
        WatchProvidersResponse
            The watch providers.
        """
        return await self._client._get(
            f"/tv/{series_id}/season/{season_number}/watch/providers",
            WatchProvidersResponse,
        )
