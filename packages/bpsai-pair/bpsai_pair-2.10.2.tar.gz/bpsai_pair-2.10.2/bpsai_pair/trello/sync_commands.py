"""
Trello sync commands: progress, sync.

This module handles syncing data between Trello and local task files.
"""
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..licensing import require_feature
from .connection import get_client, _load_config
from .auth import load_token

app = typer.Typer(name="sync", help="Trello sync commands")
console = Console()


@app.command("progress")
@require_feature("trello")
def progress_comment(
    task_id: str = typer.Argument(..., help="Task ID (e.g., TASK-001)"),
    message: str = typer.Argument(None, help="Progress message"),
    blocked: Optional[str] = typer.Option(None, "--blocked", "-b", help="Report blocking issue"),
    waiting: Optional[str] = typer.Option(None, "--waiting", "-w", help="Report waiting for dependency"),
    step: Optional[str] = typer.Option(None, "--step", "-s", help="Report completed step"),
    started: bool = typer.Option(False, "--started", help="Report task started"),
    completed: bool = typer.Option(False, "--completed", "-c", help="Report task completed"),
    review: bool = typer.Option(False, "--review", "-r", help="Report submitted for review"),
    agent: str = typer.Option("claude", "--agent", "-a", help="Agent name for comment"),
):
    """Post a progress comment to a Trello card.

    Examples:
        # Report progress
        bpsai-pair trello progress TASK-001 "Completed authentication module"

        # Report blocking issue
        bpsai-pair trello progress TASK-001 --blocked "Waiting for API access"

        # Report step completion
        bpsai-pair trello progress TASK-001 --step "Unit tests passing"

        # Report task started
        bpsai-pair trello progress TASK-001 --started

        # Report completion with summary
        bpsai-pair trello progress TASK-001 --completed "Added user auth with OAuth2"
    """
    from .progress import create_progress_reporter
    from ..core.ops import find_paircoder_dir

    paircoder_dir = find_paircoder_dir()
    if not paircoder_dir.exists():
        console.print("[red]Not in a PairCoder project directory[/red]")
        raise typer.Exit(1)

    reporter = create_progress_reporter(paircoder_dir, task_id, agent)
    if not reporter:
        console.print("[red]Could not create progress reporter. Check Trello connection.[/red]")
        raise typer.Exit(1)

    success = False

    if started:
        success = reporter.report_start()
        if success:
            console.print("[green]Posted: Task started[/green]")
    elif blocked:
        success = reporter.report_blocked(blocked)
        if success:
            console.print(f"[green]Posted: Blocked - {blocked}[/green]")
    elif waiting:
        success = reporter.report_waiting(waiting)
        if success:
            console.print(f"[green]Posted: Waiting for {waiting}[/green]")
    elif step:
        success = reporter.report_step_complete(step)
        if success:
            console.print(f"[green]Posted: Completed step - {step}[/green]")
    elif completed:
        summary = message or "Task completed"
        success = reporter.report_completion(summary)
        if success:
            console.print("[green]Posted: Task completed[/green]")
    elif review:
        success = reporter.report_review()
        if success:
            console.print("[green]Posted: Submitted for review[/green]")
    elif message:
        success = reporter.report_progress(message)
        if success:
            console.print(f"[green]Posted: {message}[/green]")
    else:
        console.print("[yellow]No progress update specified. Use --help for options.[/yellow]")
        raise typer.Exit(1)

    if not success:
        console.print("[red]Failed to post progress comment[/red]")
        raise typer.Exit(1)


@app.command("sync")
@require_feature("trello")
def trello_sync(
    from_trello: bool = typer.Option(False, "--from-trello", help="Sync changes FROM Trello to local tasks"),
    preview: bool = typer.Option(False, "--preview", "-p", help="Preview changes without applying"),
    list_name: Optional[str] = typer.Option(None, "--list", "-l", help="Only sync cards from specific list"),
):
    """Sync tasks between Trello and local files.

    By default, previews what would be synced. Use --from-trello to pull
    changes from Trello cards and update local task files.

    Examples:
        # Preview what would be synced
        bpsai-pair trello sync --preview

        # Pull changes from Trello to local
        bpsai-pair trello sync --from-trello

        # Only sync cards from a specific list
        bpsai-pair trello sync --from-trello --list "In Progress"
    """
    from .sync import TrelloToLocalSync
    from .client import TrelloService
    from ..core.ops import find_paircoder_dir

    paircoder_dir = find_paircoder_dir()
    if not paircoder_dir.exists():
        console.print("[red]Not in a PairCoder project directory[/red]")
        raise typer.Exit(1)

    config = _load_config()
    board_id = config.get("trello", {}).get("board_id")
    if not board_id:
        console.print("[red]No board configured. Run: bpsai-pair trello use-board <id>[/red]")
        raise typer.Exit(1)

    token_data = load_token()
    if not token_data:
        console.print("[red]Not connected to Trello. Run: bpsai-pair trello connect[/red]")
        raise typer.Exit(1)

    # Create sync instance
    try:
        service = TrelloService(token_data["api_key"], token_data["token"])
        service.set_board(board_id)
        sync_manager = TrelloToLocalSync(service, paircoder_dir / "tasks")
    except Exception as e:
        console.print(f"[red]Failed to connect to Trello: {e}[/red]")
        raise typer.Exit(1)

    if preview or not from_trello:
        # Preview mode
        console.print("\n[bold]Sync Preview (Trello → Local)[/bold]\n")

        preview_results = sync_manager.get_sync_preview()
        if not preview_results:
            console.print("[dim]No cards with task IDs found on board[/dim]")
            return

        table = Table()
        table.add_column("Task ID", style="cyan")
        table.add_column("Action", style="yellow")
        table.add_column("Details")

        updates_pending = 0
        for item in preview_results:
            task_id = item["task_id"]
            action = item["action"]

            if action == "update":
                details = f"{item['field']}: {item['from']} → {item['to']}"
                table.add_row(task_id, "[green]update[/green]", details)
                updates_pending += 1
            elif action == "skip":
                reason = item.get("reason", "No changes")
                table.add_row(task_id, "[dim]skip[/dim]", f"[dim]{reason}[/dim]")
            elif action == "error":
                table.add_row(task_id, "[red]error[/red]", item.get("reason", "Unknown error"))

        console.print(table)
        console.print(f"\n[bold]{updates_pending}[/bold] task(s) would be updated")

        if updates_pending > 0 and not from_trello:
            console.print("\n[dim]Run with --from-trello to apply changes[/dim]")

    else:
        # Apply changes
        console.print("\n[bold]Syncing from Trello → Local[/bold]\n")

        list_filter = [list_name] if list_name else None
        results = sync_manager.sync_all_cards(list_filter=list_filter)

        if not results:
            console.print("[dim]No cards with task IDs found on board[/dim]")
            return

        updated = 0
        skipped = 0
        errors = 0

        for result in results:
            if result.action == "updated":
                updated += 1
                changes_str = ", ".join(
                    f"{k}: {v['from']} → {v['to']}"
                    for k, v in result.changes.items()
                )
                console.print(f"  [green]✓[/green] {result.task_id}: {changes_str}")

                # Show conflicts if any
                for conflict in result.conflicts:
                    console.print(f"    [yellow]⚠ Conflict: {conflict.field} ({conflict.resolution})[/yellow]")

            elif result.action == "skipped":
                skipped += 1
            elif result.action == "error":
                errors += 1
                console.print(f"  [red]✗[/red] {result.task_id}: {result.error}")

        console.print(f"\n[bold]Summary:[/bold] {updated} updated, {skipped} skipped, {errors} errors")
