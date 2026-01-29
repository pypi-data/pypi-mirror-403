# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Synchronous TMDB Client."""

from __future__ import annotations

import typing

import msgspec

from tmdbfusion.api.account import AccountAPI
from tmdbfusion.api.account_v4 import AccountV4API
from tmdbfusion.api.auth_v4 import AuthV4API
from tmdbfusion.api.authentication import AuthenticationAPI
from tmdbfusion.api.certifications import CertificationsAPI
from tmdbfusion.api.changes import ChangesAPI
from tmdbfusion.api.collections import CollectionsAPI
from tmdbfusion.api.companies import CompaniesAPI
from tmdbfusion.api.configuration import ConfigurationAPI
from tmdbfusion.api.credits import CreditsAPI
from tmdbfusion.api.discover import DiscoverAPI
from tmdbfusion.api.find import FindAPI
from tmdbfusion.api.genres import GenresAPI
from tmdbfusion.api.guest_session import GuestSessionAPI
from tmdbfusion.api.keywords import KeywordsAPI
from tmdbfusion.api.lists import ListsAPI
from tmdbfusion.api.lists_v4 import ListsV4API
from tmdbfusion.api.movies import MoviesAPI
from tmdbfusion.api.networks import NetworksAPI
from tmdbfusion.api.people import PeopleAPI
from tmdbfusion.api.reviews import ReviewsAPI
from tmdbfusion.api.search import SearchAPI
from tmdbfusion.api.trending import TrendingAPI
from tmdbfusion.api.tv import TVAPI
from tmdbfusion.api.tv_episode_groups import TVEpisodeGroupsAPI
from tmdbfusion.api.tv_episodes import TVEpisodesAPI
from tmdbfusion.api.tv_seasons import TVSeasonsAPI
from tmdbfusion.api.watch_providers import WatchProvidersAPI
from tmdbfusion.core.base import BaseClient
from tmdbfusion.core.cache import Cache
from tmdbfusion.core.http import HttpxSyncTransport
from tmdbfusion.core.http import TransportResponse
from tmdbfusion.features.batch import BatchContext
from tmdbfusion.features.pagination import PaginatedIterator
from tmdbfusion.utils.images import ImagesAPI


T = typing.TypeVar("T")


