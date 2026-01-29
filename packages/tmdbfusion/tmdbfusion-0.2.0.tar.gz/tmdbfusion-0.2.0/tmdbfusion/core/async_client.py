# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Asynchronous TMDB Client."""

from __future__ import annotations

import typing

from tmdbfusion.api.account import AsyncAccountAPI
from tmdbfusion.api.account_v4 import AsyncAccountV4API
from tmdbfusion.api.auth_v4 import AsyncAuthV4API
from tmdbfusion.api.authentication import AsyncAuthenticationAPI
from tmdbfusion.api.certifications import AsyncCertificationsAPI
from tmdbfusion.api.changes import AsyncChangesAPI
from tmdbfusion.api.collections import AsyncCollectionsAPI
from tmdbfusion.api.companies import AsyncCompaniesAPI
from tmdbfusion.api.configuration import AsyncConfigurationAPI
from tmdbfusion.api.credits import AsyncCreditsAPI
from tmdbfusion.api.discover import AsyncDiscoverAPI
from tmdbfusion.api.find import AsyncFindAPI
from tmdbfusion.api.genres import AsyncGenresAPI
from tmdbfusion.api.guest_session import AsyncGuestSessionAPI
from tmdbfusion.api.keywords import AsyncKeywordsAPI
from tmdbfusion.api.lists import AsyncListsAPI
from tmdbfusion.api.lists_v4 import AsyncListsV4API
from tmdbfusion.api.movies import AsyncMoviesAPI
from tmdbfusion.api.networks import AsyncNetworksAPI
from tmdbfusion.api.people import AsyncPeopleAPI
from tmdbfusion.api.reviews import AsyncReviewsAPI
from tmdbfusion.api.search import AsyncSearchAPI
from tmdbfusion.api.trending import AsyncTrendingAPI
from tmdbfusion.api.tv import AsyncTVAPI
from tmdbfusion.api.tv_episode_groups import AsyncTVEpisodeGroupsAPI
from tmdbfusion.api.tv_episodes import AsyncTVEpisodesAPI
from tmdbfusion.api.tv_seasons import AsyncTVSeasonsAPI
from tmdbfusion.api.watch_providers import AsyncWatchProvidersAPI
from tmdbfusion.core.base import BaseClient
from tmdbfusion.core.cache import Cache
from tmdbfusion.core.http import HttpxAsyncTransport
from tmdbfusion.core.http import TransportResponse
from tmdbfusion.features.batch import AsyncBatchContext
from tmdbfusion.features.pagination import AsyncPaginatedIterator
from tmdbfusion.utils.images import ImagesAPI


T = typing.TypeVar("T")


