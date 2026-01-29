# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Credits API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.responses import CreditDetails


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class CreditsAPI(BaseAPI):
    """
    Synchronous Credits API.

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

    def details(self, credit_id: str) -> CreditDetails:
        """
        Get credit details.

        Parameters
        ----------
        credit_id : str
            The credit ID.

        Returns
        -------
        CreditDetails
            The CreditDetails response.
        """
        return self._client._get(
            f"/credit/{credit_id}",
            CreditDetails,
        )


class AsyncCreditsAPI(AsyncBaseAPI):
    """
    Asynchronous Credits API.

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

    async def details(self, credit_id: str) -> CreditDetails:
        """
        Get credit details.

        Parameters
        ----------
        credit_id : str
            The credit ID.

        Returns
        -------
        CreditDetails
            The CreditDetails response.
        """
        return await self._client._get(
            f"/credit/{credit_id}",
            CreditDetails,
        )
