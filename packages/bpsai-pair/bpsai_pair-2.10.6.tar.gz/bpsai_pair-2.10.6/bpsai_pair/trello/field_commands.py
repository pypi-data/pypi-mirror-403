"""
Trello field commands: list-fields, fields, set-field, apply-defaults.

This module handles custom field operations on Trello cards.
"""
import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..licensing import require_feature
from .connection import get_client, _load_config, _save_config

app = typer.Typer(name="field", help="Trello custom field commands")
console = Console()


@app.command("list-fields")
@require_feature("trello")
def list_fields():
    """List all custom fields on the active board (table format).

    Shows field names, types, and available options for dropdown fields.

    Examples:
        bpsai-pair trello list-fields
    """
    config = _load_config()
    board_id = config.get("trello", {}).get("board_id")

    if not board_id:
        console.print("[red]No board configured. Run: bpsai-pair trello use-board <id>[/red]")
        raise typer.Exit(1)

    client = get_client()
    client.set_board(board_id)

    fields = client.get_custom_fields()

    if not fields:
        console.print("[yellow]No custom fields found on this board[/yellow]")
        raise typer.Exit(0)

    table = Table(title="Custom Fields")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Options", style="dim")

    for field in fields:
        options = ""
        if field.field_type == "list" and field.options:
            options = ", ".join(field.options.values())
        table.add_row(field.name, field.field_type, options)

    console.print(table)


