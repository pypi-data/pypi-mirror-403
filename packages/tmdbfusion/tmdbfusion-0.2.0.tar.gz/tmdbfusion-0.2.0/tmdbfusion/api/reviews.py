# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Reviews API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.responses import ReviewDetails


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class ReviewsAPI(BaseAPI):
    """
    Synchronous Reviews API.

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

    def details(self, review_id: str) -> ReviewDetails:
        """
        Get review details.

        Parameters
        ----------
        review_id : str
            The review ID.

        Returns
        -------
        ReviewDetails
            The ReviewDetails response.
        """
        return self._client._get(
            f"/review/{review_id}",
            ReviewDetails,
        )


class AsyncReviewsAPI(AsyncBaseAPI):
    """
    Asynchronous Reviews API.

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

    async def details(self, review_id: str) -> ReviewDetails:
        """
        Get review details.

        Parameters
        ----------
        review_id : str
            The review ID.

        Returns
        -------
        ReviewDetails
            The ReviewDetails response.
        """
        return await self._client._get(
            f"/review/{review_id}",
            ReviewDetails,
        )
