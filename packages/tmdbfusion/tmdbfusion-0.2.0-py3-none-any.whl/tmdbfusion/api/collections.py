# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Collections API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.responses import CollectionDetails
from tmdbfusion.models.responses import ImagesResponse
from tmdbfusion.models.responses import TranslationsResponse


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class CollectionsAPI(BaseAPI):
    """
    Synchronous Collections API.

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

    def details(self, collection_id: int) -> CollectionDetails:
        """
        Get collection details.

        Parameters
        ----------
        collection_id : int
            The collection ID.

        Returns
        -------
        CollectionDetails
            The CollectionDetails response.
        """
        return self._client._get(
            f"/collection/{collection_id}",
            CollectionDetails,
        )

    def images(self, collection_id: int) -> ImagesResponse:
        """
        Get collection images.

        Parameters
        ----------
        collection_id : int
            The collection ID.

        Returns
        -------
        ImagesResponse
            The images.
        """
        return self._client._get(
            f"/collection/{collection_id}/images",
            ImagesResponse,
        )

    def translations(self, collection_id: int) -> TranslationsResponse:
        """
        Get collection translations.

        Parameters
        ----------
        collection_id : int
            The collection ID.

        Returns
        -------
        TranslationsResponse
            The translations.
        """
        return self._client._get(
            f"/collection/{collection_id}/translations",
            TranslationsResponse,
        )


class AsyncCollectionsAPI(AsyncBaseAPI):
    """
    Asynchronous Collections API.

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

    async def details(self, collection_id: int) -> CollectionDetails:
        """
        Get collection details.

        Parameters
        ----------
        collection_id : int
            The collection ID.

        Returns
        -------
        CollectionDetails
            The CollectionDetails response.
        """
        return await self._client._get(
            f"/collection/{collection_id}",
            CollectionDetails,
        )

    async def images(self, collection_id: int) -> ImagesResponse:
        """
        Get collection images.

        Parameters
        ----------
        collection_id : int
            The collection ID.

        Returns
        -------
        ImagesResponse
            The images.
        """
        return await self._client._get(
            f"/collection/{collection_id}/images",
            ImagesResponse,
        )

    async def translations(self, collection_id: int) -> TranslationsResponse:
        """
        Get collection translations.

        Parameters
        ----------
        collection_id : int
            The collection ID.

        Returns
        -------
        TranslationsResponse
            The translations.
        """
        return await self._client._get(
            f"/collection/{collection_id}/translations",
            TranslationsResponse,
        )
