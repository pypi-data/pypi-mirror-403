"""API route handlers for enforcement configuration.

This module contains the API endpoint for the enforcement settings step.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from bpsai_pair.wizard.session import SESSION_COOKIE_NAME
from bpsai_pair.wizard.state import get_session, mark_step_completed, update_session
from bpsai_pair.wizard.steps import ROUTE_STEP_MAP

VALID_PRESETS = {"permissive", "balanced", "strict"}
PRO_TIERS = {"pro", "team", "enterprise"}


class EnforcementRequest(BaseModel):
    """Request body for enforcement configuration."""

    preset: str
    ac_verification: bool = True
    state_machine: bool = True
    bypass_audit: bool = True
    protected_paths: list[str] | None = None


def _validate_enforcement_request(request: EnforcementRequest) -> str | None:
    """Validate enforcement request data. Returns error message or None."""
    if request.preset not in VALID_PRESETS:
        return f"Invalid preset. Must be one of: {', '.join(sorted(VALID_PRESETS))}"
    return None


def _get_next_url(tier: str) -> str:
    """Get the next URL after enforcement. All tiers flow through all pages."""
    return "/wizard/trello"


async def _handle_enforcement(request: Request, enforcement_request: EnforcementRequest, tier: str) -> JSONResponse:
    """Handle enforcement configuration submission."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "No session"})

    session = get_session(session_id)
    if not session:
        return JSONResponse(status_code=400, content={"success": False, "error": "Session not found"})

    error = _validate_enforcement_request(enforcement_request)
    if error:
        return JSONResponse(status_code=400, content={"success": False, "error": error})

    enforcement_data = {
        "preset": enforcement_request.preset,
        "ac_verification": enforcement_request.ac_verification,
        "state_machine": enforcement_request.state_machine,
        "bypass_audit": enforcement_request.bypass_audit,
    }

    if enforcement_request.protected_paths is not None:
        enforcement_data["protected_paths"] = enforcement_request.protected_paths

    current_data = session.data or {}
    current_data["enforcement"] = enforcement_data
    update_session(session_id, data=current_data)

    # Mark enforcement step as completed
    mark_step_completed(session_id, ROUTE_STEP_MAP["/wizard/enforcement"])

    return JSONResponse(content={
        "success": True,
        "next_url": _get_next_url(tier),
    })


def setup_enforcement_api_routes(app: FastAPI, tier: str = "solo") -> None:
    """Set up API routes for enforcement configuration."""

    @app.post("/api/enforcement")
    async def submit_enforcement(request: Request, enforcement_request: EnforcementRequest) -> JSONResponse:
        return await _handle_enforcement(request, enforcement_request, tier)
