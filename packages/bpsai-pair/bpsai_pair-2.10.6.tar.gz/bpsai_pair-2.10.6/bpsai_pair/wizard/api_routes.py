"""API route handlers for wizard state management.

This module contains the API endpoints for state, navigation, and reset.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from bpsai_pair.wizard.chat_api import setup_chat_api_routes
from bpsai_pair.wizard.enforcement_api import setup_enforcement_api_routes
from bpsai_pair.wizard.update_api import setup_update_api_routes
from bpsai_pair.wizard.project_api import setup_project_api_routes
from bpsai_pair.wizard.review_api import setup_review_api_routes
from bpsai_pair.wizard.budget_api import setup_budget_api_routes
from bpsai_pair.wizard.github_api import setup_github_api_routes
from bpsai_pair.wizard.mcp_api import setup_mcp_api_routes
from bpsai_pair.wizard.trello_api import setup_trello_api_routes
from bpsai_pair.wizard.session import SESSION_COOKIE_NAME, _set_session_cookie, is_demo_request
from bpsai_pair.wizard.state import (
    create_session,
    delete_session,
    get_available_steps,
    get_session,
    mark_step_completed,
    navigate_to_step,
    update_session,
)


class LicenseInstallRequest(BaseModel):
    """Request body for license installation."""

    json_data: str | None = None


class NavigateRequest(BaseModel):
    """Request body for navigation."""

    step: int


class UpdateDataRequest(BaseModel):
    """Request body for updating form data."""

    data: dict | None = None


class SelectTrackRequest(BaseModel):
    """Request body for track selection."""

    track: str


class DebugTierRequest(BaseModel):
    """Request body for debug tier switching."""

    tier: str


async def _handle_install_license(request: LicenseInstallRequest) -> JSONResponse:
    """Handle license installation."""
    if not request.json_data:
        return JSONResponse(status_code=400, content={"error": "No license data provided"})

    from bpsai_pair.wizard.license_installer import verify_and_install_license

    result = verify_and_install_license(request.json_data)
    if not result.get("success"):
        return JSONResponse(status_code=400, content={"error": result.get("error", "Unknown error")})

    return JSONResponse(content=result)


async def _handle_get_state(request: Request) -> JSONResponse:
    """Handle get state request."""
    from bpsai_pair.wizard.demo import get_config_path

    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(status_code=200, content={"session": None, "message": "No session"})

    session = get_session(session_id)
    if not session:
        return JSONResponse(status_code=200, content={"session": None, "message": "Session not found"})

    available_steps = get_available_steps(session.tier, session.track)
    config_path = get_config_path(session.session_id, session.demo_mode)
    return JSONResponse(content={
        "session_id": session.session_id,
        "tier": session.tier,
        "track": session.track,
        "current_step": session.current_step,
        "completed_steps": sorted(session.completed_steps),
        "data": session.data,
        "steps": [{"id": s.id, "name": s.name} for s in available_steps],
        "demo_mode": session.demo_mode,
        "config_path": str(config_path),
    })


async def _handle_reset_session(request: Request, tier: str) -> JSONResponse:
    """Handle session reset (start over)."""
    from bpsai_pair.wizard.demo import cleanup_demo_session

    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        # Clean up demo directory if it was a demo session
        old_session = get_session(session_id)
        if old_session and old_session.demo_mode:
            cleanup_demo_session(session_id)
        delete_session(session_id)

    demo_mode = is_demo_request(request)
    new_session = create_session(tier, demo_mode=demo_mode)
    response = JSONResponse(content={
        "success": True,
        "session_id": new_session.session_id,
        "demo_mode": new_session.demo_mode,
        "message": "Session reset successfully",
    })
    _set_session_cookie(response, new_session)
    return response


async def _handle_navigate(request: Request, nav_request: NavigateRequest) -> JSONResponse:
    """Handle navigation to a step."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "No session"})

    session = get_session(session_id)
    if not session:
        return JSONResponse(status_code=400, content={"success": False, "error": "Session not found"})

    success = navigate_to_step(session_id, nav_request.step)
    if not success:
        return JSONResponse(status_code=400, content={"success": False, "error": "Cannot navigate to that step"})

    return JSONResponse(content={"success": True, "current_step": nav_request.step})


