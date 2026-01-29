# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Unit tests for batch module."""

import pytest

from tmdbfusion.features.batch import AsyncBatchContext
from tmdbfusion.features.batch import BatchContext
from tmdbfusion.features.batch import BatchResult


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_empty_result(self) -> None:
        """Test empty result properties."""
        result = BatchResult()
        assert result.success_count == 0
        assert result.failure_count == 0
        assert result.all_succeeded is True

    def test_with_results(self) -> None:
        """Test result with successes."""
        result = BatchResult(results=["a", "b", None], errors=[(2, ValueError())])
        assert result.success_count == 2
        assert result.failure_count == 1
        assert result.all_succeeded is False


class TestBatchContext:
    """Tests for synchronous BatchContext."""

    def test_queue_and_execute(self) -> None:
        """Test queuing and executing operations."""

        def fetch(x: int) -> int:
            return x * 2

        with BatchContext() as batch:
            batch.queue(fetch, 1)
            batch.queue(fetch, 2)
            batch.queue(fetch, 3)

        assert batch.result.results == [2, 4, 6]
        assert batch.result.all_succeeded is True

    def test_handles_errors(self) -> None:
        """Test error handling in batch."""

        def error_func(x: int) -> int:
            if x == 2:
                msg = "fail"
                raise ValueError(msg)
            return x

        with BatchContext() as batch:
            batch.queue(error_func, 1)
            batch.queue(error_func, 2)
            batch.queue(error_func, 3)

        results = batch.result.results
        assert results[0] == 1
        assert results[1] is None
        assert results[2] == 3
        assert batch.result.failure_count == 1

    def test_exception_suppression(self) -> None:
        """Test that batch execution is skipped on exceptions."""

        def fetch(x: int) -> int:
            return x

        try:
            with BatchContext() as batch:
                batch.queue(fetch, 1)
                msg = "outer error"
                raise RuntimeError(msg)
        except RuntimeError:
            pass

        # Batch should not have executed
        assert batch.result.results == []


@pytest.mark.asyncio
class TestAsyncBatchContext:
    """Tests for asynchronous AsyncBatchContext."""

    async def test_async_queue_and_execute(self) -> None:
        """Test async queuing and execution."""

        async def fetch(x: int) -> int:
            return x * 2

        async with AsyncBatchContext(concurrency=2) as batch:
            batch.queue(fetch, 1)
            batch.queue(fetch, 2)

        assert sorted(batch.result.results) == [2, 4]

    async def test_async_handles_errors(self) -> None:
        """Test async error handling."""

        async def error_func(x: int) -> int:
            if x == 2:
                msg = "fail"
                raise ValueError(msg)
            return x

        async with AsyncBatchContext() as batch:
            batch.queue(error_func, 1)
            batch.queue(error_func, 2)

        # One success, one failure
        assert batch.result.failure_count == 1
        assert batch.result.success_count == 1
