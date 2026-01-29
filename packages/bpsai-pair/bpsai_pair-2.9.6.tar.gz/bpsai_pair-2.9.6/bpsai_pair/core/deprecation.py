"""
Deprecation utilities for PairCoder CLI commands.

Provides decorators and helpers for marking commands as deprecated with
helpful migration guidance.
"""

from __future__ import annotations

from datetime import date
from functools import wraps
from pathlib import Path
from typing import Callable, Optional, TypeVar, Any

import typer

# Type variable for preserving function signatures
F = TypeVar("F", bound=Callable[..., Any])

# Global flag to suppress deprecation warnings (for CI/CD)
_suppress_warnings = False


def suppress_deprecation_warnings(suppress: bool = True) -> None:
    """Set global suppression of deprecation warnings.

    Args:
        suppress: If True, suppress all deprecation warnings
    """
    global _suppress_warnings
    _suppress_warnings = suppress


def is_warnings_suppressed() -> bool:
    """Check if deprecation warnings are currently suppressed."""
    return _suppress_warnings


def deprecated_command(
    message: str,
    alternative: Optional[str] = None,
    removal_version: str = "2.11.0",
) -> Callable[[F], F]:
    """Decorator to mark CLI commands as deprecated.

    Displays a warning to stderr before executing the command, with optional
    alternative command suggestion and removal version.

    Args:
        message: Main deprecation message explaining why it's deprecated
        alternative: Suggested alternative command or action
        removal_version: Version when the command will be removed

    Returns:
        Decorator function

    Example:
        @app.command("old-cmd")
        @deprecated_command(
            message="This command is deprecated in favor of skills.",
            alternative="bpsai-pair skill list",
            removal_version="2.11.0"
        )
        def old_cmd():
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not _suppress_warnings:
                _emit_deprecation_warning(message, alternative, removal_version)
            return func(*args, **kwargs)
        return wrapper  # type: ignore
    return decorator


def _emit_deprecation_warning(
    message: str,
    alternative: Optional[str] = None,
    removal_version: str = "2.11.0",
) -> None:
    """Emit a deprecation warning to stderr.

    Args:
        message: Main deprecation message
        alternative: Suggested alternative
        removal_version: Version when feature will be removed
    """
    warning_lines = [
        typer.style(f"DEPRECATED: {message}", fg=typer.colors.YELLOW, bold=True)
    ]

    if alternative:
        warning_lines.append(
            typer.style(f"   Use instead: {alternative}", fg=typer.colors.YELLOW)
        )

    warning_lines.append(
        typer.style(
            f"   Will be removed in v{removal_version}",
            fg=typer.colors.YELLOW,
            dim=True,
        )
    )

    for line in warning_lines:
        typer.echo(line, err=True)
    typer.echo("", err=True)  # Blank line for readability


def show_migration_hint_once(hint_id: str = "flows_to_skills") -> bool:
    """Show a migration hint once per day.

    Uses a cache file to track when hints were last shown to avoid
    spamming users with the same hint repeatedly.

    Args:
        hint_id: Unique identifier for this hint

    Returns:
        True if the hint was shown, False if it was already shown today
    """
    if _suppress_warnings:
        return False

    cache_dir = Path.home() / ".cache" / "paircoder"
    cache_file = cache_dir / f"deprecation_hint_{hint_id}"
    today = date.today().isoformat()

    # Check if already shown today
    if cache_file.exists():
        try:
            last_shown = cache_file.read_text(encoding="utf-8").strip()
            if last_shown == today:
                return False
        except (IOError, OSError):
            pass

    # Show the hint
    typer.echo("", err=True)
    typer.echo(
        typer.style("Ready to migrate from flows to skills?", fg=typer.colors.CYAN),
        err=True,
    )
    typer.echo(
        typer.style(
            "   See: docs/MIGRATION.md or run: bpsai-pair skill list",
            fg=typer.colors.CYAN,
            dim=True,
        ),
        err=True,
    )
    typer.echo("", err=True)

    # Record that we showed it
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(today, encoding="utf-8")
    except (IOError, OSError):
        pass  # Don't fail if we can't write cache

    return True


def warn_deprecated_config(config_key: str, alternative: Optional[str] = None) -> None:
    """Warn about a deprecated configuration option.

    Args:
        config_key: The deprecated config key (e.g., "workflow.flows_dir")
        alternative: Suggested alternative configuration
    """
    if _suppress_warnings:
        return

    warning = typer.style(
        f"Config '{config_key}' is deprecated.",
        fg=typer.colors.YELLOW,
    )
    typer.echo(warning, err=True)

    if alternative:
        alt_msg = typer.style(
            f"   Consider: {alternative}",
            fg=typer.colors.YELLOW,
            dim=True,
        )
        typer.echo(alt_msg, err=True)
