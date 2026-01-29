# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Certifications API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.responses import CertificationsResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class CertificationsAPI(BaseAPI):
    """
    Synchronous Certifications API.

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

    def movie_list(self) -> CertificationsResponse:
        """
        Get movie certifications.

        Returns
        -------
        CertificationsResponse
            The CertificationsResponse response.
        """
        return self._client._get(
            "/certification/movie/list",
            CertificationsResponse,
            include_language=False,
        )

    def tv_list(self) -> CertificationsResponse:
        """
        Get TV certifications.

        Returns
        -------
        CertificationsResponse
            The CertificationsResponse response.
        """
        return self._client._get(
            "/certification/tv/list",
            CertificationsResponse,
            include_language=False,
        )


class AsyncCertificationsAPI(AsyncBaseAPI):
    """
    Asynchronous Certifications API.

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

    async def movie_list(self) -> CertificationsResponse:
        """
        Get movie certifications.

        Returns
        -------
        CertificationsResponse
            The CertificationsResponse response.
        """
        return await self._client._get(
            "/certification/movie/list",
            CertificationsResponse,
            include_language=False,
        )

    async def tv_list(self) -> CertificationsResponse:
        """
        Get TV certifications.

        Returns
        -------
        CertificationsResponse
            The CertificationsResponse response.
        """
        return await self._client._get(
            "/certification/tv/list",
            CertificationsResponse,
            include_language=False,
        )
