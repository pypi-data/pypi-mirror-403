# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Base API service class."""

from __future__ import annotations

import typing


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient


class BaseAPI:
    """
    Base class for sync API services.

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
        self._client = client


class AsyncBaseAPI:
    """
    Base class for async API services.

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
        self._client = client
