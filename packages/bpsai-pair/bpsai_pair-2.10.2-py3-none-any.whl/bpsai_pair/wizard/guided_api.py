"""API routes for guided track integration.

Connects chat output to the wizard flow:
- POST /api/chat/create   — parse config from chat, fill forms, go to Review
- POST /api/chat/customize — parse config, pre-fill, switch to Quick Setup
- POST /api/chat/reset     — clear conversation history
"""

from __future__ import annotations

import re

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bpsai_pair.wizard.config_parser import ConfigParseError, parse_config_from_response
from bpsai_pair.wizard.session import SESSION_COOKIE_NAME
from bpsai_pair.wizard.state import get_session, mark_step_completed, update_session
from bpsai_pair.wizard.steps import ROUTE_STEP_MAP


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


def _extract_config_from_chat(session) -> tuple[dict[str, str] | None, JSONResponse | None]:
    """Extract parsed config from the last assistant message in chat history.

    Returns (config_dict, None) on success or (None, error_response) on failure.
    """
    chat_data = (session.data or {}).get("chat", {})
    history = chat_data.get("history", [])

    # Search backwards for the most recent assistant message with config
    for msg in reversed(history):
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", "")
        try:
            config = parse_config_from_response(content)
        except ConfigParseError:
            return None, JSONResponse(
                status_code=400,
                content={"success": False, "error": "Config XML is malformed"},
            )
        if config is not None:
            return config, None

    return None, JSONResponse(
        status_code=400,
        content={"success": False, "error": "No config found in chat history"},
    )


def _generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from a project name."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:50]


def _config_to_project_data(config: dict[str, str]) -> dict:
    """Convert parsed XML config to the project data format the wizard expects."""
    project: dict = {
        "name": config["project_name"],
        "slug": _generate_slug(config["project_name"]),
        "goal": config.get("primary_goal", config.get("description", "")),
        "preset": config.get("preset", "default"),
        "coverage_target": int(config.get("coverage_target", "80")),
    }
    if "description" in config:
        project["description"] = config["description"]
    return project


def _config_to_enforcement_data(config: dict[str, str]) -> dict:
    """Convert parsed XML config to enforcement data format."""
    return {
        "preset": config.get("enforcement", "balanced"),
        "ac_verification": True,
        "state_machine": True,
        "bypass_audit": True,
    }


def _validate_config(config: dict[str, str]) -> JSONResponse | None:
    """Validate that the parsed config has required fields.

    Returns an error response if invalid, None if valid.
    """
    if "project_name" not in config:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Config missing project_name"},
        )
    return None


async def _handle_create_from_chat(request: Request) -> JSONResponse:
    """Parse config from chat, fill wizard state, redirect to review."""
    session_id, session, error = _get_session_or_error(request)
    if error:
        return error

    config, error = _extract_config_from_chat(session)
    if error:
        return error
    assert config is not None

    validation_error = _validate_config(config)
    if validation_error:
        return validation_error

    project_data = _config_to_project_data(config)
    enforcement_data = _config_to_enforcement_data(config)

    current_data = session.data or {}
    current_data["project"] = project_data
    current_data["enforcement"] = enforcement_data
    update_session(session_id, data=current_data)

    # Mark guided steps as completed (chat covers project + enforcement)
    mark_step_completed(session_id, ROUTE_STEP_MAP["/wizard/chat"])
    # Also mark project step since config covers it
    mark_step_completed(session_id, ROUTE_STEP_MAP["/wizard/project"])

    return JSONResponse(content={
        "success": True,
        "next_url": "/wizard/review",
    })


async def _handle_customize_from_chat(request: Request) -> JSONResponse:
    """Parse config from chat, pre-fill, switch to Quick Setup."""
    session_id, session, error = _get_session_or_error(request)
    if error:
        return error

    config, config_error = _extract_config_from_chat(session)
    if config is not None:
        project_data = _config_to_project_data(config)
        enforcement_data = _config_to_enforcement_data(config)

        current_data = session.data or {}
        current_data["project"] = project_data
        current_data["enforcement"] = enforcement_data
        update_session(session_id, data=current_data)

    # Switch to quick track
    update_session(session_id, track="quick")

    return JSONResponse(content={
        "success": True,
        "next_url": "/wizard/project",
    })


async def _handle_reset_chat(request: Request) -> JSONResponse:
    """Clear chat history from the session."""
    session_id, session, error = _get_session_or_error(request)
    if error:
        return error

    current_data = session.data or {}
    current_data["chat"] = {"history": []}
    update_session(session_id, data=current_data)

    return JSONResponse(content={
        "success": True,
    })


def setup_guided_api_routes(app: FastAPI) -> None:
    """Set up API routes for guided track integration."""

    @app.post("/api/chat/create")
    async def create_from_chat(request: Request) -> JSONResponse:
        return await _handle_create_from_chat(request)

    @app.post("/api/chat/customize")
    async def customize_from_chat(request: Request) -> JSONResponse:
        return await _handle_customize_from_chat(request)

    @app.post("/api/chat/reset")
    async def reset_chat(request: Request) -> JSONResponse:
        return await _handle_reset_chat(request)
