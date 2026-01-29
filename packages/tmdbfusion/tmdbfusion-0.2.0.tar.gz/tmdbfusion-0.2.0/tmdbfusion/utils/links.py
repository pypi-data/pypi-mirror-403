# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Watch Link Generator.

Generate deep links to streaming services from watch provider data.
"""

from __future__ import annotations

import typing
from dataclasses import dataclass
from dataclasses import field


if typing.TYPE_CHECKING:
    from tmdbfusion.core.sync_client import TMDBClient


# Provider IDs for common services
PROVIDER_IDS = {
    "netflix": 8,
    "amazon_prime": 9,
    "disney_plus": 337,
    "hbo_max": 384,
    "hulu": 15,
    "apple_tv": 350,
    "paramount_plus": 531,
    "peacock": 386,
    "crunchyroll": 283,
}

# Deep link templates (where available)
DEEP_LINK_TEMPLATES: dict[int, str] = {
    8: "https://www.netflix.com/search?q={title}",
    9: "https://www.amazon.com/s?k={title}&i=instant-video",
    337: "https://www.disneyplus.com/search/{title}",
    15: "https://www.hulu.com/search?q={title}",
}


@dataclass
class ProviderLink:
    """Link to a streaming provider.

    Attributes
    ----------
    provider_id : int
        TMDB provider ID.
    provider_name : str
        Display name.
    link : str
        Deep link or search URL.
    logo_path : str | None
        Provider logo path.

    """

    provider_id: int
    provider_name: str
    link: str
    logo_path: str | None = None


@dataclass
class MediaLinks:
    """Watch links for a single media item.

    Attributes
    ----------
    media_id : int
        Movie or TV ID.
    media_title : str
        Title for search links.
    tmdb_link : str
        Link to TMDB page.
    justwatch_link : str | None
        JustWatch page link.
    flatrate : list[ProviderLink]
        Subscription streaming services.
    rent : list[ProviderLink]
        Rental options.
    buy : list[ProviderLink]
        Purchase options.

    """

    media_id: int
    media_title: str
    tmdb_link: str
    justwatch_link: str | None = None
    flatrate: list[ProviderLink] = field(default_factory=list)
    rent: list[ProviderLink] = field(default_factory=list)
    buy: list[ProviderLink] = field(default_factory=list)

    @property
    def netflix(self) -> str | None:
        """Get Netflix link if available.

        Returns
        -------
        str | None
            Netflix link or None.

        """
        return self._find_provider(8)

    @property
    def amazon_prime(self) -> str | None:
        """Get Amazon Prime link if available.

        Returns
        -------
        str | None
            Amazon link or None.

        """
        return self._find_provider(9)

    @property
    def disney_plus(self) -> str | None:
        """Get Disney+ link if available.

        Returns
        -------
        str | None
            Disney+ link or None.

        """
        return self._find_provider(337)

    @property
    def hbo_max(self) -> str | None:
        """Get HBO Max link if available.

        Returns
        -------
        str | None
            HBO Max link or None.

        """
        return self._find_provider(384)

    @property
    def all_flatrate(self) -> list[ProviderLink]:
        """Get all subscription streaming options.

        Returns
        -------
        list[ProviderLink]
            All flatrate providers.

        """
        return self.flatrate

    def _find_provider(self, provider_id: int) -> str | None:
        """Find provider link by ID.

        Parameters
        ----------
        provider_id : int
            Provider ID to find.

        Returns
        -------
        str | None
            Link if found.

        """
        for provider in self.flatrate:
            if provider.provider_id == provider_id:
                return provider.link
        return None


class WatchLinks:
    """Generate watch links for movies and TV shows.

    Examples
    --------
    >>> links = WatchLinks(client, region="US")
    >>> movie_links = links.for_movie(550)
    >>> print(movie_links.netflix)

    Parameters
    ----------
    client : TMDBClient
        TMDB client instance.
    region : str
        Region code for provider availability.

    """

    def __init__(self, client: TMDBClient, region: str = "US") -> None:
        self._client = client
        self._region = region

    def for_movie(self, movie_id: int) -> MediaLinks:
        """Get watch links for a movie.

        Parameters
        ----------
        movie_id : int
            Movie ID.

        Returns
        -------
        MediaLinks
            Watch links for the movie.

        """
        details = self._client.movies.details(movie_id)
        title = getattr(details, "title", "") or ""
        providers = self._client.movies.watch_providers(movie_id)

        return self._build_links(
            media_id=movie_id,
            media_title=title,
            media_type="movie",
            providers=providers,
        )

    def for_tv(self, tv_id: int) -> MediaLinks:
        """Get watch links for a TV show.

        Parameters
        ----------
        tv_id : int
            TV show ID.

        Returns
        -------
        MediaLinks
            Watch links for the show.

        """
        details = self._client.tv.details(tv_id)
        title = getattr(details, "name", "") or ""
        providers = self._client.tv.watch_providers(tv_id)

        return self._build_links(
            media_id=tv_id,
            media_title=title,
            media_type="tv",
            providers=providers,
        )

    def for_movies(
        self,
        movie_ids: list[int],
    ) -> list[MediaLinks]:
        """Get watch links for multiple movies.

        Parameters
        ----------
        movie_ids : list[int]
            List of movie IDs.

        Returns
        -------
        list[MediaLinks]
            Watch links for each movie.

        """
        return [self.for_movie(mid) for mid in movie_ids]

    def _build_links(
        self,
        media_id: int,
        media_title: str,
        media_type: str,
        providers: object,
    ) -> MediaLinks:
        """Build MediaLinks from provider response.

        Parameters
        ----------
        media_id : int
            Media ID.
        media_title : str
            Media title.
        media_type : str
            "movie" or "tv".
        providers : object
            Watch providers response.

        Returns
        -------
        MediaLinks
            Built links.

        """
        tmdb_link = f"https://www.themoviedb.org/{media_type}/{media_id}"

        # Get region-specific providers
        results = getattr(providers, "results", {})
        region_data = results.get(self._region, {}) if isinstance(results, dict) else {}

        # Extract JustWatch link
        jw_link = (
            region_data.get("link")
            if isinstance(
                region_data,
                dict,
            )
            else None
        )

        # Build provider links
        flatrate = self._extract_providers(
            region_data.get("flatrate", [])
            if isinstance(
                region_data,
                dict,
            )
            else [],
            media_title,
        )
        rent = self._extract_providers(
            region_data.get("rent", [])
            if isinstance(
                region_data,
                dict,
            )
            else [],
            media_title,
        )
        buy = self._extract_providers(
            region_data.get("buy", [])
            if isinstance(
                region_data,
                dict,
            )
            else [],
            media_title,
        )

        return MediaLinks(
            media_id=media_id,
            media_title=media_title,
            tmdb_link=tmdb_link,
            justwatch_link=jw_link,
            flatrate=flatrate,
            rent=rent,
            buy=buy,
        )

    def _extract_providers(
        self,
        providers: list[object],
        title: str,
    ) -> list[ProviderLink]:
        """Extract provider links from response.

        Parameters
        ----------
        providers : list[object]
            Provider list from API.
        title : str
            Media title for search links.

        Returns
        -------
        list[ProviderLink]
            Extracted provider links.

        """
        links: list[ProviderLink] = []
        encoded_title = title.replace(" ", "%20")

        for provider in providers:
            pid = getattr(provider, "provider_id", 0)
            name = getattr(provider, "provider_name", "") or ""
            logo = getattr(provider, "logo_path", None)

            # Generate link
            if pid in DEEP_LINK_TEMPLATES:
                link = DEEP_LINK_TEMPLATES[pid].format(title=encoded_title)
            else:
                # Fallback to Google search
                link = f"https://www.google.com/search?q={encoded_title}+{name}"

            links.append(
                ProviderLink(
                    provider_id=pid,
                    provider_name=name,
                    link=link,
                    logo_path=logo,
                )
            )

        return links
