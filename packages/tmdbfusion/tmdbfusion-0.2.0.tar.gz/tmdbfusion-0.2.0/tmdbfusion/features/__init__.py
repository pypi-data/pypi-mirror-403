# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
High-level features.

Batch processing, bulk fetching, pagination, and rate limiting.
"""

from tmdbfusion.features.batch import AsyncBatchContext
from tmdbfusion.features.batch import BatchContext
from tmdbfusion.features.batch import BatchResult
from tmdbfusion.features.bulk import BulkFetcher
from tmdbfusion.features.bulk import BulkResult
from tmdbfusion.features.bulk import bulk_fetch
from tmdbfusion.features.bulk import bulk_fetch_async
from tmdbfusion.features.pagination import AsyncPaginatedIterator
from tmdbfusion.features.pagination import PaginatedIterator
from tmdbfusion.features.rate_limit import RateLimitHandler
from tmdbfusion.features.rate_limit import RateLimitStats
from tmdbfusion.features.rate_limit import with_rate_limit
from tmdbfusion.features.rate_limit import with_rate_limit_async


__all__ = [
    # Batch
    "AsyncBatchContext",
    # Pagination
    "AsyncPaginatedIterator",
    "BatchContext",
    "BatchResult",
    "BulkFetcher",
    "BulkResult",
    "PaginatedIterator",
    # Rate Limit
    "RateLimitHandler",
    "RateLimitStats",
    # Bulk
    "bulk_fetch",
    "bulk_fetch_async",
    "with_rate_limit",
    "with_rate_limit_async",
]
