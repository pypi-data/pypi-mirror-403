"""API route and utilities for launching editors and terminals.

Provides:
- POST /api/open-editor — Detect and launch an IDE or terminal
- detect_editor() — Find an available code editor on PATH
- detect_terminal() — Find an available terminal emulator
"""

from __future__ import annotations

import platform
import shutil
import subprocess

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# Editors checked in priority order
_EDITOR_CANDIDATES = ["pycharm", "charm", "code", "cursor", "zed", "subl", "atom"]

# Terminal candidates per platform
_TERMINAL_CANDIDATES_LINUX = [
    "gnome-terminal",
    "konsole",
    "xfce4-terminal",
    "xterm",
]
_TERMINAL_CANDIDATES_MACOS = ["open"]  # open -a Terminal


class OpenEditorRequest(BaseModel):
    """Request body for open-editor endpoint."""

    editor: str = "ide"


def detect_editor() -> str | None:
    """Find the first available code editor on PATH.

    Returns the command name (e.g. 'code', 'cursor') or None.
    """
    for cmd in _EDITOR_CANDIDATES:
        if shutil.which(cmd):
            return cmd
    return None


def detect_terminal() -> str | None:
    """Find the first available terminal emulator.

    Returns the command name or None.
    """
    system = platform.system()
    if system == "Darwin":
        candidates = _TERMINAL_CANDIDATES_MACOS
    else:
        candidates = _TERMINAL_CANDIDATES_LINUX

    for cmd in candidates:
        if shutil.which(cmd):
            return cmd
    return None


def launch_editor(cmd: str, cwd: str = ".") -> bool:
    """Launch an editor in the background pointing at cwd."""
    try:
        subprocess.Popen(
            [cmd, cwd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def launch_terminal(cmd: str, cwd: str = ".") -> bool:
    """Launch a terminal emulator in the background at cwd."""
    try:
        system = platform.system()
        if system == "Darwin" and cmd == "open":
            args = ["open", "-a", "Terminal", cwd]
        else:
            args = [cmd, f"--working-directory={cwd}"]
        subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


async def _handle_open_editor(request: Request, body: OpenEditorRequest) -> JSONResponse:
    """Handle editor/terminal launch request."""
    from bpsai_pair.wizard.demo import get_config_path
    from bpsai_pair.wizard.session import SESSION_COOKIE_NAME
    from bpsai_pair.wizard.state import get_session

    # Determine working directory from session
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    cwd = "."
    if session_id:
        session = get_session(session_id)
        if session:
            config_path = get_config_path(session.session_id, session.demo_mode)
            cwd = str(config_path.parent)

    if body.editor == "terminal":
        terminal = detect_terminal()
        if not terminal:
            return JSONResponse(content={
                "success": False,
                "error": "No supported terminal emulator found",
            })
        ok = launch_terminal(terminal, cwd)
        return JSONResponse(content={"success": ok, "editor": terminal})

    # IDE mode
    editor = detect_editor()
    if not editor:
        return JSONResponse(content={
            "success": False,
            "error": "No supported editor found. Install PyCharm, VS Code, Cursor, or Zed.",
        })
    ok = launch_editor(editor, cwd)
    return JSONResponse(content={"success": ok, "editor": editor})


def setup_editor_api_routes(app: FastAPI) -> None:
    """Set up the open-editor API route."""

    @app.post("/api/open-editor")
    async def open_editor(request: Request, body: OpenEditorRequest) -> JSONResponse:
        return await _handle_open_editor(request, body)