async def _handle_update_data(request: Request, data_request: UpdateDataRequest) -> JSONResponse:
    """Handle form data update."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "No session"})

    if data_request.data:
        update_session(session_id, data=data_request.data)

    return JSONResponse(content={"success": True})


async def _handle_select_track(request: Request, track_request: SelectTrackRequest) -> JSONResponse:
    """Handle track selection."""
    valid_tracks = {"quick", "guided", "update"}
    if track_request.track not in valid_tracks:
        return JSONResponse(status_code=400, content={"success": False, "error": "Invalid track"})

    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "No session"})

    session = get_session(session_id)
    if not session:
        return JSONResponse(status_code=400, content={"success": False, "error": "Session not found"})

    # Update session with selected track
    track = track_request.track if track_request.track != "update" else "quick"
    update_session(session_id, track=track)

    # Mark Welcome (step 1) as completed
    mark_step_completed(session_id, 1)

    # Route to the correct first page for the selected track
    next_url = "/wizard/chat" if track_request.track == "guided" else "/wizard/project"

    return JSONResponse(content={
        "success": True,
        "track": track_request.track,
        "next_url": next_url,
    })


async def _handle_debug_tier(request: Request, tier_request: DebugTierRequest) -> JSONResponse:
    """Handle debug tier switching (demo mode only)."""
    valid_tiers = {"solo", "pro", "team", "enterprise"}
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "No session"})

    session = get_session(session_id)
    if not session:
        return JSONResponse(status_code=400, content={"success": False, "error": "Session not found"})

    if not session.demo_mode:
        return JSONResponse(status_code=403, content={"success": False, "error": "Debug tier switch is only available in demo mode"})

    if tier_request.tier not in valid_tiers:
        return JSONResponse(status_code=400, content={"success": False, "error": f"Invalid tier. Must be one of: {', '.join(sorted(valid_tiers))}"})

    update_session(session_id, tier=tier_request.tier)
    return JSONResponse(content={"success": True, "tier": tier_request.tier})


def setup_api_routes(app: FastAPI, tier: str) -> None:
    """Set up API routes for state management."""

    @app.post("/api/install-license")
    async def install_license(request: LicenseInstallRequest) -> JSONResponse:
        return await _handle_install_license(request)

    @app.get("/api/state")
    async def get_state(request: Request) -> JSONResponse:
        return await _handle_get_state(request)

    @app.post("/api/reset")
    async def reset_session(request: Request) -> JSONResponse:
        return await _handle_reset_session(request, tier)

    @app.post("/api/navigate")
    async def navigate(request: Request, nav_request: NavigateRequest) -> JSONResponse:
        return await _handle_navigate(request, nav_request)

    @app.post("/api/update-data")
    async def update_data(request: Request, data_request: UpdateDataRequest) -> JSONResponse:
        return await _handle_update_data(request, data_request)

    @app.post("/api/select-track")
    async def select_track(request: Request, track_request: SelectTrackRequest) -> JSONResponse:
        return await _handle_select_track(request, track_request)

    @app.post("/api/debug/tier")
    async def debug_tier(request: Request, tier_request: DebugTierRequest) -> JSONResponse:
        return await _handle_debug_tier(request, tier_request)

    # Set up step API routes from dedicated modules
    setup_project_api_routes(app)
    setup_enforcement_api_routes(app, tier)
    setup_review_api_routes(app)
    setup_trello_api_routes(app)
    setup_github_api_routes(app)
    setup_budget_api_routes(app)
    setup_mcp_api_routes(app)
    setup_chat_api_routes(app)

    from bpsai_pair.wizard.guided_api import setup_guided_api_routes
    setup_guided_api_routes(app)
    setup_update_api_routes(app)

    from bpsai_pair.wizard.editor_api import setup_editor_api_routes
    setup_editor_api_routes(app)
