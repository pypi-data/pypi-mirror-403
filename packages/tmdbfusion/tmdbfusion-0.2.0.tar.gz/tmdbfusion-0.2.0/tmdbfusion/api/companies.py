# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Companies API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.responses import CompanyAlternativeNamesResponse
from tmdbfusion.models.responses import CompanyDetails
from tmdbfusion.models.responses import CompanyImagesResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class CompaniesAPI(BaseAPI):
    """
    Synchronous Companies API.

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

    def details(self, company_id: int) -> CompanyDetails:
        """
        Get company details.

        Parameters
        ----------
        company_id : int
            The company ID.

        Returns
        -------
        CompanyDetails
            The CompanyDetails response.
        """
        return self._client._get(
            f"/company/{company_id}",
            CompanyDetails,
        )

    def alternative_names(
        self,
        company_id: int,
    ) -> CompanyAlternativeNamesResponse:
        """
        Get company alternative names.

        Parameters
        ----------
        company_id : int
            The company ID.

        Returns
        -------
        CompanyAlternativeNamesResponse
            The CompanyAlternativeNamesResponse response.
        """
        return self._client._get(
            f"/company/{company_id}/alternative_names",
            CompanyAlternativeNamesResponse,
        )

    def images(self, company_id: int) -> CompanyImagesResponse:
        """
        Get company images.

        Parameters
        ----------
        company_id : int
            The company ID.

        Returns
        -------
        CompanyImagesResponse
            The CompanyImagesResponse response.
        """
        return self._client._get(
            f"/company/{company_id}/images",
            CompanyImagesResponse,
        )


class AsyncCompaniesAPI(AsyncBaseAPI):
    """
    Asynchronous Companies API.

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

    async def details(self, company_id: int) -> CompanyDetails:
        """
        Get company details.

        Parameters
        ----------
        company_id : int
            The company ID.

        Returns
        -------
        CompanyDetails
            The CompanyDetails response.
        """
        return await self._client._get(
            f"/company/{company_id}",
            CompanyDetails,
        )

    async def alternative_names(
        self,
        company_id: int,
    ) -> CompanyAlternativeNamesResponse:
        """
        Get company alternative names.

        Parameters
        ----------
        company_id : int
            The company ID.

        Returns
        -------
        CompanyAlternativeNamesResponse
            The CompanyAlternativeNamesResponse response.
        """
        return await self._client._get(
            f"/company/{company_id}/alternative_names",
            CompanyAlternativeNamesResponse,
        )

    async def images(self, company_id: int) -> CompanyImagesResponse:
        """
        Get company images.

        Parameters
        ----------
        company_id : int
            The company ID.

        Returns
        -------
        CompanyImagesResponse
            The CompanyImagesResponse response.
        """
        return await self._client._get(
            f"/company/{company_id}/images",
            CompanyImagesResponse,
        )
