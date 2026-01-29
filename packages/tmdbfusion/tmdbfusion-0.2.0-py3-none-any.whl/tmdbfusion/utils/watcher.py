# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Change Watcher.

Track changes to TMDB content over time by comparing snapshots.
"""

from __future__ import annotations

import copy
import hashlib
import time
import typing
from dataclasses import dataclass
from dataclasses import field

import msgspec


if typing.TYPE_CHECKING:
    from collections.abc import Callable

T = typing.TypeVar("T")


@dataclass
class Snapshot[T]:
    """Snapshot of content at a point in time.

    Attributes
    ----------
    content_id : str
        Unique identifier for the content.
    timestamp : float
        Unix timestamp when snapshot was taken.
    data : T
        The actual content data.
    checksum : str
        Hash of serialized content for quick comparison.

    """

    content_id: str
    timestamp: float
    data: T
    checksum: str


@dataclass
class FieldChange:
    """Single field change.

    Attributes
    ----------
    field_path : str
        Dot-separated path to the changed field.
    old_value : object
        Previous value.
    new_value : object
        New value.

    """

    field_path: str
    old_value: object
    new_value: object


@dataclass
class ContentDiff:
    """Differences between two snapshots.

    Attributes
    ----------
    content_id : str
        Content identifier.
    old_timestamp : float
        Timestamp of older snapshot.
    new_timestamp : float
        Timestamp of newer snapshot.
    changes : list[FieldChange]
        List of field changes.
    has_changes : bool
        Whether any changes were detected.

    """

    content_id: str
    old_timestamp: float
    new_timestamp: float
    changes: list[FieldChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes.

        Returns
        -------
        bool
            True if changes exist.

        """
        return len(self.changes) > 0

    @property
    def changed_fields(self) -> list[str]:
        """Get list of changed field paths.

        Returns
        -------
        list[str]
            Field paths that changed.

        """
        return [c.field_path for c in self.changes]


class SnapshotStore[T]:
    """In-memory store for content snapshots.

    Parameters
    ----------
    max_snapshots_per_id : int
        Maximum snapshots to keep per content ID.

    """

    def __init__(self, max_snapshots_per_id: int = 10) -> None:
        self._store: dict[str, list[Snapshot[T]]] = {}
        self._max_per_id = max_snapshots_per_id

    def add(self, snapshot: Snapshot[T]) -> None:
        """Add a snapshot to the store.

        Parameters
        ----------
        snapshot : Snapshot[T]
            Snapshot to add.

        """
        if snapshot.content_id not in self._store:
            self._store[snapshot.content_id] = []

        self._store[snapshot.content_id].append(snapshot)

        # Trim old snapshots
        if len(self._store[snapshot.content_id]) > self._max_per_id:
            self._store[snapshot.content_id] = self._store[snapshot.content_id][-self._max_per_id :]

    def get_latest(self, content_id: str) -> Snapshot[T] | None:
        """Get the most recent snapshot for content.

        Parameters
        ----------
        content_id : str
            Content identifier.

        Returns
        -------
        Snapshot[T] | None
            Latest snapshot or None.

        """
        if content_id not in self._store or not self._store[content_id]:
            return None
        return self._store[content_id][-1]

    def get_all(self, content_id: str) -> list[Snapshot[T]]:
        """Get all snapshots for content.

        Parameters
        ----------
        content_id : str
            Content identifier.

        Returns
        -------
        list[Snapshot[T]]
            List of snapshots, newest last.

        """
        return self._store.get(content_id, [])

    def clear(self, content_id: str | None = None) -> None:
        """Clear snapshots.

        Parameters
        ----------
        content_id : str | None
            If provided, clear only this content. Otherwise clear all.

        """
        if content_id:
            self._store.pop(content_id, None)
        else:
            self._store.clear()


def _compute_checksum(data: object) -> str:
    """Compute checksum for data.

    Parameters
    ----------
    data : object
        Data to hash.

    Returns
    -------
    str
        MD5 checksum.

    """
    try:
        serialized = msgspec.json.encode(data)
    except (TypeError, ValueError):
        serialized = str(data).encode()
    return hashlib.md5(serialized).hexdigest()  # noqa: S324


