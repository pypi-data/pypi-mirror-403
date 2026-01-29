# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Watch Providers API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.responses import AvailableRegionsResponse
from tmdbfusion.models.responses import WatchProviderListResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class WatchProvidersAPI(BaseAPI):
    """
    Synchronous Watch Providers API.

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

    def available_regions(self) -> AvailableRegionsResponse:
        """
        Get available watch provider regions.

        Returns
        -------
        AvailableRegionsResponse
            The AvailableRegionsResponse response.
        """
        return self._client._get(
            "/watch/providers/regions",
            AvailableRegionsResponse,
        )

    def movie_providers(
        self,
        *,
        watch_region: str | None = None,
    ) -> WatchProviderListResponse:
        """
        Get movie watch providers.

        Parameters
        ----------
        watch_region : str | None, optional
            Filter by watch region.

        Returns
        -------
        WatchProviderListResponse
            The WatchProviderListResponse response.
        """
        params: dict[str, typing.Any] = {}
        if watch_region:
            params["watch_region"] = watch_region
        return self._client._get(
            "/watch/providers/movie",
            WatchProviderListResponse,
            params=params,
        )

    def tv_providers(
        self,
        *,
        watch_region: str | None = None,
    ) -> WatchProviderListResponse:
        """
        Get TV watch providers.

        Parameters
        ----------
        watch_region : str | None, optional
            Filter by watch region.

        Returns
        -------
        WatchProviderListResponse
            The WatchProviderListResponse response.
        """
        params: dict[str, typing.Any] = {}
        if watch_region:
            params["watch_region"] = watch_region
        return self._client._get(
            "/watch/providers/tv",
            WatchProviderListResponse,
            params=params,
        )


class AsyncWatchProvidersAPI(AsyncBaseAPI):
    """
    Asynchronous Watch Providers API.

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

    async def available_regions(self) -> AvailableRegionsResponse:
        """
        Get available watch provider regions.

        Returns
        -------
        AvailableRegionsResponse
            The AvailableRegionsResponse response.
        """
        return await self._client._get(
            "/watch/providers/regions",
            AvailableRegionsResponse,
        )

    async def movie_providers(
        self,
        *,
        watch_region: str | None = None,
    ) -> WatchProviderListResponse:
        """
        Get movie watch providers.

        Parameters
        ----------
        watch_region : str | None, optional
            Filter by watch region.

        Returns
        -------
        WatchProviderListResponse
            The WatchProviderListResponse response.
        """
        params: dict[str, typing.Any] = {}
        if watch_region:
            params["watch_region"] = watch_region
        return await self._client._get(
            "/watch/providers/movie",
            WatchProviderListResponse,
            params=params,
        )

    async def tv_providers(
        self,
        *,
        watch_region: str | None = None,
    ) -> WatchProviderListResponse:
        """
        Get TV watch providers.

        Parameters
        ----------
        watch_region : str | None, optional
            Filter by watch region.

        Returns
        -------
        WatchProviderListResponse
            The WatchProviderListResponse response.
        """
        params: dict[str, typing.Any] = {}
        if watch_region:
            params["watch_region"] = watch_region
        return await self._client._get(
            "/watch/providers/tv",
            WatchProviderListResponse,
            params=params,
        )
