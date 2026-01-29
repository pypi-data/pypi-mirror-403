# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Image URL utilities.

Helper for constructing full image URLs from TMDB image paths.
"""

from __future__ import annotations

import typing


if typing.TYPE_CHECKING:
    from tmdbfusion.core.client import AsyncTMDBClient
    from tmdbfusion.core.client import TMDBClient
    from tmdbfusion.models.responses import ConfigurationDetails


# Official TMDB image base URL
IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

# Available poster sizes
POSTER_SIZES = ("w92", "w154", "w185", "w342", "w500", "w780", "original")

# Available backdrop sizes
BACKDROP_SIZES = ("w300", "w780", "w1280", "original")

# Available profile (person) sizes
PROFILE_SIZES = ("w45", "w185", "h632", "original")

# Available still (episode) sizes
STILL_SIZES = ("w92", "w185", "w300", "original")

# Available logo sizes
LOGO_SIZES = ("w45", "w92", "w154", "w185", "w300", "w500", "original")


class ImageSize:
    """Image size constants."""

    # Posters
    POSTER_SMALL = "w185"
    POSTER_MEDIUM = "w342"
    POSTER_LARGE = "w500"
    POSTER_XLARGE = "w780"
    POSTER_ORIGINAL = "original"

    # Backdrops
    BACKDROP_SMALL = "w300"
    BACKDROP_MEDIUM = "w780"
    BACKDROP_LARGE = "w1280"
    BACKDROP_ORIGINAL = "original"

    # Profiles
    PROFILE_SMALL = "w45"
    PROFILE_MEDIUM = "w185"
    PROFILE_LARGE = "h632"
    PROFILE_ORIGINAL = "original"

    # Stills
    STILL_SMALL = "w92"
    STILL_MEDIUM = "w185"
    STILL_LARGE = "w300"
    STILL_ORIGINAL = "original"


class ImagesAPI:
    """Image URL builder.

    Examples
    --------
    >>> client.images.url("/abc123.jpg", "w500")
    'https://image.tmdb.org/t/p/w500/abc123.jpg'

    >>> client.images.poster_url("/abc123.jpg")
    'https://image.tmdb.org/t/p/w500/abc123.jpg'

    Parameters
    ----------
    client : TMDBClient | AsyncTMDBClient
        TMDB client instance.

    """

    def __init__(self, client: TMDBClient | AsyncTMDBClient) -> None:
        self._client = client
        self._config: ConfigurationDetails | None = None

    def set_configuration(self, config: ConfigurationDetails) -> None:
        """Set API configuration.

        Parameters
        ----------
        config : ConfigurationDetails
            Configuration details from API.

        Returns
        -------
        None

        """
        self._config = config

    def url(self, path: str | None, size: str = "original") -> str | None:
        """Build full image URL from path.

        Parameters
        ----------
        path : str | None
            Image path from API response (e.g., "/abc123.jpg").
        size : str
            Image size (e.g., "w500", "original").

        Returns
        -------
        str | None
            Full image URL, or None if path is None.

        """
        if path is None:
            return None
        # Ensure path starts with /
        if not path.startswith("/"):
            path = f"/{path}"

        base_url = IMAGE_BASE_URL
        if self._config and self._config.images:
            base_url = self._config.images.secure_base_url or self._config.images.base_url

        # Remove trailing slash from base_url if present
        base_url = base_url.removesuffix("/")

        return f"{base_url}/{size}{path}"

    def poster_url(
        self,
        path: str | None,
        size: str = ImageSize.POSTER_LARGE,
    ) -> str | None:
        """Build poster image URL."""
        return self.url(path, size)

    def backdrop_url(
        self,
        path: str | None,
        size: str = ImageSize.BACKDROP_LARGE,
    ) -> str | None:
        """Build backdrop image URL."""
        return self.url(path, size)

    def profile_url(
        self,
        path: str | None,
        size: str = ImageSize.PROFILE_MEDIUM,
    ) -> str | None:
        """Build profile image URL."""
        return self.url(path, size)

    def still_url(
        self,
        path: str | None,
        size: str = ImageSize.STILL_LARGE,
    ) -> str | None:
        """Build still image URL."""
        return self.url(path, size)

    def logo_url(self, path: str | None, size: str = "w300") -> str | None:
        """Build logo image URL."""
        return self.url(path, size)