class TMDBClient(BaseClient):
    """Synchronous TMDB API Client."""

    def __init__(
        self,
        api_key: str,
        *,
        access_token: str | None = None,
        language: str = "en-US",
        timeout: float = 30.0,
        retries: int = 3,
        backoff_factor: float = 0.5,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        cache_ttl: float | None = None,
        log_hook: typing.Callable[[str, str, int], None] | None = None,
    ) -> None:
        super().__init__(api_key, access_token=access_token, language=language)
        self._transport = HttpxSyncTransport(
            timeout=timeout,
            retries=retries,
            backoff_factor=backoff_factor,
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            log_hook=log_hook,
        )
        self._cache = Cache(cache_ttl) if cache_ttl is not None else None
        self._init_namespaces()

    def _init_namespaces(self) -> None:
        """Initialize API namespaces."""
        # V3
        self.account = AccountAPI(self)
        self.authentication = AuthenticationAPI(self)
        self.certifications = CertificationsAPI(self)
        self.changes = ChangesAPI(self)
        self.collections = CollectionsAPI(self)
        self.companies = CompaniesAPI(self)
        self.configuration = ConfigurationAPI(self)
        self.credits = CreditsAPI(self)
        self.discover = DiscoverAPI(self)
        self.find = FindAPI(self)
        self.genres = GenresAPI(self)
        self.guest_session = GuestSessionAPI(self)
        self.keywords = KeywordsAPI(self)
        self.lists = ListsAPI(self)
        self.movies = MoviesAPI(self)
        self.networks = NetworksAPI(self)
        self.people = PeopleAPI(self)
        self.reviews = ReviewsAPI(self)
        self.search = SearchAPI(self)
        self.trending = TrendingAPI(self)
        self.tv = TVAPI(self)
        self.tv_seasons = TVSeasonsAPI(self)
        self.tv_episodes = TVEpisodesAPI(self)
        self.tv_episode_groups = TVEpisodeGroupsAPI(self)
        self.watch_providers = WatchProvidersAPI(self)

        # V4
        self.account_v4 = AccountV4API(self)
        self.auth_v4 = AuthV4API(self)
        self.lists_v4 = ListsV4API(self)

        # Utilities
        self.images = ImagesAPI(self)

    def sync_config(self) -> None:
        """Fetch and set API configuration."""
        config = self.configuration.details()
        self.images.set_configuration(config)

    def batch(self, concurrency: int = 10) -> BatchContext:
        """Create batch context for queued operations.

        Parameters
        ----------
        concurrency : int
            Maximum concurrent operations.

        Returns
        -------
        BatchContext
            Context manager for batching.

        """
        return BatchContext(concurrency=concurrency)

    def get(
        self,
        id_or_external: int | str,
        *,
        append: list[str] | None = None,
    ) -> object:
        """Get media details by ID with auto-detection.

        Parameters
        ----------
        id_or_external : int | str
            TMDB ID or external ID (e.g., "tt0111161").
        append : list[str] | None
            Append to response fields.

        Returns
        -------
        object
            Movie, TV, or Person details.

        """
        append_str = ",".join(append) if append else None

        # Handle external IDs (IMDb, etc.)
        if isinstance(id_or_external, str):
            # Check for explicit prefix
            if ":" in id_or_external:
                prefix, mid = id_or_external.split(":", 1)
                tmdb_id = int(mid)
                if prefix == "movie":
                    return self.movies.details(
                        tmdb_id,
                        append_to_response=append_str,
                    )
                if prefix == "tv":
                    return self.tv.details(
                        tmdb_id,
                        append_to_response=append_str,
                    )
                if prefix == "person":
                    return self.people.details(
                        tmdb_id,
                        append_to_response=append_str,
                    )

            # IMDb ID detection
            if id_or_external.startswith("tt"):
                result = self.find.by_id(
                    id_or_external,
                    external_source="imdb_id",
                )
                if result.movie_results:
                    mid = result.movie_results[0].id
                    return self.movies.details(
                        mid,
                        append_to_response=append_str,
                    )
                if result.tv_results:
                    tid = result.tv_results[0].id
                    return self.tv.details(
                        tid,
                        append_to_response=append_str,
                    )

            msg = f"Could not resolve: {id_or_external}"
            raise ValueError(msg)

        # Direct TMDB ID - assume movie
        return self.movies.details(
            id_or_external,
            append_to_response=append_str,
        )

    def paginate(
        self,
        method: typing.Callable[..., typing.Any],
        *,
        map_response: typing.Callable[[typing.Any], list[typing.Any]] | None = None,
        **kwargs: typing.Any,
    ) -> typing.Iterator[typing.Any]:
        """Paginate through API results.

        Parameters
        ----------
        method : typing.Callable[..., typing.Any]
            The API method to call (e.g., client.movies.popular).
        map_response : typing.Callable[[typing.Any], list[typing.Any]] | None
            Optional function to extract results list from response.
            Defaults to extracting 'results' attribute or key.
        **kwargs : typing.Any
            Arguments passed to the API method.

        Returns
        -------
        typing.Iterator[typing.Any]
            Result iterator.

        """
        if map_response is None:

            def _default_map(response: typing.Any) -> list[typing.Any]:
                if hasattr(response, "results"):
                    return list(response.results)  # type: ignore[no-any-return]
                if isinstance(response, dict):
                    return list(response.get("results", []))  # type: ignore[no-any-return]
                return []

            map_response = _default_map

        return PaginatedIterator(method, map_response=map_response, **kwargs)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, typing.Any] | None = None,
        headers: dict[str, str] | None = None,
        body: object | None = None,
        version: int = 3,
        include_language: bool = True,
    ) -> TransportResponse:
        """Make an API request."""
        url = self._build_url(path, version=version)
        headers = self._build_headers(use_bearer=version == 4)
        if headers:
            headers.update(headers or {})

        params = self._build_params(params, include_language=include_language)

        # Check cache for GET requests
        cache_key = None
        if self._cache and method == "GET":
            # Create a stable key from URL and params
            key_parts = [url]
            if params:
                for k, v in sorted(params.items()):
                    key_parts.append(f"{k}={v}")
            cache_key = "&".join(key_parts)

            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached  # type: ignore[return-value]

        content = msgspec.json.encode(body) if body is not None else None

        response = self._transport.request(
            method,
            url,
            params=params,
            headers=headers,
            content=content,
        )

        self._update_rate_limits(response)

        # Cache successful GET responses
        if (self._cache and method == "GET" and 200 <= response.status_code < 300) and cache_key:
            self._cache.set(cache_key, response)

        return response

    def _get(
        self,
        path: str,
        response_type: type[T],
        *,
        params: dict[str, typing.Any] | None = None,
        version: int = 3,
        include_language: bool = True,
    ) -> T:
        """Make a GET request."""
        response = self._request(
            "GET",
            path,
            params=params,
            version=version,
            include_language=include_language,
        )
        return self._decode(response, response_type)

    def _post(
        self,
        path: str,
        response_type: type[T],
        *,
        body: object | None = None,
        params: dict[str, typing.Any] | None = None,
        version: int = 3,
    ) -> T:
        """Make a POST request."""
        response = self._request(
            "POST",
            path,
            params=params,
            body=body,
            version=version,
            include_language=False,
        )
        return self._decode(response, response_type)

    def _delete(
        self,
        path: str,
        response_type: type[T],
        *,
        body: object | None = None,
        params: dict[str, typing.Any] | None = None,
        version: int = 3,
    ) -> T:
        """Make a DELETE request."""
        response = self._request(
            "DELETE",
            path,
            params=params,
            body=body,
            version=version,
            include_language=False,
        )
        return self._decode(response, response_type)

    def _put(
        self,
        path: str,
        response_type: type[T],
        *,
        body: object | None = None,
        params: dict[str, typing.Any] | None = None,
        version: int = 3,
    ) -> T:
        """Make a PUT request."""
        response = self._request(
            "PUT",
            path,
            params=params,
            body=body,
            version=version,
            include_language=False,
        )
        return self._decode(response, response_type)

    def close(self) -> None:
        """Close the client."""
        self._transport.close()

    def __enter__(self) -> typing.Self:
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.close()
