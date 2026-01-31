"""
Task lifecycle commands for Trello: start, done, block.

These commands manage the lifecycle state of tasks on Trello.
"""
import logging
from typing import Optional

import typer
import yaml
from rich.console import Console

from ..licensing import require_feature
from .list_resolver import ListResolver
from .task_helpers import (
    get_board_client,
    format_card_id,
    log_activity,
    get_unchecked_ac_items,
    log_bypass,
    get_task_id_from_card,
    update_local_task_status,
    run_completion_hooks,
    update_plan_status_if_needed,
    check_task_budget,
    auto_check_acceptance_criteria,
    sync_local_ac_for_completion,
    complete_task_with_state_machine,
)

logger = logging.getLogger(__name__)
console = Console()


@require_feature("trello")
def task_start(
    card_id: str = typer.Argument(..., help="Card ID to start"),
    summary: str = typer.Option("Beginning work", "--summary", "-s", help="Start summary"),
    budget_override: bool = typer.Option(
        False, "--budget-override",
        help="Start despite budget warning (logged for audit)"
    ),
):
    """Start working on a task (moves to In Progress).

    Checks token budget before starting. Use --budget-override to bypass
    budget limits (logged for audit).
    """
    client, config = get_board_client()
    card, lst = client.find_card(card_id)

    if not card:
        console.print(f"[red]Card not found: {card_id}[/red]")
        raise typer.Exit(1)

    # Check token budget BEFORE starting
    task_id = get_task_id_from_card(card)
    if task_id:
        budget_ok = check_task_budget(task_id, card_id, budget_override)
        if not budget_ok:
            raise typer.Exit(1)

    if client.is_card_blocked(card):
        console.print("[red]Cannot start - card has unchecked dependencies[/red]")
        raise typer.Exit(1)

    # Move to In Progress
    resolver = ListResolver(client)
    target = resolver.find_list_for_status("in_progress")
    in_progress_list = target["name"] if target else "In Progress"
    client.move_card(card, in_progress_list)

    # Update Status custom field
    try:
        client.set_card_status(card, "In Progress")
    except Exception as e:
        logger.warning(f"Could not update Status field: {e}")

    # Log activity
    log_activity(card, "started", summary)

    console.print(f"[green]✓ Started: {card.name}[/green]")
    console.print(f"  Moved to: {in_progress_list}")
    console.print(f"  URL: {card.url}")

    # Update local task status and trigger plan transitions
    if task_id:
        try:
            from ..core.ops import find_paircoder_dir
            from ..planning.parser import TaskParser

            paircoder_dir = find_paircoder_dir()
            if paircoder_dir.exists():
                task_parser = TaskParser(paircoder_dir / "tasks")
                if task_parser.update_status(task_id, "in_progress"):
                    console.print(f"[green]✓ Local task {task_id} updated to in_progress[/green]")
                    update_plan_status_if_needed(task_id)
        except Exception as e:
            console.print(f"[yellow]⚠ Could not update local task: {e}[/yellow]")


