# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Unit tests for sync module."""

from datetime import date

from tmdbfusion.data.sync import DiffResult
from tmdbfusion.data.sync import ExportItem


class TestExportItem:
    """Tests for ExportItem."""

    def test_name_from_title(self) -> None:
        """Test name property with title."""
        item = ExportItem(id=1, original_title="Fight Club")
        assert item.name == "Fight Club"

    def test_name_from_name(self) -> None:
        """Test name property with name."""
        item = ExportItem(id=1, original_name="Breaking Bad")
        assert item.name == "Breaking Bad"

    def test_name_empty(self) -> None:
        """Test name property when neither set."""
        item = ExportItem(id=1)
        assert item.name == ""


class TestDiffResult:
    """Tests for DiffResult."""

    def test_empty_diff(self) -> None:
        """Test empty diff."""
        diff = DiffResult()
        assert diff.new_count == 0
        assert diff.removed_count == 0

    def test_with_changes(self) -> None:
        """Test diff with changes."""
        diff = DiffResult(new_ids={1, 2, 3}, removed_ids={4})
        assert diff.new_count == 3
        assert diff.removed_count == 1
