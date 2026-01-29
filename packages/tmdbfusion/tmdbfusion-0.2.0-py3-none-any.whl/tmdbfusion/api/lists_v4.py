# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""V4 Lists API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class ListsV4API(BaseAPI):
    """
    Synchronous V4 Lists API.

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

    def details(self, list_id: int, *, page: int = 1) -> dict[str, typing.Any]:
        """
        Get V4 list details.

        Parameters
        ----------
        list_id : int
            The list ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return self._client._get(
            f"/list/{list_id}",
            dict[str, typing.Any],
            params={"page": page},
            version=4,
        )

    def add_items(
        self,
        list_id: int,
        *,
        items: list[dict[str, typing.Any]],
    ) -> dict[str, typing.Any]:
        """
        Add items to V4 list.

        Parameters
        ----------
        list_id : int
            The list ID.
        items : list[dict[str, typing.Any]]
            List of items to add or remove.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return self._client._post(
            f"/list/{list_id}/items",
            dict[str, typing.Any],
            body={"items": items},
            version=4,
        )

    def clear(self, list_id: int) -> dict[str, typing.Any]:
        """
        Clear V4 list.

        Parameters
        ----------
        list_id : int
            The list ID.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return self._client._get(
            f"/list/{list_id}/clear",
            dict[str, typing.Any],
            version=4,
        )

    def create(
        self,
        *,
        name: str,
        iso_639_1: str = "en",
        description: str = "",
        public: bool = True,
    ) -> dict[str, typing.Any]:
        """
        Create a V4 list.

        Parameters
        ----------
        name : str
            The list name.
        iso_639_1 : str, optional
            ISO 639-1 language code.
        description : str, optional
            The list description.
        public : bool, optional
            Whether the list is public.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return self._client._post(
            "/list",
            dict[str, typing.Any],
            body={
                "name": name,
                "iso_639_1": iso_639_1,
                "description": description,
                "public": public,
            },
            version=4,
        )

    def delete(self, list_id: int) -> dict[str, typing.Any]:
        """
        Delete V4 list.

        Parameters
        ----------
        list_id : int
            The list ID.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return self._client._delete(
            f"/list/{list_id}",
            dict[str, typing.Any],
            version=4,
        )

    def item_status(
        self,
        list_id: int,
        *,
        media_id: int,
        media_type: str,
    ) -> dict[str, typing.Any]:
        """
        Check item status in V4 list.

        Parameters
        ----------
        list_id : int
            The list ID.
        media_id : int
            The media ID.
        media_type : str
            The media type (movie or tv).

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return self._client._get(
            f"/list/{list_id}/item_status",
            dict[str, typing.Any],
            params={"media_id": media_id, "media_type": media_type},
            version=4,
        )

    def remove_items(
        self,
        list_id: int,
        *,
        items: list[dict[str, typing.Any]],
    ) -> dict[str, typing.Any]:
        """
        Remove items from V4 list.

        Parameters
        ----------
        list_id : int
            The list ID.
        items : list[dict[str, typing.Any]]
            List of items to add or remove.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return self._client._delete(
            f"/list/{list_id}/items",
            dict[str, typing.Any],
            body={"items": items},
            version=4,
        )

    def update(
        self,
        list_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        public: bool | None = None,
        sort_by: str | None = None,
    ) -> dict[str, typing.Any]:
        """
        Update V4 list.

        Parameters
        ----------
        list_id : int
            The list ID.
        name : str | None, optional
            The list name.
        description : str | None, optional
            The list description.
        public : bool | None, optional
            Whether the list is public.
        sort_by : str | None, optional
            Sort order for results.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        body: dict[str, typing.Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if public is not None:
            body["public"] = public
        if sort_by is not None:
            body["sort_by"] = sort_by
        return self._client._put(
            f"/list/{list_id}",
            dict[str, typing.Any],
            body=body,
            version=4,
        )

    def update_items(
        self,
        list_id: int,
        *,
        items: list[dict[str, typing.Any]],
    ) -> dict[str, typing.Any]:
        """
        Update items in V4 list.

        Parameters
        ----------
        list_id : int
            The list ID.
        items : list[dict[str, typing.Any]]
            List of items to add or remove.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return self._client._put(
            f"/list/{list_id}/items",
            dict[str, typing.Any],
            body={"items": items},
            version=4,
        )


