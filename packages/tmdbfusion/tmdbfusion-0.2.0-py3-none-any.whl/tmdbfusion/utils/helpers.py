# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Helper utilities for TMDB models.

Common operations for filtering and extracting data from response models.
"""

from __future__ import annotations

import typing


if typing.TYPE_CHECKING:
    from collections.abc import Sequence

    from tmdbfusion.models.common import Video
    from tmdbfusion.models.common import WatchProvider


class VideoHelper:
    """Helper for Video models."""

    @staticmethod
    def get_urls(
        videos: Sequence[Video],
        *,
        site: str = "YouTube",
        video_type: str = "Trailer",
        official: bool | None = True,
    ) -> list[str]:
        """Get URLs for videos matching criteria.

        Parameters
        ----------
        videos : Sequence[Video]
            List of videos to filter.
        site : str
            Video site (e.g., "YouTube").
        video_type : str
            Video type (e.g., "Trailer", "Teaser").
        official : bool | None
            Filter by official status. If None, ignore status.

        Returns
        -------
        list[str]
            List of video URLs.

        """
        urls: list[str] = []
        for video in videos:
            if video.site != site:
                continue
            if video.type != video_type:
                continue
            if official is not None and video.official != official:
                continue

            if site == "YouTube":
                urls.append(f"https://www.youtube.com/watch?v={video.key}")
            elif site == "Vimeo":
                urls.append(f"https://vimeo.com/{video.key}")

        return urls

    @classmethod
    def get_trailer(
        cls,
        videos: Sequence[Video],
        *,
        site: str = "YouTube",
    ) -> str | None:
        """Get the first matching trailer URL.

        Parameters
        ----------
        videos : Sequence[Video]
            List of videos.
        site : str
            Video site (default "YouTube").

        Returns
        -------
        str | None
            Trailer URL or None.

        """
        urls = cls.get_urls(videos, site=site, video_type="Trailer")
        return urls[0] if urls else None

    @classmethod
    def get_teaser(
        cls,
        videos: Sequence[Video],
        *,
        site: str = "YouTube",
    ) -> str | None:
        """Get the first matching teaser URL.

        Parameters
        ----------
        videos : Sequence[Video]
            List of videos.
        site : str
            Video site (default "YouTube").

        Returns
        -------
        str | None
            Teaser URL or None.

        """
        urls = cls.get_urls(videos, site=site, video_type="Teaser")
        return urls[0] if urls else None


class WatchProviderHelper:
    """Helper for WatchProvider models."""

    @staticmethod
    def filter_by_priority(
        providers: Sequence[WatchProvider],
        threshold: int = 10,
    ) -> list[WatchProvider]:
        """Filter providers by display priority.

        Parameters
        ----------
        providers : Sequence[WatchProvider]
            List of providers.
        threshold : int
            Max display priority (lower is better, usually).
            TMDB priority: 0 is highest? Actually checks docs.
            Usually lower number = higher priority.

        Returns
        -------
        list[WatchProvider]
            Filtered list sorted by priority.

        """
        # Sort by display_priority
        sorted_providers = sorted(
            providers,
            key=lambda p: p.display_priority,
        )
        return [p for p in sorted_providers if p.display_priority <= threshold]
