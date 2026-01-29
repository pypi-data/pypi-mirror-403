# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Unit tests for download module."""

from pathlib import Path

from tmdbfusion.data.download import BulkDownloadResult
from tmdbfusion.data.download import DownloadResult


class TestDownloadResult:
    """Tests for DownloadResult."""

    def test_success_result(self) -> None:
        """Test successful download result."""
        result = DownloadResult(path=Path("/tmp/test.jpg"), success=True)
        assert result.success is True
        assert result.error is None

    def test_failed_result(self) -> None:
        """Test failed download result."""
        result = DownloadResult(
            path=Path("/tmp/test.jpg"),
            success=False,
            error="Network error",
        )
        assert result.success is False
        assert result.error == "Network error"


class TestBulkDownloadResult:
    """Tests for BulkDownloadResult."""

    def test_empty_result(self) -> None:
        """Test empty bulk result."""
        result = BulkDownloadResult()
        assert result.success_count == 0
        assert result.failure_count == 0

    def test_mixed_results(self) -> None:
        """Test mixed success/failure."""
        success = DownloadResult(Path("/a.jpg"), True)
        failure = DownloadResult(Path("/b.jpg"), False, "error")
        result = BulkDownloadResult(successful=[success], failed=[failure])
        assert result.success_count == 1
        assert result.failure_count == 1
