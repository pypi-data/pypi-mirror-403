"""
Shared helpers for Trello task commands.

This module contains utility functions used across task commands:
- Board client initialization
- Card formatting
- Activity logging
- Acceptance criteria helpers
- Local task synchronization
- Budget checking
"""
import logging
import re
from typing import Optional, Tuple, List, Dict, Any

import typer
import yaml
from rich.console import Console

from .auth import load_token
from .client import TrelloService

logger = logging.getLogger(__name__)
console = Console()

AGENT_TYPE = "claude"  # Identifies this agent in comments


def get_board_client(board_id: Optional[str] = None) -> Tuple[TrelloService, Dict[str, Any]]:
    """Get client with board already set.

    Args:
        board_id: Optional board ID override (uses config if not provided)

    Returns:
        Tuple of (TrelloService, config dict)

    Raises:
        typer.Exit: If not connected or no board configured
    """
    creds = load_token()
    if not creds:
        console.print("[red]Not connected to Trello. Run: bpsai-pair trello connect[/red]")
        raise typer.Exit(1)

    # Load config
    config: Dict[str, Any] = {}
    try:
        from ..core.ops import find_project_root
        config_file = find_project_root() / ".paircoder" / "config.yaml"
        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
    except Exception:
        pass

    if board_id is None:
        board_id = config.get("trello", {}).get("board_id")

    if not board_id:
        console.print("[red]No board configured. Run: bpsai-pair trello use-board <id>[/red]")
        raise typer.Exit(1)

    try:
        client = TrelloService(api_key=creds["api_key"], token=creds["token"])
        client.set_board(board_id)
    except ImportError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    return client, config


def format_card_id(card: Any) -> str:
    """Format card ID for display.

    Args:
        card: Trello card object

    Returns:
        Formatted card ID string (e.g., "TRELLO-123")
    """
    return f"TRELLO-{card.short_id}"


def log_activity(card: Any, action: str, summary: str) -> None:
    """Add activity comment to card.

    Args:
        card: Trello card object
        action: Action type (started, completed, blocked, progress)
        summary: Summary text
    """
    comment = f"[{AGENT_TYPE}] {action}: {summary}"
    try:
        card.comment(comment)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not add comment: {e}[/yellow]")


def get_unchecked_ac_items(card: Any, checklist_name: str = "Acceptance Criteria") -> List[Dict[str, Any]]:
    """Get all unchecked items in the Acceptance Criteria checklist.

    Args:
        card: Trello card object
        checklist_name: Name of the checklist to check (default: "Acceptance Criteria")

    Returns:
        List of unchecked item dicts with 'id' and 'name' keys
    """
    if not card.checklists:
        return []

    unchecked = []
    for checklist in card.checklists:
        if checklist.name.lower() != checklist_name.lower():
            continue

        for item in checklist.items:
            if not item.get("checked"):
                unchecked.append(item)

    return unchecked


def log_bypass(command: str, task_id: str, reason: str = "forced") -> None:
    """Log bypass to audit file - delegates to core module."""
    from ..core.bypass_log import log_bypass as core_log_bypass
    core_log_bypass(command=command, target=task_id, reason=reason)


def get_task_id_from_card(card: Any) -> Optional[str]:
    """Extract local task ID from Trello card.

    Looks for task ID in:
    1. Card name pattern "[T29.6.2]" or "[TASK-123]" (bracketed)
    2. Card name pattern "T29.6.2: ..." or "TASK-123: ..." (at start)
    3. Card description containing "Task: T29.6.2"

    Supports both 2-part (T29.6) and 3-part (T29.6.2) sprint task IDs.

    Args:
        card: Trello card object with name and description attributes

    Returns:
        Task ID string (e.g., "T29.6.2") or None if not found
    """
    # Get card name
    name = card.name if hasattr(card, 'name') else ""
    if not isinstance(name, str):
        name = ""

    # Pattern for task IDs: T29.6 or T29.6.2 (2-part or 3-part sprint IDs)
    # Also matches TASK-123 format
    task_id_pattern = r'T\d+\.\d+(?:\.\d+)?|TASK-\d+'

    # Try bracketed pattern first (e.g., "[T29.6.2] Create module")
    if name:
        match = re.search(rf'\[({task_id_pattern})]', name)
        if match:
            return match.group(1)

        # Try start of name pattern (e.g., "T29.6.2: Create module" or "T29.6.2 - Create")
        match = re.match(rf'^({task_id_pattern})[\s:\-]', name)
        if match:
            return match.group(1)

    # Try description
    desc = card.description if hasattr(card, 'description') else ""
    if desc and isinstance(desc, str):
        match = re.search(rf'Task:\s*({task_id_pattern})', desc)
        if match:
            return match.group(1)

    return None


