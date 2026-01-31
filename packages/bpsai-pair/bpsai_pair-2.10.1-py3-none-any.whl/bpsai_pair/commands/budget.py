"""Budget commands for token estimation and checking.

Part of Sprint 25 Token Budget System (EPIC-003 continuation).
"""

from __future__ import annotations

import json
import sys
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
    from ..tokens import (
        count_file_tokens,
        estimate_task_tokens,
        estimate_from_task_file,
        get_budget_status,
        MODEL_LIMITS,
        THRESHOLDS,
    )
except ImportError:
    from bpsai_pair.core import ops
    from bpsai_pair.tokens import (
        count_file_tokens,
        estimate_from_task_file,
        get_budget_status,
        MODEL_LIMITS,
        THRESHOLDS,
    )


def repo_root() -> Path:
    """Get repo root with better error message."""
    p = ops.find_project_root()
    if not ops.GitOps.is_repo(p):
        console.print(
            "[red]Error: Not in a git repository.[/red]\n"
            "Please run from your project root directory (where .git exists)."
        )
        raise typer.Exit(1)
    return p


def _find_task_file(task_id: str, root: Path) -> Optional[Path]:
    """Find task file by ID."""
    # Try various task file patterns
    patterns = [
        f".paircoder/tasks/{task_id}.task.md",
        f".paircoder/tasks/TASK-{task_id}.task.md",
        f".paircoder/tasks/{task_id.upper()}.task.md",
    ]
    for pattern in patterns:
        path = root / pattern
        if path.exists():
            return path

    # Try glob for flexibility
    tasks_dir = root / ".paircoder" / "tasks"
    if tasks_dir.exists():
        for f in tasks_dir.glob("*.task.md"):
            # Check if task_id is in filename (case-insensitive)
            if task_id.lower() in f.stem.lower():
                return f

    return None


def _format_tokens(tokens: int) -> str:
    """Format token count with thousands separator."""
    return f"{tokens:,}"


def _status_icon(status: str) -> str:
    """Get status icon for display."""
    icons = {
        "ok": "[green]OK[/green]",
        "info": "[blue]INFO[/blue]",
        "warning": "[yellow]WARNING[/yellow]",
        "critical": "[red]CRITICAL[/red]",
    }
    return icons.get(status, status)


