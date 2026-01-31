"""Timer commands for time tracking integration.

Extracted from cli.py as part of EPIC-003 CLI Architecture Refactor.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..licensing import require_feature

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
    from ..integrations import TimeTrackingManager, TimeTrackingConfig
except ImportError:
    from bpsai_pair.core import ops
    from bpsai_pair.integrations import TimeTrackingManager, TimeTrackingConfig


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


# Timer sub-app
app = typer.Typer(
    help="Time tracking integration",
    context_settings={"help_option_names": ["-h", "--help"]}
)


def _get_time_manager() -> TimeTrackingManager:
    """Get a time tracking manager instance."""
    root = repo_root()
    cache_path = root / ".paircoder" / "history" / "time-entries.json"
    config = TimeTrackingConfig()  # Will use defaults or env vars
    return TimeTrackingManager(config, cache_path)


@app.command("start")
@require_feature("timer")
def timer_start(
    task_id: str = typer.Argument(..., help="Task ID to track time for"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Timer description"),
):
    """Start a timer for a task."""
    manager = _get_time_manager()

    desc = description or f"{task_id}: Working on task"
    timer_id = manager.provider.start_timer(task_id, desc)

    console.print(f"[green]✓[/green] Timer started: {desc}")
    console.print(f"  Timer ID: {timer_id}")


@app.command("stop")
@require_feature("timer")
def timer_stop():
    """Stop the current timer."""
    manager = _get_time_manager()

    current = manager.get_status()
    if not current:
        console.print("[yellow]No active timer[/yellow]")
        return

    entry = manager.provider.stop_timer(current.id)

    duration_str = manager.format_duration(entry.duration) if entry.duration else "0m"
    console.print(f"[green]✓[/green] Timer stopped: {duration_str}")
    console.print(f"  Task: {entry.task_id}")
    console.print(f"  Description: {entry.description}")


@app.command("status")
@require_feature("timer")
def timer_status():
    """Show current timer status."""
    manager = _get_time_manager()

    current = manager.get_status()
    if not current:
        console.print("[dim]No active timer[/dim]")
        return

    elapsed = datetime.now() - current.start
    elapsed_str = manager.format_duration(elapsed)

    console.print("[bold]Active Timer[/bold]")
    console.print(f"  Task: {current.task_id}")
    console.print(f"  Description: {current.description}")
    console.print(f"  Started: {current.start.strftime('%H:%M:%S')}")
    console.print(f"  Elapsed: {elapsed_str}")


@app.command("show")
@require_feature("timer")
def timer_show(
    task_id: str = typer.Argument(..., help="Task ID"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show time entries for a task."""
    manager = _get_time_manager()

    entries = manager.get_task_entries(task_id)
    total = manager.get_task_time(task_id)

    if json_out:
        print_json({
            "task_id": task_id,
            "entries": [e.to_dict() for e in entries],
            "total_seconds": total.total_seconds(),
            "total_formatted": manager.format_duration(total),
        })
        return

    console.print(f"[bold]Time for {task_id}[/bold]")
    console.print(f"Total: {manager.format_duration(total)}")
    console.print("")

    if entries:
        console.print("Entries:")
        for entry in entries:
            date_str = entry.start.strftime("%Y-%m-%d")
            time_str = entry.start.strftime("%H:%M")
            duration_str = manager.format_duration(entry.duration) if entry.duration else "running"
            console.print(f"  - {date_str} {time_str} ({duration_str})")
    else:
        console.print("[dim]No entries recorded[/dim]")


@app.command("summary")
@require_feature("timer")
def timer_summary(
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Filter by plan"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show time summary across tasks."""
    manager = _get_time_manager()

    task_ids = manager.cache.get_all_tasks()

    if plan_id:
        # Filter by plan prefix
        task_ids = [t for t in task_ids if t.startswith(plan_id) or plan_id in t]

    summary = {}
    total = manager.provider.cache.get_total("_total") if hasattr(manager.provider, "cache") else None

    for task_id in task_ids:
        if task_id.startswith("_"):
            continue
        time_spent = manager.get_task_time(task_id)
        if time_spent.total_seconds() > 0:
            summary[task_id] = {
                "seconds": time_spent.total_seconds(),
                "formatted": manager.format_duration(time_spent),
            }

    if json_out:
        print_json(summary)
        return

    if not summary:
        console.print("[dim]No time entries found[/dim]")
        return

    table = Table(title="Time Summary")
    table.add_column("Task", style="cyan")
    table.add_column("Time", justify="right")

    grand_total = sum(v["seconds"] for v in summary.values())

    for task_id, data in sorted(summary.items()):
        table.add_row(task_id, data["formatted"])

    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {manager.format_duration(timedelta(seconds=grand_total))}")
