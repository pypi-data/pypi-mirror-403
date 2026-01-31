"""Step definitions and tier-aware step generation.

This module defines the wizard steps for each track and provides
functions to get available steps based on tier.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StepDefinition:
    """Definition of a wizard step."""

    id: str
    name: str
    route: str
    required_feature: str | None  # None = available to all


# Step definitions for each track
STEPS: dict[str, list[StepDefinition]] = {
    "quick": [
        StepDefinition("welcome", "Welcome", "/wizard/welcome", None),
        StepDefinition("project", "Project Basics", "/wizard/project", None),
        StepDefinition("enforcement", "Enforcement", "/wizard/enforcement", None),
        StepDefinition("trello", "Trello", "/wizard/trello", "trello"),
        StepDefinition("github", "GitHub", "/wizard/github", "github"),
        StepDefinition("budget", "Budget", "/wizard/budget", "token_budget"),
        StepDefinition("mcp", "MCP", "/wizard/mcp", "mcp"),
        StepDefinition("review", "Review", "/wizard/review", None),
        StepDefinition("success", "Done", "/wizard/success", None),
    ],
    "guided": [
        StepDefinition("welcome", "Welcome", "/wizard/welcome", None),
        StepDefinition("chat", "Chat", "/wizard/chat", None),
        StepDefinition("review", "Review", "/wizard/review", None),
        StepDefinition("success", "Done", "/wizard/success", None),
    ],
}


# Map page routes to step indicator numbers (4-step model)
ROUTE_STEP_MAP: dict[str, int] = {
    "/wizard/project": 1,
    "/wizard/enforcement": 2,
    "/wizard/chat": 2,
    "/wizard/trello": 3,
    "/wizard/github": 3,
    "/wizard/budget": 4,
    "/wizard/mcp": 4,
    "/wizard/review": 5,
    "/wizard/success": 5,
}


def _has_feature(tier: str, feature: str) -> bool:
    """Check if a tier has access to a feature."""
    pro_tiers = {"pro", "team", "enterprise"}
    pro_features = {"trello", "github", "token_budget", "mcp", "timer"}

    if feature in pro_features:
        return tier in pro_tiers
    return True


def get_available_steps(tier: str, track: str) -> list[StepDefinition]:
    """Get steps available for a tier and track.

    Args:
        tier: The user's license tier
        track: The wizard track ("quick" or "guided")

    Returns:
        List of StepDefinition objects available to this tier
    """
    if track not in STEPS:
        track = "quick"

    all_steps = STEPS[track]
    available = []

    for step in all_steps:
        if step.required_feature is None:
            available.append(step)
        elif _has_feature(tier, step.required_feature):
            available.append(step)

    return available
