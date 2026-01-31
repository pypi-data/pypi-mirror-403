"""FastAPI application for the PairCoder Setup Wizard.

This module provides a web-based setup wizard with license-aware templates.
License information is loaded on startup and passed to all templates.
"""

from __future__ import annotations

import platform
import subprocess
import webbrowser
from pathlib import Path
from typing import TypedDict

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Default port for the wizard server
DEFAULT_PORT = 8765

# Paths for templates and static files
WIZARD_DIR = Path(__file__).parent
TEMPLATES_DIR = WIZARD_DIR / "templates"
STATIC_DIR = WIZARD_DIR / "static"


class WizardStep(TypedDict):
    """Type definition for a wizard step."""

    number: int
    name: str
    description: str
    locked: bool
    current: bool
    completed: bool


# Re-export ROUTE_STEP_MAP from steps module (canonical location)
from bpsai_pair.wizard.steps import ROUTE_STEP_MAP  # noqa: E402


# Step definitions with tier requirements - by track
WIZARD_STEPS_BY_TRACK = {
    "quick": [
        {
            "number": 1,
            "name": "Project Setup",
            "description": "Configure your project settings and preferences.",
            "requires_tier": None,
        },
        {
            "number": 2,
            "name": "Enforcement",
            "description": "Set up enforcement rules and validation.",
            "requires_tier": None,
        },
        {
            "number": 3,
            "name": "Integrations",
            "description": "Connect to Trello, GitHub, and other services.",
            "requires_tier": "pro",
        },
        {
            "number": 4,
            "name": "AI Settings",
            "description": "Configure AI agents and MCP servers.",
            "requires_tier": "pro",
        },
    ],
    "guided": [
        {
            "number": 1,
            "name": "Welcome",
            "description": "Get started with PairCoder.",
            "requires_tier": None,
        },
        {
            "number": 2,
            "name": "Chat",
            "description": "Describe your project and get a config.",
            "requires_tier": None,
        },
        {
            "number": 3,
            "name": "Review",
            "description": "Review and confirm your configuration.",
            "requires_tier": None,
        },
        {
            "number": 4,
            "name": "Done",
            "description": "Setup complete.",
            "requires_tier": None,
        },
    ],
}

# Default steps for backwards compatibility
WIZARD_STEPS = WIZARD_STEPS_BY_TRACK["quick"]


def get_tier() -> str:
    """Get the current license tier."""
    try:
        from bpsai_pair.licensing import get_tier as _get_tier

        return _get_tier()
    except ImportError:
        return "solo"


def get_current_tier_display_name() -> str:
    """Get the display name for the current tier."""
    try:
        from bpsai_pair.licensing import (
            get_current_tier_display_name as _get_display,
        )

        return _get_display()
    except ImportError:
        return "Solo"


def _is_wsl() -> bool:
    """Check if running in Windows Subsystem for Linux."""
    try:
        return "microsoft" in platform.uname().release.lower()
    except Exception:
        return False


def open_browser(url: str) -> None:
    """Open the given URL in the default web browser.

    Handles WSL environments where standard browser opening may fail.
    """
    if _is_wsl():
        try:
            # Use Windows explorer.exe to open URL from WSL
            subprocess.run(["explorer.exe", url], check=False, capture_output=True)
            return
        except FileNotFoundError:
            pass  # Fall through to standard webbrowser

    webbrowser.open(url)


def get_steps_for_tier(
    tier: str,
    current_step: int = 1,
    completed_steps: set[int] | None = None,
    track: str = "quick",
) -> list[WizardStep]:
    """Get wizard steps with completion and current status.

    Step locking is no longer handled at the indicator level — all tiers
    see all 4 step indicators. Locking is handled at the page content
    level instead (locked overlay for Solo tier on Pro pages).

    Completion is based on actual form submission (completed_steps set),
    not on the current step position.

    Args:
        tier: The user's license tier
        current_step: The current step number
        completed_steps: Set of completed step numbers
        track: The wizard track ("quick" or "guided")
    """
    done = completed_steps or set()
    step_defs = WIZARD_STEPS_BY_TRACK.get(track, WIZARD_STEPS)
    steps: list[WizardStep] = []
    for step_def in step_defs:
        steps.append({
            "number": step_def["number"],
            "name": step_def["name"],
            "description": step_def["description"],
            "locked": False,
            "current": step_def["number"] == current_step,
            "completed": step_def["number"] in done,
        })

    return steps


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    from bpsai_pair.wizard.routes import setup_routes

    app = FastAPI(
        title="PairCoder Setup Wizard",
        description="Web-based setup wizard for PairCoder configuration",
        docs_url=None,
        redoc_url=None,
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Configure templates
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.state.templates = templates

    # Load license info and set up routes
    tier = get_tier()
    tier_display = get_current_tier_display_name()
    setup_routes(app, templates, tier, tier_display)

    return app
