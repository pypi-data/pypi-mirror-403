# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""Unit tests for dataset module."""

from tmdbfusion.data.dataset import Dataset
from tmdbfusion.data.dataset import DatasetRow


class TestDatasetRow:
    """Tests for DatasetRow."""

    def test_getitem(self) -> None:
        """Test dict-like access."""
        row = DatasetRow(data={"id": 1, "title": "Test"})
        assert row["id"] == 1
        assert row["title"] == "Test"
        assert row["missing"] is None


class TestDataset:
    """Tests for Dataset."""

    def test_len(self) -> None:
        """Test length."""
        rows = [DatasetRow({"id": 1}), DatasetRow({"id": 2})]
        dataset = Dataset(rows=rows, columns=["id"])
        assert len(dataset) == 2

    def test_iter(self) -> None:
        """Test iteration."""
        rows = [DatasetRow({"id": 1}), DatasetRow({"id": 2})]
        dataset = Dataset(rows=rows, columns=["id"])
        ids = [row["id"] for row in dataset]
        assert ids == [1, 2]

    def test_to_dicts(self) -> None:
        """Test conversion to dicts."""
        rows = [DatasetRow({"id": 1, "name": "a"})]
        dataset = Dataset(rows=rows, columns=["id", "name"])
        dicts = dataset.to_dicts()
        assert dicts == [{"id": 1, "name": "a"}]
