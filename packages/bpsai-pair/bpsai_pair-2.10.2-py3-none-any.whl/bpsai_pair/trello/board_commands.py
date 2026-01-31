"""
Trello board management commands: boards, use-board, lists, config.

This module handles board selection and configuration.
"""
import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..licensing import require_feature
from .connection import get_client, _load_config, _save_config

app = typer.Typer(name="board", help="Trello board management commands")
console = Console()


@app.command()
@require_feature("trello")
def boards(
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List available Trello boards."""
    client = get_client()
    board_list = client.list_boards()

    # Filter out closed boards
    open_boards = [b for b in board_list if not b.closed]

    if as_json:
        boards_data = [
            {
                "id": board.id,
                "name": board.name,
                "url": board.url,
                "shortUrl": getattr(board, "shortUrl", board.url),
            }
            for board in open_boards
        ]
        console.print(json.dumps(boards_data, indent=2))
        return

    table = Table(title="Trello Boards")
    table.add_column("Name", style="cyan")
    table.add_column("ID", style="green", no_wrap=True)
    table.add_column("URL", style="blue")

    for board in open_boards:
        table.add_row(board.name, board.id, board.url)

    console.print(table)


@app.command("use-board")
@require_feature("trello")
def use_board(board_id: str = typer.Argument(..., help="Board ID to use")):
    """Set the active Trello board for this project."""
    client = get_client()
    board = client.set_board(board_id)

    config = _load_config()
    if "trello" not in config:
        config["trello"] = {}
    config["trello"]["board_id"] = board_id
    config["trello"]["board_name"] = board.name
    config["trello"]["enabled"] = True
    _save_config(config)

    console.print(f"[green]✓ Using board: {board.name}[/green]")

    lists = client.get_board_lists()
    console.print(f"\nLists: {', '.join(lists.keys())}")


@app.command()
@require_feature("trello")
def lists():
    """Show lists on the active board."""
    config = _load_config()
    board_id = config.get("trello", {}).get("board_id")

    if not board_id:
        console.print("[red]No board configured. Run: bpsai-pair trello use-board <id>[/red]")
        raise typer.Exit(1)

    client = get_client()
    client.set_board(board_id)

    table = Table(title=f"Lists on {config['trello'].get('board_name', board_id)}")
    table.add_column("Name")
    table.add_column("Cards", justify="right")

    for name, lst in client.get_board_lists().items():
        card_count = len(lst.list_cards())
        table.add_row(name, str(card_count))

    console.print(table)


@app.command("config")
@require_feature("trello")
def trello_config(
    show: bool = typer.Option(False, "--show", help="Show current config"),
    set_list: Optional[str] = typer.Option(None, "--set-list", help="Set list mapping (format: status=ListName)"),
    set_field: Optional[str] = typer.Option(None, "--set-field", help="Set custom field (format: field=FieldName)"),
    agent: Optional[str] = typer.Option(None, "--agent", help="Set agent identity (claude/codex)"),
):
    """View or modify Trello configuration."""
    config = _load_config()
    trello = config.get("trello", {})

    # Merge with defaults
    defaults = {
        "enabled": False,
        "board_id": None,
        "board_name": None,
        "lists": {
            "backlog": "Backlog",
            "sprint": "Sprint",
            "in_progress": "In Progress",
            "review": "In Review",
            "done": "Done",
            "blocked": "Blocked",
        },
        "custom_fields": {
            "agent_task": "Agent Task",
            "priority": "Priority",
        },
        "agent_identity": "claude",
        "auto_sync": True,
    }

    for key, default in defaults.items():
        if key not in trello:
            trello[key] = default
        elif isinstance(default, dict) and isinstance(trello.get(key), dict):
            trello[key] = {**default, **trello[key]}

    if show or (not set_list and not set_field and not agent):
        console.print("[bold]Trello Configuration[/bold]\n")
        console.print(f"Enabled: {trello['enabled']}")
        console.print(f"Board: {trello['board_name']} ({trello['board_id']})")
        console.print(f"Agent: {trello['agent_identity']}")
        console.print(f"Auto-sync: {trello['auto_sync']}")
        console.print("\n[dim]List Mappings:[/dim]")
        for status, list_name in trello.get('lists', {}).items():
            console.print(f"  {status}: {list_name}")
        console.print("\n[dim]Custom Fields:[/dim]")
        for field, name in trello.get('custom_fields', {}).items():
            console.print(f"  {field}: {name}")
        return

    updates_made = False

    if set_list:
        if "=" not in set_list:
            console.print("[red]Invalid format. Use: --set-list status=ListName[/red]")
            raise typer.Exit(1)
        status, list_name = set_list.split("=", 1)
        if "lists" not in trello:
            trello["lists"] = {}
        trello["lists"][status] = list_name
        console.print(f"[green]✓ Set list mapping: {status} → {list_name}[/green]")
        updates_made = True

    if set_field:
        if "=" not in set_field:
            console.print("[red]Invalid format. Use: --set-field field=FieldName[/red]")
            raise typer.Exit(1)
        field, name = set_field.split("=", 1)
        if "custom_fields" not in trello:
            trello["custom_fields"] = {}
        trello["custom_fields"][field] = name
        console.print(f"[green]✓ Set custom field: {field} → {name}[/green]")
        updates_made = True

    if agent:
        if agent not in ["claude", "codex"]:
            console.print("[red]Agent must be 'claude' or 'codex'[/red]")
            raise typer.Exit(1)
        trello["agent_identity"] = agent
        console.print(f"[green]✓ Set agent identity: {agent}[/green]")
        updates_made = True

    if updates_made:
        config["trello"] = trello
        _save_config(config)
