"""Task CLI commands.

Commands for managing tasks (list, show, update, archive, etc.).
"""

from typing import Optional
import json

import typer
from rich.table import Table

from .models import Task, TaskStatus
from .parser import PlanParser, TaskParser
from .helpers import (
    console,
    find_paircoder_dir,
    get_state_manager,
    is_trello_enabled,
    get_linked_trello_card,
    log_bypass,
    check_state_md_updated,
    check_for_manual_edits,
    show_time_tracking,
    run_status_hooks,
    sync_local_ac_for_completion,
    complete_task_with_state_machine,
)

# Import archive commands from extracted module
from .task_archive_commands import (
    task_archive,
    task_restore,
    task_list_archived,
    task_cleanup,
    task_changelog_preview,
)

task_app = typer.Typer(
    help="Manage tasks",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@task_app.command("list")
def task_list(
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Filter by plan ID"),
    status: Optional[str] = typer.Option(
        None, "--status", "-s",
        help="Filter: pending|in_progress|review|done|blocked"
    ),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List tasks."""
    paircoder_dir = find_paircoder_dir()
    task_parser = TaskParser(paircoder_dir / "tasks")
    plan_parser = PlanParser(paircoder_dir / "plans")

    # Determine plan slug
    plan_slug = None
    if plan_id:
        plan = plan_parser.get_plan_by_id(plan_id)
        if plan:
            plan_slug = plan.slug

    tasks = task_parser.parse_all(plan_slug)

    if status:
        tasks = [t for t in tasks if t.status.value == status]

    if json_out:
        data = [t.to_dict() for t in tasks]
        console.print(json.dumps(data, indent=2))
        return

    if not tasks:
        console.print("[dim]No tasks found.[/dim]")
        return

    # Check for manual edits
    manual_edits = check_for_manual_edits(paircoder_dir, tasks)
    if manual_edits:
        console.print()
        for edit in manual_edits:
            console.print(f"[yellow]⚠️  Warning: {edit['task_id']} status changed outside CLI (hooks may not have fired)[/yellow]")
            console.print(f"   [dim]File status: {edit['current_status']} | Last CLI status: {edit['last_cli_status']}[/dim]")
            console.print(f"   [dim]To sync: bpsai-pair task update {edit['task_id']} --resync[/dim]")
        console.print()

    table = Table(title=f"Tasks ({len(tasks)})")
    table.add_column("Status", width=3)
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Plan")
    table.add_column("Priority")
    table.add_column("Complexity", justify="right")

    for task in tasks:
        table.add_row(
            task.status_emoji,
            task.id,
            task.title[:40] + "..." if len(task.title) > 40 else task.title,
            task.plan_id or "-",
            task.priority,
            str(task.complexity),
        )

    console.print(table)


@task_app.command("show")
def task_show(
    task_id: str = typer.Argument(..., help="Task ID"),
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Plan ID to narrow search"),
):
    """Show details of a specific task."""
    paircoder_dir = find_paircoder_dir()
    task_parser = TaskParser(paircoder_dir / "tasks")
    plan_parser = PlanParser(paircoder_dir / "plans")

    plan_slug = None
    if plan_id:
        plan = plan_parser.get_plan_by_id(plan_id)
        if plan:
            plan_slug = plan.slug

    task = task_parser.get_task_by_id(task_id, plan_slug)

    if not task:
        console.print(f"[red]Task not found: {task_id}[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]{task.status_emoji} {task.id}[/bold]")
    console.print(f"{'=' * 60}")
    console.print(f"[cyan]Title:[/cyan] {task.title}")
    console.print(f"[cyan]Plan:[/cyan] {task.plan_id}")
    console.print(f"[cyan]Type:[/cyan] {task.type}")
    console.print(f"[cyan]Priority:[/cyan] {task.priority}")
    console.print(f"[cyan]Complexity:[/cyan] {task.complexity}")
    console.print(f"[cyan]Status:[/cyan] {task.status.value}")
    console.print(f"[cyan]Est. Tokens:[/cyan] {task.estimated_tokens_str}")

    if task.sprint:
        console.print(f"[cyan]Sprint:[/cyan] {task.sprint}")

    if task.tags:
        console.print(f"[cyan]Tags:[/cyan] {', '.join(task.tags)}")

    # Show estimated vs actual hours
    show_time_tracking(task, paircoder_dir)

    if task.body:
        console.print(f"\n{'-' * 60}")
        console.print(task.body)


@task_app.command("update")
def task_update(
    task_id: str = typer.Argument(..., help="Task ID"),
    status: str = typer.Option(
        None, "--status", "-s",
        help="New status: pending|in_progress|review|done|blocked|cancelled"
    ),
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Plan ID to narrow search"),
    no_hooks: bool = typer.Option(False, "--no-hooks", help="Skip running hooks"),
    skip_state_check: bool = typer.Option(
        False, "--skip-state-check",
        help="Skip checking if state.md was updated (not recommended)"
    ),
    resync: bool = typer.Option(
        False, "--resync",
        help="Re-trigger hooks for current status (use after manual file edits)"
    ),
    local_only: bool = typer.Option(
        False, "--local-only",
        help="Update local file only, skip Trello sync check (requires --reason)"
    ),
    reason: str = typer.Option(
        "", "--reason",
        help="Reason for local-only update (required with --local-only)"
    ),
    strict: bool = typer.Option(
        True, "--strict/--no-strict",
        help="Block if acceptance criteria unchecked (default: strict)"
    ),
    auto_check: bool = typer.Option(
        False, "--auto-check",
        help="Auto-check all acceptance criteria items before completion"
    ),
):
    """Update a task's status."""
    # ENFORCEMENT: Block --local-only bypass when strict_ac_verification is enabled
    if status and status.lower() == "done" and local_only:
        import yaml
        config_path = find_paircoder_dir() / "config.yaml"
        strict_ac = False
        if config_path.exists():
            with open(config_path, encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            strict_ac = config.get("enforcement", {}).get("strict_ac_verification", False)

        if strict_ac:
            console.print("\n[red]❌ BLOCKED: --local-only is disabled when strict_ac_verification is enabled.[/red]")
            console.print("")
            console.print("[yellow]Use the proper Trello workflow:[/yellow]")
            console.print("  [cyan]bpsai-pair ttask done <TRELLO-ID> --summary \"...\"[/cyan]")
            console.print("")
            console.print("To find the Trello card ID:")
            console.print("  [cyan]bpsai-pair ttask list[/cyan]")
            console.print("")
            console.print("[dim]This ensures acceptance criteria are verified before completion.[/dim]")
            raise typer.Exit(1)

    # ENFORCEMENT: Block --no-hooks when completing tasks in strict mode
    if status and status.lower() == "done" and no_hooks:
        import yaml
        config_path = find_paircoder_dir() / "config.yaml"
        strict_ac = False
        if config_path.exists():
            with open(config_path, encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            strict_ac = config.get("enforcement", {}).get("strict_ac_verification", False)

        if strict_ac:
            console.print("\n[red]❌ BLOCKED: --no-hooks is disabled when completing tasks in strict mode.[/red]")
            console.print("")
            console.print("[yellow]Hooks ensure proper workflow:[/yellow]")
            console.print("  - Trello card sync")
            console.print("  - Timer tracking")
            console.print("  - Metrics recording")
            console.print("")
            console.print("[dim]Use the proper Trello workflow instead:[/dim]")
            console.print("  [cyan]bpsai-pair ttask done <TRELLO-ID> --summary \"...\"[/cyan]")
            raise typer.Exit(1)

    # ENFORCEMENT: Block status=done if task has linked Trello card
    if status and status.lower() == "done" and not local_only:
        trello_card_id = get_linked_trello_card(task_id)
        if trello_card_id:
            console.print(f"\n[red]❌ BLOCKED: Task has linked Trello card {trello_card_id}[/red]")
            console.print("")
            console.print("[yellow]Complete via Trello:[/yellow]")
            console.print(f"  [cyan]bpsai-pair ttask done {trello_card_id} --summary \"...\"[/cyan]")
            console.print("")
            console.print("[dim]This ensures acceptance criteria are verified.[/dim]")
            raise typer.Exit(1)

        elif is_trello_enabled():
            console.print("\n[red]❌ BLOCKED: This project uses Trello integration.[/red]")
            console.print("")
            console.print("[yellow]Complete via Trello:[/yellow]")
            console.print("  [cyan]bpsai-pair ttask done <TRELLO-ID> --summary \"...\"[/cyan]")
            console.print("")
            console.print("[dim]Find card ID with: bpsai-pair ttask list[/dim]")
            raise typer.Exit(1)

    # If using --local-only, require reason and log bypass
    if local_only:
        if not reason:
            console.print("[red]❌ --local-only requires --reason to explain the bypass[/red]")
            raise typer.Exit(1)
        log_bypass("task update --local-only", task_id, reason)
        console.print(f"[yellow]⚠ Updating local task only (logged): {reason}[/yellow]")

    paircoder_dir = find_paircoder_dir()
    task_parser = TaskParser(paircoder_dir / "tasks")
    plan_parser = PlanParser(paircoder_dir / "plans")

    plan_slug = None
    if plan_id:
        plan = plan_parser.get_plan_by_id(plan_id)
        if plan:
            plan_slug = plan.slug

    # Get the task before updating (for hook context)
    task = task_parser.get_task_by_id(task_id, plan_slug)
    if not task:
        console.print(f"[red]Task not found: {task_id}[/red]")
        raise typer.Exit(1)

    old_status = task.status.value

    # Handle --resync: use current status from file and trigger hooks
    if resync:
        if status:
            console.print("[yellow]Warning: --status ignored when using --resync[/yellow]")
        status = old_status  # Use current status from file

        # Record CLI update to cache
        from .cli_update_cache import get_cli_update_cache
        cli_cache = get_cli_update_cache(paircoder_dir)
        cli_cache.record_update(task_id, status)

        console.print(f"[cyan]Resyncing {task_id} (status: {status})[/cyan]")

        # Run hooks for current status
        if not no_hooks:
            run_status_hooks(paircoder_dir, task_id, status, task)

        console.print(f"[green]✓ Resync complete for {task_id}[/green]")
        return

    # Require --status when not using --resync
    if not status:
        console.print("[red]--status is required (or use --resync to re-trigger hooks)[/red]")
        raise typer.Exit(1)

    # ENFORCEMENT: Block --skip-state-check when strict_ac_verification is enabled
    if status == "done" and skip_state_check:
        import yaml
        config_path = find_paircoder_dir() / "config.yaml"
        strict_ac = False
        if config_path.exists():
            with open(config_path, encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            strict_ac = config.get("enforcement", {}).get("strict_ac_verification", False)

        if strict_ac:
            console.print(
                "\n[red]❌ BLOCKED: --skip-state-check is disabled when strict_ac_verification is enabled.[/red]")
            console.print("")
            console.print("[yellow]You must update state.md before completing tasks:[/yellow]")
            console.print("  1. Edit [cyan].paircoder/context/state.md[/cyan]")
            console.print(f"  2. Mark [yellow]{task_id}[/yellow] as done in task list")
            console.print("  3. Add session entry under \"What Was Just Done\"")
            console.print("  4. Update \"What's Next\" section")
            console.print("")
            console.print("[dim]This ensures all work is properly documented.[/dim]")
            raise typer.Exit(1)

    # Check state.md update requirement when completing a task
    if status == "done" and not skip_state_check:
        check_result = check_state_md_updated(paircoder_dir, task_id)
        if not check_result["updated"]:
            console.print("\n[red]Cannot complete task: state.md not updated since task started.[/red]\n")
            console.print("Please update [cyan].paircoder/context/state.md[/cyan] with:")
            console.print(f"  - Mark [yellow]{task_id}[/yellow] as done in task list")
            console.print("  - Add session entry under [yellow]\"What Was Just Done\"[/yellow]")
            console.print("  - Update [yellow]\"What's Next\"[/yellow] section\n")
            console.print(f"Then retry: [cyan]bpsai-pair task update {task_id} --status done[/cyan]")
            console.print("\n[dim]Use --skip-state-check to bypass (not recommended)[/dim]")
            raise typer.Exit(1)
    elif status == "done" and skip_state_check:
        console.print("[yellow]Warning: Skipping state.md check - task completion not documented[/yellow]")

    # ACCEPTANCE CRITERIA VERIFICATION (for non-Trello tasks completing locally)
    # This mirrors the AC verification in ttask done for Trello cards
    if status == "done":
        # Auto-check AC items if requested (before strict verification)
        if auto_check:
            checked_count = task_parser.check_all_ac_items(task_id, plan_slug)
            if checked_count > 0:
                console.print(f"[green]✓ Auto-checked {checked_count} acceptance criteria item(s)[/green]")
                # Reload task to get updated AC
                task = task_parser.get_task_by_id(task_id, plan_slug)

        # Verify AC if in strict mode
        if strict:
            unchecked_ac = task.unchecked_ac if task else []
            if unchecked_ac:
                console.print(f"\n[red]❌ Cannot complete: {len(unchecked_ac)} acceptance criteria item(s) unchecked[/red]")
                console.print("\n[dim]Unchecked items:[/dim]")
                for ac in unchecked_ac:
                    console.print(f"  ○ {ac.text}")
                console.print("\n[dim]Options:[/dim]")
                console.print(f"  1. Check items: [cyan]bpsai-pair task check {task_id} \"<item text>\"[/cyan]")
                console.print(f"  2. Check all:   [cyan]bpsai-pair task update {task_id} --status done --auto-check[/cyan]")
                console.print("  3. Edit task file directly")
                if auto_check:
                    console.print("\n[yellow]Note: --auto-check ran but some items could not be matched.[/yellow]")
                raise typer.Exit(1)
            console.print("[green]✓ All acceptance criteria verified[/green]")

            # STATE MACHINE: Transition to LOCAL_AC_VERIFIED (non-Trello path)
            local_ac_ok, local_ac_msg = sync_local_ac_for_completion(task_id, is_trello=False)
            if not local_ac_ok:
                console.print(f"[red]❌ BLOCKED: {local_ac_msg}[/red]")
                raise typer.Exit(1)
        else:
            # Not strict - warn about unchecked items but proceed
            unchecked_ac = task.unchecked_ac if task else []
            if unchecked_ac:
                console.print(f"[yellow]⚠ Completing with {len(unchecked_ac)} unchecked AC item(s)[/yellow]")
                log_bypass("task update --no-strict", task_id, f"{len(unchecked_ac)} unchecked AC items")

    # Update the status
    success = task_parser.update_status(task_id, status, plan_slug)

    if success:
        emoji_map = {
            "pending": "\u23f3",
            "in_progress": "\U0001f504",
            "review": "\U0001f50d",
            "done": "\u2705",
            "blocked": "\U0001f6ab",
            "cancelled": "\u274c",
        }
        checkmark = "\u2713"
        console.print(f"{emoji_map.get(status, checkmark)} Updated {task_id} -> {status}")

        # Record CLI update to cache (for manual edit detection)
        from .cli_update_cache import get_cli_update_cache
        cli_cache = get_cli_update_cache(paircoder_dir)
        cli_cache.record_update(task_id, status)

        # Run hooks if status actually changed and hooks not disabled
        if not no_hooks and old_status != status:
            run_status_hooks(paircoder_dir, task_id, status, task)

        # STATE MACHINE: Final transition to COMPLETED
        if status == "done":
            complete_ok, complete_msg = complete_task_with_state_machine(task_id, trigger="task_update")
            if not complete_ok:
                console.print(f"[yellow]⚠ State machine: {complete_msg}[/yellow]")

        # Update plan status based on task status changes
        if task.plan_id and old_status != status:
            plan_updated = plan_parser.check_and_update_plan_status(
                task.plan_id, paircoder_dir / "tasks"
            )
            if plan_updated:
                plan = plan_parser.get_plan_by_id(task.plan_id)
                if plan:
                    console.print(f"  → Plan {plan.id} is now {plan.status.value}")
    else:
        console.print(f"[red]Failed to update task: {task_id}[/red]")
        raise typer.Exit(1)


@task_app.command("next")
def task_next(
    start: bool = typer.Option(False, "--start", "-s", help="Automatically start the next task"),
):
    """Show the next task to work on.

    Use --start to automatically set the task to in_progress.
    """
    state_manager = get_state_manager()
    task = state_manager.get_next_task()

    if not task:
        console.print("[dim]No tasks available. Create a plan first![/dim]")
        return

    # If --start flag, auto-assign the task
    if start and task.status != TaskStatus.IN_PROGRESS:
        from .auto_assign import auto_assign_next

        paircoder_dir = find_paircoder_dir()
        task = auto_assign_next(paircoder_dir, plan_id=task.plan_id)

        if task:
            console.print(f"[green]✓ Auto-started task:[/green] {task.id}")
        else:
            console.print("[red]Failed to auto-start task[/red]")
            return

    console.print(f"[bold]Next task:[/bold] {task.status_emoji} {task.id}")
    console.print(f"[cyan]Title:[/cyan] {task.title}")
    console.print(f"[cyan]Priority:[/cyan] {task.priority} | Complexity: {task.complexity}")

    if task.body:
        # Show first section of body
        lines = task.body.split("\n")
        preview = "\n".join(lines[:10])
        console.print(f"\n{preview}")
        if len(lines) > 10:
            console.print(f"\n[dim]... ({len(lines) - 10} more lines)[/dim]")

    if task.status != TaskStatus.IN_PROGRESS:
        console.print("\n[dim]To start: bpsai-pair task next --start[/dim]")
        console.print(f"[dim]Or: bpsai-pair task update {task.id} --status in_progress[/dim]")


@task_app.command("auto-next")
def task_auto_next(
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Plan ID to filter tasks"),
):
    """Automatically assign and start the next pending task.

    This command finds the highest-priority pending task and sets it to in_progress.
    Tasks are prioritized by: priority (P0 > P1 > P2), then complexity (lower first).
    """
    from .auto_assign import auto_assign_next

    paircoder_dir = find_paircoder_dir()
    task = auto_assign_next(paircoder_dir, plan_id=plan_id)

    if not task:
        console.print("[yellow]No pending tasks available[/yellow]")
        return

    console.print(f"[green]✓ Auto-assigned:[/green] {task.id}")
    console.print(f"[cyan]Title:[/cyan] {task.title}")
    console.print(f"[cyan]Priority:[/cyan] {task.priority} | Complexity: {task.complexity}")
    console.print(f"[cyan]Status:[/cyan] {task.status_emoji} {task.status.value}")


@task_app.command("check")
def task_check(
    task_id: str = typer.Argument(..., help="Task ID"),
    item_text: str = typer.Argument(
        None,
        help="Text of AC item to check (partial match). Omit to list all AC items."
    ),
    uncheck: bool = typer.Option(False, "--uncheck", "-u", help="Uncheck instead of check"),
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Plan ID to narrow search"),
):
    """Check or uncheck acceptance criteria items.

    Use without item_text to list all AC items and their status.
    Use with item_text to check/uncheck a specific item (partial text match).

    Examples:
        bpsai-pair task check T29.6.3                        # List all AC items
        bpsai-pair task check T29.6.3 "tests pass"           # Check item containing "tests pass"
        bpsai-pair task check T29.6.3 "tests pass" --uncheck # Uncheck item
    """
    paircoder_dir = find_paircoder_dir()
    task_parser = TaskParser(paircoder_dir / "tasks")
    plan_parser = PlanParser(paircoder_dir / "plans")

    plan_slug = None
    if plan_id:
        plan = plan_parser.get_plan_by_id(plan_id)
        if plan:
            plan_slug = plan.slug

    task = task_parser.get_task_by_id(task_id, plan_slug)
    if not task:
        console.print(f"[red]Task not found: {task_id}[/red]")
        raise typer.Exit(1)

    ac_items = task.acceptance_criteria
    if not ac_items:
        console.print(f"[yellow]No acceptance criteria found in task {task_id}[/yellow]")
        console.print("[dim]AC items should be in the task file under '# Acceptance Criteria'[/dim]")
        console.print("[dim]Format: - [ ] Item text[/dim]")
        return

    # If no item_text, list all AC items
    if not item_text:
        console.print(f"[bold]Acceptance Criteria for {task_id}[/bold]")
        console.print(f"{'=' * 50}")
        for ac in ac_items:
            check = "✓" if ac.checked else "○"
            color = "green" if ac.checked else "dim"
            console.print(f"  [{color}]{check}[/{color}] {ac.text}")

        unchecked_count = len([ac for ac in ac_items if not ac.checked])
        if unchecked_count > 0:
            console.print(f"\n[yellow]{unchecked_count} item(s) unchecked[/yellow]")
        else:
            console.print(f"\n[green]All {len(ac_items)} item(s) checked ✓[/green]")
        return

    # Check/uncheck the specified item
    success = task_parser.update_ac_item(task_id, item_text, not uncheck, plan_slug)

    if success:
        action = "Unchecked" if uncheck else "Checked"
        console.print(f"[green]✓ {action}: {item_text}[/green]")

        # Show updated AC status
        task = task_parser.get_task_by_id(task_id, plan_slug)
        if task:
            unchecked = task.unchecked_ac
            if not unchecked:
                console.print(f"[green]All acceptance criteria now verified![/green]")
            else:
                console.print(f"[dim]{len(unchecked)} item(s) remaining[/dim]")
    else:
        console.print(f"[red]Item not found matching: {item_text}[/red]")
        console.print("[dim]Use 'bpsai-pair task check {task_id}' to see all items[/dim]")
        raise typer.Exit(1)


@task_app.command("ac")
def task_ac(
    task_id: str = typer.Argument(..., help="Task ID"),
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Plan ID to narrow search"),
):
    """Show acceptance criteria status for a task.

    Alias for 'task check <task_id>' without an item.
    """
    # Delegate to task_check
    task_check(task_id=task_id, item_text=None, uncheck=False, plan_id=plan_id)


# Register archive commands from extracted module
task_app.command("archive")(task_archive)
task_app.command("restore")(task_restore)
task_app.command("list-archived")(task_list_archived)
task_app.command("cleanup")(task_cleanup)
task_app.command("changelog-preview")(task_changelog_preview)
