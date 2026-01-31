"""Page rendering routes for Pro-tier wizard steps.

This module contains the page route handlers for Pro-tier integration
steps: Trello, GitHub, Budget/Model Routing, and MCP/Timer.

Solo-tier users see a locked overlay with upgrade/skip options.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from bpsai_pair.wizard.session import _set_session_cookie, get_or_create_session, resolve_tier
from bpsai_pair.wizard.state import update_session
from bpsai_pair.wizard.steps import ROUTE_STEP_MAP

PRO_TIERS = {"pro", "team", "enterprise"}

# Feature metadata for locked overlay on each Pro page
LOCKED_PAGE_META: dict[str, dict] = {
    "trello": {
        "feature_name": "Trello Integration",
        "feature_description": "Sync tasks, track progress, and automate workflow with Trello boards.",
        "feature_highlights": [
            "Two-way task sync with Trello boards",
            "Automatic card movement on status change",
            "Custom field mapping for projects and stacks",
        ],
        "skip_url": "/wizard/github",
    },
    "github": {
        "feature_name": "GitHub Integration",
        "feature_description": "Auto-create PRs, detect repositories, and streamline code review.",
        "feature_highlights": [
            "Auto-detect repository from git remotes",
            "Create pull requests with task context",
            "Configure default reviewers and auto-PR settings",
        ],
        "skip_url": "/wizard/budget",
    },
    "budget": {
        "feature_name": "Token Budget & Model Routing",
        "feature_description": "Configure spending limits and choose AI models for each role.",
        "feature_highlights": [
            "Set warning and critical budget thresholds",
            "Route different AI models to Navigator, Driver, Reviewer",
            "Track token usage and costs per task",
        ],
        "skip_url": "/wizard/mcp",
    },
    "mcp": {
        "feature_name": "MCP & Timer Setup",
        "feature_description": "Configure the MCP server and time tracking integration.",
        "feature_highlights": [
            "Run a local MCP server for autonomous agent operation",
            "Connect Toggl for automatic time tracking",
            "Link time entries to tasks and sprints",
        ],
        "skip_url": "/wizard/review",
    },
}


def _locked_context(page_key: str, tier: str) -> dict:
    """Build template context for locked page overlay."""
    meta = LOCKED_PAGE_META[page_key]
    return {
        "is_locked": tier not in PRO_TIERS,
        **meta,
    }


def setup_trello_route(
    app: FastAPI,
    templates: Jinja2Templates,
    tier: str,
    tier_display: str,
) -> None:
    """Set up the Trello integration page route."""
    from bpsai_pair.wizard.app import get_steps_for_tier
    from bpsai_pair.wizard.demo import get_config_path

    @app.get("/wizard/trello", response_class=HTMLResponse)
    async def trello_page(request: Request) -> HTMLResponse:
        """Render the Trello integration configuration page."""
        session, is_new = get_or_create_session(request, tier)
        eff_tier, eff_display = resolve_tier(session, tier, tier_display)
        step_number = ROUTE_STEP_MAP["/wizard/trello"]
        update_session(session.session_id, current_step=step_number)
        steps = get_steps_for_tier(eff_tier, step_number, session.completed_steps, session.track)
        config_path = get_config_path(session.session_id, session.demo_mode)
        response = templates.TemplateResponse(
            request,
            "trello.html",
            {
                "tier": eff_tier,
                "tier_display": eff_display,
                "steps": steps,
                "demo_mode": session.demo_mode,
                "config_path": str(config_path),
                **_locked_context("trello", eff_tier),
            },
        )
        if is_new:
            _set_session_cookie(response, session)
        return response


def setup_github_route(
    app: FastAPI,
    templates: Jinja2Templates,
    tier: str,
    tier_display: str,
) -> None:
    """Set up the GitHub integration page route."""
    from bpsai_pair.wizard.app import get_steps_for_tier
    from bpsai_pair.wizard.demo import get_config_path

    @app.get("/wizard/github", response_class=HTMLResponse)
    async def github_page(request: Request) -> HTMLResponse:
        """Render the GitHub integration configuration page."""
        session, is_new = get_or_create_session(request, tier)
        eff_tier, eff_display = resolve_tier(session, tier, tier_display)
        step_number = ROUTE_STEP_MAP["/wizard/github"]
        update_session(session.session_id, current_step=step_number)
        steps = get_steps_for_tier(eff_tier, step_number, session.completed_steps, session.track)
        config_path = get_config_path(session.session_id, session.demo_mode)
        response = templates.TemplateResponse(
            request,
            "github.html",
            {
                "tier": eff_tier,
                "tier_display": eff_display,
                "steps": steps,
                "demo_mode": session.demo_mode,
                "config_path": str(config_path),
                **_locked_context("github", eff_tier),
            },
        )
        if is_new:
            _set_session_cookie(response, session)
        return response


def setup_budget_route(
    app: FastAPI,
    templates: Jinja2Templates,
    tier: str,
    tier_display: str,
) -> None:
    """Set up the Token Budget & Model Routing page route."""
    from bpsai_pair.wizard.app import get_steps_for_tier
    from bpsai_pair.wizard.demo import get_config_path

    @app.get("/wizard/budget", response_class=HTMLResponse)
    async def budget_page(request: Request) -> HTMLResponse:
        """Render the budget & model routing configuration page."""
        session, is_new = get_or_create_session(request, tier)
        eff_tier, eff_display = resolve_tier(session, tier, tier_display)
        step_number = ROUTE_STEP_MAP["/wizard/budget"]
        update_session(session.session_id, current_step=step_number)
        steps = get_steps_for_tier(eff_tier, step_number, session.completed_steps, session.track)
        config_path = get_config_path(session.session_id, session.demo_mode)
        response = templates.TemplateResponse(
            request,
            "budget.html",
            {
                "tier": eff_tier,
                "tier_display": eff_display,
                "steps": steps,
                "demo_mode": session.demo_mode,
                "config_path": str(config_path),
                **_locked_context("budget", eff_tier),
            },
        )
        if is_new:
            _set_session_cookie(response, session)
        return response


def setup_mcp_route(
    app: FastAPI,
    templates: Jinja2Templates,
    tier: str,
    tier_display: str,
) -> None:
    """Set up the MCP & Timer Setup page route."""
    from bpsai_pair.wizard.app import get_steps_for_tier
    from bpsai_pair.wizard.demo import get_config_path

    @app.get("/wizard/mcp", response_class=HTMLResponse)
    async def mcp_page(request: Request) -> HTMLResponse:
        """Render the MCP & timer setup configuration page."""
        session, is_new = get_or_create_session(request, tier)
        eff_tier, eff_display = resolve_tier(session, tier, tier_display)
        step_number = ROUTE_STEP_MAP["/wizard/mcp"]
        update_session(session.session_id, current_step=step_number)
        steps = get_steps_for_tier(eff_tier, step_number, session.completed_steps, session.track)
        config_path = get_config_path(session.session_id, session.demo_mode)
        response = templates.TemplateResponse(
            request,
            "mcp.html",
            {
                "tier": eff_tier,
                "tier_display": eff_display,
                "steps": steps,
                "demo_mode": session.demo_mode,
                "config_path": str(config_path),
                **_locked_context("mcp", eff_tier),
            },
        )
        if is_new:
            _set_session_cookie(response, session)
        return response