def update_local_task_status(card: Any, status: str, summary: str = "") -> Tuple[bool, Optional[str]]:
    """Update the corresponding local task file after ttask operation.

    Args:
        card: Trello card object (with name and description attributes)
        status: The new status to set
        summary: Optional completion summary

    Returns:
        Tuple of (success: bool, task_id: Optional[str])

    Raises:
        FileNotFoundError: If task ID is found but local task file doesn't exist
    """
    try:
        # Extract task ID from card
        task_id = get_task_id_from_card(card)
        if not task_id:
            return False, None

        # Find paircoder dir
        from ..core.ops import find_paircoder_dir
        paircoder_dir = find_paircoder_dir()
        if not paircoder_dir.exists():
            return False, task_id

        # Import task parser
        from ..planning.parser import TaskParser

        task_parser = TaskParser(paircoder_dir / "tasks")

        # Check if task file exists before attempting update
        # This allows caller to distinguish "file not found" from "update failed"
        task = task_parser.get_task_by_id(task_id)
        if not task:
            raise FileNotFoundError(f"Task file not found for {task_id}")

        success = task_parser.update_status(task_id, status)

        return success, task_id
    except FileNotFoundError:
        raise  # Re-raise for caller to handle
    except Exception as e:
        console.print(f"[yellow]⚠ Could not update local task file: {e}[/yellow]")
        return False, None


def run_completion_hooks(task_id: str) -> bool:
    """Run completion hooks to update state.md and other side effects.

    Args:
        task_id: The task ID that was completed

    Returns:
        True if hooks ran successfully, False otherwise
    """
    try:
        from ..core.ops import find_paircoder_dir

        paircoder_dir = find_paircoder_dir()
        if not paircoder_dir.exists():
            return False

        # Record CLI update to cache (for manual edit detection)
        try:
            from ..planning.cli_update_cache import get_cli_update_cache
            cli_cache = get_cli_update_cache(paircoder_dir)
            cli_cache.record_update(task_id, "done")
        except Exception:
            pass  # Best effort

        # Try to run hooks if available
        try:
            from ..core.hooks import HookRunner, HookContext, load_config
            from ..planning.parser import TaskParser

            config = load_config(paircoder_dir)
            hook_runner = HookRunner(config, paircoder_dir)

            # Load the task object for hooks that need it
            task = None
            try:
                tasks_dir = paircoder_dir / "tasks"
                parser = TaskParser(tasks_dir)
                task = parser.get_task_by_id(task_id)
            except Exception:
                pass

            # Create context for completion hooks
            context = HookContext(
                task_id=task_id,
                task=task,
                event="on_task_complete",
            )
            hook_runner.run_hooks("on_task_complete", context)
            return True
        except ImportError:
            return False
        except Exception as e:
            console.print(f"[yellow]⚠ Could not run completion hooks: {e}[/yellow]")
            return False
    except Exception:
        return False


