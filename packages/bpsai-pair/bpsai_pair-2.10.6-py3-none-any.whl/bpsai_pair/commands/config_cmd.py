"""User configuration CLI commands.

Provides commands for managing global user preferences.
"""

from __future__ import annotations

import typer
from rich.console import Console

from bpsai_pair.core.preferences import (
    get_preference,
    load_preferences,
    set_preference,
)

console = Console()

app = typer.Typer(
    help="Manage user preferences",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Preference key (e.g., editor.preferred)"),
    value: str = typer.Argument(..., help="Value to set"),
):
    """Set a user preference.

    Examples:
        bpsai-pair config prefs set editor.preferred pycharm
        bpsai-pair config prefs set editor.preferred code
        bpsai-pair config prefs set terminal.preferred wt.exe
    """
    if set_preference(key, value):
        console.print(f"[green]✓[/green] Set {key} = {value}")
    else:
        console.print(f"[red]Error:[/red] Failed to save preference")
        raise typer.Exit(1)


@app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Preference key to get"),
):
    """Get a user preference value."""
    value = get_preference(key)
    if value is not None:
        console.print(value)
    else:
        console.print(f"[dim](not set)[/dim]")


@app.command("list")
def config_list():
    """List all user preferences."""
    prefs = load_preferences()
    if not prefs:
        console.print("[dim]No preferences set.[/dim]")
        console.print()
        console.print("Set preferences with:")
        console.print("  [cyan]bpsai-pair config prefs set editor.preferred pycharm[/cyan]")
        return

    console.print("[bold]User Preferences[/bold]")
    console.print("─" * 40)
    _print_dict(prefs)


def _print_dict(d: dict, prefix: str = ""):
    """Recursively print dictionary."""
    for key, value in d.items():
        full_key = f"{prefix}{key}" if prefix else key
        if isinstance(value, dict):
            _print_dict(value, f"{full_key}.")
        else:
            console.print(f"  {full_key}: [cyan]{value}[/cyan]")
