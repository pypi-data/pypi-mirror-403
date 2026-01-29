# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Daily Export Sync.

Sync with TMDB's daily file exports for large-scale data ingestion.
"""

from __future__ import annotations

import gzip
import json
import logging
import typing
from dataclasses import dataclass
from dataclasses import field
from datetime import date
from datetime import timedelta
from pathlib import Path


if typing.TYPE_CHECKING:
    from collections.abc import Iterator


logger = logging.getLogger("tmdbfusion.sync")

# TMDB export base URL
EXPORT_BASE_URL = "http://files.tmdb.org/p/exports"

# Available export types
EXPORT_TYPES = {
    "movie_ids": "movie_ids",
    "tv_series_ids": "tv_series_ids",
    "person_ids": "person_ids",
    "collection_ids": "collection_ids",
    "tv_network_ids": "tv_network_ids",
    "keyword_ids": "keyword_ids",
    "production_company_ids": "production_company_ids",
}


@dataclass
class ExportItem:
    """Single item from export file.

    Attributes
    ----------
    id : int
        TMDB ID.
    original_title : str | None
        Original title (movies).
    original_name : str | None
        Original name (TV/people).
    popularity : float
        Popularity score.
    adult : bool
        Adult content flag.

    """

    id: int
    original_title: str | None = None
    original_name: str | None = None
    popularity: float = 0.0
    adult: bool = False

    @property
    def name(self) -> str:
        """Get display name.

        Returns
        -------
        str
            Title or name.

        """
        return self.original_title or self.original_name or ""


@dataclass
class SyncResult:
    """Result from sync operation.

    Attributes
    ----------
    export_date : date
        Date of the export file.
    item_count : int
        Total items in export.
    file_path : Path
        Path to downloaded file.

    """

    export_date: date
    item_count: int
    file_path: Path


@dataclass
class DiffResult:
    """Result from diff operation.

    Attributes
    ----------
    new_ids : set[int]
        IDs present in new but not old.
    removed_ids : set[int]
        IDs present in old but not new.

    """

    new_ids: set[int] = field(default_factory=set)
    removed_ids: set[int] = field(default_factory=set)

    @property
    def new_count(self) -> int:
        """Get count of new IDs.

        Returns
        -------
        int
            New ID count.

        """
        return len(self.new_ids)

    @property
    def removed_count(self) -> int:
        """Get count of removed IDs.

        Returns
        -------
        int
            Removed ID count.

        """
        return len(self.removed_ids)


class DailyExportSync:
    """Sync with TMDB daily export files.

    Examples
    --------
    >>> sync = DailyExportSync("movie_ids", output_dir="./exports")
    >>> result = sync.download_latest()
    >>> for item in sync.iter_items(result.file_path):
    ...     print(item.id, item.name)

    Parameters
    ----------
    export_type : str
        Type of export (movie_ids, tv_series_ids, etc.).
    output_dir : str | Path
        Directory to save export files.

    """

    def __init__(
        self,
        export_type: str,
        output_dir: str | Path = "./exports",
    ) -> None:
        if export_type not in EXPORT_TYPES:
            msg = f"Unknown export type: {export_type}"
            raise ValueError(msg)

        self._export_type = export_type
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def _get_export_url(self, export_date: date) -> str:
        """Build export URL for a date.

        Parameters
        ----------
        export_date : date
            Date of export.

        Returns
        -------
        str
            Full URL.

        """
        date_str = export_date.strftime("%m_%d_%Y")
        filename = f"{self._export_type}_{date_str}.json.gz"
        return f"{EXPORT_BASE_URL}/{filename}"

    def _find_latest_date(self) -> date:
        """Find the most recent available export date.

        Returns
        -------
        date
            Latest available export date.

        Raises
        ------
        RuntimeError
            If no export found in last 7 days.

        """
        import httpx

        # Exports are typically available next day at midnight UTC
        check_date = date.today() - timedelta(days=1)

        for _ in range(7):
            url = self._get_export_url(check_date)
            try:
                response = httpx.head(url, timeout=10.0)
                if response.status_code == 200:
                    return check_date
            except httpx.HTTPError:
                pass

            check_date -= timedelta(days=1)

        msg = "Could not find TMDB export file in last 7 days"
        raise RuntimeError(msg)

    def download_latest(self) -> SyncResult:
        """Download the latest export file.

        Returns
        -------
        SyncResult
            Sync result with file path.

        Raises
        ------
        RuntimeError
            If download fails.

        """
        import httpx

        export_date = self._find_latest_date()
        url = self._get_export_url(export_date)

        date_str = export_date.strftime("%Y%m%d")
        filename = f"{self._export_type}_{date_str}.json.gz"
        output_path = self._output_dir / filename

        if output_path.exists():
            logger.info("Export already exists: %s", output_path)
            item_count = sum(1 for _ in self.iter_items(output_path))
            return SyncResult(
                export_date=export_date,
                item_count=item_count,
                file_path=output_path,
            )

        logger.info("Downloading: %s", url)

        try:
            with httpx.stream("GET", url, timeout=300.0) as response:
                response.raise_for_status()
                with output_path.open("wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
        except httpx.HTTPError as e:
            msg = f"Failed to download export: {e}"
            raise RuntimeError(msg) from e

        item_count = sum(1 for _ in self.iter_items(output_path))
        logger.info("Downloaded %d items", item_count)

        return SyncResult(
            export_date=export_date,
            item_count=item_count,
            file_path=output_path,
        )

    def download_for_date(self, export_date: date) -> SyncResult:
        """Download export for a specific date.

        Parameters
        ----------
        export_date : date
            Date to download.

        Returns
        -------
        SyncResult
            Sync result.

        Raises
        ------
        RuntimeError
            If download fails.

        """
        import httpx

        url = self._get_export_url(export_date)

        date_str = export_date.strftime("%Y%m%d")
        filename = f"{self._export_type}_{date_str}.json.gz"
        output_path = self._output_dir / filename

        if output_path.exists():
            item_count = sum(1 for _ in self.iter_items(output_path))
            return SyncResult(
                export_date=export_date,
                item_count=item_count,
                file_path=output_path,
            )

        try:
            with httpx.stream("GET", url, timeout=300.0) as response:
                response.raise_for_status()
                with output_path.open("wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
        except httpx.HTTPError as e:
            msg = f"Failed to download export for {export_date}: {e}"
            raise RuntimeError(msg) from e

        item_count = sum(1 for _ in self.iter_items(output_path))

        return SyncResult(
            export_date=export_date,
            item_count=item_count,
            file_path=output_path,
        )

    def iter_items(self, file_path: Path) -> Iterator[ExportItem]:
        """Iterate over items in export file.

        Parameters
        ----------
        file_path : Path
            Path to gzipped export file.

        Yields
        ------
        ExportItem
            Each item from the export.

        """
        with gzip.open(file_path, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    yield ExportItem(
                        id=data.get("id", 0),
                        original_title=data.get("original_title"),
                        original_name=data.get("original_name"),
                        popularity=data.get("popularity", 0.0),
                        adult=data.get("adult", False),
                    )
                except json.JSONDecodeError:
                    continue

    def get_all_ids(self, file_path: Path) -> set[int]:
        """Get all IDs from export file.

        Parameters
        ----------
        file_path : Path
            Path to export file.

        Returns
        -------
        set[int]
            Set of all IDs.

        """
        return {item.id for item in self.iter_items(file_path)}

    def diff(
        self,
        old_file: Path,
        new_file: Path,
    ) -> DiffResult:
        """Compare two export files.

        Parameters
        ----------
        old_file : Path
            Older export file.
        new_file : Path
            Newer export file.

        Returns
        -------
        DiffResult
            Difference between exports.

        """
        old_ids = self.get_all_ids(old_file)
        new_ids = self.get_all_ids(new_file)

        return DiffResult(
            new_ids=new_ids - old_ids,
            removed_ids=old_ids - new_ids,
        )

    def diff_since(
        self,
        old_date: date,
    ) -> DiffResult:
        """Get diff since a previous date.

        Parameters
        ----------
        old_date : date
            Previous export date.

        Returns
        -------
        DiffResult
            Changes since old date.

        Raises
        ------
        RuntimeError
            If either export unavailable.

        """
        old_result = self.download_for_date(old_date)
        new_result = self.download_latest()

        return self.diff(old_result.file_path, new_result.file_path)
