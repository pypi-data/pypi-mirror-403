"""Session and compaction commands for bpsai-pair CLI - Hub file.

This module registers all session-related commands by importing from focused modules:
- session_check: session check/status commands
- compaction_commands: compaction snapshot/check/recover/cleanup
- containment_commands: contained-auto, claude666, containment rollback/list/cleanup
"""

import typer

# Create the session sub-app
session_app = typer.Typer(
    help="Session management and context reload",
    context_settings={"help_option_names": ["-h", "--help"]}
)

# Create the compaction sub-app
compaction_app = typer.Typer(
    help="Context compaction detection and recovery",
    context_settings={"help_option_names": ["-h", "--help"]}
)

# Import command functions from focused modules
from .session_check import (
    session_check,
    session_status,
    repo_root,
    _get_progress_bar,
    _get_current_task_id,
)
from .compaction_commands import (
    compaction_snapshot_save,
    compaction_snapshot_list,
    compaction_check,
    compaction_recover,
    compaction_cleanup,
    compaction_snapshot_app,
)
from .containment_commands import (
    contained_auto,
    claude666,
    containment_rollback,
    containment_list,
    containment_cleanup,
    containment_app,
    _cleanup_containment,
    ROBOT_DEVIL_ART,
    _active_containment_manager,
)

# Register session check commands
session_app.command("check")(session_check)
session_app.command("status")(session_status)

# Register compaction commands
compaction_app.add_typer(compaction_snapshot_app, name="snapshot")
compaction_app.command("check")(compaction_check)
compaction_app.command("recover")(compaction_recover)
compaction_app.command("cleanup")(compaction_cleanup)

# Re-export for backward compatibility
console = None  # Will be imported lazily if needed


def _get_console():
    """Lazy console import for backward compatibility."""
    global console
    if console is None:
        from rich.console import Console
        console = Console()
    return console
