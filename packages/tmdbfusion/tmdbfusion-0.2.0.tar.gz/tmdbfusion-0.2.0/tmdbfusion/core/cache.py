# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Response caching utilities."""

from __future__ import annotations

import time
import typing
from collections import OrderedDict
from dataclasses import dataclass


T = typing.TypeVar("T")


@dataclass
class CacheStats:
    """Cache statistics.

    Attributes
    ----------
    hits : int
        Number of cache hits.
    misses : int
        Number of cache misses.
    evictions : int
        Number of LRU evictions.
    expirations : int
        Number of TTL expirations.

    """

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0

    @property
    def hit_rate(self) -> float:
        """Get cache hit rate.

        Returns
        -------
        float
            Hit rate as percentage (0-100).

        """
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100

    def reset(self) -> None:
        """Reset all statistics."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0


@dataclass
class CacheEntry:
    """Cache entry with value and expiry.

    Attributes
    ----------
    value : typing.Any
        Cached value.
    expiry : float
        Expiration timestamp.

    """

    value: typing.Any
    expiry: float


class Cache:
    """In-memory cache with TTL, LRU eviction, and statistics.

    Examples
    --------
    >>> cache = Cache(default_ttl=300, max_size=1000)
    >>> cache.set("key", data)
    >>> cache.set("key2", data2, ttl=60)  # Custom TTL
    >>> value = cache.get("key")
    >>> print(cache.stats.hit_rate)

    Parameters
    ----------
    default_ttl : float
        Default time-to-live in seconds.
    max_size : int | None
        Maximum cache size. None for unlimited.
    ttl_overrides : dict[str, float] | None
        Per-key pattern TTL overrides.

    """

    def __init__(
        self,
        default_ttl: float = 300.0,
        max_size: int | None = None,
        ttl_overrides: dict[str, float] | None = None,
    ) -> None:
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._ttl_overrides = ttl_overrides or {}
        self._data: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats()

    @property
    def stats(self) -> CacheStats:
        """Get cache statistics.

        Returns
        -------
        CacheStats
            Current cache statistics.

        """
        return self._stats

    @property
    def size(self) -> int:
        """Get current cache size.

        Returns
        -------
        int
            Number of items in cache.

        """
        return len(self._data)

    def _get_ttl_for_key(self, key: str) -> float:
        """Get TTL for a specific key.

        Parameters
        ----------
        key : str
            Cache key.

        Returns
        -------
        float
            TTL in seconds.

        """
        # Check for pattern matches
        for pattern, ttl in self._ttl_overrides.items():
            if key.startswith(pattern):
                return ttl
        return self._default_ttl

    def _evict_if_needed(self) -> None:
        """Evict oldest entries if cache is full."""
        if self._max_size is None:
            return

        while len(self._data) >= self._max_size:
            # Remove oldest (first) item
            self._data.popitem(last=False)
            self._stats.evictions += 1

    def get(self, key: str) -> typing.Any | None:
        """Get item from cache.

        Parameters
        ----------
        key : str
            Cache key.

        Returns
        -------
        typing.Any | None
            Cached value or None if not found/expired.

        """
        if key not in self._data:
            self._stats.misses += 1
            return None

        entry = self._data[key]
        if time.time() > entry.expiry:
            del self._data[key]
            self._stats.expirations += 1
            self._stats.misses += 1
            return None

        # Move to end (most recently used)
        self._data.move_to_end(key)
        self._stats.hits += 1
        return entry.value

    def set(
        self,
        key: str,
        value: typing.Any,
        ttl: float | None = None,
    ) -> None:
        """Set item in cache.

        Parameters
        ----------
        key : str
            Cache key.
        value : typing.Any
            Value to cache.
        ttl : float | None
            Optional TTL override for this key.

        """
        # Remove existing to update position
        if key in self._data:
            del self._data[key]
        else:
            self._evict_if_needed()

        actual_ttl = ttl if ttl is not None else self._get_ttl_for_key(key)
        expiry = time.time() + actual_ttl
        self._data[key] = CacheEntry(value=value, expiry=expiry)

    def delete(self, key: str) -> bool:
        """Delete item from cache.

        Parameters
        ----------
        key : str
            Cache key.

        Returns
        -------
        bool
            True if item was deleted, False if not found.

        """
        if key in self._data:
            del self._data[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._data.clear()

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns
        -------
        int
            Number of entries removed.

        """
        now = time.time()
        expired = [k for k, v in self._data.items() if now > v.expiry]
        for key in expired:
            del self._data[key]
            self._stats.expirations += 1
        return len(expired)

    def contains(self, key: str) -> bool:
        """Check if key exists and is not expired.

        Parameters
        ----------
        key : str
            Cache key.

        Returns
        -------
        bool
            True if key exists and is valid.

        """
        if key not in self._data:
            return False
        return not time.time() > self._data[key].expiry

    def set_ttl_override(self, pattern: str, ttl: float) -> None:
        """Set TTL override for key pattern.

        Parameters
        ----------
        pattern : str
            Key prefix pattern.
        ttl : float
            TTL in seconds for matching keys.

        """
        self._ttl_overrides[pattern] = ttl
