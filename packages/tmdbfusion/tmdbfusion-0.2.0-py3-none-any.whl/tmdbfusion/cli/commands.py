# Copyright (c) 2026 Xsyncio
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

"""
CLI Tool (tmdbf).

Command-line interface for TMDB exploration and operations.
Requires optional 'click' and 'rich' dependencies.
"""

from __future__ import annotations

import json
import os
import sys
import typing
from pathlib import Path


# Check for click availability
_CLICK_AVAILABLE = False
try:
    import click

    _CLICK_AVAILABLE = True
except ImportError:
    pass

# Check for rich availability
_RICH_AVAILABLE = False
try:
    from rich.console import Console
    from rich.table import Table

    _RICH_AVAILABLE = True
except ImportError:
    pass


def _ensure_deps() -> None:
    """Ensure CLI dependencies are available.

    Raises
    ------
    ImportError
        If required dependencies missing.

    """
    if not _CLICK_AVAILABLE:
        msg = "The 'click' library is required for CLI. Install with: pip install tmdbfusion[cli]"
        raise ImportError(msg)


# Config file path
CONFIG_DIR = Path.home() / ".tmdbfusion"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load_config() -> dict[str, str]:
    """Load configuration from file.

    Returns
    -------
    dict[str, str]
        Configuration dictionary.

    """
    if not CONFIG_FILE.exists():
        return {}
    try:
        return dict(json.loads(CONFIG_FILE.read_text()))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_config(config: dict[str, str]) -> None:
    """Save configuration to file.

    Parameters
    ----------
    config : dict[str, str]
        Configuration to save.

    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def _get_api_key() -> str | None:
    """Get API key from config or environment.

    Returns
    -------
    str | None
        API key if found.

    """
    # Check environment first
    env_key = os.environ.get("TMDB_API_KEY")
    if env_key:
        return env_key

    # Check config file
    config = _load_config()
    return config.get("api_key")


def _print_json(data: object) -> None:
    """Print data as JSON.

    Parameters
    ----------
    data : object
        Data to print.

    """
    import msgspec

    if hasattr(data, "__dict__"):
        msgspec.json.encode(data)
    else:
        json.dumps(data).encode()


def _print_table(
    items: list[object],
    columns: list[str],
    title: str | None = None,
) -> None:
    """Print items as table.

    Parameters
    ----------
    items : list[object]
        Items to display.
    columns : list[str]
        Column names.
    title : str | None
        Table title.

    """
    if _RICH_AVAILABLE:
        console = Console()
        table = Table(title=title)
        for col in columns:
            table.add_column(col)

        for item in items:
            row = []
            for col in columns:
                val = getattr(item, col, None)
                if val is None and isinstance(item, dict):
                    val = item.get(col, "")
                row.append(str(val) if val is not None else "")
            table.add_row(*row)

        console.print(table)
    else:
        # Fallback to simple output
        for item in items:
            parts = []
            for col in columns:
                val = getattr(item, col, None)
                if val is None and isinstance(item, dict):
                    val = item.get(col, "")
                parts.append(f"{col}={val}")


def _get_client() -> typing.Any:
    """Get TMDB client with configured API key.

    Returns
    -------
    TMDBClient
        Configured client.

    Raises
    ------
    click.ClickException
        If no API key configured.

    """
    from tmdbfusion import TMDBClient

    api_key = _get_api_key()
    if not api_key:
        msg = "No API key configured. Run 'tmdbf config set api-key YOUR_KEY'"
        raise click.ClickException(msg)
    return TMDBClient(api_key=api_key)


# Only define CLI if click is available
if _CLICK_AVAILABLE:

    @click.group()
    @click.version_option(version="0.1.0")
    def cli() -> None:
        """TMDB Fusion CLI - Explore The Movie Database."""

    @cli.command()
    @click.argument("movie_id", type=int)
    @click.option(
        "--append",
        "-a",
        default="",
        help="Append to response (comma-separated)",
    )
    @click.option(
        "--format",
        "-f",
        "output_format",
        type=click.Choice(["json", "table"]),
        default="table",
        help="Output format",
    )
    def movie(movie_id: int, append: str, output_format: str) -> None:
        """Get movie details."""
        client = _get_client()

        append_list = append.split(",") if append else None
        append_str = ",".join(append_list) if append_list else None

        if append_str:
            result = client.movies.details(
                movie_id,
                append_to_response=append_str,
            )
        else:
            result = client.movies.details(movie_id)

        if output_format == "json":
            _print_json(result)
        else:
            cols = ["id", "title", "release_date", "vote_average"]
            _print_table([result], cols, title="Movie Details")

    @cli.command()
    @click.argument("tv_id", type=int)
    @click.option("--format", "-f", "output_format", default="table")
    def tv(tv_id: int, output_format: str) -> None:
        """Get TV show details."""
        client = _get_client()
        result = client.tv.details(tv_id)

        if output_format == "json":
            _print_json(result)
        else:
            cols = ["id", "name", "first_air_date", "vote_average"]
            _print_table([result], cols, title="TV Show Details")

    @cli.command()
    @click.argument("person_id", type=int)
    @click.option("--format", "-f", "output_format", default="table")
    def person(person_id: int, output_format: str) -> None:
        """Get person details."""
        client = _get_client()
        result = client.people.details(person_id)

        if output_format == "json":
            _print_json(result)
        else:
            cols = ["id", "name", "birthday", "known_for_department"]
            _print_table([result], cols, title="Person Details")

    @cli.group()
    def search() -> None:
        """Search TMDB."""

    @search.command("movie")
    @click.argument("query")
    @click.option("--limit", "-l", default=10, help="Max results")
    @click.option("--format", "-f", "output_format", default="table")
    def search_movie(query: str, limit: int, output_format: str) -> None:
        """Search for movies."""
        client = _get_client()
        result = client.search.movie(query=query)
        items = result.results[:limit]

        if output_format == "json":
            _print_json(items)
        else:
            cols = ["id", "title", "release_date", "vote_average"]
            _print_table(items, cols, title=f"Search: {query}")

    @search.command("tv")
    @click.argument("query")
    @click.option("--limit", "-l", default=10, help="Max results")
    @click.option("--format", "-f", "output_format", default="table")
    def search_tv(query: str, limit: int, output_format: str) -> None:
        """Search for TV shows."""
        client = _get_client()
        result = client.search.tv(query=query)
        items = result.results[:limit]

        if output_format == "json":
            _print_json(items)
        else:
            cols = ["id", "name", "first_air_date", "vote_average"]
            _print_table(items, cols, title=f"Search: {query}")

    @search.command("person")
    @click.argument("query")
    @click.option("--limit", "-l", default=10, help="Max results")
    @click.option("--format", "-f", "output_format", default="table")
    def search_person(query: str, limit: int, output_format: str) -> None:
        """Search for people."""
        client = _get_client()
        result = client.search.person(query=query)
        items = result.results[:limit]

        if output_format == "json":
            _print_json(items)
        else:
            cols = ["id", "name", "known_for_department"]
            _print_table(items, cols, title=f"Search: {query}")

    @cli.group()
    def bulk() -> None:
        """Bulk operations."""

    @bulk.command("movies")
    @click.argument("ids", nargs=-1, type=int)
    @click.option("--format", "-f", "output_format", default="table")
    @click.option("--output", "-o", help="Output file path")
    def bulk_movies(
        ids: tuple[int, ...],
        output_format: str,
        output: str | None,
    ) -> None:
        """Get multiple movies."""
        from tmdbfusion.features.bulk import bulk_fetch

        client = _get_client()
        result = bulk_fetch(list(ids), client.movies.details)

        items = result.get_results()

        if output:
            import msgspec

            data = [msgspec.to_builtins(m) for m in items]
            Path(output).write_text(json.dumps(data, indent=2), encoding="utf-8")
            click.echo(f"Saved to {output}")
        elif output_format == "json":
            _print_json(items)
        else:
            cols = ["id", "title", "release_date", "vote_average"]
            _print_table(items, cols, title="Bulk Movies")

    @cli.group()
    def config() -> None:
        """Configuration management."""

    @config.command("set")
    @click.argument("key")
    @click.argument("value")
    def config_set(key: str, value: str) -> None:
        """Set configuration value."""
        cfg = _load_config()
        # Normalize key
        key = key.replace("-", "_")
        cfg[key] = value
        _save_config(cfg)
        click.echo(f"Set {key}")

    @config.command("get")
    @click.argument("key")
    def config_get(key: str) -> None:
        """Get configuration value."""
        cfg = _load_config()
        key = key.replace("-", "_")
        value = cfg.get(key, "")
        if key == "api_key" and value:
            # Mask API key
            click.echo(f"{key}: {value[:4]}...{value[-4:]}")
        else:
            click.echo(f"{key}: {value}")

    @config.command("show")
    def config_show() -> None:
        """Show all configuration."""
        cfg = _load_config()
        if not cfg:
            click.echo("No configuration set.")
            return
        for key, value in cfg.items():
            if key == "api_key" and value:
                click.echo(f"{key}: {value[:4]}...{value[-4:]}")
            else:
                click.echo(f"{key}: {value}")

    def main() -> None:
        """CLI entry point."""
        _ensure_deps()
        cli()

else:

    def main() -> None:
        """CLI entry point (dependencies missing)."""
        sys.exit(1)


if __name__ == "__main__":
    main()
