"""Global user preferences management.

Stores user preferences in ~/.paircoder/preferences.yaml
These are user-level settings that persist across all projects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _get_preferences_path() -> Path:
    """Get path to global preferences file."""
    return Path.home() / ".paircoder" / "preferences.yaml"


def load_preferences() -> dict[str, Any]:
    """Load user preferences from ~/.paircoder/preferences.yaml."""
    path = _get_preferences_path()
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text()) or {}
    except Exception:
        return {}


def save_preferences(prefs: dict[str, Any]) -> bool:
    """Save user preferences to ~/.paircoder/preferences.yaml."""
    path = _get_preferences_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.dump(prefs, default_flow_style=False, sort_keys=False))
        return True
    except Exception:
        return False


def get_preference(key: str, default: Any = None) -> Any:
    """Get a single preference value."""
    prefs = load_preferences()
    # Support dotted keys like "editor.preferred"
    parts = key.split(".")
    value = prefs
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return default
    return value if value is not None else default


def set_preference(key: str, value: Any) -> bool:
    """Set a single preference value."""
    prefs = load_preferences()
    # Support dotted keys
    parts = key.split(".")
    target = prefs
    for part in parts[:-1]:
        if part not in target:
            target[part] = {}
        target = target[part]
    target[parts[-1]] = value
    return save_preferences(prefs)


# Convenience functions for common preferences
def get_preferred_editor() -> str | None:
    """Get user's preferred editor."""
    return get_preference("editor.preferred")


def set_preferred_editor(editor: str) -> bool:
    """Set user's preferred editor."""
    return set_preference("editor.preferred", editor)


def get_preferred_terminal() -> str | None:
    """Get user's preferred terminal."""
    return get_preference("terminal.preferred")


def set_preferred_terminal(terminal: str) -> bool:
    """Set user's preferred terminal."""
    return set_preference("terminal.preferred", terminal)
