# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Export Utilities.

Export TMDB API responses to various formats (JSON, CSV).
"""

from __future__ import annotations

import csv
import io
import typing
from dataclasses import dataclass
from pathlib import Path

import msgspec


T = typing.TypeVar("T")


@dataclass
class ExportConfig:
    """Configuration for exports.

    Attributes
    ----------
    include_fields : list[str] | None
        Fields to include (None = all fields).
    exclude_fields : list[str] | None
        Fields to exclude.
    flatten_nested : bool
        Whether to flatten nested objects for CSV.
    max_depth : int
        Maximum depth for flattening.

    """

    include_fields: list[str] | None = None
    exclude_fields: list[str] | None = None
    flatten_nested: bool = True
    max_depth: int = 3


def _to_dict(obj: object) -> dict[str, typing.Any]:
    """Convert object to dictionary.

    Parameters
    ----------
    obj : object
        Object to convert.

    Returns
    -------
    dict[str, typing.Any]
        Dictionary representation.

    """
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__struct_fields__"):
        # msgspec Struct
        return {
            f: getattr(obj, f)
            for f in obj.__struct_fields__  # type: ignore[union-attr]
        }
    # Fallback: try JSON round-trip
    try:
        return msgspec.json.decode(msgspec.json.encode(obj))
    except (TypeError, ValueError):
        return {"value": obj}


def _flatten_dict(
    data: dict[str, typing.Any],
    prefix: str = "",
    sep: str = ".",
    max_depth: int = 3,
    current_depth: int = 0,
) -> dict[str, typing.Any]:
    """Flatten nested dictionary.

    Parameters
    ----------
    data : dict[str, typing.Any]
        Dictionary to flatten.
    prefix : str
        Prefix for keys.
    sep : str
        Separator for nested keys.
    max_depth : int
        Maximum recursion depth.
    current_depth : int
        Current depth.

    Returns
    -------
    dict[str, typing.Any]
        Flattened dictionary.

    """
    items: dict[str, typing.Any] = {}

    for key, value in data.items():
        new_key = f"{prefix}{sep}{key}" if prefix else key

        if current_depth >= max_depth:
            items[new_key] = value
        elif isinstance(value, dict):
            items.update(
                _flatten_dict(
                    value,
                    new_key,
                    sep,
                    max_depth,
                    current_depth + 1,
                ),
            )
        elif isinstance(value, list):
            # Convert list to string or expand if simple
            if all(isinstance(v, (str, int, float)) for v in value):
                items[new_key] = ",".join(str(v) for v in value)
            else:
                items[new_key] = str(value)
        else:
            items[new_key] = value

    return items


def _apply_field_filter(
    data: dict[str, typing.Any],
    config: ExportConfig,
) -> dict[str, typing.Any]:
    """Apply field include/exclude filters.

    Parameters
    ----------
    data : dict[str, typing.Any]
        Data to filter.
    config : ExportConfig
        Export configuration.

    Returns
    -------
    dict[str, typing.Any]
        Filtered data.

    """
    if config.include_fields:
        data = {k: v for k, v in data.items() if k in config.include_fields}
    if config.exclude_fields:
        data = {k: v for k, v in data.items() if k not in config.exclude_fields}
    return data


class Exporter:
    """Export TMDB data to various formats.

    Examples
    --------
    >>> exporter = Exporter()
    >>> json_str = exporter.to_json(movie_details)
    >>> csv_str = exporter.to_csv([movie1, movie2])

    Parameters
    ----------
    config : ExportConfig | None
        Export configuration.

    """

    def __init__(self, config: ExportConfig | None = None) -> None:
        self._config = config or ExportConfig()

    def to_dict(self, obj: object) -> dict[str, typing.Any]:
        """Convert object to filtered dictionary.

        Parameters
        ----------
        obj : object
            Object to convert.

        Returns
        -------
        dict[str, typing.Any]
            Dictionary representation.

        """
        data = _to_dict(obj)
        return _apply_field_filter(data, self._config)

    def to_json(
        self,
        data: object,
        *,
        pretty: bool = False,
    ) -> str:
        """Export to JSON string.

        Parameters
        ----------
        data : object
            Data to export.
        pretty : bool
            Whether to format with indentation.

        Returns
        -------
        str
            JSON string.

        """
        if isinstance(data, list):
            items = [self.to_dict(item) for item in data]
            encoded = msgspec.json.encode(items)
        else:
            encoded = msgspec.json.encode(self.to_dict(data))

        if pretty:
            # Re-encode with formatting
            decoded = msgspec.json.decode(encoded)
            return msgspec.json.format(msgspec.json.encode(decoded)).decode()

        return encoded.decode()

    def to_json_file(
        self,
        data: object,
        path: str | Path,
        *,
        pretty: bool = True,
    ) -> None:
        """Export to JSON file.

        Parameters
        ----------
        data : object
            Data to export.
        path : str | Path
            File path.
        pretty : bool
            Whether to format with indentation.

        """
        content = self.to_json(data, pretty=pretty)
        Path(path).write_text(content, encoding="utf-8")

    def to_csv(
        self,
        data: list[object],
        *,
        include_header: bool = True,
    ) -> str:
        """Export list of objects to CSV string.

        Parameters
        ----------
        data : list[object]
            List of objects to export.
        include_header : bool
            Whether to include header row.

        Returns
        -------
        str
            CSV string.

        """
        if not data:
            return ""

        # Convert all items
        rows: list[dict[str, typing.Any]] = []
        for item in data:
            item_dict = self.to_dict(item)
            if self._config.flatten_nested:
                item_dict = _flatten_dict(
                    item_dict,
                    max_depth=self._config.max_depth,
                )
            rows.append(item_dict)

        # Get all field names
        all_fields: list[str] = []
        seen_fields: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen_fields:
                    all_fields.append(key)
                    seen_fields.add(key)

        # Write CSV
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=all_fields,
            extrasaction="ignore",
        )

        if include_header:
            writer.writeheader()

        for row in rows:
            writer.writerow(row)

        return output.getvalue()

    def to_csv_file(
        self,
        data: list[object],
        path: str | Path,
        *,
        include_header: bool = True,
    ) -> None:
        """Export to CSV file.

        Parameters
        ----------
        data : list[object]
            List of objects to export.
        path : str | Path
            File path.
        include_header : bool
            Whether to include header row.

        """
        content = self.to_csv(data, include_header=include_header)
        Path(path).write_text(content, encoding="utf-8")


def export_to_json(
    data: object,
    *,
    pretty: bool = False,
    include_fields: list[str] | None = None,
    exclude_fields: list[str] | None = None,
) -> str:
    """Convenience function to export to JSON.

    Parameters
    ----------
    data : object
        Data to export.
    pretty : bool
        Format with indentation.
    include_fields : list[str] | None
        Fields to include.
    exclude_fields : list[str] | None
        Fields to exclude.

    Returns
    -------
    str
        JSON string.

    Examples
    --------
    >>> json_str = export_to_json(movie, pretty=True)

    """
    config = ExportConfig(
        include_fields=include_fields,
        exclude_fields=exclude_fields,
    )
    return Exporter(config).to_json(data, pretty=pretty)


def export_to_csv(
    data: list[object],
    *,
    include_fields: list[str] | None = None,
    exclude_fields: list[str] | None = None,
    flatten: bool = True,
) -> str:
    """Convenience function to export list to CSV.

    Parameters
    ----------
    data : list[object]
        List of objects.
    include_fields : list[str] | None
        Fields to include.
    exclude_fields : list[str] | None
        Fields to exclude.
    flatten : bool
        Flatten nested objects.

    Returns
    -------
    str
        CSV string.

    Examples
    --------
    >>> csv_str = export_to_csv([movie1, movie2])

    """
    config = ExportConfig(
        include_fields=include_fields,
        exclude_fields=exclude_fields,
        flatten_nested=flatten,
    )
    return Exporter(config).to_csv(data)
