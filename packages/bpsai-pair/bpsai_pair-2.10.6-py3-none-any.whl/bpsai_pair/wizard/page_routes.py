"""Page rendering routes for the wizard application.

This module contains the Solo-tier page route handlers:
welcome, project, enforcement, review, and success.

Pro-tier routes are in pro_page_routes.py.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from bpsai_pair.wizard.session import _set_session_cookie, get_or_create_session, resolve_tier
from bpsai_pair.wizard.state import (
    get_available_integrations_for_tier,
    get_integration_status,
    get_session,
    update_session,
)
from bpsai_pair.wizard.steps import ROUTE_STEP_MAP


def _check_existing_project(session_id: str, demo_mode: bool) -> bool:
    """Check if an existing .paircoder directory exists."""
    from bpsai_pair.wizard.demo import get_config_path

    config_path = get_config_path(session_id, demo_mode)
    return config_path.exists()


def setup_welcome_route(
    app: FastAPI,
    templates: Jinja2Templates,
    tier: str,
    tier_display: str,
) -> None:
    """Set up the welcome page route."""
    from bpsai_pair.wizard.app import get_steps_for_tier
    from bpsai_pair.wizard.demo import get_config_path

    @app.get("/welcome", response_class=HTMLResponse)
    async def welcome(request: Request) -> HTMLResponse:
        """Render the welcome page with track selection."""
        session, is_new = get_or_create_session(request, tier)
        eff_tier, eff_display = resolve_tier(session, tier, tier_display)
        steps = get_steps_for_tier(eff_tier, session.current_step, session.completed_steps, session.track)
        config_path = get_config_path(session.session_id, session.demo_mode)
        has_existing = _check_existing_project(session.session_id, session.demo_mode)
        response = templates.TemplateResponse(
            request,
            "welcome.html",
            {
                "tier": eff_tier,
                "tier_display": eff_display,
                "steps": steps,
                "demo_mode": session.demo_mode,
                "config_path": str(config_path),
                "has_existing_project": has_existing,
            },
        )
        if is_new:
            _set_session_cookie(response, session)
        return response


def setup_project_route(
    app: FastAPI,
    templates: Jinja2Templates,
    tier: str,
    tier_display: str,
) -> None:
    """Set up the project basics page route."""
    from bpsai_pair.wizard.app import get_steps_for_tier
    from bpsai_pair.wizard.demo import get_config_path

    @app.get("/wizard/project", response_class=HTMLResponse)
    async def project_page(request: Request) -> HTMLResponse:
        """Render the project basics configuration page."""
        session, is_new = get_or_create_session(request, tier)
        eff_tier, eff_display = resolve_tier(session, tier, tier_display)
        step_number = ROUTE_STEP_MAP["/wizard/project"]
        update_session(session.session_id, current_step=step_number)
        steps = get_steps_for_tier(eff_tier, step_number, session.completed_steps, session.track)
        config_path = get_config_path(session.session_id, session.demo_mode)
        # Get session data for pre-filling in update mode
        session_data = session.data if session.data else {}
        project_data = session_data.get("project", {})
        update_mode = session_data.get("update_mode", {})
        response = templates.TemplateResponse(
            request,
            "project.html",
            {
                "tier": eff_tier,
                "tier_display": eff_display,
                "steps": steps,
                "demo_mode": session.demo_mode,
                "config_path": str(config_path),
                "update_mode": bool(update_mode),
                "project_data": project_data,
            },
        )
        if is_new:
            _set_session_cookie(response, session)
        return response


def setup_enforcement_route(
    app: FastAPI,
    templates: Jinja2Templates,
    tier: str,
    tier_display: str,
) -> None:
    """Set up the enforcement settings page route."""
    from bpsai_pair.wizard.app import get_steps_for_tier
    from bpsai_pair.wizard.demo import get_config_path

    @app.get("/wizard/enforcement", response_class=HTMLResponse)
    async def enforcement_page(request: Request) -> HTMLResponse:
        """Render the enforcement settings configuration page."""
        session, is_new = get_or_create_session(request, tier)
        eff_tier, eff_display = resolve_tier(session, tier, tier_display)
        step_number = ROUTE_STEP_MAP["/wizard/enforcement"]
        update_session(session.session_id, current_step=step_number)
        steps = get_steps_for_tier(eff_tier, step_number, session.completed_steps, session.track)
        config_path = get_config_path(session.session_id, session.demo_mode)
        # Get session data for pre-filling in update mode
        session_data = session.data if session.data else {}
        enforcement_data = session_data.get("enforcement", {})
        update_mode = session_data.get("update_mode", {})
        response = templates.TemplateResponse(
            request,
            "enforcement.html",
            {
                "tier": eff_tier,
                "tier_display": eff_display,
                "steps": steps,
                "demo_mode": session.demo_mode,
                "config_path": str(config_path),
                "update_mode": bool(update_mode),
                "enforcement_data": enforcement_data,
            },
        )
        if is_new:
            _set_session_cookie(response, session)
        return response


def setup_review_route(
    app: FastAPI,
    templates: Jinja2Templates,
    tier: str,
    tier_display: str,
) -> None:
    """Set up the review page route."""
    from bpsai_pair.wizard.app import get_steps_for_tier
    from bpsai_pair.wizard.demo import get_config_path

    @app.get("/wizard/review", response_class=HTMLResponse)
    async def review_page(request: Request) -> HTMLResponse:
        """Render the review and create page."""
        session, is_new = get_or_create_session(request, tier)
        eff_tier, eff_display = resolve_tier(session, tier, tier_display)
        step_number = ROUTE_STEP_MAP["/wizard/review"]
        update_session(session.session_id, current_step=step_number)
        steps = get_steps_for_tier(eff_tier, step_number, session.completed_steps, session.track)
        config_path = get_config_path(session.session_id, session.demo_mode)

        # Get integration info for Pro/Enterprise tiers
        integrations = get_available_integrations_for_tier(eff_tier)
        integration_status = get_integration_status(session.session_id)

        response = templates.TemplateResponse(
            request,
            "review.html",
            {
                "tier": eff_tier,
                "tier_display": eff_display,
                "steps": steps,
                "demo_mode": session.demo_mode,
                "config_path": str(config_path),
                "integrations": integrations,
                "integration_status": integration_status,
            },
        )
        if is_new:
            _set_session_cookie(response, session)
        return response


def setup_chat_route(
    app: FastAPI,
    templates: Jinja2Templates,
    tier: str,
    tier_display: str,
) -> None:
    """Set up the guided chat page route."""
    from bpsai_pair.wizard.app import get_steps_for_tier
    from bpsai_pair.wizard.demo import get_config_path

    @app.get("/wizard/chat", response_class=HTMLResponse)
    async def chat_page(request: Request) -> HTMLResponse:
        """Render the guided chat page."""
        session, is_new = get_or_create_session(request, tier)
        eff_tier, eff_display = resolve_tier(session, tier, tier_display)
        step_number = ROUTE_STEP_MAP["/wizard/chat"]
        update_session(session.session_id, current_step=step_number)
        steps = get_steps_for_tier(eff_tier, step_number, session.completed_steps, session.track)
        config_path = get_config_path(session.session_id, session.demo_mode)
        response = templates.TemplateResponse(
            request,
            "chat.html",
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


def setup_success_route(
    app: FastAPI,
    templates: Jinja2Templates,
    tier: str,
    tier_display: str,
) -> None:
    """Set up the success page route."""
    from bpsai_pair.wizard.app import get_steps_for_tier
    from bpsai_pair.wizard.demo import get_config_path

    @app.get("/wizard/success", response_class=HTMLResponse)
    async def success_page(request: Request) -> HTMLResponse:
        """Render the success page with tier-appropriate next steps."""
        session, is_new = get_or_create_session(request, tier)
        eff_tier, eff_display = resolve_tier(session, tier, tier_display)
        step_number = ROUTE_STEP_MAP["/wizard/success"]
        update_session(session.session_id, current_step=step_number)
        steps = get_steps_for_tier(eff_tier, step_number, session.completed_steps, session.track)
        config_path = get_config_path(session.session_id, session.demo_mode)
        response = templates.TemplateResponse(
            request,
            "success.html",
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
