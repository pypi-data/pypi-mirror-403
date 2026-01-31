"""API route handlers for GitHub integration configuration.

This module contains the API endpoints for the GitHub setup step,
including connection testing, repository detection, and configuration submission.
"""

from __future__ import annotations

import subprocess

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


class GitHubTestRequest(BaseModel):
    """Request body for GitHub connection test."""

    token: str


class GitHubConfigRequest(BaseModel):
    """Request body for GitHub configuration submission."""

    enabled: bool = False
    token: str | None = None
    repo_url: str | None = None
    auto_pr: bool = True
    default_reviewers: str | None = None


def _test_github_connection(token: str) -> dict:
    """Test GitHub connection and return username if successful."""
    try:
        from github import Github, GithubException

        g = Github(token)
        user = g.get_user()
        username = user.login
        return {"success": True, "username": username}
    except ImportError:
        return {"success": False, "error": "PyGithub not installed. Install with: pip install PyGithub"}
    except Exception as e:
        return {"success": False, "error": f"Connection failed: {e!s}"}


def _detect_repo_url() -> str | None:
    """Auto-detect repository URL from .git config."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            if url.startswith("git@github.com:"):
                url = url.replace("git@github.com:", "https://github.com/")
            if url.endswith(".git"):
                url = url[:-4]
            return url
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


async def _handle_test_connection(request: Request, test_request: GitHubTestRequest) -> JSONResponse:
    """Handle GitHub connection test."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "No session"})

    result = _test_github_connection(test_request.token)
    if not result.get("success"):
        return JSONResponse(status_code=400, content=result)

    return JSONResponse(content=result)


async def _handle_detect_repo(request: Request) -> JSONResponse:
    """Handle repository URL auto-detection."""
    repo_url = _detect_repo_url()
    return JSONResponse(content={"repo_url": repo_url or ""})


async def _handle_submit_github(request: Request, github_request: GitHubConfigRequest) -> JSONResponse:
    """Handle GitHub configuration submission."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "No session"})

    session = get_session(session_id)
    if not session:
        return JSONResponse(status_code=400, content={"success": False, "error": "Session not found"})

    github_data: dict = {"enabled": github_request.enabled}

    if github_request.enabled:
        github_data.update({
            "token": github_request.token,
            "repo_url": github_request.repo_url,
            "auto_pr": github_request.auto_pr,
            "default_reviewers": github_request.default_reviewers,
        })

    current_data = session.data or {}
    current_data["github"] = github_data
    update_session(session_id, data=current_data)
    mark_step_completed(session_id, ROUTE_STEP_MAP["/wizard/github"])

    # Get next URL - may be next pending integration or return to review
    next_url = get_next_url_after_integration(session_id, "/wizard/budget")

    return JSONResponse(content={
        "success": True,
        "next_url": next_url,
    })


def setup_github_api_routes(app: FastAPI) -> None:
    """Set up API routes for GitHub integration."""

    @app.post("/api/github/test")
    async def test_github(request: Request, test_request: GitHubTestRequest) -> JSONResponse:
        return await _handle_test_connection(request, test_request)

    @app.get("/api/github/detect-repo")
    async def detect_repo(request: Request) -> JSONResponse:
        return await _handle_detect_repo(request)

    @app.post("/api/github")
    async def submit_github(request: Request, github_request: GitHubConfigRequest) -> JSONResponse:
        return await _handle_submit_github(request, github_request)
