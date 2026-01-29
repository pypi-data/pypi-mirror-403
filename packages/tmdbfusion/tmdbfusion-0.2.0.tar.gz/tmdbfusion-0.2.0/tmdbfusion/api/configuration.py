# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Configuration API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.responses import ConfigurationDetails
from tmdbfusion.models.responses import Country
from tmdbfusion.models.responses import Job
from tmdbfusion.models.responses import Language
from tmdbfusion.models.responses import Timezone


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class ConfigurationAPI(BaseAPI):
    """
    Synchronous Configuration API.

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

    def details(self) -> ConfigurationDetails:
        """
        Get API configuration.

        Returns
        -------
        ConfigurationDetails
            The ConfigurationDetails response.
        """
        return self._client._get(
            "/configuration",
            ConfigurationDetails,
            include_language=False,
        )

    def countries(self) -> list[Country]:
        """
        Get list of countries.

        Returns
        -------
        list[Country]
            The list[Country] response.
        """
        return self._client._get(
            "/configuration/countries",
            list[Country],
            include_language=False,
        )

    def jobs(self) -> list[Job]:
        """
        Get list of jobs/departments.

        Returns
        -------
        list[Job]
            The list[Job] response.
        """
        return self._client._get(
            "/configuration/jobs",
            list[Job],
            include_language=False,
        )

    def languages(self) -> list[Language]:
        """
        Get list of languages.

        Returns
        -------
        list[Language]
            The list[Language] response.
        """
        return self._client._get(
            "/configuration/languages",
            list[Language],
            include_language=False,
        )

    def primary_translations(self) -> list[str]:
        """
        Get list of primary translations.

        Returns
        -------
        list[str]
            The list[str] response.
        """
        return self._client._get(
            "/configuration/primary_translations",
            list[str],
            include_language=False,
        )

    def timezones(self) -> list[Timezone]:
        """
        Get list of timezones.

        Returns
        -------
        list[Timezone]
            The list[Timezone] response.
        """
        return self._client._get(
            "/configuration/timezones",
            list[Timezone],
            include_language=False,
        )


class AsyncConfigurationAPI(AsyncBaseAPI):
    """
    Asynchronous Configuration API.

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

    async def details(self) -> ConfigurationDetails:
        """
        Get API configuration.

        Returns
        -------
        ConfigurationDetails
            The ConfigurationDetails response.
        """
        return await self._client._get(
            "/configuration",
            ConfigurationDetails,
            include_language=False,
        )

    async def countries(self) -> list[Country]:
        """
        Get list of countries.

        Returns
        -------
        list[Country]
            The list[Country] response.
        """
        return await self._client._get(
            "/configuration/countries",
            list[Country],
            include_language=False,
        )

    async def jobs(self) -> list[Job]:
        """
        Get list of jobs/departments.

        Returns
        -------
        list[Job]
            The list[Job] response.
        """
        return await self._client._get(
            "/configuration/jobs",
            list[Job],
            include_language=False,
        )

    async def languages(self) -> list[Language]:
        """
        Get list of languages.

        Returns
        -------
        list[Language]
            The list[Language] response.
        """
        return await self._client._get(
            "/configuration/languages",
            list[Language],
            include_language=False,
        )

    async def primary_translations(self) -> list[str]:
        """
        Get list of primary translations.

        Returns
        -------
        list[str]
            The list[str] response.
        """
        return await self._client._get(
            "/configuration/primary_translations",
            list[str],
            include_language=False,
        )

    async def timezones(self) -> list[Timezone]:
        """
        Get list of timezones.

        Returns
        -------
        list[Timezone]
            The list[Timezone] response.
        """
        return await self._client._get(
            "/configuration/timezones",
            list[Timezone],
            include_language=False,
        )
