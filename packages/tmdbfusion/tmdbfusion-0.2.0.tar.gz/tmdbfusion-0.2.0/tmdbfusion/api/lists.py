# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Lists API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.responses import ListDetails
from tmdbfusion.models.responses import ListItemStatus
from tmdbfusion.models.responses import StatusResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class ListsAPI(BaseAPI):
    """
    Synchronous Lists API.

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

    def details(self, list_id: int) -> ListDetails:
        """
        Get list details.

        Parameters
        ----------
        list_id : int
            The list ID.

        Returns
        -------
        ListDetails
            The ListDetails response.
        """
        return self._client._get(f"/list/{list_id}", ListDetails)

    def check_item_status(
        self,
        list_id: int,
        *,
        movie_id: int,
    ) -> ListItemStatus:
        """
        Check if movie is in list.

        Parameters
        ----------
        list_id : int
            The list ID.
        movie_id : int
            The movie ID.

        Returns
        -------
        ListItemStatus
            The ListItemStatus response.
        """
        return self._client._get(
            f"/list/{list_id}/item_status",
            ListItemStatus,
            params={"movie_id": movie_id},
        )

    def create(
        self,
        *,
        session_id: str,
        name: str,
        description: str = "",
        language: str = "en",
    ) -> StatusResponse:
        """
        Create a new list.

        Parameters
        ----------
        session_id : str
            The session ID.
        name : str
            The list name.
        description : str, optional
            The list description.
        language : str, optional
            Filter by language code.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return self._client._post(
            "/list",
            StatusResponse,
            params={"session_id": session_id},
            body={
                "name": name,
                "description": description,
                "language": language,
            },
        )

    def add_movie(
        self,
        list_id: int,
        *,
        session_id: str,
        media_id: int,
    ) -> StatusResponse:
        """
        Add movie to list.

        Parameters
        ----------
        list_id : int
            The list ID.
        session_id : str
            The session ID.
        media_id : int
            The media ID.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return self._client._post(
            f"/list/{list_id}/add_item",
            StatusResponse,
            params={"session_id": session_id},
            body={"media_id": media_id},
        )

    def remove_movie(
        self,
        list_id: int,
        *,
        session_id: str,
        media_id: int,
    ) -> StatusResponse:
        """
        Remove movie from list.

        Parameters
        ----------
        list_id : int
            The list ID.
        session_id : str
            The session ID.
        media_id : int
            The media ID.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return self._client._post(
            f"/list/{list_id}/remove_item",
            StatusResponse,
            params={"session_id": session_id},
            body={"media_id": media_id},
        )

    def clear(
        self,
        list_id: int,
        *,
        session_id: str,
        confirm: bool = True,
    ) -> StatusResponse:
        """
        Clear all items from list.

        Parameters
        ----------
        list_id : int
            The list ID.
        session_id : str
            The session ID.
        confirm : bool, optional
            The confirm.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return self._client._post(
            f"/list/{list_id}/clear",
            StatusResponse,
            params={"session_id": session_id, "confirm": confirm},
        )

    def delete(self, list_id: int, *, session_id: str) -> StatusResponse:
        """
        Delete list.

        Parameters
        ----------
        list_id : int
            The list ID.
        session_id : str
            The session ID.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return self._client._delete(
            f"/list/{list_id}",
            StatusResponse,
            params={"session_id": session_id},
        )


class AsyncListsAPI(AsyncBaseAPI):
    """
    Asynchronous Lists API.

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

    async def details(self, list_id: int) -> ListDetails:
        """
        Get list details.

        Parameters
        ----------
        list_id : int
            The list ID.

        Returns
        -------
        ListDetails
            The ListDetails response.
        """
        return await self._client._get(f"/list/{list_id}", ListDetails)

    async def check_item_status(
        self,
        list_id: int,
        *,
        movie_id: int,
    ) -> ListItemStatus:
        """
        Check if movie is in list.

        Parameters
        ----------
        list_id : int
            The list ID.
        movie_id : int
            The movie ID.

        Returns
        -------
        ListItemStatus
            The ListItemStatus response.
        """
        return await self._client._get(
            f"/list/{list_id}/item_status",
            ListItemStatus,
            params={"movie_id": movie_id},
        )

    async def create(
        self,
        *,
        session_id: str,
        name: str,
        description: str = "",
    ) -> StatusResponse:
        """
        Create a new list.

        Parameters
        ----------
        session_id : str
            The session ID.
        name : str
            The list name.
        description : str, optional
            The list description.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return await self._client._post(
            "/list",
            StatusResponse,
            params={"session_id": session_id},
            body={"name": name, "description": description},
        )

    async def add_movie(
        self,
        list_id: int,
        *,
        session_id: str,
        media_id: int,
    ) -> StatusResponse:
        """
        Add movie to list.

        Parameters
        ----------
        list_id : int
            The list ID.
        session_id : str
            The session ID.
        media_id : int
            The media ID.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return await self._client._post(
            f"/list/{list_id}/add_item",
            StatusResponse,
            params={"session_id": session_id},
            body={"media_id": media_id},
        )

    async def remove_movie(
        self,
        list_id: int,
        *,
        session_id: str,
        media_id: int,
    ) -> StatusResponse:
        """
        Remove movie from list.

        Parameters
        ----------
        list_id : int
            The list ID.
        session_id : str
            The session ID.
        media_id : int
            The media ID.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return await self._client._post(
            f"/list/{list_id}/remove_item",
            StatusResponse,
            params={"session_id": session_id},
            body={"media_id": media_id},
        )

    async def delete(self, list_id: int, *, session_id: str) -> StatusResponse:
        """
        Delete list.

        Parameters
        ----------
        list_id : int
            The list ID.
        session_id : str
            The session ID.

        Returns
        -------
        StatusResponse
            The status response.
        """
        return await self._client._delete(
            f"/list/{list_id}",
            StatusResponse,
            params={"session_id": session_id},
        )