class AsyncListsV4API(AsyncBaseAPI):
    """
    Asynchronous V4 Lists API.

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
        list_id: int,
        *,
        page: int = 1,
    ) -> dict[str, typing.Any]:
        """
        Get V4 list details.

        Parameters
        ----------
        list_id : int
            The list ID.
        page : int, optional
            The page number to retrieve.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return await self._client._get(
            f"/list/{list_id}",
            dict[str, typing.Any],
            params={"page": page},
            version=4,
        )

    async def add_items(
        self,
        list_id: int,
        *,
        items: list[dict[str, typing.Any]],
    ) -> dict[str, typing.Any]:
        """
        Add items to V4 list.

        Parameters
        ----------
        list_id : int
            The list ID.
        items : list[dict[str, typing.Any]]
            List of items to add or remove.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return await self._client._post(
            f"/list/{list_id}/items",
            dict[str, typing.Any],
            body={"items": items},
            version=4,
        )

    async def clear(self, list_id: int) -> dict[str, typing.Any]:
        """
        Clear V4 list.

        Parameters
        ----------
        list_id : int
            The list ID.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return await self._client._get(
            f"/list/{list_id}/clear",
            dict[str, typing.Any],
            version=4,
        )

    async def create(
        self,
        *,
        name: str,
        iso_639_1: str = "en",
        description: str = "",
        public: bool = True,
    ) -> dict[str, typing.Any]:
        """
        Create a V4 list.

        Parameters
        ----------
        name : str
            The list name.
        iso_639_1 : str, optional
            ISO 639-1 language code.
        description : str, optional
            The list description.
        public : bool, optional
            Whether the list is public.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return await self._client._post(
            "/list",
            dict[str, typing.Any],
            body={
                "name": name,
                "iso_639_1": iso_639_1,
                "description": description,
                "public": public,
            },
            version=4,
        )

    async def delete(self, list_id: int) -> dict[str, typing.Any]:
        """
        Delete V4 list.

        Parameters
        ----------
        list_id : int
            The list ID.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return await self._client._delete(
            f"/list/{list_id}",
            dict[str, typing.Any],
            version=4,
        )

    async def item_status(
        self,
        list_id: int,
        *,
        media_id: int,
        media_type: str,
    ) -> dict[str, typing.Any]:
        """
        Check item status in V4 list.

        Parameters
        ----------
        list_id : int
            The list ID.
        media_id : int
            The media ID.
        media_type : str
            The media type (movie or tv).

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return await self._client._get(
            f"/list/{list_id}/item_status",
            dict[str, typing.Any],
            params={"media_id": media_id, "media_type": media_type},
            version=4,
        )

    async def remove_items(
        self,
        list_id: int,
        *,
        items: list[dict[str, typing.Any]],
    ) -> dict[str, typing.Any]:
        """
        Remove items from V4 list.

        Parameters
        ----------
        list_id : int
            The list ID.
        items : list[dict[str, typing.Any]]
            List of items to add or remove.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return await self._client._delete(
            f"/list/{list_id}/items",
            dict[str, typing.Any],
            body={"items": items},
            version=4,
        )

    async def update(
        self,
        list_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        public: bool | None = None,
    ) -> dict[str, typing.Any]:
        """
        Update V4 list.

        Parameters
        ----------
        list_id : int
            The list ID.
        name : str | None, optional
            The list name.
        description : str | None, optional
            The list description.
        public : bool | None, optional
            Whether the list is public.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        body: dict[str, typing.Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if public is not None:
            body["public"] = public
        return await self._client._put(
            f"/list/{list_id}",
            dict[str, typing.Any],
            body=body,
            version=4,
        )

    async def update_items(
        self,
        list_id: int,
        *,
        items: list[dict[str, typing.Any]],
    ) -> dict[str, typing.Any]:
        """
        Update items in V4 list.

        Parameters
        ----------
        list_id : int
            The list ID.
        items : list[dict[str, typing.Any]]
            List of items to add or remove.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return await self._client._put(
            f"/list/{list_id}/items",
            dict[str, typing.Any],
            body={"items": items},
            version=4,
        )
