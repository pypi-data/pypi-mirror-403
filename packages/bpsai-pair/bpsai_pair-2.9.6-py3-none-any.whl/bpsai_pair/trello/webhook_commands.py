"""
CLI commands for Trello webhook server.
"""
import logging
import typer
from rich.console import Console

from ..planning.commands import find_paircoder_dir
from .auth import load_token
from .webhook import (
    TrelloWebhookServer,
    create_combined_handler,
    LIST_STATUS_MAP,
    READY_LISTS,
)

app = typer.Typer(name="webhook", help="Trello webhook server commands")
console = Console()


@app.command("serve")
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8765, "--port", "-p", help="Port to listen on"),
    agent_name: str = typer.Option("claude", "--agent", "-a", help="Agent name for assignment"),
    auto_assign: bool = typer.Option(True, "--auto-assign/--no-auto-assign", help="Auto-assign agent when cards move to Ready"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Start the Trello webhook server with agent assignment.

    The server listens for Trello webhook callbacks and:
    1. Updates local task status when cards move between lists
    2. Auto-assigns agent when cards move to "Planned / Ready"
    3. Optionally auto-starts tasks (moves to In Progress)

    List mappings:
    - Intake / Backlog, Planned / Ready → pending
    - In Progress, Review / Testing → in_progress
    - Deployed / Done → done
    - Issues / Tech Debt → blocked

    Agent assignment (when card moves to Ready):
    - Adds "Agent: <name>" label (purple)
    - Adds assignment comment
    - Auto-moves to "In Progress" and updates local task

    Example:
        # Start server with default settings
        bpsai-pair trello webhook serve

        # Start with custom agent name
        bpsai-pair trello webhook serve --agent codex

        # Disable auto-assignment
        bpsai-pair trello webhook serve --no-auto-assign

    Note: You must expose this server to the internet (e.g., via ngrok)
    and register the webhook URL with Trello for webhooks to work.
    """
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # Check Trello connection
    creds = load_token()
    if not creds:
        console.print("[red]Not connected to Trello. Run: bpsai-pair trello connect[/red]")
        raise typer.Exit(1)

    # Find paircoder directory
    try:
        paircoder_dir = find_paircoder_dir()
    except FileNotFoundError:
        console.print("[red]Not in a PairCoder project directory[/red]")
        raise typer.Exit(1)

    # Create combined handler (status updates + agent assignment)
    on_card_move = create_combined_handler(
        paircoder_dir=paircoder_dir,
        api_key=creds["api_key"],
        token=creds["token"],
        agent_name=agent_name,
        auto_assign=auto_assign,
    )

    # Start server
    console.print(f"[green]Starting Trello webhook server on {host}:{port}[/green]")
    console.print(f"\n[cyan]Agent:[/cyan] {agent_name}")
    console.print(f"[cyan]Auto-assign:[/cyan] {'enabled' if auto_assign else 'disabled'}")
    console.print("\n[yellow]List → Status mappings:[/yellow]")
    for list_name, status in LIST_STATUS_MAP.items():
        console.print(f"  {list_name} → {status}")
    if auto_assign:
        console.print("\n[yellow]Agent assignment triggers:[/yellow]")
        for list_name in READY_LISTS:
            console.print(f"  {list_name} → assign agent, move to In Progress")
    console.print("\n[dim]Press Ctrl+C to stop[/dim]\n")

    server = TrelloWebhookServer(
        host=host,
        port=port,
        on_card_move=on_card_move,
    )
    server.start()


@app.command("register")
def register(
    callback_url: str = typer.Argument(..., help="Public URL for webhook callbacks"),
    board_id: str = typer.Option(None, "--board", "-b", help="Board ID (uses configured board if not specified)"),
):
    """Register a webhook with Trello.

    This creates a webhook subscription on the specified Trello board.
    When cards are moved, Trello will POST updates to your callback URL.

    Example:
        # Register webhook (requires ngrok or similar)
        ngrok http 8765
        bpsai-pair trello webhook register https://abc123.ngrok.io

    Prerequisites:
    1. Start the webhook server: bpsai-pair trello webhook serve
    2. Expose it via ngrok: ngrok http 8765
    3. Register the webhook with this command
    """
    creds = load_token()
    if not creds:
        console.print("[red]Not connected to Trello. Run: bpsai-pair trello connect[/red]")
        raise typer.Exit(1)

    # Get board ID from config if not specified
    if not board_id:
        try:
            paircoder_dir = find_paircoder_dir()
            import yaml
            config_path = paircoder_dir / "config.yaml"
            if config_path.exists():
                with open(config_path, encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                board_id = config.get("trello", {}).get("board_id")
        except Exception:
            pass

    if not board_id:
        console.print("[red]No board ID specified and none configured.[/red]")
        console.print("Use --board <board-id> or run: bpsai-pair trello use-board <id>")
        raise typer.Exit(1)

    # Register webhook via Trello API
    import requests

    url = "https://api.trello.com/1/webhooks"
    params = {
        "key": creds["api_key"],
        "token": creds["token"],
        "callbackURL": callback_url,
        "idModel": board_id,
        "description": "PairCoder task sync webhook",
    }

    try:
        response = requests.post(url, params=params)
        if response.status_code == 200:
            webhook_data = response.json()
            console.print("[green]✓ Webhook registered successfully[/green]")
            console.print(f"  ID: {webhook_data.get('id')}")
            console.print(f"  Board: {board_id}")
            console.print(f"  Callback: {callback_url}")
        else:
            console.print(f"[red]Failed to register webhook: {response.status_code}[/red]")
            console.print(response.text)
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error registering webhook: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_webhooks():
    """List all registered webhooks for the current token."""
    creds = load_token()
    if not creds:
        console.print("[red]Not connected to Trello. Run: bpsai-pair trello connect[/red]")
        raise typer.Exit(1)

    import requests
    from rich.table import Table

    url = f"https://api.trello.com/1/tokens/{creds['token']}/webhooks"
    params = {
        "key": creds["api_key"],
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            webhooks = response.json()

            if not webhooks:
                console.print("[yellow]No webhooks registered[/yellow]")
                return

            table = Table(title="Registered Webhooks")
            table.add_column("ID", style="dim")
            table.add_column("Description")
            table.add_column("Callback URL")
            table.add_column("Active")

            for wh in webhooks:
                table.add_row(
                    wh.get("id", "")[:12] + "...",
                    wh.get("description", ""),
                    wh.get("callbackURL", ""),
                    "✓" if wh.get("active") else "✗",
                )

            console.print(table)
        else:
            console.print(f"[red]Failed to list webhooks: {response.status_code}[/red]")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error listing webhooks: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_webhook(
    webhook_id: str = typer.Argument(..., help="Webhook ID to delete"),
):
    """Delete a registered webhook."""
    creds = load_token()
    if not creds:
        console.print("[red]Not connected to Trello. Run: bpsai-pair trello connect[/red]")
        raise typer.Exit(1)

    import requests

    url = f"https://api.trello.com/1/webhooks/{webhook_id}"
    params = {
        "key": creds["api_key"],
        "token": creds["token"],
    }

    try:
        response = requests.delete(url, params=params)
        if response.status_code == 200:
            console.print(f"[green]✓ Webhook deleted: {webhook_id}[/green]")
        else:
            console.print(f"[red]Failed to delete webhook: {response.status_code}[/red]")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error deleting webhook: {e}[/red]")
        raise typer.Exit(1)
