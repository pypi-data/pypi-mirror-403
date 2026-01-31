"""Session check commands: check, status.

This module handles session state detection and status display.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

# Try relative imports first, fall back to absolute
try:
    from ..core import ops
except ImportError:
    from bpsai_pair.core import ops

# Initialize Rich console
console = Console()

# Session sub-app for session management
app = typer.Typer(
    help="Session management and context reload",
    context_settings={"help_option_names": ["-h", "--help"]}
)


def repo_root() -> Path:
    """Get repo root with better error message."""
    p = ops.find_project_root()
    if not ops.GitOps.is_repo(p):
        console.print(
            "[red]x Not in a git repository.[/red]\n"
            "Please run from your project root directory (where .git exists).\n"
            "[dim]Hint: cd to your project directory first[/dim]"
        )
        raise typer.Exit(1)
    return p


def _get_progress_bar(percent: float, width: int = 20) -> str:
    """Create a text-based progress bar."""
    filled = int(percent / 100 * width)
    empty = width - filled

    # Color based on thresholds
    if percent >= 90:
        color = "red"
    elif percent >= 75:
        color = "yellow"
    elif percent >= 50:
        color = "blue"
    else:
        color = "green"

    bar = "█" * filled + "░" * empty
    return f"[{color}]{bar}[/{color}]"


def _get_current_task_id(paircoder_dir: Path) -> Optional[str]:
    """Get the current in-progress task ID."""
    tasks_dir = paircoder_dir / "tasks"
    if not tasks_dir.exists():
        return None

    for task_file in tasks_dir.glob("*.task.md"):
        try:
            content = task_file.read_text(encoding="utf-8")
            if "status: in_progress" in content:
                # Extract task ID
                for line in content.split('\n'):
                    if line.startswith('id:'):
                        return line.split(':', 1)[1].strip()
        except Exception:
            pass
    return None


@app.command("check")
def session_check(
    force: bool = typer.Option(False, "--force", "-f", help="Force context display even if continuing session"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress errors and always exit 0 (for hooks)"),
):
    """Check session state and display context if new session.

    This command detects if this is a new session (>30 min gap) and displays
    relevant context from state.md. Also checks for compaction recovery needs.
    Used by Claude Code hooks to enforce reading context at session start.

    Output is designed for use with UserPromptSubmit hook - outputs context
    summary if new session or after compaction, minimal output otherwise.

    Use --quiet for cross-platform hooks (instead of '2>/dev/null || true').
    """
    try:
        from ..session import SessionManager
        from ..compaction import CompactionManager
    except ImportError:
        from bpsai_pair.session import SessionManager
        from bpsai_pair.compaction import CompactionManager

    try:
        root = repo_root()
    except (SystemExit, typer.Exit, ops.ProjectRootNotFoundError):
        if quiet:
            return  # Silent exit for hooks
        raise

    paircoder_dir = root / ".paircoder"

    if not paircoder_dir.exists():
        # No PairCoder directory - skip silently
        return

    try:
        # Check for compaction recovery first
        compaction_mgr = CompactionManager(paircoder_dir)
        compaction_marker = compaction_mgr.check_compaction()

        if compaction_marker:
            # Compaction detected - recover context
            output = compaction_mgr.recover_context()
            console.print(output)
            return

        # Check session state
        session_mgr = SessionManager(paircoder_dir)
        session = session_mgr.check_session()

        if session.is_new or force:
            # New session or forced - show context
            context = session_mgr.get_context()
            output = session_mgr.format_context_output(context)
            console.print(output)
        # Continuing session - no output (silent continuation)
    except Exception:
        if quiet:
            return  # Silent exit for hooks
        raise


@app.command("status")
def session_status(
    show_budget: bool = typer.Option(True, "--budget/--no-budget", help="Show token budget section"),
):
    """Show current session status including token budget."""
    try:
        from ..session import SessionManager, SessionState
    except ImportError:
        from bpsai_pair.session import SessionManager, SessionState

    root = repo_root()
    paircoder_dir = root / ".paircoder"

    if not paircoder_dir.exists():
        console.print("[yellow]No .paircoder directory found[/yellow]")
        raise typer.Exit(1)

    manager = SessionManager(paircoder_dir)
    session_file = manager.session_file

    if not session_file.exists():
        console.print("[dim]No active session[/dim]")
        return

    try:
        import json
        with open(session_file, encoding='utf-8') as f:
            data = json.load(f)
        state = SessionState.from_dict(data)

        from datetime import datetime
        now = datetime.now()
        gap = now - state.last_activity
        gap_minutes = int(gap.total_seconds() / 60)

        console.print(f"[cyan]Session ID:[/cyan] {state.session_id}")
        console.print(f"[cyan]Last activity:[/cyan] {state.last_activity.isoformat()}")
        console.print(f"[cyan]Gap:[/cyan] {gap_minutes} minutes")
        console.print(f"[cyan]Timeout:[/cyan] {manager.timeout_minutes} minutes")

        if gap_minutes > manager.timeout_minutes:
            console.print("[yellow]Session expired - next check will start new session[/yellow]")
        else:
            remaining = manager.timeout_minutes - gap_minutes
            console.print(f"[green]Session active ({remaining} min until timeout)[/green]")

        # Token Budget Section
        if show_budget:
            console.print()
            console.print("[bold]Token Budget:[/bold]")

            try:
                from ..tokens import estimate_from_task_file, get_budget_status, MODEL_LIMITS
            except ImportError:
                from bpsai_pair.tokens import estimate_from_task_file, get_budget_status, MODEL_LIMITS

            # Try to find current in-progress task
            current_task_id = _get_current_task_id(paircoder_dir)

            if current_task_id:
                # Find task file
                task_file = None
                for pattern in [f"tasks/{current_task_id}.task.md", f"tasks/TASK-{current_task_id}.task.md"]:
                    path = paircoder_dir / pattern
                    if path.exists():
                        task_file = path
                        break

                if task_file:
                    estimate = estimate_from_task_file(task_file)
                    if estimate:
                        status = get_budget_status(estimate.total)
                        bar = _get_progress_bar(estimate.budget_percent)
                        console.print(f"  {bar} {estimate.budget_percent}% ({estimate.total:,} / {status.limit:,})")

                        # Status with color
                        status_colors = {"ok": "green", "info": "blue", "warning": "yellow", "critical": "red"}
                        color = status_colors.get(status.status, "white")
                        console.print(f"  Status: [{color}]{status.status.upper()}[/{color}] - {status.message}")
                        console.print(f"  [dim]Task: {current_task_id}[/dim]")
                    else:
                        console.print("  [dim]Could not estimate tokens for current task[/dim]")
                else:
                    console.print(f"  [dim]Task file not found for {current_task_id}[/dim]")
            else:
                # No active task - show default budget info
                limit = MODEL_LIMITS.get("claude-sonnet-4-5", 200000)
                console.print(f"  [dim]No active task. Budget limit: {limit:,} tokens[/dim]")

    except Exception as e:
        console.print(f"[red]Error reading session: {e}[/red]")
