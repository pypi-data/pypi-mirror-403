"""Unit tests for pagination logic."""

import pytest
import collections
from unittest import mock
from tmdbfusion.features.pagination import PaginatedIterator, AsyncPaginatedIterator


class MockResponse:
    def __init__(self, data, total_pages=1):
        self.results = data
        self.total_pages = total_pages


class MockDictResponse:
    def __init__(self, data):
        self._data = data


class TestPaginatedIterator:
    def test_iteration(self):
        """Test standard iteration over multiple pages."""
        # Setup mock method calls
        mock_method = mock.Mock()
        mock_method.side_effect = [
            MockResponse(["a", "b"], total_pages=2),  # Page 1
            MockResponse(["c", "d"], total_pages=2),  # Page 2
        ]

        def mapper(response):
            return response.results

        iterator = PaginatedIterator(mock_method, map_response=mapper)

        results = list(iterator)

        assert results == ["a", "b", "c", "d"]
        assert mock_method.call_count == 2
        mock_method.assert_any_call(page=1)
        mock_method.assert_any_call(page=2)

    def test_stop_early(self):
        """Test iteration stops if no results returned even if total_pages says otherwise."""
        mock_method = mock.Mock()
        # Page 1 returns valid, Page 2 returns empty list (unexpected but possible)
        mock_method.side_effect = [
            MockResponse(["a"], total_pages=3),
            MockResponse([], total_pages=3),
        ]

        iterator = PaginatedIterator(mock_method, map_response=lambda r: r.results)
        results = list(iterator)

        assert results == ["a"]
        # Logic dictates it fetches page 2, sees empty results, and stops
        assert mock_method.call_count == 2

    def test_empty_start(self):
        """Test iterator yields nothing if first page is empty."""
        mock_method = mock.Mock(return_value=MockResponse([], total_pages=1))
        iterator = PaginatedIterator(mock_method, map_response=lambda r: r.results)
        assert list(iterator) == []

    def test_dict_response_fallback(self):
        """Test dict response handling for total_pages."""
        mock_method = mock.Mock(return_value={"total_pages": 1, "results": ["a"]})
        iterator = PaginatedIterator(mock_method, map_response=lambda r: r["results"])
        assert list(iterator) == ["a"]

    def test_unknown_response_type_fallback(self):
        """Test unknown object response handling (default to 1 page)."""
        # An object with no total_pages attr and not a dict
        mock_method = mock.Mock(return_value=object())
        # Mapper just returns a list
        iterator = PaginatedIterator(mock_method, map_response=lambda r: ["a"])
        assert list(iterator) == ["a"]

    def test_stop_iteration_buffer_empty_check(self):
        """Hit the final check 'if not self._buffer: raise StopIteration'."""
        # This is tricky because the loop naturally exits, but we can force it
        # by having a mapper return empty list on first call
        mock_method = mock.Mock(return_value=MockResponse([], total_pages=1))
        iterator = PaginatedIterator(mock_method, map_response=lambda r: [])
        with pytest.raises(StopIteration):
            next(iterator)


@pytest.mark.asyncio
class TestAsyncPaginatedIterator:
    async def test_async_iteration(self):
        """Test async iteration."""
        mock_method = mock.AsyncMock()
        mock_method.side_effect = [
            MockResponse([1, 2], total_pages=2),
            MockResponse([3, 4], total_pages=2),
        ]

        iterator = AsyncPaginatedIterator(mock_method, map_response=lambda r: r.results)

        results = []
        async for item in iterator:
            results.append(item)

        assert results == [1, 2, 3, 4]
        assert mock_method.call_count == 2

    async def test_async_dict_response(self):
        """Test async dict response handling."""
        mock_method = mock.AsyncMock(return_value={"total_pages": 1, "results": [1]})
        iterator = AsyncPaginatedIterator(
            mock_method, map_response=lambda r: r["results"]
        )
        results = []
        async for item in iterator:
            results.append(item)
        assert results == [1]

    async def test_async_unknown_response(self):
        """Test async unknown response type."""
        mock_method = mock.AsyncMock(return_value=object())
        iterator = AsyncPaginatedIterator(mock_method, map_response=lambda r: [1])
        results = []
        async for item in iterator:
            results.append(item)
        assert results == [1]

    async def test_async_stop_iteration_buffer_empty(self):
        mock_method = mock.AsyncMock(return_value=MockResponse([], total_pages=1))
        iterator = AsyncPaginatedIterator(mock_method, map_response=lambda r: [])
        with pytest.raises(StopAsyncIteration):
            await iterator.__anext__()
