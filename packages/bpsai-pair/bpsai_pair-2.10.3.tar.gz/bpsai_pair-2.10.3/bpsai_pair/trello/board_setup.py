"""
Trello board setup commands: init-board.

This module handles board initialization from templates.
"""
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .connection import get_client, _load_config, _save_config

app = typer.Typer(name="setup", help="Trello board setup commands")
console = Console()


@app.command("init-board")
def init_board(
    name: str = typer.Option(..., "--name", "-n", help="Name for the new board"),
    from_template: str = typer.Option(
        "BPS AI Project Template",
        "--from-template", "-t",
        help="Name of the template board to copy"
    ),
    keep_cards: bool = typer.Option(False, "--keep-cards", help="Copy cards from template"),
    set_active: bool = typer.Option(True, "--set-active/--no-set-active", help="Set as active board for this project"),
):
    """Create a new Trello board from a template.

    Creates a board by copying from a template board, preserving:
    - All lists and their order
    - Custom field definitions
    - Labels with colors
    - Butler automation rules

    Examples:
        # Create board from default BPS template
        bpsai-pair trello init-board --name "My New Project"

        # Create from custom template
        bpsai-pair trello init-board --name "My Project" --from-template "My Template"

        # Copy template cards too
        bpsai-pair trello init-board --name "My Project" --keep-cards
    """
    client = get_client()

    # Check if template exists
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Finding template board...", total=None)

        template = client.find_board_by_name(from_template)
        if not template:
            progress.stop()
            console.print(f"[red]Template board '{from_template}' not found[/red]")
            console.print("\n[dim]Available boards:[/dim]")
            for board in client.list_boards():
                if not board.closed:
                    console.print(f"  - {board.name}")
            raise typer.Exit(1)

        progress.update(task, description=f"Creating board from '{template.name}'...")

        try:
            new_board = client.copy_board_from_template(
                template_name=from_template,
                new_board_name=name,
                keep_cards=keep_cards
            )
        except ValueError as e:
            progress.stop()
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)

        if not new_board:
            progress.stop()
            console.print("[red]Failed to create board from template[/red]")
            raise typer.Exit(1)

        progress.update(task, description="Getting board info...")

        # Get info about the new board
        board_info = client.get_board_info(new_board)

    console.print(f"\n[green]✓ Created board: {new_board.name}[/green]")
    console.print(f"  URL: {new_board.url}")
    console.print(f"  ID: {new_board.id}")

    if 'lists' in board_info:
        console.print(f"\n  [bold]Lists:[/bold] {', '.join(board_info['lists'])}")
    if 'custom_fields' in board_info and board_info['custom_fields']:
        console.print(f"  [bold]Custom Fields:[/bold] {', '.join(board_info['custom_fields'])}")
    if 'labels' in board_info and board_info['labels']:
        console.print(f"  [bold]Labels:[/bold] {', '.join(board_info['labels'])}")

    # Set as active board if requested
    if set_active:
        config = _load_config()
        if "trello" not in config:
            config["trello"] = {}
        config["trello"]["board_id"] = new_board.id
        config["trello"]["board_name"] = new_board.name
        config["trello"]["enabled"] = True
        _save_config(config)
        console.print("\n[green]✓ Set as active board for this project[/green]")
    else:
        console.print("\n[dim]To use this board, run:[/dim]")
        console.print(f"  bpsai-pair trello use-board {new_board.id}")
