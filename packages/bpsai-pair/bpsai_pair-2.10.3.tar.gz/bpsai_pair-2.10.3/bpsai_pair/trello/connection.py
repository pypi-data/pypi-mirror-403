"""
Trello connection commands: connect, disconnect, status.

This module handles authentication and connection status for Trello.
"""
import typer
from rich.console import Console

from ..licensing import require_feature
from .auth import load_token, store_token, clear_token, is_connected
from .client import TrelloService

app = typer.Typer(name="connection", help="Trello connection commands")
console = Console()


def get_client() -> TrelloService:
    """Get an authenticated Trello client.

    Returns:
        TrelloService instance

    Raises:
        typer.Exit: If not connected to Trello
    """
    creds = load_token()
    if not creds:
        console.print("[red]Not connected to Trello. Run: bpsai-pair trello connect[/red]")
        raise typer.Exit(1)
    return TrelloService(api_key=creds["api_key"], token=creds["token"])


def _load_config() -> dict:
    """Load project config with error handling."""
    try:
        from ..core.ops import find_project_root
        import yaml

        root = find_project_root()
        config_file = root / ".paircoder" / "config.yaml"
        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}
    except Exception:
        return {}


def _save_config(config: dict) -> None:
    """Save project config."""
    try:
        from ..core.ops import find_project_root
        import yaml

        root = find_project_root()
        config_dir = root / ".paircoder"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.yaml"

        with open(config_file, 'w', encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not save config: {e}[/yellow]")


@app.command()
@require_feature("trello")
def connect(
    api_key: str = typer.Option(..., prompt=True, help="Trello API key"),
    token: str = typer.Option(..., prompt=True, hide_input=True, help="Trello token"),
):
    """Connect to Trello (validates and stores credentials)."""
    try:
        client = TrelloService(api_key=api_key, token=token)
    except ImportError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    if not client.healthcheck():
        console.print("[red]Failed to validate Trello credentials[/red]")
        raise typer.Exit(1)

    store_token(token=token, api_key=api_key)
    console.print("[green]✓ Connected to Trello[/green]")


@app.command()
@require_feature("trello")
def status():
    """Check Trello connection status."""
    if is_connected():
        console.print("[green]✓ Connected to Trello[/green]")

        config = _load_config()
        board_id = config.get("trello", {}).get("board_id")
        board_name = config.get("trello", {}).get("board_name")

        if board_id:
            console.print(f"  Board: {board_name} ({board_id})")
        else:
            console.print("  [yellow]No board configured. Run: bpsai-pair trello use-board <id>[/yellow]")
    else:
        console.print("[yellow]Not connected. Run: bpsai-pair trello connect[/yellow]")


@app.command()
@require_feature("trello")
def disconnect():
    """Remove stored Trello credentials."""
    clear_token()
    console.print("[green]✓ Disconnected from Trello[/green]")
