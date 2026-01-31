"""API route handlers for Trello integration configuration.

This module contains the API endpoints for the Trello setup step,
including connection testing, board listing, and configuration submission.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from bpsai_pair.wizard.session import SESSION_COOKIE_NAME
from bpsai_pair.wizard.state import (
    get_next_url_after_integration,
    get_session,
    mark_step_completed,
    update_session,
)
from bpsai_pair.wizard.steps import ROUTE_STEP_MAP


class TrelloTestRequest(BaseModel):
    """Request body for Trello connection test."""

    api_key: str
    token: str


class TrelloConfigRequest(BaseModel):
    """Request body for Trello configuration submission."""

    enabled: bool = False
    api_key: str | None = None
    token: str | None = None
    board_id: str | None = None
    board_name: str | None = None
    default_project: str | None = None
    default_stack: str | None = None
    repo_url: str | None = None
    mode: str = "native"


def _test_trello_connection(api_key: str, token: str) -> dict:
    """Test Trello connection and return boards if successful."""
    try:
        from bpsai_pair.trello.client import TrelloService

        service = TrelloService(api_key=api_key, token=token)
        if not service.healthcheck():
            return {"success": False, "error": "Connection failed. Check credentials."}

        boards = service.list_boards()
        board_list = [
            {"id": b.id, "name": b.name}
            for b in boards
            if not getattr(b, "closed", False)
        ]
        return {"success": True, "boards": board_list}
    except ImportError:
        return {"success": False, "error": "Trello library not installed. Install with: pip install py-trello"}
    except Exception as e:
        return {"success": False, "error": f"Connection failed: {e!s}"}


async def _handle_test_connection(request: Request, test_request: TrelloTestRequest) -> JSONResponse:
    """Handle Trello connection test."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "No session"})

    result = _test_trello_connection(test_request.api_key, test_request.token)
    if not result.get("success"):
        return JSONResponse(status_code=400, content=result)

    return JSONResponse(content=result)


async def _handle_submit_trello(request: Request, trello_request: TrelloConfigRequest) -> JSONResponse:
    """Handle Trello configuration submission."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "No session"})

    session = get_session(session_id)
    if not session:
        return JSONResponse(status_code=400, content={"success": False, "error": "Session not found"})

    trello_data: dict = {"enabled": trello_request.enabled}

    if trello_request.enabled:
        trello_data.update({
            "api_key": trello_request.api_key,
            "token": trello_request.token,
            "board_id": trello_request.board_id,
            "board_name": trello_request.board_name,
            "default_project": trello_request.default_project,
            "default_stack": trello_request.default_stack,
            "repo_url": trello_request.repo_url,
            "mode": trello_request.mode,
        })

    current_data = session.data or {}
    current_data["trello"] = trello_data
    update_session(session_id, data=current_data)
    mark_step_completed(session_id, ROUTE_STEP_MAP["/wizard/trello"])

    # Get next URL - may be next pending integration or return to review
    next_url = get_next_url_after_integration(session_id, "/wizard/github")

    return JSONResponse(content={
        "success": True,
        "next_url": next_url,
    })


def setup_trello_api_routes(app: FastAPI) -> None:
    """Set up API routes for Trello integration."""

    @app.post("/api/trello/test")
    async def test_trello(request: Request, test_request: TrelloTestRequest) -> JSONResponse:
        return await _handle_test_connection(request, test_request)

    @app.post("/api/trello")
    async def submit_trello(request: Request, trello_request: TrelloConfigRequest) -> JSONResponse:
        return await _handle_submit_trello(request, trello_request)