def update_plan_status_if_needed(task_id: str) -> bool:
    """Update plan status based on task status change.

    Args:
        task_id: The task ID that was updated

    Returns:
        True if plan status was updated, False otherwise
    """
    try:
        from ..core.ops import find_paircoder_dir
        from ..planning.parser import TaskParser, PlanParser

        paircoder_dir = find_paircoder_dir()
        if not paircoder_dir.exists():
            return False

        task_parser = TaskParser(paircoder_dir / "tasks")
        task = task_parser.get_task_by_id(task_id)
        if not task or not task.plan_id:
            return False

        plan_parser = PlanParser(paircoder_dir / "plans")
        plan_updated = plan_parser.check_and_update_plan_status(
            task.plan_id, paircoder_dir / "tasks"
        )

        if plan_updated:
            plan = plan_parser.get_plan_by_id(task.plan_id)
            if plan:
                console.print(f"  → Plan {plan.id} is now {plan.status.value}")

        return plan_updated
    except Exception as e:
        console.print(f"[yellow]⚠ Could not update plan status: {e}[/yellow]")
        return False


def check_task_budget(task_id: str, card_id: str, budget_override: bool = False) -> bool:
    """Check if task can proceed within token budget.

    Args:
        task_id: The task ID to estimate tokens for
        card_id: The Trello card ID (for display)
        budget_override: If True, log bypass and allow anyway

    Returns:
        True if task can proceed, False if blocked
    """
    try:
        from ..core.ops import find_paircoder_dir
        from ..planning.parser import TaskParser
        from ..metrics.estimation import TokenEstimator
        from ..metrics.budget import BudgetEnforcer
        from ..metrics.collector import MetricsCollector

        paircoder_dir = find_paircoder_dir()
        if not paircoder_dir.exists():
            return True

        task_parser = TaskParser(paircoder_dir / "tasks")
        task = task_parser.get_task_by_id(task_id)
        if not task:
            return True

        estimator = TokenEstimator()
        token_estimate = estimator.estimate_for_task(task)
        estimated_tokens = token_estimate.total_tokens

        # Convert tokens to estimated cost
        estimated_cost_usd = (estimated_tokens / 1000) * 0.015

        collector = MetricsCollector(paircoder_dir / "metrics")
        budget = BudgetEnforcer(collector)
        can_proceed, reason = budget.can_proceed(estimated_cost_usd)

        if not can_proceed:
            if budget_override:
                log_bypass("budget_override", task_id, f"User override: {reason}")
                console.print(f"[yellow]⚠ Starting despite budget limit (logged): {reason}[/yellow]")
                return True
            else:
                status = budget.check_budget()
                console.print("[red]❌ BLOCKED: Task would exceed token budget[/red]")
                console.print("")
                console.print(f"[dim]Estimated tokens:[/dim] {estimated_tokens:,}")
                console.print(f"[dim]Estimated cost:[/dim]   ${estimated_cost_usd:.2f}")
                console.print(f"[dim]Daily remaining:[/dim]  ${status.daily_remaining:.2f}")
                console.print(f"[dim]Daily limit:[/dim]      ${status.daily_limit:.2f}")
                console.print("")
                console.print("[yellow]Options:[/yellow]")
                console.print("  1. Wait until tomorrow (limit resets)")
                console.print(f"  2. Override: [cyan]bpsai-pair ttask start {card_id} --budget-override[/cyan]")
                console.print("  3. Check budget: [cyan]bpsai-pair budget status[/cyan]")
                return False

        console.print(f"[dim]Budget check passed ({estimated_tokens:,} tokens, ~${estimated_cost_usd:.2f})[/dim]")
        return True

    except ImportError as e:
        console.print(f"[dim]Budget check skipped: {e}[/dim]")
        return True
    except Exception as e:
        console.print(f"[dim]Budget check skipped: {e}[/dim]")
        return True


