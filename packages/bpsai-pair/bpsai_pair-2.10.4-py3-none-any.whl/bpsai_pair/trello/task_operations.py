"""
Task operations commands for Trello: move, comment, check, uncheck.

These commands perform various operations on Trello tasks.
"""
import logging
from typing import Optional

import typer
from rich.console import Console

from ..licensing import require_feature
from .task_helpers import get_board_client, log_activity

logger = logging.getLogger(__name__)
console = Console()


@require_feature("trello")
def task_move(
    card_id: str = typer.Argument(..., help="Card ID"),
    list_name: str = typer.Option(..., "--list", "-l", help="Target list name"),
):
    """Move a task to a different list."""
    client, _ = get_board_client()
    card, lst = client.find_card(card_id)

    if not card:
        console.print(f"[red]Card not found: {card_id}[/red]")
        raise typer.Exit(1)

    old_list = lst.name if lst else "Unknown"
    client.move_card(card, list_name)

    # Try to update Status custom field based on target list
    list_lower = list_name.lower()
    status_value = None
    if "done" in list_lower or "deployed" in list_lower:
        status_value = "Done"
    elif "progress" in list_lower:
        status_value = "In Progress"
    elif "review" in list_lower or "testing" in list_lower:
        status_value = "In Review"
    elif "blocked" in list_lower or "issue" in list_lower or "debt" in list_lower:
        status_value = "Blocked"
    elif "ready" in list_lower or "planned" in list_lower or "backlog" in list_lower:
        status_value = "Ready"

    if status_value:
        try:
            client.set_card_status(card, status_value)
        except Exception as e:
            logger.warning(f"Could not update Status field: {e}")

    console.print(f"[green]✓ Moved: {card.name}[/green]")
    console.print(f"  {old_list} → {list_name}")


@require_feature("trello")
def task_comment(
    task_id: str = typer.Argument(..., help="Task or Card ID (e.g., TASK-001 or TRELLO-123)"),
    message: str = typer.Argument(..., help="Comment message"),
):
    """Add a progress comment to a task.

    Uses structured activity logging with emojis and timestamps.
    """
    from .activity import TrelloActivityLogger

    client, _ = get_board_client()

    # Create activity logger for structured comments
    activity_logger = TrelloActivityLogger(client)

    # Try to log via activity logger (handles both TASK-XXX and TRELLO-XXX)
    success = activity_logger.log_progress(task_id, note=message)

    if success:
        console.print(f"[green]✓ Progress logged for: {task_id}[/green]")
        console.print(f"  📝 {message}")
    else:
        # Fall back to direct card lookup
        card, lst = client.find_card(task_id)

        if not card:
            console.print(f"[red]Card not found: {task_id}[/red]")
            raise typer.Exit(1)

        # Log as progress update
        log_activity(card, "progress", message)
        console.print(f"[green]✓ Comment added to: {card.name}[/green]")


