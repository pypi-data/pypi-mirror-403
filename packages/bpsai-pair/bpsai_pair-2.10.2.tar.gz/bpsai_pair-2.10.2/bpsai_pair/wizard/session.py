"""Session cookie management for the wizard.

This module handles cookie-based session identification.
"""

from __future__ import annotations

from fastapi import Request, Response

from bpsai_pair.wizard.state import WizardState, create_session, get_session

SESSION_COOKIE_NAME = "paircoder_wizard_session"


def is_demo_request(request: Request) -> bool:
    """Check if request is for demo mode."""
    return request.query_params.get("demo") == "1"


def get_or_create_session(request: Request, tier: str) -> tuple[WizardState, bool]:
    """Get existing session or create new one.

    Returns:
        Tuple of (session, is_new) where is_new indicates if session was created
    """
    demo_mode = is_demo_request(request)
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if session_id:
        session = get_session(session_id)
        if session:
            # If requesting demo but session isn't demo, create new
            if demo_mode and not session.demo_mode:
                session = create_session(tier, demo_mode=True)
                return session, True
            return session, False

    session = create_session(tier, demo_mode=demo_mode)
    return session, True


_TIER_DISPLAY: dict[str, str] = {
    "solo": "Solo",
    "pro": "Pro",
    "team": "Team",
    "enterprise": "Enterprise",
}


def resolve_tier(session: WizardState, default_tier: str, default_display: str) -> tuple[str, str]:
    """Return the effective (tier, tier_display) for template rendering.

    In demo mode the session's tier (set via the debug switcher) takes
    precedence.  Outside demo mode the startup tier is used.
    """
    if session.demo_mode:
        t = session.tier
        return t, _TIER_DISPLAY.get(t, t.title())
    return default_tier, default_display


def _set_session_cookie(response: Response, session: WizardState) -> None:
    """Set the session cookie on a response."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session.session_id,
        httponly=True,
        samesite="lax",
        max_age=86400,  # 24 hours
    )
