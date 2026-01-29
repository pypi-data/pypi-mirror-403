"""
Trello CLI commands for PairCoder - Hub file.

This module registers all trello commands by importing from focused modules:
- connection: connect/disconnect/status
- board_commands: boards/use-board/lists/config
- sync_commands: progress/sync
- field_commands: list-fields/fields/set-field/apply-defaults
- board_setup: init-board
- webhook_commands: webhook serve/register/list/delete
"""
import typer

# Create the main app
app = typer.Typer(name="trello", help="Trello integration commands")

# Import command functions from focused modules
from .connection import connect, status, disconnect, get_client, _load_config, _save_config
from .board_commands import boards, use_board, lists, trello_config
from .sync_commands import progress_comment, trello_sync
from .field_commands import list_fields, fields_cmd, set_field, apply_defaults
from .board_setup import init_board

# Register connection commands
app.command()(connect)
app.command()(status)
app.command()(disconnect)

# Register board management commands
app.command()(boards)
app.command("use-board")(use_board)
app.command()(lists)
app.command("config")(trello_config)

# Register sync commands
app.command("progress")(progress_comment)
app.command("sync")(trello_sync)

# Register field commands
app.command("list-fields")(list_fields)
app.command("fields")(fields_cmd)
app.command("set-field")(set_field)
app.command("apply-defaults")(apply_defaults)

# Register board setup commands
app.command("init-board")(init_board)

# Register webhook subcommands (already in webhook_commands.py)
from .webhook_commands import app as webhook_app
app.add_typer(webhook_app, name="webhook")

# Re-export for backward compatibility
console = None  # Will be imported lazily if needed


def _get_console():
    """Lazy console import for backward compatibility."""
    global console
    if console is None:
        from rich.console import Console
        console = Console()
    return console
