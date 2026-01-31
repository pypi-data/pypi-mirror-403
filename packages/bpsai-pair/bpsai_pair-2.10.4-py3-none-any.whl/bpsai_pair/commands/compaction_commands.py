"""Compaction commands: snapshot save/list, check, recover, cleanup.

This module handles compaction detection, snapshot management, and recovery.
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


# Compaction sub-app for context compaction management
app = typer.Typer(
    help="Context compaction detection and recovery",
    context_settings={"help_option_names": ["-h", "--help"]}
)

# Snapshot sub-app under compaction
compaction_snapshot_app = typer.Typer(
    help="Manage compaction snapshots",
    context_settings={"help_option_names": ["-h", "--help"]}
)
app.add_typer(compaction_snapshot_app, name="snapshot")


@compaction_snapshot_app.command("save")
def compaction_snapshot_save(
    trigger: str = typer.Option("manual", "--trigger", "-t", help="Trigger type: auto or manual"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Reason for snapshot"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress errors and always exit 0 (for hooks)"),
):
    """Save a compaction snapshot with current context.

    Creates a snapshot of the current state before compaction occurs.
    Called automatically by PreCompact hook or manually for backup.

    Use --quiet for cross-platform hooks (instead of '2>/dev/null || true').
    """
    try:
        from ..compaction import CompactionManager
    except ImportError:
        from bpsai_pair.compaction import CompactionManager

    try:
        root = repo_root()
    except (SystemExit, typer.Exit, ops.ProjectRootNotFoundError):
        if quiet:
            return  # Silent exit for hooks
        raise

    paircoder_dir = root / ".paircoder"

    if not paircoder_dir.exists():
        if quiet:
            return  # Silent exit for hooks
        console.print("[yellow]No .paircoder directory found[/yellow]")
        raise typer.Exit(1)

    try:
        manager = CompactionManager(paircoder_dir)
        snapshot_path = manager.save_snapshot(trigger=trigger, reason=reason)

        if not quiet:
            console.print(f"[green]Snapshot saved:[/green] {snapshot_path.name}")
            console.print(f"[dim]Trigger: {trigger}[/dim]")
    except Exception:
        if quiet:
            return  # Silent exit for hooks
        raise


@compaction_snapshot_app.command("list")
def compaction_snapshot_list():
    """List available compaction snapshots."""
    try:
        from ..compaction import CompactionManager
    except ImportError:
        from bpsai_pair.compaction import CompactionManager

    root = repo_root()
    paircoder_dir = root / ".paircoder"

    if not paircoder_dir.exists():
        console.print("[yellow]No .paircoder directory found[/yellow]")
        raise typer.Exit(1)

    manager = CompactionManager(paircoder_dir)
    snapshots = manager.list_snapshots()

    if not snapshots:
        console.print("[dim]No compaction snapshots found[/dim]")
        return

    console.print(f"[cyan]Compaction Snapshots ({len(snapshots)}):[/cyan]")
    for snap in snapshots[:10]:  # Show last 10
        task_info = snap.current_task_id or "none"
        console.print(f"  {snap.timestamp.strftime('%Y-%m-%d %H:%M')} [{snap.trigger}] task={task_info}")


@app.command("check")
def compaction_check():
    """Check if compaction recently occurred.

    Detects if context compaction happened and recovery is needed.
    Used by UserPromptSubmit hook to auto-recover context.
    """
    try:
        from ..compaction import CompactionManager
    except ImportError:
        from bpsai_pair.compaction import CompactionManager

    root = repo_root()
    paircoder_dir = root / ".paircoder"

    if not paircoder_dir.exists():
        # Silent exit if not in a PairCoder project
        return

    manager = CompactionManager(paircoder_dir)
    marker = manager.check_compaction()

    if marker:
        console.print(f"[yellow]Compaction detected[/yellow] ({marker.trigger})")
        console.print(f"[dim]Timestamp: {marker.timestamp.isoformat()}[/dim]")
        console.print("[dim]Run 'bpsai-pair compaction recover' to restore context[/dim]")
    else:
        console.print("[dim]No unrecovered compaction detected[/dim]")


@app.command("recover")
def compaction_recover():
    """Recover context after compaction.

    Reads state.md and any available snapshots to restore context
    that was lost during compaction.
    """
    try:
        from ..compaction import CompactionManager
    except ImportError:
        from bpsai_pair.compaction import CompactionManager

    root = repo_root()
    paircoder_dir = root / ".paircoder"

    if not paircoder_dir.exists():
        console.print("[yellow]No .paircoder directory found[/yellow]")
        raise typer.Exit(1)

    manager = CompactionManager(paircoder_dir)
    output = manager.recover_context()
    console.print(output)


@app.command("cleanup")
def compaction_cleanup(
    keep: int = typer.Option(5, "--keep", "-k", help="Number of snapshots to keep"),
):
    """Remove old compaction snapshots."""
    try:
        from ..compaction import CompactionManager
    except ImportError:
        from bpsai_pair.compaction import CompactionManager

    root = repo_root()
    paircoder_dir = root / ".paircoder"

    if not paircoder_dir.exists():
        console.print("[yellow]No .paircoder directory found[/yellow]")
        raise typer.Exit(1)

    manager = CompactionManager(paircoder_dir)
    removed = manager.cleanup_old_snapshots(keep=keep)

    if removed > 0:
        console.print(f"[green]Removed {removed} old snapshot(s)[/green]")
    else:
        console.print("[dim]No snapshots to remove[/dim]")
