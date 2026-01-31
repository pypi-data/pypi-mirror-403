"""CLI commands for skill validation and installation.

This module serves as a hub that re-exports the Typer apps from
specialized command modules:
- skill_commands: skill_app (8 skill management commands)
- subagent_commands: subagent_app (1 subagent detection command)
- gaps_commands: gaps_app (4 unified gap commands)
"""

# Re-export Typer apps from specialized modules
from .skill_commands import skill_app
from .subagent_commands import subagent_app
from .gaps_commands import gaps_app

# Re-export for backward compatibility
__all__ = [
    "skill_app",
    "subagent_app",
    "gaps_app",
]
