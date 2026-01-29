"""Task archive CLI commands.

Commands for archiving and managing archived tasks.
Extracted from task_commands.py for better modularity.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List
import json

import typer
from rich.table import Table

from .models import Task, TaskStatus
from .parser import PlanParser, TaskParser
from .helpers import (
    console,
    find_paircoder_dir,
    get_state_manager,
)

# Import task lifecycle management
try:
    from ..tasks import TaskArchiver, TaskLifecycle, ChangelogGenerator, TaskState
except ImportError:
    TaskArchiver = None
    TaskLifecycle = None
    ChangelogGenerator = None
    TaskState = None

task_archive_app = typer.Typer(
    help="Task archive commands",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@task_archive_app.command("archive")
def task_archive(
    task_ids: Optional[List[str]] = typer.Argument(None, help="Task IDs to archive"),
    completed: bool = typer.Option(False, "--completed", help="Archive all completed tasks"),
    sprint: Optional[str] = typer.Option(None, "--sprint", "-s", help="Archive tasks from sprint(s), comma-separated"),
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Plan slug (optional filter)"),
    version: Optional[str] = typer.Option(None, "--version", "-v", help="Version for changelog entry"),
    no_changelog: bool = typer.Option(False, "--no-changelog", help="Skip changelog update"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be archived"),
):
    """Archive completed tasks.

    When --completed is used without --plan, archives completed tasks from all plan directories.
    Use --plan to filter to a specific plan.
    """
    if TaskArchiver is None:
        console.print("[red]Task lifecycle module not available[/red]")
        raise typer.Exit(1)

    paircoder_dir = find_paircoder_dir()
    root_dir = paircoder_dir.parent
    tasks_dir = paircoder_dir / "tasks"

    archiver = TaskArchiver(root_dir)
    lifecycle = TaskLifecycle(tasks_dir)

    # Determine which plan directories to scan
    plan_dirs_to_scan: list[tuple[Path, str]] = []  # (path, slug)

    if plan_id:
        # Normalize plan slug (remove plan- prefix and date)
        plan_slug = plan_id
        if plan_slug.startswith("plan-"):
            parts = plan_slug.split("-")
            if len(parts) > 3:
                plan_slug = "-".join(parts[3:])
        plan_dir = tasks_dir / plan_slug
        if not plan_dir.exists():
            console.print(f"[red]Plan directory not found: {plan_dir}[/red]")
            raise typer.Exit(1)
        plan_dirs_to_scan.append((plan_dir, plan_slug))
    elif completed or sprint:
        # Scan for tasks - supports both flat storage and plan subdirectories
        state_manager = get_state_manager()
        state = state_manager.load_state()

        # Check for flat storage first (tasks directly in tasks/)
        flat_task_files = list(tasks_dir.glob("*.task.md"))
        if flat_task_files:
            # Use flat storage with "default" as plan slug for archiving
            plan_dirs_to_scan.append((tasks_dir, "default"))
        else:
            # Try plan subdirectories
            if state and state.active_plan_id:
                # Use active plan as default
                plan_slug = state.active_plan_id
                if plan_slug.startswith("plan-"):
                    parts = plan_slug.split("-")
                    if len(parts) > 3:
                        plan_slug = "-".join(parts[3:])
                plan_dir = tasks_dir / plan_slug
                if plan_dir.exists() and plan_dir.is_dir():
                    plan_dirs_to_scan.append((plan_dir, plan_slug))

            # If no active plan or no tasks found, scan all plan subdirectories
            if not plan_dirs_to_scan:
                for subdir in tasks_dir.iterdir():
                    if subdir.is_dir() and not subdir.name.startswith("."):
                        plan_dirs_to_scan.append((subdir, subdir.name))

        if not plan_dirs_to_scan:
            console.print("[dim]No task files or plan directories found to scan.[/dim]")
            return
    elif task_ids:
        # For specific task IDs, we need a plan context
        state_manager = get_state_manager()
        state = state_manager.load_state()
        if state and state.active_plan_id:
            plan_slug = state.active_plan_id
            if plan_slug.startswith("plan-"):
                parts = plan_slug.split("-")
                if len(parts) > 3:
                    plan_slug = "-".join(parts[3:])
            plan_dir = tasks_dir / plan_slug
            if plan_dir.exists():
                plan_dirs_to_scan.append((plan_dir, plan_slug))
            else:
                console.print(f"[red]Plan directory not found: {plan_dir}[/red]")
                raise typer.Exit(1)
        else:
            console.print("[red]Specify --plan when archiving specific task IDs without an active plan[/red]")
            raise typer.Exit(1)
    else:
        console.print("[red]Specify --completed, --sprint, or task IDs[/red]")
        raise typer.Exit(1)

    # Collect tasks to archive from all plan directories
    tasks_by_plan: dict[str, list] = {}

    for plan_dir, plan_slug in plan_dirs_to_scan:
        tasks_in_plan = []

        if task_ids:
            # Archive specific tasks
            for task_id in task_ids:
                task_file = plan_dir / f"{task_id}.task.md"
                if task_file.exists():
                    task = lifecycle.load_task(task_file)
                    tasks_in_plan.append(task)
        elif sprint:
            # Archive by sprint
            sprints = [s.strip() for s in sprint.split(",")]
            tasks_in_plan = lifecycle.get_tasks_by_sprint(plan_dir, sprints)
        elif completed:
            # Archive all completed
            tasks_in_plan = lifecycle.get_tasks_by_status(
                plan_dir, [TaskState.COMPLETED, TaskState.CANCELLED]
            )

        if tasks_in_plan:
            tasks_by_plan[plan_slug] = tasks_in_plan

    # Flatten for display
    all_tasks = []
    for tasks in tasks_by_plan.values():
        all_tasks.extend(tasks)

    if not all_tasks:
        console.print("[dim]No tasks to archive.[/dim]")
        return

    # Show what will be archived
    if dry_run:
        console.print("[bold]Would archive:[/bold]")
        for plan_slug, tasks in tasks_by_plan.items():
            if len(plan_dirs_to_scan) > 1:
                console.print(f"\n[cyan]{plan_slug}:[/cyan]")
            for task in tasks:
                console.print(f"  {task.id}: {task.title} ({task.status.value})")
        console.print(f"\n[dim]Total: {len(all_tasks)} tasks[/dim]")
        return

    # Perform archive for each plan
    total_archived = []
    total_skipped = []
    total_errors = []
    last_archive_path = None

    console.print(f"Archiving {len(all_tasks)} tasks...")
    for plan_slug, tasks in tasks_by_plan.items():
        result = archiver.archive_batch(tasks, plan_slug, version)
        total_archived.extend(result.archived)
        total_skipped.extend(result.skipped)
        total_errors.extend(result.errors)
        if result.archive_path:
            last_archive_path = result.archive_path

    for task in total_archived:
        console.print(f"  [green]\u2713[/green] {task.id}: {task.title}")

    for skip in total_skipped:
        console.print(f"  [yellow]\u23f8[/yellow] {skip}")

    for error in total_errors:
        console.print(f"  [red]\u2717[/red] {error}")

    # Update changelog
    if not no_changelog and total_archived and version:
        changelog_path = root_dir / "CHANGELOG.md"
        changelog = ChangelogGenerator(changelog_path)
        changelog.update_changelog(total_archived, version)
        console.print(f"\n[green]Updated CHANGELOG.md with {version}[/green]")

    console.print(f"\n[green]Archived {len(total_archived)} tasks[/green]")
    if last_archive_path:
        console.print(f"  {last_archive_path.parent}")


@task_archive_app.command("restore")
def task_restore(
    task_id: str = typer.Argument(..., help="Task ID to restore"),
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Plan slug"),
):
    """Restore a task from archive."""
    if TaskArchiver is None:
        console.print("[red]Task lifecycle module not available[/red]")
        raise typer.Exit(1)

    paircoder_dir = find_paircoder_dir()
    root_dir = paircoder_dir.parent

    # Determine plan slug
    if not plan_id:
        state_manager = get_state_manager()
        state = state_manager.load_state()
        if state and state.active_plan_id:
            plan_id = state.active_plan_id

    plan_slug = plan_id
    if plan_slug and plan_slug.startswith("plan-"):
        parts = plan_slug.split("-")
        if len(parts) > 3:
            plan_slug = "-".join(parts[3:])

    archiver = TaskArchiver(root_dir)

    try:
        restored_path = archiver.restore_task(task_id, plan_slug)
        console.print(f"[green]\u2713 Restored {task_id} to:[/green]")
        console.print(f"  {restored_path}")
    except FileNotFoundError:
        console.print(f"[red]Archived task not found: {task_id}[/red]")
        raise typer.Exit(1)


@task_archive_app.command("list-archived")
def task_list_archived(
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Plan slug"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List archived tasks."""
    if TaskArchiver is None:
        console.print("[red]Task lifecycle module not available[/red]")
        raise typer.Exit(1)

    paircoder_dir = find_paircoder_dir()
    root_dir = paircoder_dir.parent

    plan_slug = plan_id
    if plan_slug and plan_slug.startswith("plan-"):
        parts = plan_slug.split("-")
        if len(parts) > 3:
            plan_slug = "-".join(parts[3:])

    archiver = TaskArchiver(root_dir)
    archived = archiver.list_archived(plan_slug)

    if json_out:
        from dataclasses import asdict
        data = [asdict(t) for t in archived]
        console.print(json.dumps(data, indent=2))
        return

    if not archived:
        console.print("[dim]No archived tasks found.[/dim]")
        return

    table = Table(title=f"Archived Tasks ({len(archived)})")
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Sprint")
    table.add_column("Archived At")

    for task in archived:
        table.add_row(
            task.id,
            task.title[:40] + "..." if task.title and len(task.title) > 40 else task.title or "",
            task.sprint or "-",
            task.archived_at[:10] if task.archived_at else "-",
        )

    console.print(table)


