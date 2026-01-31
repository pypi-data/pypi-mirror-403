"""API routes for update mode — loading existing config and diff preview.

Provides:
- POST /api/load-existing — Load existing config.yaml into session
- GET /api/preview/diff   — Compare current session data with original config
"""

from __future__ import annotations

from typing import Any

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bpsai_pair.wizard.creator import ProjectCreator
from bpsai_pair.wizard.loader import load_existing_config
from bpsai_pair.wizard.session import SESSION_COOKIE_NAME
from bpsai_pair.wizard.state import get_session, update_session


def _get_session_or_error(request: Request) -> tuple[str, object | None, JSONResponse | None]:
    """Extract and validate session from request cookies."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return "", None, JSONResponse(
            status_code=400,
            content={"success": False, "error": "No session"},
        )
    session = get_session(session_id)
    if not session:
        return "", None, JSONResponse(
            status_code=400,
            content={"success": False, "error": "Session not found"},
        )
    return session_id, session, None


def _compute_changes(
    original_yaml: str,
    session_data: dict[str, Any],
) -> list[dict[str, str]]:
    """Compute a list of field-level changes between original and current.

    Returns a list of dicts with keys: field, old, new.
    """
    try:
        original = yaml.safe_load(original_yaml)
    except yaml.YAMLError:
        return []

    if not isinstance(original, dict):
        return []

    creator = ProjectCreator(session_data=session_data)
    current = creator._build_config()

    changes: list[dict[str, str]] = []
    _diff_dicts("", original, current, changes)
    return changes


def _diff_dicts(
    prefix: str,
    old: dict,
    new: dict,
    changes: list[dict[str, str]],
) -> None:
    """Recursively diff two dicts, appending changes."""
    all_keys = set(old.keys()) | set(new.keys())
    for key in sorted(all_keys):
        path = f"{prefix}.{key}" if prefix else key
        old_val = old.get(key)
        new_val = new.get(key)

        if isinstance(old_val, dict) and isinstance(new_val, dict):
            _diff_dicts(path, old_val, new_val, changes)
        elif old_val != new_val:
            changes.append({
                "field": path,
                "old": str(old_val) if old_val is not None else "(none)",
                "new": str(new_val) if new_val is not None else "(none)",
            })


async def _handle_load_existing(request: Request) -> JSONResponse:
    """Load existing config.yaml into session state."""
    from bpsai_pair.wizard.demo import get_config_path

    session_id, session, error = _get_session_or_error(request)
    if error:
        return error

    config_dir = get_config_path(session.session_id, session.demo_mode)
    result = load_existing_config(config_dir)
    if result is None:
        if session.demo_mode:
            msg = "Demo mode starts with an empty project. Create a project first, then use Update mode to modify it."
        else:
            msg = "Config not found — no .paircoder/config.yaml"
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": msg},
        )

    current_data = session.data or {}
    current_data["project"] = result["project"]
    current_data["enforcement"] = result["enforcement"]
    current_data["update_mode"] = {
        "active": True,
        "button_label": "Update",
        "original_yaml": result["original_yaml"],
    }

    # Populate optional sections if the loader extracted them
    for key in ("trello", "budget", "mcp"):
        if key in result and result[key]:
            current_data[key] = result[key]

    update_session(session_id, data=current_data)

    return JSONResponse(content={
        "success": True,
        "project": result["project"],
        "next_url": "/wizard/project",
    })


async def _handle_diff_preview(request: Request) -> JSONResponse:
    """Compare current session data with original loaded config."""
    session_id, session, error = _get_session_or_error(request)
    if error:
        return error

    update_data = (session.data or {}).get("update_mode", {})
    if not update_data.get("active"):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Not in update mode"},
        )

    original_yaml = update_data.get("original_yaml", "")
    changes = _compute_changes(original_yaml, session.data or {})

    return JSONResponse(content={
        "success": True,
        "has_changes": len(changes) > 0,
        "changes": changes,
    })


def setup_update_api_routes(app: FastAPI) -> None:
    """Set up API routes for update mode."""

    @app.post("/api/load-existing")
    async def load_existing(request: Request) -> JSONResponse:
        return await _handle_load_existing(request)

    @app.get("/api/preview/diff")
    async def diff_preview(request: Request) -> JSONResponse:
        return await _handle_diff_preview(request)