@require_feature("trello")
def task_done(
    card_id: str = typer.Argument(..., help="Card ID to complete"),
    summary: str = typer.Option(..., "--summary", "-s", prompt=True, help="Completion summary"),
    list_name: Optional[str] = typer.Option(None, "--list", "-l", help="Target list (default: Deployed/Done)"),
    auto_check: bool = typer.Option(False, "--auto-check",
                                    help="Auto-check all acceptance criteria (use with caution)"),
    strict: bool = typer.Option(True, "--strict/--no-strict",
                                help="Block if acceptance criteria unchecked (default: strict)"),
):
    """Complete a task (moves to Done list)."""

    # ENFORCEMENT: Block --no-strict when strict_ac_verification is enabled
    if not strict:
        try:
            from ..core.ops import find_paircoder_dir
            config_path = find_paircoder_dir() / "config.yaml"
            if config_path.exists():
                with open(config_path, encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                strict_ac = config.get("enforcement", {}).get("strict_ac_verification", False)
                if strict_ac:
                    console.print(
                        "\n[red]❌ BLOCKED: --no-strict is disabled when strict_ac_verification is enabled.[/red]")
                    console.print("")
                    console.print("[yellow]You must verify acceptance criteria before completion:[/yellow]")
                    console.print("  1. Check items manually on Trello card")
                    console.print(f"  2. Use: [cyan]bpsai-pair ttask check {card_id} \"<item text>\"[/cyan]")
                    console.print(f"  3. Then: [cyan]bpsai-pair ttask done {card_id} --summary \"...\"[/cyan]")
                    console.print("")
                    console.print("[dim]This ensures all acceptance criteria are verified before completion.[/dim]")
                    raise typer.Exit(1)
        except (ImportError, FileNotFoundError):
            pass

    client, config = get_board_client()
    card, lst = client.find_card(card_id)

    if not card:
        console.print(f"[red]Card not found: {card_id}[/red]")
        raise typer.Exit(1)

    # Refresh card to get checklists
    try:
        card.fetch()
    except Exception:
        pass

    # Handle AC verification based on flags
    ac_status_msg = ""

    # AUTO-CHECK FIRST (if requested) - before strict verification
    if auto_check:
        checked_count = auto_check_acceptance_criteria(card, client)
        if checked_count > 0:
            console.print(f"[green]✓ Auto-checked {checked_count} acceptance criteria item(s)[/green]")
            try:
                card.fetch()
            except Exception:
                pass

    # Now verify (strict mode or after auto-check)
    task_id = get_task_id_from_card(card)
    if strict:
        unchecked = get_unchecked_ac_items(card)
        if unchecked:
            console.print(f"[red]❌ Cannot complete: {len(unchecked)} acceptance criteria item(s) unchecked[/red]")
            console.print("\n[dim]Unchecked items:[/dim]")
            for item in unchecked:
                console.print(f"  ○ {item.get('name', '')}")
            console.print("\n[dim]Options:[/dim]")
            console.print(f"  1. Check items: [cyan]bpsai-pair ttask check {card_id} \"<item text>\"[/cyan]")
            console.print("  2. Check on Trello directly")
            if auto_check:
                console.print("\n[yellow]Note: --auto-check ran but some items could not be checked.[/yellow]")
            raise typer.Exit(1)
        console.print("[green]✓ All Trello acceptance criteria verified[/green]")
        ac_status_msg = "All AC items verified"

        # STATE MACHINE: Transition to AC_VERIFIED (Trello AC complete)
        try:
            from ..core.task_state import TaskState, get_state_manager, is_state_machine_enabled
            if is_state_machine_enabled() and task_id:
                manager = get_state_manager()
                current = manager.get_state(task_id)
                if current == TaskState.IN_PROGRESS:
                    manager.transition(task_id, TaskState.AC_VERIFIED, trigger="trello_ac_verified")
        except Exception as e:
            logger.warning(f"State machine transition failed: {e}")
    else:
        unchecked = get_unchecked_ac_items(card)
        if unchecked:
            console.print(f"[yellow]⚠ Completing with {len(unchecked)} unchecked AC item(s)[/yellow]")
            log_bypass("ttask done", card_id, f"--no-strict with {len(unchecked)} unchecked AC items")
            ac_status_msg = f"Bypassed with {len(unchecked)} unchecked AC items (logged)"
        else:
            ac_status_msg = "AC verification skipped (all items already complete)"

    # Determine target list
    if list_name is None:
        resolver = ListResolver(client)
        target = resolver.find_list_for_status("done")
        list_name = target["name"] if target else "Deployed/Done"

    # Move to target list
    client.move_card(card, list_name)

    # Update Status custom field
    try:
        client.set_card_status(card, "Done")
    except Exception as e:
        logger.warning(f"Could not update Status field: {e}")

    # Log activity with AC status
    completion_msg = f"{summary} | {ac_status_msg}"
    log_activity(card, "completed", completion_msg)

    console.print(f"[green]✓ Completed: {card.name}[/green]")
    console.print(f"  Moved to: {list_name}")
    console.print(f"  Summary: {summary}")

    # STATE MACHINE: Sync local AC and transition to LOCAL_AC_VERIFIED
    # This ensures local task file AC items are checked before completion
    if task_id:
        local_ac_ok, local_ac_msg = sync_local_ac_for_completion(task_id, is_trello=True)
        if not local_ac_ok:
            console.print(f"[red]❌ BLOCKED: {local_ac_msg}[/red]")
            console.print("\n[dim]The Trello card was moved to Done, but local AC verification failed.[/dim]")
            console.print("[dim]Please check and update local AC items before completing.[/dim]")
            raise typer.Exit(1)
        console.print("[green]✓ Local acceptance criteria verified[/green]")

    # Auto-update local task file and run completion hooks
    # ENFORCEMENT: If task ID can be extracted and local file exists, update MUST succeed
    try:
        success, task_id_result = update_local_task_status(card, "done", summary)
        # Use task_id_result to avoid overwriting existing task_id
        if not task_id and task_id_result:
            task_id = task_id_result
        if success and task_id:
            console.print(f"[green]✓ Local task {task_id} updated to done[/green]")
            run_completion_hooks(task_id)
            update_plan_status_if_needed(task_id)

            # STATE MACHINE: Final transition to COMPLETED
            complete_ok, complete_msg = complete_task_with_state_machine(task_id, trigger="ttask_done")
            if not complete_ok:
                console.print(f"[yellow]⚠ State machine: {complete_msg}[/yellow]")
        elif task_id:
            # Task ID found but update failed - this is a blocking error
            console.print(f"[red]❌ BLOCKED: Could not update local task file for {task_id}[/red]")
            console.print(f"[dim]The Trello card was moved to Done, but local task file could not be updated.[/dim]")
            console.print(f"[dim]Please manually update: .paircoder/tasks/{task_id}.task.md[/dim]")
            raise typer.Exit(1)
        # If no task_id found, that's OK - card may not have a local task file
    except FileNotFoundError:
        task_id = get_task_id_from_card(card)
        if task_id:
            # Task ID found but file doesn't exist - warn but don't block
            # (file may have been deleted or never created)
            console.print(f"[yellow]⚠ Local task file not found for {task_id}[/yellow]")
            console.print(f"[dim]Expected: .paircoder/tasks/{task_id}.task.md[/dim]")
    except typer.Exit:
        raise  # Re-raise Exit exceptions
    except Exception as e:
        task_id = get_task_id_from_card(card)
        if task_id:
            console.print(f"[red]❌ BLOCKED: Error syncing local task {task_id}: {e}[/red]")
            raise typer.Exit(1)
        console.print(f"[yellow]⚠ Could not sync local task: {e}[/yellow]")


@require_feature("trello")
def task_block(
    card_id: str = typer.Argument(..., help="Card ID to block"),
    reason: str = typer.Option(..., "--reason", "-r", prompt=True, help="Block reason"),
):
    """Mark a task as blocked."""
    client, config = get_board_client()
    card, lst = client.find_card(card_id)

    if not card:
        console.print(f"[red]Card not found: {card_id}[/red]")
        raise typer.Exit(1)

    # Move to Blocked
    resolver = ListResolver(client)
    target = resolver.find_list_for_status("blocked")
    blocked_list = target["name"] if target else "Issues/Tech Debt"
    client.move_card(card, blocked_list)

    # Update Status custom field
    try:
        client.set_card_status(card, "Blocked")
    except Exception as e:
        logger.warning(f"Could not update Status field: {e}")

    # Log activity
    log_activity(card, "blocked", reason)

    console.print(f"[yellow]Blocked: {card.name}[/yellow]")
    console.print(f"  Reason: {reason}")