def _compare_values(
    old: object,
    new: object,
    path: str,
    changes: list[FieldChange],
    *,
    ignore_fields: set[str] | None = None,
) -> None:
    """Recursively compare values and record changes.

    Parameters
    ----------
    old : object
        Old value.
    new : object
        New value.
    path : str
        Current field path.
    changes : list[FieldChange]
        List to append changes to.
    ignore_fields : set[str] | None
        Fields to ignore.

    """
    if ignore_fields and path in ignore_fields:
        return

    if old == new:
        return

    # Handle dict comparison
    if isinstance(old, dict) and isinstance(new, dict):
        all_keys = set(old.keys()) | set(new.keys())
        for key in all_keys:
            new_path = f"{path}.{key}" if path else str(key)
            old_val = old.get(key)
            new_val = new.get(key)
            _compare_values(
                old_val,
                new_val,
                new_path,
                changes,
                ignore_fields=ignore_fields,
            )

    # Handle list comparison
    elif isinstance(old, list) and isinstance(new, list):
        if len(old) != len(new):
            changes.append(FieldChange(path, old, new))
            return
        for i, (old_item, new_item) in enumerate(zip(old, new, strict=True)):
            _compare_values(
                old_item,
                new_item,
                f"{path}[{i}]",
                changes,
                ignore_fields=ignore_fields,
            )

    # Handle msgspec Struct
    elif hasattr(old, "__struct_fields__") and hasattr(new, "__struct_fields__"):
        for field_name in old.__struct_fields__:
            new_path = f"{path}.{field_name}" if path else field_name
            old_val = getattr(old, field_name, None)
            new_val = getattr(new, field_name, None)
            _compare_values(
                old_val,
                new_val,
                new_path,
                changes,
                ignore_fields=ignore_fields,
            )

    # Primitive value change
    else:
        changes.append(FieldChange(path, old, new))


class ChangeWatcher[T]:
    """Watch for changes to content over time.

    Examples
    --------
    >>> watcher = ChangeWatcher[MovieDetails]()
    >>> watcher.snapshot("movie_550", movie_data)
    >>> # Later...
    >>> watcher.snapshot("movie_550", new_movie_data)
    >>> diff = watcher.get_diff("movie_550")
    >>> if diff and diff.has_changes:
    ...     print(diff.changed_fields)

    Parameters
    ----------
    max_snapshots : int
        Maximum snapshots per content ID.
    ignore_fields : set[str] | None
        Field paths to ignore in comparisons.

    """

    def __init__(
        self,
        max_snapshots: int = 10,
        ignore_fields: set[str] | None = None,
    ) -> None:
        self._store: SnapshotStore[T] = SnapshotStore(max_snapshots)
        self._ignore_fields = ignore_fields or set()

    def snapshot(self, content_id: str, data: T) -> Snapshot[T]:
        """Take a snapshot of content.

        Parameters
        ----------
        content_id : str
            Unique content identifier (e.g., "movie_550").
        data : T
            Content data to snapshot.

        Returns
        -------
        Snapshot[T]
            The created snapshot.

        """
        snap = Snapshot(
            content_id=content_id,
            timestamp=time.time(),
            data=copy.deepcopy(data),
            checksum=_compute_checksum(data),
        )
        self._store.add(snap)
        return snap

    def get_latest(self, content_id: str) -> Snapshot[T] | None:
        """Get the latest snapshot.

        Parameters
        ----------
        content_id : str
            Content identifier.

        Returns
        -------
        Snapshot[T] | None
            Latest snapshot or None.

        """
        return self._store.get_latest(content_id)

    def get_diff(
        self,
        content_id: str,
        index: int = -2,
    ) -> ContentDiff | None:
        """Get diff between snapshots.

        Parameters
        ----------
        content_id : str
            Content identifier.
        index : int
            Index of older snapshot (default -2 for second-to-last).

        Returns
        -------
        ContentDiff | None
            Diff between snapshots, or None if not enough snapshots.

        """
        snapshots = self._store.get_all(content_id)
        if len(snapshots) < 2:
            return None

        old_snap = snapshots[index]
        new_snap = snapshots[-1]

        # Quick check with checksum
        if old_snap.checksum == new_snap.checksum:
            return ContentDiff(
                content_id=content_id,
                old_timestamp=old_snap.timestamp,
                new_timestamp=new_snap.timestamp,
            )

        changes: list[FieldChange] = []
        _compare_values(
            old_snap.data,
            new_snap.data,
            "",
            changes,
            ignore_fields=self._ignore_fields,
        )

        return ContentDiff(
            content_id=content_id,
            old_timestamp=old_snap.timestamp,
            new_timestamp=new_snap.timestamp,
            changes=changes,
        )

    def has_changed(self, content_id: str) -> bool:
        """Check if content has changed since last snapshot.

        Parameters
        ----------
        content_id : str
            Content identifier.

        Returns
        -------
        bool
            True if content changed.

        """
        diff = self.get_diff(content_id)
        return diff is not None and diff.has_changes

    def clear(self, content_id: str | None = None) -> None:
        """Clear snapshots.

        Parameters
        ----------
        content_id : str | None
            Content ID to clear, or None for all.

        """
        self._store.clear(content_id)

    def watch(
        self,
        content_id: str,
        fetcher: Callable[[], T],
    ) -> ContentDiff | None:
        """Fetch new data and compare to previous snapshot.

        Parameters
        ----------
        content_id : str
            Content identifier.
        fetcher : Callable[[], T]
            Function to fetch current data.

        Returns
        -------
        ContentDiff | None
            Diff if previous snapshot exists, None otherwise.

        """
        data = fetcher()
        self.snapshot(content_id, data)
        return self.get_diff(content_id)
