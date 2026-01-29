# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Find API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI
from tmdbfusion.models.responses import FindResults


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class FindAPI(BaseAPI):
    """
    Synchronous Find API.

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

    def by_id(
        self,
        external_id: str,
        *,
        external_source: str,
    ) -> FindResults:
        """
        Find by external ID.

        Parameters
        ----------
        external_id : str
            The external ID value.
        external_source : str
            The external source type.

        Returns
        -------
        FindResults
            The FindResults response.
        """
        return self._client._get(
            f"/find/{external_id}",
            FindResults,
            params={"external_source": external_source},
        )


class AsyncFindAPI(AsyncBaseAPI):
    """
    Asynchronous Find API.

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

    async def by_id(
        self,
        external_id: str,
        *,
        external_source: str,
    ) -> FindResults:
        """
        Find by external ID.

        Parameters
        ----------
        external_id : str
            The external ID value.
        external_source : str
            The external source type.

        Returns
        -------
        FindResults
            The FindResults response.
        """
        return await self._client._get(
            f"/find/{external_id}",
            FindResults,
            params={"external_source": external_source},
        )