def sync_local_ac_for_completion(task_id: str, is_trello: bool = True) -> tuple[bool, str]:
    """Sync local AC items and verify state machine transition for completion.

    This function:
    1. If is_trello: Auto-checks all local AC items (sync from Trello)
    2. Verifies local AC items are all checked
    3. Transitions state machine to LOCAL_AC_VERIFIED (if enabled)

    Args:
        task_id: The task ID to sync AC for
        is_trello: True if coming from ttask done (Trello path), False for local path

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        from ..core.task_state import (
            TaskState,
            get_state_manager,
            is_state_machine_enabled,
            verify_local_ac,
            sync_trello_ac_to_local,
        )

        # For Trello path: auto-check all local AC items (sync from Trello completion)
        if is_trello:
            sync_result = sync_trello_ac_to_local(task_id)
            if sync_result.get("error"):
                return False, f"Failed to sync local AC: {sync_result['error']}"
            if sync_result.get("checked_count", 0) > 0:
                console.print(f"[green]✓ Synced {sync_result['checked_count']} local AC item(s)[/green]")

        # Verify all local AC items are checked
        ac_result = verify_local_ac(task_id)
        if ac_result.get("error"):
            return False, f"AC verification error: {ac_result['error']}"

        if not ac_result["verified"]:
            unchecked = ac_result["unchecked_items"]
            unchecked_list = "\n".join(f"  ○ {item}" for item in unchecked[:5])
            if len(unchecked) > 5:
                unchecked_list += f"\n  ... and {len(unchecked) - 5} more"
            return False, (
                f"{len(unchecked)} local AC item(s) unchecked:\n{unchecked_list}\n"
                f"Check items: bpsai-pair task check {task_id}"
            )

        # Transition state machine if enabled
        if is_state_machine_enabled():
            manager = get_state_manager()
            current = manager.get_state(task_id)

            # Determine the appropriate source state
            if is_trello and current == TaskState.AC_VERIFIED:
                # Trello path: AC_VERIFIED → LOCAL_AC_VERIFIED
                manager.transition(task_id, TaskState.LOCAL_AC_VERIFIED, trigger="sync_local_ac")
            elif current == TaskState.IN_PROGRESS:
                # Non-Trello path: IN_PROGRESS → LOCAL_AC_VERIFIED
                manager.transition(task_id, TaskState.LOCAL_AC_VERIFIED, trigger="verify_local_ac")
            elif current == TaskState.LOCAL_AC_VERIFIED:
                # Already in correct state
                pass
            # else: state machine not tracking this task yet - that's OK

        return True, "Local AC verified"

    except Exception as e:
        return False, f"Error syncing local AC: {e}"


def complete_task_with_state_machine(task_id: str, trigger: str = "completion") -> tuple[bool, str]:
    """Transition task to COMPLETED state via state machine (if enabled).

    Args:
        task_id: The task ID to complete
        trigger: Description of what triggered completion

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        from ..core.task_state import (
            TaskState,
            get_state_manager,
            is_state_machine_enabled,
        )

        if not is_state_machine_enabled():
            return True, "State machine not enabled"

        manager = get_state_manager()
        current = manager.get_state(task_id)

        # Can only complete from LOCAL_AC_VERIFIED
        if current != TaskState.LOCAL_AC_VERIFIED:
            allowed, reason = manager.can_transition(task_id, TaskState.COMPLETED)
            if not allowed:
                return False, reason

        manager.transition(task_id, TaskState.COMPLETED, trigger=trigger)
        return True, "Task completed"

    except Exception as e:
        return False, f"Error completing task: {e}"


def auto_check_acceptance_criteria(card: Any, client: TrelloService, checklist_name: str = "Acceptance Criteria") -> int:
    """Check off all items in the Acceptance Criteria checklist.

    Args:
        card: Trello card object
        client: TrelloService instance
        checklist_name: Name of the checklist to check off

    Returns:
        Number of items that were checked off
    """
    import requests

    if not card.checklists:
        return 0

    checked_count = 0

    for checklist in card.checklists:
        if checklist.name.lower() != checklist_name.lower():
            continue

        for item in checklist.items:
            if item.get("checked"):
                continue

            item_name = item.get("name", "")

            try:
                checklist.set_checklist_item(item_name, checked=True)
                checked_count += 1
            except AttributeError:
                try:
                    creds = load_token()
                    check_item_id = item.get("id")
                    url = f"https://api.trello.com/1/cards/{card.id}/checkItem/{check_item_id}"

                    response = requests.put(
                        url,
                        params={
                            "key": creds["api_key"],
                            "token": creds["token"],
                            "state": "complete"
                        }
                    )

                    if response.status_code == 200:
                        checked_count += 1
                except Exception:
                    pass

    return checked_count
