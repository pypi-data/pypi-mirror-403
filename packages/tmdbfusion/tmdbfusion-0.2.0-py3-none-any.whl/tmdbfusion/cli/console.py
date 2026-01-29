# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
Rich Console Output.

Beautiful terminal output for debugging and exploration.
Requires optional 'rich' dependency.
"""

from __future__ import annotations

import typing


if typing.TYPE_CHECKING:
    from collections.abc import Sequence

# Check for rich availability
_RICH_AVAILABLE = False
try:
    from rich.console import Console as RichConsole
    from rich.panel import Panel
    from rich.table import Table
    from rich.tree import Tree

    _RICH_AVAILABLE = True
except ImportError:
    pass


def _ensure_rich() -> None:
    """Raise ImportError if rich is not installed.

    Raises
    ------
    ImportError
        If rich library is not available.

    """
    if not _RICH_AVAILABLE:
        msg = "The 'rich' library is required for console output. Install it with: pip install tmdbfusion[rich]"
        raise ImportError(msg)


def _to_dict(obj: object) -> dict[str, object]:
    """Convert object to dictionary for display.

    Parameters
    ----------
    obj : object
        Object to convert.

    Returns
    -------
    dict[str, object]
        Dictionary representation.

    """
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    if isinstance(obj, dict):
        return dict(obj)  # type: ignore[arg-type]
    return {"value": obj}


def pretty_print(
    obj: object,
    *,
    title: str | None = None,
    expand: bool = True,
) -> None:
    """Pretty print any object with syntax highlighting.

    Parameters
    ----------
    obj : object
        Object to print (model, dict, or any).
    title : str | None
        Optional panel title.
    expand : bool
        Whether to expand the panel to full width.

    """
    _ensure_rich()
    console = RichConsole()

    # Determine title
    if title is None:
        title = type(obj).__name__

    # Convert to dict for display
    data = _to_dict(obj)

    console.print(Panel.fit(repr(data), title=title, expand=expand))


def table(
    items: Sequence[object],
    columns: Sequence[str] | None = None,
    *,
    title: str | None = None,
    max_rows: int = 50,
) -> None:
    """Display items as a table.

    Parameters
    ----------
    items : Sequence[object]
        List of objects to display.
    columns : Sequence[str] | None
        Column names to include (None = auto-detect).
    title : str | None
        Optional table title.
    max_rows : int
        Maximum rows to display.

    """
    _ensure_rich()
    console = RichConsole()

    if not items:
        console.print("[dim]No items to display[/dim]")
        return

    # Auto-detect columns from first item
    first = _to_dict(items[0])
    if columns is None:
        columns = list(first.keys())[:10]  # Limit columns

    # Create table
    rich_table = Table(title=title, show_lines=True)
    for col in columns:
        rich_table.add_column(col, overflow="fold")

    # Add rows
    for item in items[:max_rows]:
        data = _to_dict(item)
        row = [str(data.get(col, "")) for col in columns]
        rich_table.add_row(*row)

    if len(items) > max_rows:
        console.print(f"[dim]Showing {max_rows} of {len(items)} items[/dim]")

    console.print(rich_table)


def tree(
    obj: object,
    *,
    title: str | None = None,
    max_depth: int = 3,
) -> None:
    """Display object as a tree structure.

    Parameters
    ----------
    obj : object
        Object to display (e.g., TV show with seasons).
    title : str | None
        Root node title.
    max_depth : int
        Maximum tree depth.

    """
    _ensure_rich()
    console = RichConsole()

    if title is None:
        title = type(obj).__name__

    rich_tree = Tree(f"[bold]{title}[/bold]")
    _build_tree(rich_tree, obj, depth=0, max_depth=max_depth)
    console.print(rich_tree)


def _build_tree(
    parent: Tree,  # type: ignore[type-arg]
    obj: object,
    depth: int,
    max_depth: int,
) -> None:
    """Recursively build tree from object.

    Parameters
    ----------
    parent : Tree
        Parent tree node.
    obj : object
        Object to add.
    depth : int
        Current depth.
    max_depth : int
        Maximum depth.

    """
    if depth >= max_depth:
        return

    data = _to_dict(obj)

    for key, value in data.items():
        if isinstance(value, list):
            branch = parent.add(f"[cyan]{key}[/cyan] ({len(value)} items)")
            for i, item in enumerate(value[:5]):
                item_title = _get_item_title(item, i)
                child = branch.add(item_title)
                _build_tree(child, item, depth + 1, max_depth)
            if len(value) > 5:
                branch.add(f"[dim]... and {len(value) - 5} more[/dim]")
        elif isinstance(value, dict) or hasattr(value, "__dict__"):
            branch = parent.add(f"[cyan]{key}[/cyan]")
            _build_tree(branch, value, depth + 1, max_depth)
        else:
            parent.add(f"[cyan]{key}:[/cyan] {value}")


def _get_item_title(item: object, index: int) -> str:
    """Get display title for list item.

    Parameters
    ----------
    item : object
        Item to get title for.
    index : int
        Item index.

    Returns
    -------
    str
        Display title.

    """
    # Try common title fields
    for attr in ("title", "name", "id"):
        if hasattr(item, attr):
            val = getattr(item, attr)
            if val is not None:
                return f"[green]{val}[/green]"
    return f"[dim]Item {index}[/dim]"
