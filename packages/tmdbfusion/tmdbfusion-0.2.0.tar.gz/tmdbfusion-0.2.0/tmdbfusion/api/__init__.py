# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
API namespace init.
"""

from tmdbfusion.api.movies import AsyncMoviesAPI
from tmdbfusion.api.movies import MoviesAPI
from tmdbfusion.api.search import AsyncSearchAPI
from tmdbfusion.api.search import SearchAPI
from tmdbfusion.api.tv import TVAPI
from tmdbfusion.api.tv import AsyncTVAPI


__all__ = [
    "TVAPI",
    "AsyncMoviesAPI",
    "AsyncSearchAPI",
    "AsyncTVAPI",
    "MoviesAPI",
    "SearchAPI",
]
