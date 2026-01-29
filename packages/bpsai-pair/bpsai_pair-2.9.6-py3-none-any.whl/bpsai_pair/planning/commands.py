"""Planning commands - Hub file for app registration.

This module re-exports all planning-related Typer apps and key utilities.
The actual command implementations are in separate focused modules:

- plan_commands.py: Plan management (new, list, show, tasks, status, etc.)
- task_commands.py: Task management (list, show, update, archive, etc.)
- intent_commands.py: Intent detection commands
- standup_commands.py: Daily standup commands
- helpers.py: Shared utilities

To integrate into main CLI:
    from .planning.commands import plan_app, task_app, intent_app, standup_app
    app.add_typer(plan_app, name="plan")
    app.add_typer(task_app, name="task")
    app.add_typer(intent_app, name="intent")
    app.add_typer(standup_app, name="standup")
"""

# Plan commands (8 commands)
from .plan_commands import plan_app, planning_status

# Task commands (10 commands)
from .task_commands import task_app

# Intent commands (3 commands)
from .intent_commands import intent_app

# Standup commands (2 commands)
from .standup_commands import standup_app

# Shared utilities (re-exported for backward compatibility)
from .helpers import (
    console,
    find_paircoder_dir,
    get_state_manager,
)

__all__ = [
    # Typer apps
    "plan_app",
    "task_app",
    "intent_app",
    "standup_app",
    # Status function
    "planning_status",
    # Utilities
    "console",
    "find_paircoder_dir",
    "get_state_manager",
]
