"""API route handlers for MCP & Timer configuration.

This module contains the API endpoints for the MCP setup step,
including Toggl connection testing and configuration submission.
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


class TogglTestRequest(BaseModel):
    """Request body for Toggl connection test."""

    api_key: str


class McpConfigRequest(BaseModel):
    """Request body for MCP configuration submission."""

    mcp_enabled: bool = False
    mcp_port: int = 3000
    toggl_enabled: bool = False
    toggl_api_key: str | None = None
    toggl_workspace_id: str | None = None
    toggl_workspace_name: str | None = None


def _test_toggl_connection(api_key: str) -> dict:
    """Test Toggl connection and return workspaces if successful."""
    try:
        import requests as http_requests

        resp = http_requests.get(
            "https://api.track.toggl.com/api/v9/me",
            auth=(api_key, "api_token"),
            timeout=10,
        )
        if resp.status_code != 200:
            return {"success": False, "error": "Invalid API key."}

        ws_resp = http_requests.get(
            "https://api.track.toggl.com/api/v9/workspaces",
            auth=(api_key, "api_token"),
            timeout=10,
        )
        workspaces = []
        if ws_resp.status_code == 200:
            for ws in ws_resp.json():
                workspaces.append({"id": str(ws.get("id", "")), "name": ws.get("name", "")})

        return {"success": True, "workspaces": workspaces}
    except ImportError:
        return {"success": False, "error": "requests library not available."}
    except Exception as e:
        return {"success": False, "error": f"Connection failed: {e!s}"}


async def _handle_test_toggl(request: Request, test_request: TogglTestRequest) -> JSONResponse:
    """Handle Toggl connection test."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "No session"})

    result = _test_toggl_connection(test_request.api_key)
    if not result.get("success"):
        return JSONResponse(status_code=400, content=result)

    return JSONResponse(content=result)


async def _handle_submit_mcp(request: Request, mcp_request: McpConfigRequest) -> JSONResponse:
    """Handle MCP configuration submission."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "No session"})

    session = get_session(session_id)
    if not session:
        return JSONResponse(status_code=400, content={"success": False, "error": "Session not found"})

    mcp_data: dict = {
        "mcp_enabled": mcp_request.mcp_enabled,
        "mcp_port": mcp_request.mcp_port,
        "toggl_enabled": mcp_request.toggl_enabled,
    }

    if mcp_request.toggl_enabled:
        mcp_data.update({
            "toggl_api_key": mcp_request.toggl_api_key,
            "toggl_workspace_id": mcp_request.toggl_workspace_id,
            "toggl_workspace_name": mcp_request.toggl_workspace_name,
        })

    current_data = session.data or {}
    current_data["mcp"] = mcp_data
    update_session(session_id, data=current_data)
    mark_step_completed(session_id, ROUTE_STEP_MAP["/wizard/mcp"])

    # Get next URL - may be next pending integration or return to review
    next_url = get_next_url_after_integration(session_id, "/wizard/review")

    return JSONResponse(content={
        "success": True,
        "next_url": next_url,
    })


def setup_mcp_api_routes(app: FastAPI) -> None:
    """Set up API routes for MCP configuration."""

    @app.post("/api/mcp/test-toggl")
    async def test_toggl(request: Request, test_request: TogglTestRequest) -> JSONResponse:
        return await _handle_test_toggl(request, test_request)

    @app.post("/api/mcp")
    async def submit_mcp(request: Request, mcp_request: McpConfigRequest) -> JSONResponse:
        return await _handle_submit_mcp(request, mcp_request)
