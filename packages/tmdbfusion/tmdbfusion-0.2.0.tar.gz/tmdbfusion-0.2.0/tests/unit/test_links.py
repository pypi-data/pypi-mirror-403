# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Unit tests for links module."""

from tmdbfusion.utils.links import MediaLinks
from tmdbfusion.utils.links import ProviderLink


class TestMediaLinks:
    """Tests for MediaLinks."""

    def test_netflix_property(self) -> None:
        """Test Netflix shortcut."""
        netflix = ProviderLink(8, "Netflix", "https://netflix.com/search")
        links = MediaLinks(
            media_id=550,
            media_title="Fight Club",
            tmdb_link="https://tmdb.org/movie/550",
            flatrate=[netflix],
        )
        assert links.netflix == "https://netflix.com/search"

    def test_missing_provider(self) -> None:
        """Test missing provider returns None."""
        links = MediaLinks(
            media_id=550,
            media_title="Fight Club",
            tmdb_link="https://tmdb.org/movie/550",
        )
        assert links.netflix is None
        assert links.amazon_prime is None

    def test_all_flatrate(self) -> None:
        """Test all_flatrate property."""
        providers = [
            ProviderLink(8, "Netflix", "https://netflix.com"),
            ProviderLink(9, "Amazon", "https://amazon.com"),
        ]
        links = MediaLinks(
            media_id=550,
            media_title="Test",
            tmdb_link="https://tmdb.org/movie/550",
            flatrate=providers,
        )
        assert len(links.all_flatrate) == 2