@task_archive_app.command("cleanup")
def task_cleanup(
    retention_days: int = typer.Option(90, "--retention", "-r", help="Retention period in days"),
    dry_run: bool = typer.Option(True, "--dry-run/--confirm", help="Dry run or confirm deletion"),
):
    """Clean up old archived tasks."""
    if TaskArchiver is None:
        console.print("[red]Task lifecycle module not available[/red]")
        raise typer.Exit(1)

    paircoder_dir = find_paircoder_dir()
    root_dir = paircoder_dir.parent

    archiver = TaskArchiver(root_dir)
    to_remove = archiver.cleanup(retention_days, dry_run)

    if not to_remove:
        console.print(f"[dim]No tasks older than {retention_days} days.[/dim]")
        return

    if dry_run:
        console.print(f"[bold]Would remove ({len(to_remove)} tasks older than {retention_days} days):[/bold]")
        for item in to_remove:
            console.print(f"  {item}")
        console.print("\n[dim]Run with --confirm to delete[/dim]")
    else:
        console.print(f"[green]Removed {len(to_remove)} archived tasks:[/green]")
        for item in to_remove:
            console.print(f"  [red]\u2717[/red] {item}")


@task_archive_app.command("changelog-preview")
def task_changelog_preview(
    sprint: Optional[str] = typer.Option(None, "--sprint", "-s", help="Sprint(s) to preview, comma-separated"),
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Plan slug"),
    version: str = typer.Option("vX.Y.Z", "--version", "-v", help="Version string"),
):
    """Preview changelog entry for tasks."""
    if TaskArchiver is None or ChangelogGenerator is None:
        console.print("[red]Task lifecycle module not available[/red]")
        raise typer.Exit(1)

    paircoder_dir = find_paircoder_dir()
    root_dir = paircoder_dir.parent

    # Determine plan slug
    if not plan_id:
        state_manager = get_state_manager()
        state = state_manager.load_state()
        if state and state.active_plan_id:
            plan_id = state.active_plan_id

    plan_slug = plan_id
    if plan_slug and plan_slug.startswith("plan-"):
        parts = plan_slug.split("-")
        if len(parts) > 3:
            plan_slug = "-".join(parts[3:])

    lifecycle = TaskLifecycle(paircoder_dir / "tasks")
    plan_dir = paircoder_dir / "tasks" / plan_slug

    if not plan_dir.exists():
        console.print(f"[red]Plan directory not found: {plan_dir}[/red]")
        raise typer.Exit(1)

    # Get tasks
    if sprint:
        sprints = [s.strip() for s in sprint.split(",")]
        tasks = lifecycle.get_tasks_by_sprint(plan_dir, sprints)
    else:
        tasks = lifecycle.get_tasks_by_status(plan_dir, [TaskState.COMPLETED])

    if not tasks:
        console.print("[dim]No completed tasks found.[/dim]")
        return

    # Convert to ArchivedTask format for changelog generator
    from ..tasks.archiver import ArchivedTask
    archived_tasks = [
        ArchivedTask(
            id=t.id,
            title=t.title,
            sprint=t.sprint,
            status=t.status.value,
            completed_at=t.completed_at.isoformat() if t.completed_at else None,
            archived_at="",
            changelog_entry=t.changelog_entry,
            tags=t.tags,
        )
        for t in tasks
    ]

    changelog = ChangelogGenerator(root_dir / "CHANGELOG.md")
    preview = changelog.preview(archived_tasks, version)

    console.print("[bold]Changelog Preview:[/bold]\n")
    console.print(preview)
