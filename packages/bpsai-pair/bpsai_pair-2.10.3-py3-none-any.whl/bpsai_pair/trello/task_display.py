"""
Task display commands for Trello: list, show.

These commands display task information from Trello.
"""
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from ..licensing import require_feature
from .list_resolver import ListResolver
from .task_helpers import get_board_client, format_card_id

console = Console()


@require_feature("trello")
def task_list(
    list_name: Optional[str] = typer.Option(None, "--list", "-l", help="Filter by list name"),
    agent_tasks: bool = typer.Option(False, "--agent", "-a", help="Only show Agent Task cards"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (backlog, sprint, in_progress, review, done, blocked)"),
):
    """List tasks from Trello board."""
    client, config = get_board_client()

    # Use ListResolver to find lists by status
    resolver = ListResolver(client)

    def get_list_name(status_key: str, fallback: str) -> str:
        target = resolver.find_list_for_status(status_key)
        return target["name"] if target else fallback

    list_mappings = {
        "backlog": get_list_name("backlog", "Intake/Backlog"),
        "sprint": get_list_name("ready", "Planned/Ready"),
        "in_progress": get_list_name("in_progress", "In Progress"),
        "review": get_list_name("review", "Review/Testing"),
        "done": get_list_name("done", "Deployed/Done"),
        "blocked": get_list_name("blocked", "Issues/Tech Debt"),
    }

    cards = []

    if list_name:
        cards = client.get_cards_in_list(list_name)
    elif status:
        target_list = list_mappings.get(status, status)
        cards = client.get_cards_in_list(target_list)
    else:
        # Default: Sprint + In Progress
        for ln in [list_mappings.get("sprint", "Sprint"), list_mappings.get("in_progress", "In Progress")]:
            cards.extend(client.get_cards_in_list(ln))

    # Filter for agent tasks if requested
    if agent_tasks:
        filtered = []
        agent_field = config.get("trello", {}).get("custom_fields", {}).get("agent_task", "Agent Task")
        for card in cards:
            try:
                field = card.get_custom_field_by_name(agent_field)
                if field and field.value == True:
                    filtered.append(card)
            except Exception:
                pass
        cards = filtered

    if not cards:
        console.print("[yellow]No tasks found matching criteria[/yellow]")
        return

    table = Table(title="Tasks")
    table.add_column("ID", style="cyan", width=12)
    table.add_column("Title", width=40)
    table.add_column("List", style="dim")
    table.add_column("Priority", justify="center")
    table.add_column("Status", justify="center")

    priority_field = config.get("trello", {}).get("custom_fields", {}).get("priority", "Priority")

    for card in cards:
        try:
            card_list = card.get_list().name
        except Exception:
            card_list = "Unknown"

        blocked = "[red]Blocked[/red]" if client.is_card_blocked(card) else "[green]Ready[/green]"

        # Try to get priority
        priority = "-"
        try:
            pfield = card.get_custom_field_by_name(priority_field)
            if pfield and pfield.value:
                priority = str(pfield.value)
        except Exception:
            pass

        table.add_row(
            format_card_id(card),
            card.name[:40],
            card_list,
            priority,
            blocked
        )

    console.print(table)


@require_feature("trello")
def task_show(card_id: str = typer.Argument(..., help="Card ID (e.g., TRELLO-123 or just 123)")):
    """Show task details from Trello."""
    client, config = get_board_client()
    card, lst = client.find_card(card_id)

    if not card:
        console.print(f"[red]Card not found: {card_id}[/red]")
        raise typer.Exit(1)

    try:
        card.fetch()  # Get full details
    except Exception:
        pass

    # Header
    console.print(Panel(f"[bold]{card.name}[/bold]", subtitle=format_card_id(card)))

    # Metadata
    if lst:
        console.print(f"[dim]List:[/dim] {lst.name}")
    console.print(f"[dim]URL:[/dim] {card.url}")

    # Labels
    try:
        if card.labels:
            labels = ", ".join([l.name for l in card.labels if l.name])
            if labels:
                console.print(f"[dim]Labels:[/dim] {labels}")
    except Exception:
        pass

    # Priority
    try:
        priority_field = config.get("trello", {}).get("custom_fields", {}).get("priority", "Priority")
        pfield = card.get_custom_field_by_name(priority_field)
        if pfield and pfield.value:
            console.print(f"[dim]Priority:[/dim] {pfield.value}")
    except Exception:
        pass

    # Blocked status
    if client.is_card_blocked(card):
        console.print("[red]BLOCKED - has unchecked dependencies[/red]")

    # Description
    try:
        if card.description:
            console.print("\n[dim]Description:[/dim]")
            console.print(Markdown(card.description))
    except Exception:
        pass

    # Checklists
    try:
        if card.checklists:
            console.print("\n[dim]Checklists:[/dim]")
            for cl in card.checklists:
                console.print(f"  [bold]{cl.name}[/bold]")
                for item in cl.items:
                    check = "[green]✓[/green]" if item.get("checked") else "○"
                    console.print(f"    {check} {item.get('name', '')}")
    except Exception:
        pass