@require_feature("trello")
def check_item(
    task_id: str = typer.Argument(..., help="Task ID (e.g., TASK-089 or TRELLO-123)"),
    item_text: str = typer.Argument(..., help="Checklist item text (partial match OK)"),
    checklist_name: Optional[str] = typer.Option(None, "--checklist", "-c", help="Checklist name (default: search all)"),
):
    """Check off a checklist item as complete.

    Use this to mark acceptance criteria as done while working on a task.
    Partial text matching is supported - just provide enough to uniquely identify the item.

    Examples:
        bpsai-pair ttask check TASK-089 "No hardcoded credentials"
        bpsai-pair ttask check TASK-089 "SQL injection" --checklist "Acceptance Criteria"
    """
    import requests
    from .auth import load_token

    client, _ = get_board_client()
    card, _ = client.find_card(task_id)

    if not card:
        console.print(f"[red]Card not found: {task_id}[/red]")
        raise typer.Exit(1)

    # Refresh card to get checklists
    try:
        card.fetch()
    except Exception:
        pass

    if not card.checklists:
        console.print(f"[yellow]No checklists found on card: {task_id}[/yellow]")
        raise typer.Exit(1)

    # Search for the item
    found_item = None
    found_checklist = None
    item_text_lower = item_text.lower()

    for checklist in card.checklists:
        # Filter by checklist name if specified
        if checklist_name and checklist.name.lower() != checklist_name.lower():
            continue

        for item in checklist.items:
            item_name = item.get("name", "")
            if item_text_lower in item_name.lower():
                if found_item is not None:
                    # Multiple matches - need more specific text
                    console.print(f"[yellow]Multiple items match '{item_text}'. Be more specific.[/yellow]")
                    console.print(f"  Found: {found_item.get('name', '')}")
                    console.print(f"  Found: {item_name}")
                    raise typer.Exit(1)
                found_item = item
                found_checklist = checklist

    if not found_item:
        console.print(f"[red]Checklist item not found: {item_text}[/red]")
        console.print("\n[dim]Available items:[/dim]")
        for checklist in card.checklists:
            console.print(f"  [bold]{checklist.name}[/bold]")
            for item in checklist.items:
                check = "✓" if item.get("checked") else "○"
                console.print(f"    {check} {item.get('name', '')}")
        raise typer.Exit(1)

    # Check if already checked
    if found_item.get("checked"):
        console.print(f"[dim]Already checked: {found_item.get('name', '')}[/dim]")
        return

    # Check the item using py-trello's method
    try:
        found_checklist.set_checklist_item(found_item.get("name"), checked=True)
        console.print(f"[green]✓ Checked: {found_item.get('name', '')}[/green]")
        log_activity(card, "checked", found_item.get("name", "")[:50])
    except AttributeError:
        # Fallback: use direct API call if py-trello method not available
        try:
            creds = load_token()
            check_item_id = found_item.get("id")
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
                console.print(f"[green]✓ Checked: {found_item.get('name', '')}[/green]")
                log_activity(card, "checked", found_item.get("name", "")[:50])
            else:
                console.print(f"[red]Failed to check item: {response.status_code}[/red]")
                raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error checking item: {e}[/red]")
            raise typer.Exit(1)


@require_feature("trello")
def uncheck_item(
    task_id: str = typer.Argument(..., help="Task ID (e.g., TASK-089 or TRELLO-123)"),
    item_text: str = typer.Argument(..., help="Checklist item text (partial match OK)"),
    checklist_name: Optional[str] = typer.Option(None, "--checklist", "-c", help="Checklist name (default: search all)"),
):
    """Uncheck a checklist item (mark as incomplete).

    Use this if you need to undo a checked item.

    Examples:
        bpsai-pair ttask uncheck TASK-089 "No hardcoded credentials"
    """
    import requests
    from .auth import load_token

    client, _ = get_board_client()
    card, _ = client.find_card(task_id)

    if not card:
        console.print(f"[red]Card not found: {task_id}[/red]")
        raise typer.Exit(1)

    try:
        card.fetch()
    except Exception:
        pass

    if not card.checklists:
        console.print(f"[yellow]No checklists found on card: {task_id}[/yellow]")
        raise typer.Exit(1)

    # Search for the item
    found_item = None
    found_checklist = None
    item_text_lower = item_text.lower()

    for checklist in card.checklists:
        if checklist_name and checklist.name.lower() != checklist_name.lower():
            continue

        for item in checklist.items:
            item_name = item.get("name", "")
            if item_text_lower in item_name.lower():
                if found_item is not None:
                    console.print(f"[yellow]Multiple items match '{item_text}'. Be more specific.[/yellow]")
                    raise typer.Exit(1)
                found_item = item
                found_checklist = checklist

    if not found_item:
        console.print(f"[red]Checklist item not found: {item_text}[/red]")
        raise typer.Exit(1)

    if not found_item.get("checked"):
        console.print(f"[dim]Already unchecked: {found_item.get('name', '')}[/dim]")
        return

    try:
        found_checklist.set_checklist_item(found_item.get("name"), checked=False)
        console.print(f"[yellow]○ Unchecked: {found_item.get('name', '')}[/yellow]")
    except AttributeError:
        try:
            creds = load_token()
            check_item_id = found_item.get("id")
            url = f"https://api.trello.com/1/cards/{card.id}/checkItem/{check_item_id}"

            response = requests.put(
                url,
                params={
                    "key": creds["api_key"],
                    "token": creds["token"],
                    "state": "incomplete"
                }
            )

            if response.status_code == 200:
                console.print(f"[yellow]○ Unchecked: {found_item.get('name', '')}[/yellow]")
            else:
                console.print(f"[red]Failed to uncheck item: {response.status_code}[/red]")
                raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error unchecking item: {e}[/red]")
            raise typer.Exit(1)