# Budget sub-app
app = typer.Typer(
    help="Token budget estimation and checking",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@app.command("estimate")
@require_feature("token_budget")
def budget_estimate(
    task_id: Optional[str] = typer.Argument(None, help="Task ID to estimate"),
    files: list[str] = typer.Option([], "-f", "--file", help="Specific files to include"),
    model: str = typer.Option("claude-sonnet-4-5", "--model", "-m", help="Model for limit"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Estimate token usage for a task or files.

    Examples:
        bpsai-pair budget estimate T25.8
        bpsai-pair budget estimate -f src/main.py -f src/utils.py
        bpsai-pair budget estimate T25.8 --json
    """
    root = repo_root()

    if task_id:
        # Estimate from task file
        task_path = _find_task_file(task_id, root)
        if not task_path:
            console.print(f"[red]Error: Task {task_id} not found[/red]")
            raise typer.Exit(2)

        estimate = estimate_from_task_file(task_path)
        if not estimate:
            console.print(f"[red]Error: Could not parse task file {task_path}[/red]")
            raise typer.Exit(2)

        # Get task title from file
        task_title = task_id
        try:
            content = task_path.read_text(encoding="utf-8")
            for line in content.split('\n'):
                if line.startswith('title:'):
                    task_title = f"{task_id} - {line.split(':', 1)[1].strip()}"
                    break
        except Exception:
            pass

        status = get_budget_status(estimate.total, model)

        if json_out:
            print_json({
                "task_id": task_id,
                "task_title": task_title,
                "breakdown": {
                    "base_context": estimate.base_context,
                    "task_file": estimate.task_file,
                    "source_files": estimate.source_files,
                    "estimated_output": estimate.estimated_output,
                    "total": estimate.total,
                },
                "budget": {
                    "percent": estimate.budget_percent,
                    "status": status.status,
                    "limit": status.limit,
                    "remaining": status.remaining,
                },
            })
        else:
            console.print(f"\n[bold]Task:[/bold] {task_title}")
            console.print()

            table = Table(title="Token Breakdown", show_header=False, box=None)
            table.add_column("Component", style="dim")
            table.add_column("Tokens", justify="right")

            table.add_row("Base context", _format_tokens(estimate.base_context))
            table.add_row("Task file", _format_tokens(estimate.task_file))
            table.add_row("Source files", _format_tokens(estimate.source_files))
            table.add_row("Est. output", _format_tokens(estimate.estimated_output))
            table.add_row("─" * 20, "─" * 10)
            table.add_row(
                "[bold]Total[/bold]",
                f"[bold]{_format_tokens(estimate.total)}[/bold] ({estimate.budget_percent}%)"
            )

            console.print(table)
            console.print()
            console.print(f"Status: {_status_icon(status.status)} - {status.message}")

    elif files:
        # Estimate from specific files
        file_paths = [Path(f) for f in files]
        total_tokens = sum(count_file_tokens(root / f) for f in file_paths)
        status = get_budget_status(total_tokens, model)

        if json_out:
            file_breakdown = {
                str(f): count_file_tokens(root / f) for f in file_paths
            }
            print_json({
                "files": file_breakdown,
                "total": total_tokens,
                "budget": {
                    "percent": status.percent,
                    "status": status.status,
                },
            })
        else:
            console.print("\n[bold]File Token Estimate[/bold]\n")

            table = Table(show_header=True, header_style="bold")
            table.add_column("File")
            table.add_column("Tokens", justify="right")

            for f in file_paths:
                tokens = count_file_tokens(root / f)
                table.add_row(str(f), _format_tokens(tokens))

            table.add_row("─" * 30, "─" * 10, style="dim")
            table.add_row("[bold]Total[/bold]", f"[bold]{_format_tokens(total_tokens)}[/bold]")

            console.print(table)
            console.print()
            console.print(f"Status: {_status_icon(status.status)}")

    else:
        console.print("[yellow]Please provide a task ID or files to estimate.[/yellow]")
        console.print("\nExamples:")
        console.print("  bpsai-pair budget estimate T25.8")
        console.print("  bpsai-pair budget estimate -f src/main.py -f src/utils.py")
        raise typer.Exit(1)


@app.command("status")
@require_feature("token_budget")
def budget_status(
    model: str = typer.Option("claude-sonnet-4-5", "--model", "-m", help="Model for limit"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show current session budget status.

    Displays the model's context limit and current thresholds.
    """
    limit = MODEL_LIMITS.get(model, 200000)

    if json_out:
        print_json({
            "model": model,
            "limit": limit,
            "thresholds": THRESHOLDS,
        })
    else:
        console.print("\n[bold]Budget Status[/bold]")
        console.print(f"\n  Model: {model}")
        console.print(f"  Context limit: {_format_tokens(limit)} tokens")
        console.print()
        console.print("  [bold]Thresholds:[/bold]")
        console.print(f"    Info:     {THRESHOLDS['info']}% ({_format_tokens(int(limit * THRESHOLDS['info'] / 100))} tokens)")
        console.print(f"    Warning:  {THRESHOLDS['warning']}% ({_format_tokens(int(limit * THRESHOLDS['warning'] / 100))} tokens)")
        console.print(f"    Critical: {THRESHOLDS['critical']}% ({_format_tokens(int(limit * THRESHOLDS['critical'] / 100))} tokens)")


@app.command("check")
@require_feature("token_budget")
def budget_check(
    task_id: str = typer.Argument(..., help="Task ID to check"),
    threshold: int = typer.Option(75, "--threshold", "-t", help="Warning threshold percentage"),
    model: str = typer.Option("claude-sonnet-4-5", "--model", "-m", help="Model for limit"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Pre-flight budget check for a task.

    Exit codes:
        0: Under threshold
        1: Over threshold
        2: Task not found or error
    """
    root = repo_root()

    task_path = _find_task_file(task_id, root)
    if not task_path:
        if json_out:
            print_json({"error": f"Task {task_id} not found", "exit_code": 2})
        else:
            console.print(f"[red]Error: Task {task_id} not found[/red]")
        raise typer.Exit(2)

    estimate = estimate_from_task_file(task_path)
    if not estimate:
        if json_out:
            print_json({"error": f"Could not parse task {task_id}", "exit_code": 2})
        else:
            console.print(f"[red]Error: Could not parse task {task_id}[/red]")
        raise typer.Exit(2)

    status = get_budget_status(estimate.total, model)
    over_threshold = estimate.budget_percent >= threshold

    if json_out:
        print_json({
            "task_id": task_id,
            "estimated_tokens": estimate.total,
            "budget_percent": estimate.budget_percent,
            "threshold": threshold,
            "over_threshold": over_threshold,
            "status": status.status,
            "exit_code": 1 if over_threshold else 0,
        })
    else:
        if over_threshold:
            console.print(f"[red]OVER THRESHOLD[/red]: {task_id}")
            console.print(f"  Estimated: {_format_tokens(estimate.total)} tokens ({estimate.budget_percent}%)")
            console.print(f"  Threshold: {threshold}%")
            console.print()
            console.print("[yellow]Consider breaking this task into smaller parts.[/yellow]")
        else:
            console.print(f"[green]OK[/green]: {task_id}")
            console.print(f"  Estimated: {_format_tokens(estimate.total)} tokens ({estimate.budget_percent}%)")
            console.print(f"  Threshold: {threshold}%")

    raise typer.Exit(1 if over_threshold else 0)
