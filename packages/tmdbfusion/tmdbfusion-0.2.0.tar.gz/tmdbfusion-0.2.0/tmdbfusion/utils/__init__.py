# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Utilities and helpers.

Various helper classes and utilities for working with TMDB data.
"""

from tmdbfusion.utils.append import Append
from tmdbfusion.utils.append import build_append
from tmdbfusion.utils.detect import DetectionResult
from tmdbfusion.utils.detect import ExternalSource
from tmdbfusion.utils.detect import MediaDetector
from tmdbfusion.utils.detect import MediaInfo
from tmdbfusion.utils.detect import MediaType
from tmdbfusion.utils.discover import DiscoverBuilder
from tmdbfusion.utils.helpers import VideoHelper
from tmdbfusion.utils.helpers import WatchProviderHelper
from tmdbfusion.utils.images import ImagesAPI
from tmdbfusion.utils.images import ImageSize
from tmdbfusion.utils.links import WatchLinks
from tmdbfusion.utils.navigator import Navigator
from tmdbfusion.utils.presets import DiscoverPresets
from tmdbfusion.utils.watcher import ChangeWatcher
from tmdbfusion.utils.watcher import ContentDiff
from tmdbfusion.utils.watcher import FieldChange
from tmdbfusion.utils.watcher import Snapshot
from tmdbfusion.utils.watcher import SnapshotStore


__all__ = [
    # Append
    "Append",
    # Watcher
    "ChangeWatcher",
    "ContentDiff",
    # Detect
    "DetectionResult",
    # Discover
    "DiscoverBuilder",
    # Presets
    "DiscoverPresets",
    "ExternalSource",
    "FieldChange",
    # Images
    "ImageSize",
    "ImagesAPI",
    "MediaDetector",
    "MediaInfo",
    "MediaType",
    # Navigator
    "Navigator",
    "Snapshot",
    "SnapshotStore",
    # Helpers
    "VideoHelper",
    # Links
    "WatchLinks",
    "WatchProviderHelper",
    "build_append",
]