class AsyncTMDBClient(BaseClient):
    """Asynchronous TMDB API Client."""

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
        self._transport = HttpxAsyncTransport(
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
        self.account = AsyncAccountAPI(self)
        self.authentication = AsyncAuthenticationAPI(self)
        self.certifications = AsyncCertificationsAPI(self)
        self.changes = AsyncChangesAPI(self)
        self.collections = AsyncCollectionsAPI(self)
        self.companies = AsyncCompaniesAPI(self)
        self.configuration = AsyncConfigurationAPI(self)
        self.credits = AsyncCreditsAPI(self)
        self.discover = AsyncDiscoverAPI(self)
        self.find = AsyncFindAPI(self)
        self.genres = AsyncGenresAPI(self)
        self.guest_session = AsyncGuestSessionAPI(self)
        self.keywords = AsyncKeywordsAPI(self)
        self.lists = AsyncListsAPI(self)
        self.movies = AsyncMoviesAPI(self)
        self.networks = AsyncNetworksAPI(self)
        self.people = AsyncPeopleAPI(self)
        self.reviews = AsyncReviewsAPI(self)
        self.search = AsyncSearchAPI(self)
        self.trending = AsyncTrendingAPI(self)
        self.tv = AsyncTVAPI(self)
        self.tv_seasons = AsyncTVSeasonsAPI(self)
        self.tv_episodes = AsyncTVEpisodesAPI(self)
        self.tv_episode_groups = AsyncTVEpisodeGroupsAPI(self)
        self.watch_providers = AsyncWatchProvidersAPI(self)

        # V4
        self.account_v4 = AsyncAccountV4API(self)
        self.auth_v4 = AsyncAuthV4API(self)
        self.lists_v4 = AsyncListsV4API(self)

        # Utilities
        self.images = ImagesAPI(self)

    async def sync_config(self) -> None:
        """Fetch and set API configuration."""
        config = await self.configuration.details()
        self.images.set_configuration(config)

    def batch(self, concurrency: int = 10) -> AsyncBatchContext:
        """Create async batch context for queued operations.

        Parameters
        ----------
        concurrency : int
            Maximum concurrent operations.

        Returns
        -------
        AsyncBatchContext
            Async context manager for batching.

        """
        return AsyncBatchContext(concurrency=concurrency)

    async def get(
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

        # Handle external IDs
        if isinstance(id_or_external, str):
            if ":" in id_or_external:
                prefix, mid = id_or_external.split(":", 1)
                tmdb_id = int(mid)
                if prefix == "movie":
                    return await self.movies.details(
                        tmdb_id,
                        append_to_response=append_str,
                    )
                if prefix == "tv":
                    return await self.tv.details(
                        tmdb_id,
                        append_to_response=append_str,
                    )
                if prefix == "person":
                    return await self.people.details(
                        tmdb_id,
                        append_to_response=append_str,
                    )

            if id_or_external.startswith("tt"):
                result = await self.find.by_id(
                    id_or_external,
                    external_source="imdb_id",
                )
                if result.movie_results:
                    mid = result.movie_results[0].id
                    return await self.movies.details(
                        mid,
                        append_to_response=append_str,
                    )
                if result.tv_results:
                    tid = result.tv_results[0].id
                    return await self.tv.details(
                        tid,
                        append_to_response=append_str,
                    )

            msg = f"Could not resolve: {id_or_external}"
            raise ValueError(msg)

        return await self.movies.details(
            id_or_external,
            append_to_response=append_str,
        )

    def paginate(
        self,
        method: typing.Callable[..., typing.Awaitable[typing.Any]],
        *,
        map_response: typing.Callable[[typing.Any], list[typing.Any]] | None = None,
        **kwargs: typing.Any,
    ) -> typing.AsyncIterator[typing.Any]:
        """Paginate through API results.

        Parameters
        ----------
        method : typing.Callable[..., typing.Awaitable[typing.Any]]
            The API method to call (e.g., client.movies.popular).
        map_response : typing.Callable[[typing.Any], list[typing.Any]] | None
            Optional function to extract results list from response.
            Defaults to extracting 'results' attribute or key.
        **kwargs : typing.Any
            Arguments passed to the API method.

        Returns
        -------
        typing.AsyncIterator[typing.Any]
            Result iterator.

        """
        if map_response is None:

            def _default_map(response: typing.Any) -> list[typing.Any]:
                if hasattr(response, "results"):
                    if typing.TYPE_CHECKING:
                        return list(response.results)  # type: ignore[attr-defined]
                    return list(response.results)
                if isinstance(response, dict):
                    return list(response.get("results", []))  # type: ignore[no-any-return]
                return []

            map_response = _default_map

        return AsyncPaginatedIterator(
            method,
            map_response=map_response,
            **kwargs,
        )

    async def batch_get(
        self,
        methods: typing.Iterable[typing.Awaitable[T]],
    ) -> list[T]:
        """Execute multiple API methods concurrently.

        Parameters
        ----------
        methods : typing.Iterable[typing.Awaitable[T]]
            List of API calls to execute.

        Returns
        -------
        list[T]
            List of results in the same order.

        """
        import asyncio

        return list(await asyncio.gather(*methods))

    async def _request(
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
        import msgspec

        url = self._build_url(path, version=version)
        headers = self._build_headers(use_bearer=version == 4)
        if headers:
            headers.update(headers or {})

        params = self._build_params(params, include_language=include_language)

        # Check cache for GET requests
        cache_key = None
        if self._cache and method == "GET":
            key_parts = [url]
            if params:
                for k, v in sorted(params.items()):
                    key_parts.append(f"{k}={v}")
            cache_key = "&".join(key_parts)

            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached  # type: ignore[return-value]

        content = msgspec.json.encode(body) if body is not None else None

        response = await self._transport.request(
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

    async def _get(
        self,
        path: str,
        response_type: type[T],
        *,
        params: dict[str, typing.Any] | None = None,
        version: int = 3,
        include_language: bool = True,
    ) -> T:
        """Make a GET request."""
        response = await self._request(
            "GET",
            path,
            params=params,
            version=version,
            include_language=include_language,
        )
        return self._decode(response, response_type)

    async def _post(
        self,
        path: str,
        response_type: type[T],
        *,
        body: object | None = None,
        params: dict[str, typing.Any] | None = None,
        version: int = 3,
    ) -> T:
        """Make a POST request."""
        response = await self._request(
            "POST",
            path,
            params=params,
            body=body,
            version=version,
            include_language=False,
        )
        return self._decode(response, response_type)

    async def _delete(
        self,
        path: str,
        response_type: type[T],
        *,
        body: object | None = None,
        params: dict[str, typing.Any] | None = None,
        version: int = 3,
    ) -> T:
        """Make a DELETE request."""
        response = await self._request(
            "DELETE",
            path,
            params=params,
            body=body,
            version=version,
            include_language=False,
        )
        return self._decode(response, response_type)

    async def _put(
        self,
        path: str,
        response_type: type[T],
        *,
        body: object | None = None,
        params: dict[str, typing.Any] | None = None,
        version: int = 3,
    ) -> T:
        """Make a PUT request."""
        response = await self._request(
            "PUT",
            path,
            params=params,
            body=body,
            version=version,
            include_language=False,
        )
        return self._decode(response, response_type)

    async def close(self) -> None:
        """Close the client."""
        await self._transport.close()

    async def __aenter__(self) -> typing.Self:
        """Context manager entry."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Context manager exit."""
        await self.close()
