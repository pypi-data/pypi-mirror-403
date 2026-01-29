# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Append to response constants and helpers."""

from __future__ import annotations


class Append:
    """Constants for append_to_response."""

    ACCOUNT_STATES = "account_states"
    ALTERNATIVE_TITLES = "alternative_titles"
    CHANGES = "changes"
    CREDITS = "credits"
    CONTENT_RATINGS = "content_ratings"
    EXTERNAL_IDS = "external_ids"
    IMAGES = "images"
    KEYWORDS = "keywords"
    LISTS = "lists"
    RECOMMENDATIONS = "recommendations"
    RELEASE_DATES = "release_dates"
    REVIEWS = "reviews"
    SIMILAR = "similar"
    TRANSLATIONS = "translations"
    VIDEOS = "videos"
    WATCH_PROVIDERS = "watch_providers"

    # TV Specific
    AGGREGATE_CREDITS = "aggregate_credits"
    EPISODE_GROUPS = "episode_groups"
    SCREENED_THEATRICALLY = "screened_theatrically"

    # Person Specific
    COMBINED_CREDITS = "combined_credits"
    MOVIE_CREDITS = "movie_credits"
    TV_CREDITS = "tv_credits"


def build_append(*args: str) -> str:
    """Build comma-separated append_to_response string.

    Examples
    --------
    >>> build_append(Append.CREDITS, Append.IMAGES)
    'credits,images'

    Parameters
    ----------
    *args : str
        Append to response values (e.g., Append.CREDITS).

    Returns
    -------
    str
        Comma-separated string.

    """
    return ",".join(args)
