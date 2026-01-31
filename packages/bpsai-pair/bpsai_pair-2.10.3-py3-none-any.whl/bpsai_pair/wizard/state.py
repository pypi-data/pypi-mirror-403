"""Wizard session state management.

This module provides server-side session storage for wizard state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from bpsai_pair.wizard.steps import STEPS, get_available_steps


@dataclass
class WizardState:
    """Session state for a wizard instance."""

    session_id: str
    tier: str
    track: str  # "quick" or "guided"
    current_step: int
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    demo_mode: bool = False
    completed_steps: set[int] = field(default_factory=set)


# Re-export for backwards compatibility
from bpsai_pair.wizard.steps import STEPS, StepDefinition, get_available_steps  # noqa: E402, F811

# In-memory session storage (for single-server deployment)
_sessions: dict[str, WizardState] = {}


def create_session(tier: str, track: str = "quick", demo_mode: bool = False) -> WizardState:
    """Create a new wizard session."""
    session_id = str(uuid.uuid4())
    session = WizardState(
        session_id=session_id,
        tier=tier,
        track=track,
        current_step=1,
        demo_mode=demo_mode,
    )
    _sessions[session_id] = session

    # Create demo directory if in demo mode
    if demo_mode:
        from bpsai_pair.wizard.demo import ensure_demo_dir
        ensure_demo_dir(session_id)

    return session


def get_session(session_id: str) -> WizardState | None:
    """Get an existing session by ID."""
    return _sessions.get(session_id)


def update_session(
    session_id: str,
    current_step: int | None = None,
    data: dict[str, Any] | None = None,
    track: str | None = None,
    tier: str | None = None,
) -> bool:
    """Update an existing session."""
    session = _sessions.get(session_id)
    if session is None:
        return False

    if current_step is not None:
        session.current_step = current_step
    if data is not None:
        session.data.update(data)
    if track is not None:
        session.track = track
    if tier is not None:
        session.tier = tier

    return True


def delete_session(session_id: str) -> bool:
    """Delete a session (for "Start Over" functionality)."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def _has_feature(tier: str, feature: str) -> bool:
    """Check if a tier has access to a feature."""
    pro_tiers = {"pro", "team", "enterprise"}
    pro_features = {"trello", "github", "token_budget", "mcp", "timer"}

    if feature in pro_features:
        return tier in pro_tiers
    return True


def mark_step_completed(session_id: str, step_number: int) -> bool:
    """Mark a step as completed in the session.

    Called after successful form submission for that step.
    """
    session = _sessions.get(session_id)
    if session is None:
        return False
    session.completed_steps.add(step_number)
    return True


def navigate_to_step(session_id: str, step_number: int) -> bool:
    """Navigate to a specific step.

    All tiers can navigate to all steps. Solo-tier users see locked
    overlays on Pro pages instead of being blocked from navigating.
    """
    session = _sessions.get(session_id)
    if session is None:
        return False

    all_steps = STEPS.get(session.track, STEPS["quick"])
    if step_number < 1 or step_number > len(all_steps):
        return False

    session.current_step = step_number
    return True


def clear_all_sessions() -> None:
    """Clear all sessions (for testing)."""
    _sessions.clear()


# Integration configuration helpers

AVAILABLE_INTEGRATIONS = {
    "trello": {
        "name": "Trello",
        "description": "Sync tasks to boards",
        "route": "/wizard/trello",
    },
    "github": {
        "name": "GitHub",
        "description": "Auto-create PRs and link tasks",
        "route": "/wizard/github",
    },
    "mcp": {
        "name": "MCP Server",
        "description": "Enable external tool access",
        "route": "/wizard/mcp",
    },
}


def get_available_integrations_for_tier(tier: str) -> list[dict]:
    """Get list of integrations available for the given tier.

    Returns empty list for Solo tier, full list for Pro/Enterprise.
    """
    if tier not in ("pro", "team", "enterprise"):
        return []

    return [
        {"id": key, **value}
        for key, value in AVAILABLE_INTEGRATIONS.items()
    ]


def get_integration_status(session_id: str) -> dict[str, bool]:
    """Get configuration status of each integration.

    Returns dict mapping integration ID to whether it's configured.
    """
    session = _sessions.get(session_id)
    if session is None:
        return {}

    data = session.data or {}
    return {
        "trello": bool(data.get("trello", {}).get("enabled")),
        "github": bool(data.get("github", {}).get("enabled")),
        "mcp": bool(data.get("mcp", {}).get("mcp_enabled")),
    }


def set_pending_integrations(session_id: str, integration_ids: list[str]) -> bool:
    """Set which integrations the user wants to configure.

    Called when user clicks "Configure Selected" on review page.
    Stores the list in session data for routing through integration pages.
    """
    session = _sessions.get(session_id)
    if session is None:
        return False

    # Filter to valid integration IDs
    valid_ids = [i for i in integration_ids if i in AVAILABLE_INTEGRATIONS]
    session.data["pending_integrations"] = valid_ids
    session.data["integration_return_to"] = "/wizard/review"
    return True


def get_next_pending_integration(session_id: str) -> str | None:
    """Get the next integration to configure and remove it from pending list.

    Returns the route to the next integration page, or None if done.
    """
    session = _sessions.get(session_id)
    if session is None:
        return None

    pending = session.data.get("pending_integrations", [])
    if not pending:
        return None

    # Pop the first one
    next_id = pending.pop(0)
    session.data["pending_integrations"] = pending

    integration = AVAILABLE_INTEGRATIONS.get(next_id)
    return integration["route"] if integration else None


def clear_pending_integrations(session_id: str) -> None:
    """Clear pending integrations list (called after configuration complete)."""
    session = _sessions.get(session_id)
    if session:
        session.data.pop("pending_integrations", None)
        session.data.pop("integration_return_to", None)


def get_next_url_after_integration(session_id: str, default_next: str) -> str:
    """Get the next URL after completing an integration configuration.

    If there are pending integrations, returns the next one.
    If returning from integration flow, returns the return_to URL.
    Otherwise, returns the default_next URL.
    """
    session = _sessions.get(session_id)
    if session is None:
        return default_next

    # Check for more pending integrations
    next_integration = get_next_pending_integration(session_id)
    if next_integration:
        return next_integration

    # Check for return URL (set when coming from review page)
    return_to = session.data.get("integration_return_to")
    if return_to:
        # Clear the return_to since we're done
        session.data.pop("integration_return_to", None)
        return return_to

    # Default flow
    return default_next