@app.command("fields")
@require_feature("trello")
def fields_cmd(
    board: Optional[str] = typer.Option(None, "--board", "-b", help="Board ID (uses config default if not specified)"),
    refresh: bool = typer.Option(False, "--refresh", help="Force refresh from API"),
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show custom fields and their valid options for a board.

    This command shows all custom fields on the board with their types
    and valid option values. Use this to discover what values can be
    set on cards.

    Examples:
        bpsai-pair trello fields
        bpsai-pair trello fields --json
        bpsai-pair trello fields --refresh
        bpsai-pair trello fields --board abc123
    """
    from .fields import get_cached_board_fields

    config = _load_config()
    board_id = board or config.get("trello", {}).get("board_id")

    if not board_id:
        console.print("[red]Board ID required. Either:[/red]")
        console.print("  1. Use --board <board-id>")
        console.print("  2. Set trello.board_id in .paircoder/config.yaml")
        console.print("\n[dim]Run 'bpsai-pair trello boards --json' to see available boards.[/dim]")
        raise typer.Exit(1)

    client = get_client()
    client.set_board(board_id)

    fields = get_cached_board_fields(board_id, client, force_refresh=refresh)

    if not fields:
        console.print("[yellow]No custom fields found on this board[/yellow]")
        raise typer.Exit(0)

    if as_json:
        console.print(json.dumps(fields, indent=2))
        return

    # Display fields with options in a readable format
    for field_name, field_data in sorted(fields.items()):
        console.print(f"\n[bold]{field_name}[/bold] ({field_data['type']})")

        if field_data["options"]:
            for opt in sorted(field_data["options"].keys()):
                console.print(f"  • {opt}")
        elif field_data["type"] == "text":
            console.print("  (free text)")
        elif field_data["type"] == "checkbox":
            console.print("  (true/false)")
        elif field_data["type"] == "number":
            console.print("  (numeric value)")
        elif field_data["type"] == "date":
            console.print("  (ISO date format)")

    console.print()  # Final newline


@app.command("set-field")
@require_feature("trello")
def set_field(
    card_id: str = typer.Argument(..., help="Card ID or URL"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Set Project field"),
    stack: Optional[str] = typer.Option(None, "--stack", "-s", help="Set Stack field"),
    status: Optional[str] = typer.Option(None, "--status", help="Set Status field"),
    effort: Optional[str] = typer.Option(None, "--effort", "-e", help="Set Effort field"),
    repo_url: Optional[str] = typer.Option(None, "--repo-url", "-r", help="Set Repo URL field"),
    field: Optional[str] = typer.Option(None, "--field", "-f", help="Custom field name"),
    value: Optional[str] = typer.Option(None, "--value", "-v", help="Value for --field"),
):
    """Set custom field values on a Trello card.

    Can set common fields directly with flags, or any field with --field/--value.

    Examples:
        # Set project field
        bpsai-pair trello set-field abc123 --project "Support App"

        # Set multiple fields
        bpsai-pair trello set-field abc123 --project "App" --stack "React" --status "In Progress"

        # Set custom field by name
        bpsai-pair trello set-field abc123 --field "Deployment Tag" --value "v2.1.0"
    """
    config = _load_config()
    board_id = config.get("trello", {}).get("board_id")

    if not board_id:
        console.print("[red]No board configured. Run: bpsai-pair trello use-board <id>[/red]")
        raise typer.Exit(1)

    # Extract card ID from URL if needed
    if "trello.com" in card_id:
        # URL format: https://trello.com/c/CARD_ID/...
        parts = card_id.split("/")
        for i, part in enumerate(parts):
            if part == "c" and i + 1 < len(parts):
                card_id = parts[i + 1]
                break

    client = get_client()
    client.set_board(board_id)

    # Get the card
    try:
        card = client.client.get_card(card_id)
    except Exception as e:
        console.print(f"[red]Failed to get card: {e}[/red]")
        raise typer.Exit(1)

    # Build field values dict
    field_values = {}
    trello_config = config.get("trello", {})
    custom_fields_config = trello_config.get("custom_fields", {})

    if project:
        field_values[custom_fields_config.get("project", "Project")] = project
    if stack:
        field_values[custom_fields_config.get("stack", "Stack")] = stack
    if status:
        field_values[custom_fields_config.get("status", "Status")] = status
    if effort:
        field_values[custom_fields_config.get("effort", "Effort")] = effort
    if repo_url:
        field_values[custom_fields_config.get("repo_url", "Repo URL")] = repo_url
    if field and value:
        field_values[field] = value

    if not field_values:
        console.print("[yellow]No fields specified. Use --project, --stack, --status, etc.[/yellow]")
        raise typer.Exit(1)

    # Set the fields
    results = client.set_card_custom_fields(card, field_values)

    success_count = sum(1 for v in results.values() if v)
    fail_count = len(results) - success_count

    console.print(f"\n[bold]Card:[/bold] {card.name}")
    for field_name, success in results.items():
        status_icon = "[green]✓[/green]" if success else "[red]✗[/red]"
        console.print(f"  {status_icon} {field_name}: {field_values[field_name]}")

    if fail_count > 0:
        console.print("\n[yellow]Some fields may not exist on this board. Run 'bpsai-pair trello list-fields' to see available fields.[/yellow]")


@app.command("apply-defaults")
@require_feature("trello")
def apply_defaults(
    card_id: str = typer.Argument(..., help="Card ID or URL"),
):
    """Apply project default values to a Trello card.

    Reads defaults from .paircoder/config.yaml trello.defaults section
    and applies them to the specified card.

    Config example:
        trello:
          defaults:
            project: "Support App"
            stack: "React"
            repo_url: "https://github.com/org/repo"

    Examples:
        bpsai-pair trello apply-defaults abc123
    """
    config = _load_config()
    board_id = config.get("trello", {}).get("board_id")

    if not board_id:
        console.print("[red]No board configured. Run: bpsai-pair trello use-board <id>[/red]")
        raise typer.Exit(1)

    trello_config = config.get("trello", {})
    defaults = trello_config.get("defaults", {})

    if not defaults:
        console.print("[yellow]No defaults configured in .paircoder/config.yaml[/yellow]")
        console.print("\n[dim]Add a defaults section:[/dim]")
        console.print("""
trello:
  defaults:
    project: "Your Project Name"
    stack: "Your Stack"
    repo_url: "https://github.com/..."
""")
        raise typer.Exit(1)

    # Extract card ID from URL if needed
    if "trello.com" in card_id:
        parts = card_id.split("/")
        for i, part in enumerate(parts):
            if part == "c" and i + 1 < len(parts):
                card_id = parts[i + 1]
                break

    client = get_client()
    client.set_board(board_id)

    # Get the card
    try:
        card = client.client.get_card(card_id)
    except Exception as e:
        console.print(f"[red]Failed to get card: {e}[/red]")
        raise typer.Exit(1)

    # Map default keys to custom field names
    custom_fields_config = trello_config.get("custom_fields", {})
    field_mapping = {
        "project": custom_fields_config.get("project", "Project"),
        "stack": custom_fields_config.get("stack", "Stack"),
        "status": custom_fields_config.get("status", "Status"),
        "effort": custom_fields_config.get("effort", "Effort"),
        "repo_url": custom_fields_config.get("repo_url", "Repo URL"),
        "deployment_tag": custom_fields_config.get("deployment_tag", "Deployment Tag"),
    }

    # Build field values from defaults
    field_values = {}
    for key, value in defaults.items():
        field_name = field_mapping.get(key, key)  # Use key directly if not mapped
        field_values[field_name] = value

    # Set the fields
    results = client.set_card_custom_fields(card, field_values)

    success_count = sum(1 for v in results.values() if v)

    console.print(f"\n[bold]Card:[/bold] {card.name}")
    for field_name, success in results.items():
        status_icon = "[green]✓[/green]" if success else "[red]✗[/red]"
        console.print(f"  {status_icon} {field_name}: {field_values[field_name]}")

    console.print(f"\n[green]Applied {success_count}/{len(results)} default fields[/green]")
