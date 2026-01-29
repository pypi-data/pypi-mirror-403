# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Networks API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.responses import CompanyAlternativeNamesResponse
from tmdbfusion.models.responses import CompanyImagesResponse
from tmdbfusion.models.responses import NetworkDetails


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class NetworksAPI(BaseAPI):
    """
    Synchronous Networks API.

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

    def details(self, network_id: int) -> NetworkDetails:
        """
        Get network details.

        Parameters
        ----------
        network_id : int
            The network ID.

        Returns
        -------
        NetworkDetails
            The NetworkDetails response.
        """
        return self._client._get(
            f"/network/{network_id}",
            NetworkDetails,
        )

    def alternative_names(
        self,
        network_id: int,
    ) -> CompanyAlternativeNamesResponse:
        """
        Get network alternative names.

        Parameters
        ----------
        network_id : int
            The network ID.

        Returns
        -------
        CompanyAlternativeNamesResponse
            The CompanyAlternativeNamesResponse response.
        """
        return self._client._get(
            f"/network/{network_id}/alternative_names",
            CompanyAlternativeNamesResponse,
        )

    def images(self, network_id: int) -> CompanyImagesResponse:
        """
        Get network images.

        Parameters
        ----------
        network_id : int
            The network ID.

        Returns
        -------
        CompanyImagesResponse
            The CompanyImagesResponse response.
        """
        return self._client._get(
            f"/network/{network_id}/images",
            CompanyImagesResponse,
        )


class AsyncNetworksAPI(AsyncBaseAPI):
    """
    Asynchronous Networks API.

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

    async def details(self, network_id: int) -> NetworkDetails:
        """
        Get network details.

        Parameters
        ----------
        network_id : int
            The network ID.

        Returns
        -------
        NetworkDetails
            The NetworkDetails response.
        """
        return await self._client._get(
            f"/network/{network_id}",
            NetworkDetails,
        )

    async def alternative_names(
        self,
        network_id: int,
    ) -> CompanyAlternativeNamesResponse:
        """
        Get network alternative names.

        Parameters
        ----------
        network_id : int
            The network ID.

        Returns
        -------
        CompanyAlternativeNamesResponse
            The CompanyAlternativeNamesResponse response.
        """
        return await self._client._get(
            f"/network/{network_id}/alternative_names",
            CompanyAlternativeNamesResponse,
        )

    async def images(self, network_id: int) -> CompanyImagesResponse:
        """
        Get network images.

        Parameters
        ----------
        network_id : int
            The network ID.

        Returns
        -------
        CompanyImagesResponse
            The CompanyImagesResponse response.
        """
        return await self._client._get(
            f"/network/{network_id}/images",
            CompanyImagesResponse,
        )
