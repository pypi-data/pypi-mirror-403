"""Cache commands for context caching.

Extracted from cli.py as part of EPIC-003 CLI Architecture Refactor.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console

# Initialize Rich console
console = Console()


def print_json(data: dict) -> None:
    """Print JSON to stdout without Rich formatting."""
    sys.stdout.write(json.dumps(data, indent=2))
    sys.stdout.write("\n")
    sys.stdout.flush()


# Try relative imports first, fall back to absolute
try:
    from ..core import ops
    from ..context import ContextCache
except ImportError:
    from bpsai_pair.core import ops
    from bpsai_pair.context import ContextCache


def repo_root() -> Path:
    """Get repo root with better error message."""
    p = ops.find_project_root()
    if not ops.GitOps.is_repo(p):
        console.print(
            "[red]✗ Not in a git repository.[/red]\n"
            "Please run from your project root directory (where .git exists).\n"
            "[dim]Hint: cd to your project directory first[/dim]"
        )
        raise typer.Exit(1)
    return p


# Cache sub-app
app = typer.Typer(
    help="Context caching for efficient context management",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@app.command("stats")
def cache_stats(
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show cache statistics."""
    root = repo_root()
    cache = ContextCache(root / ".paircoder" / "cache")
    stats = cache.stats()

    if json_out:
        print_json(stats)
    else:
        console.print("[bold]Cache Statistics[/bold]")
        console.print(f"  Entries: {stats['entries']}")
        console.print(f"  Total size: {stats['total_bytes']:,} bytes")
        if stats['oldest']:
            console.print(f"  Oldest: {stats['oldest']}")
        if stats['newest']:
            console.print(f"  Newest: {stats['newest']}")


@app.command("clear")
def cache_clear(
    confirm: bool = typer.Option(False, "--confirm", "-y", help="Confirm clear"),
):
    """Clear the context cache."""
    if not confirm:
        console.print("[yellow]Use --confirm to clear the cache[/yellow]")
        raise typer.Exit(1)

    root = repo_root()
    cache = ContextCache(root / ".paircoder" / "cache")
    count = cache.clear()
    console.print(f"[green]Cleared {count} cache entries[/green]")


@app.command("invalidate")
def cache_invalidate(
    file_path: str = typer.Argument(..., help="File path to invalidate"),
):
    """Invalidate cache for a specific file."""
    root = repo_root()
    cache = ContextCache(root / ".paircoder" / "cache")
    full_path = root / file_path

    if cache.invalidate(full_path):
        console.print(f"[green]Invalidated cache for {file_path}[/green]")
    else:
        console.print(f"[dim]No cache entry for {file_path}[/dim]")
