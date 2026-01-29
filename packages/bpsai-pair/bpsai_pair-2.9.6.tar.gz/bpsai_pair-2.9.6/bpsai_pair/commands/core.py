"""Core commands for bpsai-pair CLI - Hub file.

These are the top-level commands registered directly on the main app:
- init: Initialize repo with governance, context, prompts, scripts, and workflows
- feature: Create feature branch and scaffold context
- pack: Create agent context package
- context-sync: Update the Context Loop in state.md
- status: Show current context loop status
- validate: Validate repo structure and context consistency
- ci: Run local CI checks
- history-log: Log file changes (hidden command)

Extracted from cli.py as part of EPIC-003 CLI Architecture Refactor (Sprint 22).
Decomposed into focused modules as part of EPIC-005 Phase 2 (Sprint 29.5).
"""

from __future__ import annotations

import typer

# Import commands from focused modules
from .init_commands import (
    init_command,
    feature_command,
    repo_root as _init_repo_root,
    _select_ci_workflow,
    ensure_v2_config,
)

from .context_commands import (
    pack_command,
    context_sync_command,
    print_json as _context_print_json,
)

from .validation_commands import (
    status_command,
    validate_command,
    ci_command,
    history_log_command,
    _get_containment_status,
    print_json,
)

# Re-export for backward compatibility
repo_root = _init_repo_root


def register_core_commands(app: typer.Typer) -> None:
    """Register all core commands on the main app.

    Args:
        app: The main Typer application
    """
    app.command("init")(init_command)
    app.command("feature")(feature_command)
    app.command("pack")(pack_command)
    app.command("context-sync")(context_sync_command)
    # Alias for context-sync
    app.command("sync", hidden=True)(context_sync_command)
    app.command("status")(status_command)
    app.command("validate")(validate_command)
    app.command("ci")(ci_command)
    app.command("history-log", hidden=True)(history_log_command)


# Export all for backward compatibility
__all__ = [
    # Commands
    "init_command",
    "feature_command",
    "pack_command",
    "context_sync_command",
    "status_command",
    "validate_command",
    "ci_command",
    "history_log_command",
    # Helpers
    "repo_root",
    "print_json",
    "_select_ci_workflow",
    "ensure_v2_config",
    "_get_containment_status",
    # Registration
    "register_core_commands",
]
