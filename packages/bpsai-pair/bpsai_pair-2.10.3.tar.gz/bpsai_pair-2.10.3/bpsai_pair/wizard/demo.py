"""Demo mode utilities for the wizard.

Demo mode allows testing the wizard without affecting the real project.
All config writes go to a temp directory instead of .paircoder/
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

# Base temp directory for all demo sessions
DEMO_BASE_DIR = Path(tempfile.gettempdir()) / "paircoder-wizard-demo"


def get_demo_config_dir(session_id: str) -> Path:
    """Get the demo config directory for a session.

    Args:
        session_id: The wizard session ID

    Returns:
        Path to the session-specific demo config directory
    """
    return DEMO_BASE_DIR / session_id / ".paircoder"


def ensure_demo_dir(session_id: str) -> Path:
    """Ensure the demo config directory exists.

    Args:
        session_id: The wizard session ID

    Returns:
        Path to the created demo config directory
    """
    demo_dir = get_demo_config_dir(session_id)
    demo_dir.mkdir(parents=True, exist_ok=True)
    return demo_dir


def cleanup_demo_session(session_id: str) -> bool:
    """Clean up a demo session's temp directory.

    Args:
        session_id: The wizard session ID

    Returns:
        True if cleanup succeeded, False otherwise
    """
    session_dir = DEMO_BASE_DIR / session_id
    if session_dir.exists():
        shutil.rmtree(session_dir, ignore_errors=True)
        return True
    return False


def cleanup_all_demo_sessions() -> int:
    """Clean up all demo sessions.

    Returns:
        Number of sessions cleaned up
    """
    if not DEMO_BASE_DIR.exists():
        return 0

    count = 0
    for session_dir in DEMO_BASE_DIR.iterdir():
        if session_dir.is_dir():
            shutil.rmtree(session_dir, ignore_errors=True)
            count += 1
    return count


def get_config_path(session_id: str | None, demo_mode: bool) -> Path:
    """Get the config path based on mode.

    Args:
        session_id: The wizard session ID (required for demo mode)
        demo_mode: Whether in demo mode

    Returns:
        Path to config directory (.paircoder/ or temp)
    """
    if demo_mode and session_id:
        return get_demo_config_dir(session_id)
    return Path.cwd() / ".paircoder"
