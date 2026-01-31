"""API route handlers for project configuration.

This module contains the API endpoint for the project basics step.
"""

from __future__ import annotations

import re

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from bpsai_pair.wizard.session import SESSION_COOKIE_NAME
from bpsai_pair.wizard.state import get_session, mark_step_completed, update_session
from bpsai_pair.wizard.steps import ROUTE_STEP_MAP


class ProjectRequest(BaseModel):
    """Request body for project configuration."""

    name: str
    description: str | None = None
    goal: str
    preset: str
    coverage_target: int = 80


def _generate_slug(name: str) -> str:
    """Generate a slug from a project name."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug[:50]


def _validate_project_request(project_request: ProjectRequest) -> str | None:
    """Validate project request data. Returns error message or None if valid."""
    valid_presets = {"default", "strict", "relaxed", "pro-workflow", "enterprise"}

    if not project_request.name or len(project_request.name.strip()) < 3:
        return "Project name must be at least 3 characters"

    if len(project_request.name) > 50:
        return "Project name must be at most 50 characters"

    if not project_request.goal or len(project_request.goal.strip()) < 10:
        return "Primary goal must be at least 10 characters"

    if len(project_request.goal) > 200:
        return "Primary goal must be at most 200 characters"

    if project_request.description and len(project_request.description) > 500:
        return "Description must be at most 500 characters"

    if project_request.preset not in valid_presets:
        return f"Invalid preset. Must be one of: {', '.join(valid_presets)}"

    if not 0 <= project_request.coverage_target <= 100:
        return "Coverage target must be between 0 and 100"

    return None


async def _handle_project(request: Request, project_request: ProjectRequest) -> JSONResponse:
    """Handle project configuration submission."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "No session"})

    session = get_session(session_id)
    if not session:
        return JSONResponse(status_code=400, content={"success": False, "error": "Session not found"})

    # Validate the request
    error = _validate_project_request(project_request)
    if error:
        return JSONResponse(status_code=400, content={"success": False, "error": error})

    # Generate slug from name
    slug = _generate_slug(project_request.name)

    # Build project data
    project_data = {
        "name": project_request.name.strip(),
        "slug": slug,
        "goal": project_request.goal.strip(),
        "preset": project_request.preset,
        "coverage_target": project_request.coverage_target,
    }

    if project_request.description:
        project_data["description"] = project_request.description.strip()

    # Update session with project data
    current_data = session.data or {}
    current_data["project"] = project_data
    update_session(session_id, data=current_data)

    # Mark project step as completed
    mark_step_completed(session_id, ROUTE_STEP_MAP["/wizard/project"])

    return JSONResponse(content={
        "success": True,
        "slug": slug,
        "next_url": "/wizard/enforcement",
    })


def setup_project_api_routes(app: FastAPI) -> None:
    """Set up API routes for project configuration."""

    @app.post("/api/project")
    async def submit_project(request: Request, project_request: ProjectRequest) -> JSONResponse:
        return await _handle_project(request, project_request)
