"""API route handlers for the review and create step.

This module contains endpoints for file preview, config preview,
project creation, and integration configuration routing.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from bpsai_pair.wizard.creator import ProjectCreator
from bpsai_pair.wizard.session import SESSION_COOKIE_NAME
from bpsai_pair.wizard.state import (
    get_next_pending_integration,
    get_session,
    set_pending_integrations,
    update_session,
)


class ConfigureIntegrationsRequest(BaseModel):
    """Request body for integration configuration."""

    integrations: list[str]


def _get_creator_from_session(request: Request) -> tuple[ProjectCreator | None, JSONResponse | None]:
    """Build a ProjectCreator from session data, or return an error response."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return None, JSONResponse(status_code=400, content={"success": False, "error": "No session"})

    session = get_session(session_id)
    if not session:
        return None, JSONResponse(status_code=400, content={"success": False, "error": "Session not found"})

    project_data = (session.data or {}).get("project")
    if not project_data:
        return None, JSONResponse(status_code=400, content={"success": False, "error": "No project data"})

    creator = ProjectCreator(session_data=session.data)
    return creator, None


async def _handle_preview_files(request: Request) -> JSONResponse:
    """Handle file tree preview request."""
    creator, error = _get_creator_from_session(request)
    if error:
        return error
    assert creator is not None

    files = creator.preview_files()
    return JSONResponse(content={"success": True, "files": files})


async def _handle_preview_config(request: Request) -> JSONResponse:
    """Handle config.yaml preview request."""
    creator, error = _get_creator_from_session(request)
    if error:
        return error
    assert creator is not None

    config_yaml = creator.preview_config()
    return JSONResponse(content={"success": True, "config_yaml": config_yaml})


async def _handle_create_project(request: Request) -> JSONResponse:
    """Handle project creation request."""
    from bpsai_pair.wizard.demo import get_config_path

    creator, error = _get_creator_from_session(request)
    if error:
        return error
    assert creator is not None

    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    session = get_session(session_id)  # type: ignore[arg-type]
    assert session is not None

    # Non-demo mode requires explicit confirmation
    if not session.demo_mode:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not body.get("confirm"):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Confirmation required. Send {\"confirm\": true} to proceed.",
                },
            )

    target_dir = get_config_path(session.session_id, session.demo_mode)

    # Backup existing files if present
    backup_path = creator.backup_existing(target_dir)

    # Create the project
    success = creator.create(target_dir)
    if not success:
        return JSONResponse(status_code=500, content={"success": False, "error": "Failed to create project"})

    result: dict = {"success": True, "next_url": "/wizard/success"}
    if backup_path:
        result["backup_path"] = str(backup_path)

    return JSONResponse(content=result)


async def _handle_configure_integrations(
    request: Request, body: ConfigureIntegrationsRequest,
) -> JSONResponse:
    """Handle request to configure selected integrations.

    Stores the selected integrations and returns the first integration page URL.
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "No session"},
        )

    session = get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Session not found"},
        )

    # Verify user has Pro+ tier
    if session.tier not in ("pro", "team", "enterprise"):
        return JSONResponse(
            status_code=403,
            content={"success": False, "error": "Integrations require Pro tier or higher"},
        )

    if not body.integrations:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "No integrations selected"},
        )

    # Store pending integrations in session
    set_pending_integrations(session_id, body.integrations)

    # Get the first integration to configure
    next_url = get_next_pending_integration(session_id)
    if not next_url:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Invalid integration selection"},
        )

    return JSONResponse(content={"success": True, "next_url": next_url})


def setup_review_api_routes(app: FastAPI) -> None:
    """Set up API routes for the review and create step."""

    @app.get("/api/preview/files")
    async def preview_files(request: Request) -> JSONResponse:
        return await _handle_preview_files(request)

    @app.get("/api/preview/config")
    async def preview_config(request: Request) -> JSONResponse:
        return await _handle_preview_config(request)

    @app.post("/api/create")
    async def create_project(request: Request) -> JSONResponse:
        return await _handle_create_project(request)

    @app.post("/api/review/configure-integrations")
    async def configure_integrations(
        request: Request, body: ConfigureIntegrationsRequest,
    ) -> JSONResponse:
        return await _handle_configure_integrations(request, body)
