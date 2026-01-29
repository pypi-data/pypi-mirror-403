# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""TV Episode Groups API."""

from __future__ import annotations

import typing

from tmdbfusion.api._base import AsyncBaseAPI
from tmdbfusion.api._base import BaseAPI


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class EpisodeGroupDetails(typing.TypedDict):
    """Episode group details."""

    id: str
    name: str
    description: str
    episode_count: int
    group_count: int
    groups: list[dict[str, typing.Any]]
    type: int
    network: dict[str, typing.Any] | None


class TVEpisodeGroupsAPI(BaseAPI):
    """
    Synchronous TV Episode Groups API.

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

    def details(self, episode_group_id: str) -> dict[str, typing.Any]:
        """
        Get episode group details.

        Parameters
        ----------
        episode_group_id : str
            The episode group id.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return self._client._get(
            f"/tv/episode_group/{episode_group_id}",
            dict[str, typing.Any],
        )


class AsyncTVEpisodeGroupsAPI(AsyncBaseAPI):
    """
    Asynchronous TV Episode Groups API.

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

    async def details(self, episode_group_id: str) -> dict[str, typing.Any]:
        """
        Get episode group details.

        Parameters
        ----------
        episode_group_id : str
            The episode group id.

        Returns
        -------
        dict[str, typing.Any]
            The dict[str, typing.Any] response.
        """
        return await self._client._get(
            f"/tv/episode_group/{episode_group_id}",
            dict[str, typing.Any],
        )
