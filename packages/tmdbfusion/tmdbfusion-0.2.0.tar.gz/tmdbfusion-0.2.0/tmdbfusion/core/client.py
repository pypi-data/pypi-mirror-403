# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
TMDB Client Classes.

Main entry points for the TMDB API.
"""

from __future__ import annotations

from tmdbfusion.core.async_client import AsyncTMDBClient
from tmdbfusion.core.sync_client import TMDBClient


__all__ = ["AsyncTMDBClient", "TMDBClient"]
