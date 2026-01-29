# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Changes API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.responses import ChangesListResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class ChangesAPI(BaseAPI):
    """
    Synchronous Changes API.

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

    def movie_list(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
    ) -> ChangesListResponse:
        """
        Get list of changed movies.

        Parameters
        ----------
        start_date : str | None, optional
            Filter changes from this date.
        end_date : str | None, optional
            Filter changes until this date.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        ChangesListResponse
            The ChangesListResponse response.
        """
        params: dict[str, typing.Any] = {"page": page}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._client._get(
            "/movie/changes",
            ChangesListResponse,
            params=params,
            include_language=False,
        )

    def tv_list(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
    ) -> ChangesListResponse:
        """
        Get list of changed TV shows.

        Parameters
        ----------
        start_date : str | None, optional
            Filter changes from this date.
        end_date : str | None, optional
            Filter changes until this date.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        ChangesListResponse
            The ChangesListResponse response.
        """
        params: dict[str, typing.Any] = {"page": page}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._client._get(
            "/tv/changes",
            ChangesListResponse,
            params=params,
            include_language=False,
        )

    def person_list(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
    ) -> ChangesListResponse:
        """
        Get list of changed people.

        Parameters
        ----------
        start_date : str | None, optional
            Filter changes from this date.
        end_date : str | None, optional
            Filter changes until this date.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        ChangesListResponse
            The ChangesListResponse response.
        """
        params: dict[str, typing.Any] = {"page": page}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._client._get(
            "/person/changes",
            ChangesListResponse,
            params=params,
            include_language=False,
        )


class AsyncChangesAPI(AsyncBaseAPI):
    """
    Asynchronous Changes API.

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

    async def movie_list(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
    ) -> ChangesListResponse:
        """
        Get list of changed movies.

        Parameters
        ----------
        start_date : str | None, optional
            Filter changes from this date.
        end_date : str | None, optional
            Filter changes until this date.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        ChangesListResponse
            The ChangesListResponse response.
        """
        params: dict[str, typing.Any] = {"page": page}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return await self._client._get(
            "/movie/changes",
            ChangesListResponse,
            params=params,
            include_language=False,
        )

    async def tv_list(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
    ) -> ChangesListResponse:
        """
        Get list of changed TV shows.

        Parameters
        ----------
        start_date : str | None, optional
            Filter changes from this date.
        end_date : str | None, optional
            Filter changes until this date.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        ChangesListResponse
            The ChangesListResponse response.
        """
        params: dict[str, typing.Any] = {"page": page}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return await self._client._get(
            "/tv/changes",
            ChangesListResponse,
            params=params,
            include_language=False,
        )

    async def person_list(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
    ) -> ChangesListResponse:
        """
        Get list of changed people.

        Parameters
        ----------
        start_date : str | None, optional
            Filter changes from this date.
        end_date : str | None, optional
            Filter changes until this date.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        ChangesListResponse
            The ChangesListResponse response.
        """
        params: dict[str, typing.Any] = {"page": page}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return await self._client._get(
            "/person/changes",
            ChangesListResponse,
            params=params,
            include_language=False,
        )
