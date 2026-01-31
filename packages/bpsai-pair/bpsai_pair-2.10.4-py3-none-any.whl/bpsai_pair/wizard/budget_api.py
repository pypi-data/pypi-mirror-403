"""API route handlers for Token Budget & Model Routing configuration.

This module contains the API endpoint for the budget setup step,
including threshold validation and model routing configuration.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from bpsai_pair.wizard.session import SESSION_COOKIE_NAME
from bpsai_pair.wizard.state import get_session, mark_step_completed, update_session
from bpsai_pair.wizard.steps import ROUTE_STEP_MAP

VALID_ENFORCEMENT_MODES = {"warn", "soft", "hard"}
VALID_MODEL_PRESETS = {"recommended", "quality", "fastest", "custom"}
VALID_MODELS = {"claude-sonnet-4-5", "claude-opus-4-5", "claude-haiku-4-5"}


class BudgetConfigRequest(BaseModel):
    """Request body for budget configuration submission."""

    skip: bool = False
    warning_threshold: int = 75
    critical_threshold: int = 90
    enforcement_mode: str = "soft"
    model_preset: str = "recommended"
    navigator_model: str = "claude-sonnet-4-5"
    driver_model: str = "claude-sonnet-4-5"
    reviewer_model: str = "claude-haiku-4-5"
    cost_tracking: bool = True


def _validate_budget_config(req: BudgetConfigRequest) -> str | None:
    """Validate budget configuration. Returns error string or None."""
    if req.skip:
        return None
    if req.warning_threshold >= req.critical_threshold:
        return "Warning threshold must be less than critical threshold."
    if not (0 < req.warning_threshold <= 100):
        return "Warning threshold must be between 1 and 100."
    if not (0 < req.critical_threshold <= 100):
        return "Critical threshold must be between 1 and 100."
    if req.enforcement_mode not in VALID_ENFORCEMENT_MODES:
        return f"Invalid enforcement mode: {req.enforcement_mode}"
    return None


async def _handle_submit_budget(request: Request, budget_request: BudgetConfigRequest) -> JSONResponse:
    """Handle budget configuration submission."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "No session"})

    session = get_session(session_id)
    if not session:
        return JSONResponse(status_code=400, content={"success": False, "error": "Session not found"})

    error = _validate_budget_config(budget_request)
    if error:
        return JSONResponse(status_code=400, content={"success": False, "error": error})

    if budget_request.skip:
        budget_data: dict = {"skip": True}
    else:
        budget_data = {
            "warning_threshold": budget_request.warning_threshold,
            "critical_threshold": budget_request.critical_threshold,
            "enforcement_mode": budget_request.enforcement_mode,
            "model_preset": budget_request.model_preset,
            "navigator_model": budget_request.navigator_model,
            "driver_model": budget_request.driver_model,
            "reviewer_model": budget_request.reviewer_model,
            "cost_tracking": budget_request.cost_tracking,
        }

    current_data = session.data or {}
    current_data["budget"] = budget_data
    update_session(session_id, data=current_data)
    mark_step_completed(session_id, ROUTE_STEP_MAP["/wizard/budget"])

    return JSONResponse(content={
        "success": True,
        "next_url": "/wizard/mcp",
    })


def setup_budget_api_routes(app: FastAPI) -> None:
    """Set up API routes for budget configuration."""

    @app.post("/api/budget")
    async def submit_budget(request: Request, budget_request: BudgetConfigRequest) -> JSONResponse:
        return await _handle_submit_budget(request, budget_request)
