"""Route setup for the wizard application.

This module coordinates route setup from sub-modules.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from bpsai_pair.wizard.api_routes import setup_api_routes
from bpsai_pair.wizard.page_routes import (
    setup_chat_route,
    setup_enforcement_route,
    setup_project_route,
    setup_review_route,
    setup_success_route,
    setup_welcome_route,
)
from bpsai_pair.wizard.pro_page_routes import (
    setup_budget_route,
    setup_github_route,
    setup_mcp_route,
    setup_trello_route,
)
from bpsai_pair.wizard.session import _set_session_cookie, get_or_create_session, resolve_tier


def setup_routes(
    app: FastAPI,
    templates: Jinja2Templates,
    tier: str,
    tier_display: str,
) -> None:
    """Set up all application routes."""
    _setup_page_routes(app, templates, tier, tier_display)
    setup_welcome_route(app, templates, tier, tier_display)
    setup_project_route(app, templates, tier, tier_display)
    setup_enforcement_route(app, templates, tier, tier_display)
    setup_chat_route(app, templates, tier, tier_display)
    setup_review_route(app, templates, tier, tier_display)
    setup_success_route(app, templates, tier, tier_display)
    setup_trello_route(app, templates, tier, tier_display)
    setup_github_route(app, templates, tier, tier_display)
    setup_budget_route(app, templates, tier, tier_display)
    setup_mcp_route(app, templates, tier, tier_display)
    setup_api_routes(app, tier)


def _setup_page_routes(
    app: FastAPI,
    templates: Jinja2Templates,
    tier: str,
    tier_display: str,
) -> None:
    """Set up core page rendering routes."""
    from bpsai_pair.wizard.app import get_steps_for_tier
    from bpsai_pair.wizard.demo import get_config_path

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request) -> HTMLResponse:
        """Render the main wizard page."""
        session, is_new = get_or_create_session(request, tier)
        eff_tier, eff_display = resolve_tier(session, tier, tier_display)
        steps = get_steps_for_tier(eff_tier, session.current_step, session.completed_steps, session.track)
        config_path = get_config_path(session.session_id, session.demo_mode)
        response = templates.TemplateResponse(
            request,
            "index.html",
            {
                "tier": eff_tier,
                "tier_display": eff_display,
                "steps": steps,
                "demo_mode": session.demo_mode,
                "config_path": str(config_path),
            },
        )
        if is_new:
            _set_session_cookie(response, session)
        return response

    @app.get("/health")
    async def health() -> dict:
        """Health check endpoint."""
        return {"status": "ok", "tier": tier}
