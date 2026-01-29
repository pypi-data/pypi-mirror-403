# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
TMDB API Python Client.

A simple, high-performance Python wrapper for The Movie Database (TMDB) API.

Examples
--------
>>> from tmdbfusion import TMDBClient
>>> client = TMDBClient("your-api-key")
>>> movie = client.movies.details(550)
>>> print(movie.title)
'Fight Club'

"""

from tmdbfusion.core.client import AsyncTMDBClient
from tmdbfusion.core.client import TMDBClient
from tmdbfusion.data.dataset import Dataset
from tmdbfusion.data.dataset import DatasetBuilder
from tmdbfusion.data.download import AsyncImageDownloader
from tmdbfusion.data.download import ImageDownloader
from tmdbfusion.data.sync import DailyExportSync
from tmdbfusion.exceptions import AuthenticationError
from tmdbfusion.exceptions import AuthorizationError
from tmdbfusion.exceptions import NotFoundError
from tmdbfusion.exceptions import RateLimitError
from tmdbfusion.exceptions import ServerError
from tmdbfusion.exceptions import TMDBError
from tmdbfusion.features.batch import AsyncBatchContext
from tmdbfusion.features.batch import BatchContext
from tmdbfusion.features.batch import BatchResult
from tmdbfusion.utils.links import WatchLinks
from tmdbfusion.utils.navigator import Navigator
from tmdbfusion.utils.presets import DiscoverPresets


__all__ = [
    # Batch
    "AsyncBatchContext",
    # External
    "AsyncImageDownloader",
    # Clients
    "AsyncTMDBClient",
    # Exceptions
    "AuthenticationError",
    "AuthorizationError",
    "BatchContext",
    "BatchResult",
    "DailyExportSync",
    # Data
    "Dataset",
    "DatasetBuilder",
    "DiscoverPresets",
    "ImageDownloader",
    "Navigator",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "TMDBClient",
    "TMDBError",
    "WatchLinks",
]

__version__ = "0.1.0"
