# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Dataset Builder.

Build ML-ready datasets from TMDB data with field extraction
and optional pandas/polars integration.
"""

from __future__ import annotations

import pathlib
import typing
from dataclasses import dataclass
from dataclasses import field


if typing.TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterable

    from tmdbfusion.core.sync_client import TMDBClient

T = typing.TypeVar("T")


def _extract_field(obj: object, path: str) -> object:
    """Extract nested field using dot notation.

    Parameters
    ----------
    obj : object
        Object to extract from.
    path : str
        Dot-separated path (e.g., "genres.0.name").

    Returns
    -------
    object
        Extracted value or None.

    """
    parts = path.split(".")
    current: object = obj

    for part in parts:
        if current is None:
            return None

        # Handle list indexing
        if part.isdigit():
            idx = int(part)
            if isinstance(current, list) and idx < len(current):
                current = current[idx]
            else:
                return None
        # Handle dict
        elif isinstance(current, dict):
            current = current.get(part)
        # Handle attribute
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return None

    return current


def _flatten_list_field(obj: object, path: str) -> str:
    """Extract list field and join values.

    Parameters
    ----------
    obj : object
        Object to extract from.
    path : str
        Path ending with list (e.g., "genres.name").

    Returns
    -------
    str
        Comma-separated values.

    """
    parts = path.split(".")
    if len(parts) < 2:
        return ""

    list_path = ".".join(parts[:-1])
    item_attr = parts[-1]

    list_val = _extract_field(obj, list_path)
    if not isinstance(list_val, list):
        return ""

    values = []
    for item in list_val:
        if hasattr(item, item_attr):
            val = getattr(item, item_attr)
            if val is not None:
                values.append(str(val))
        elif isinstance(item, dict) and item_attr in item:
            val = item[item_attr]
            if val is not None:
                values.append(str(val))

    return ",".join(values)


@dataclass
class DatasetRow:
    """Single row of extracted data.

    Attributes
    ----------
    data : dict[str, object]
        Extracted field values.

    """

    data: dict[str, object] = field(default_factory=dict)

    def __getitem__(self, key: str) -> object:
        """Get field value.

        Parameters
        ----------
        key : str
            Field name.

        Returns
        -------
        object
            Field value.

        """
        return self.data.get(key)


@dataclass
class Dataset:
    """Collection of extracted data rows.

    Attributes
    ----------
    rows : list[DatasetRow]
        Data rows.
    columns : list[str]
        Column names.

    """

    rows: list[DatasetRow] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)

    def __len__(self) -> int:
        """Get row count.

        Returns
        -------
        int
            Number of rows.

        """
        return len(self.rows)

    def __iter__(self) -> typing.Iterator[DatasetRow]:
        """Iterate over rows.

        Yields
        ------
        DatasetRow
            Each row.

        """
        yield from self.rows

    def to_dicts(self) -> list[dict[str, object]]:
        """Convert to list of dictionaries.

        Returns
        -------
        list[dict[str, object]]
            List of row dictionaries.

        """
        return [row.data for row in self.rows]

    def to_csv(self, path: str) -> None:
        """Export to CSV file.

        Parameters
        ----------
        path : str
            Output file path.

        """
        import csv

        with pathlib.Path(path).open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writeheader()
            for row in self.rows:
                writer.writerow({col: row.data.get(col, "") for col in self.columns})


class DatasetBuilder:
    """Build datasets from TMDB data.

    Examples
    --------
    >>> builder = DatasetBuilder(client)
    >>> dataset = builder.from_discover(
    ...     client.discover.movie,
    ...     fields=["id", "title", "genres.name"],
    ...     max_items=100,
    ... )

    Parameters
    ----------
    client : TMDBClient
        TMDB client instance.

    """

    def __init__(self, client: TMDBClient) -> None:
        self._client = client

    def from_ids(
        self,
        ids: Iterable[int],
        fetcher: Callable[[int], T],
        fields: list[str],
    ) -> Dataset:
        """Build dataset from list of IDs.

        Parameters
        ----------
        ids : Iterable[int]
            IDs to fetch.
        fetcher : Callable[[int], T]
            Function to fetch details (e.g., client.movies.details).
        fields : list[str]
            Fields to extract (supports dot notation).

        Returns
        -------
        Dataset
            Extracted dataset.

        """
        rows: list[DatasetRow] = []

        for item_id in ids:
            try:
                item = fetcher(item_id)
                row_data = self._extract_fields(item, fields)
                rows.append(DatasetRow(data=row_data))
            except Exception:  # noqa: BLE001
                continue

        return Dataset(rows=rows, columns=fields)

    def from_discover(
        self,
        discover_method: Callable[..., object],
        fields: list[str],
        *,
        max_items: int = 100,
        max_pages: int = 10,
        **discover_params: object,
    ) -> Dataset:
        """Build dataset from discover results.

        Parameters
        ----------
        discover_method : Callable[..., object]
            Discover method (e.g., client.discover.movie).
        fields : list[str]
            Fields to extract.
        max_items : int
            Maximum items to collect.
        max_pages : int
            Maximum pages to fetch.
        **discover_params : object
            Parameters for discover method.

        Returns
        -------
        Dataset
            Extracted dataset.

        """
        rows: list[DatasetRow] = []

        for page in range(1, max_pages + 1):
            if len(rows) >= max_items:
                break

            response = discover_method(page=page, **discover_params)
            results = getattr(response, "results", [])

            if not results:
                break

            for item in results:
                if len(rows) >= max_items:
                    break
                row_data = self._extract_fields(item, fields)
                rows.append(DatasetRow(data=row_data))

        return Dataset(rows=rows, columns=fields)

    def from_search(
        self,
        query: str,
        search_method: Callable[..., object],
        fields: list[str],
        *,
        max_items: int = 100,
    ) -> Dataset:
        """Build dataset from search results.

        Parameters
        ----------
        query : str
            Search query.
        search_method : Callable[..., object]
            Search method (e.g., client.search.movie).
        fields : list[str]
            Fields to extract.
        max_items : int
            Maximum items.

        Returns
        -------
        Dataset
            Extracted dataset.

        """
        rows: list[DatasetRow] = []
        page = 1

        while len(rows) < max_items:
            response = search_method(query=query, page=page)
            results = getattr(response, "results", [])

            if not results:
                break

            for item in results:
                if len(rows) >= max_items:
                    break
                row_data = self._extract_fields(item, fields)
                rows.append(DatasetRow(data=row_data))

            page += 1
            total = getattr(response, "total_pages", 1)
            if page > total:
                break

        return Dataset(rows=rows, columns=fields)

    def _extract_fields(
        self,
        obj: object,
        fields: list[str],
    ) -> dict[str, object]:
        """Extract specified fields from object.

        Parameters
        ----------
        obj : object
            Object to extract from.
        fields : list[str]
            Field paths to extract.

        Returns
        -------
        dict[str, object]
            Extracted values.

        """
        data: dict[str, object] = {}

        for field_path in fields:
            # Check if this is a list flatten operation
            if "." in field_path:
                parts = field_path.split(".")
                list_path = ".".join(parts[:-1])
                list_val = _extract_field(obj, list_path)
                if isinstance(list_val, list):
                    data[field_path] = _flatten_list_field(obj, field_path)
                else:
                    data[field_path] = _extract_field(obj, field_path)
            else:
                data[field_path] = _extract_field(obj, field_path)

        return data
