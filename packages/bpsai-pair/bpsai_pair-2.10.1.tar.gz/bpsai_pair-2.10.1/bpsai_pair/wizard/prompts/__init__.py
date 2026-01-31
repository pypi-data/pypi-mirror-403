"""Wizard prompt loading utilities.

Loads the guided-setup system prompt from the Markdown file and
applies tier-aware customisation before handing it to Claude.
"""

from __future__ import annotations

from pathlib import Path

_PROMPT_DIR = Path(__file__).parent
_PROMPT_FILE = _PROMPT_DIR / "guided_setup.md"

# Tier-specific sections injected into the prompt template.
_TIER_CONTEXTS: dict[str, str] = {
    "solo": (
        "The user is on the **Solo** tier. "
        "Do NOT suggest Pro features such as Trello sync, GitHub integration, "
        "MCP servers, token budgets, or model routing. "
        "Keep suggestions to local-first features that are available on Solo."
    ),
    "pro": (
        "The user is on the **Pro** tier. "
        "They have access to Trello sync, GitHub integration, MCP servers, "
        "token budgets, and model routing. You may suggest these features "
        "when they are relevant to the project."
    ),
    "team": (
        "The user is on the **Team** tier. "
        "They have access to all Pro features plus team collaboration tools. "
        "You may suggest integrations and team workflows as appropriate."
    ),
    "enterprise": (
        "The user is on the **Enterprise** tier. "
        "They have access to all features including remote access, "
        "multi-workspace, and SSO. Suggest advanced workflows as appropriate."
    ),
}


def load_system_prompt(*, tier: str) -> str:
    """Load the guided-setup system prompt, customised for *tier*.

    Args:
        tier: The user's license tier (``"solo"``, ``"pro"``,
              ``"team"``, or ``"enterprise"``).

    Returns:
        The rendered system prompt string ready for Claude's ``system``
        parameter.
    """
    template = _PROMPT_FILE.read_text(encoding="utf-8")
    tier_context = _TIER_CONTEXTS.get(tier, _TIER_CONTEXTS["solo"])
    return template.replace("{{TIER_CONTEXT}}", tier_context)
