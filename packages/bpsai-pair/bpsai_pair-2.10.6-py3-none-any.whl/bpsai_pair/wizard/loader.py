"""Load existing PairCoder config into wizard-compatible session data.

Reads ``.paircoder/config.yaml`` and converts it into the ``project``
and ``enforcement`` dictionaries that the wizard forms expect.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_existing_config(config_dir: Path) -> dict[str, Any] | None:
    """Load an existing config.yaml and return wizard-compatible data.

    Args:
        config_dir: Path to the ``.paircoder/`` directory.

    Returns:
        Dictionary with ``project``, ``enforcement``, and
        ``original_yaml`` keys, or ``None`` if the config file
        doesn't exist or can't be parsed.
    """
    config_file = config_dir / "config.yaml"
    if not config_file.exists():
        return None

    raw_yaml = config_file.read_text(encoding="utf-8")

    try:
        data = yaml.safe_load(raw_yaml)
    except yaml.YAMLError:
        return None

    if not isinstance(data, dict):
        return None

    project_data = _extract_project(data)
    enforcement_data = _extract_enforcement(data)

    result: dict[str, Any] = {
        "project": project_data,
        "enforcement": enforcement_data,
        "original_yaml": raw_yaml,
    }

    trello_data = _extract_trello(data)
    if trello_data:
        result["trello"] = trello_data

    budget_data = _extract_budget(data)
    if budget_data:
        result["budget"] = budget_data

    mcp_data = _extract_mcp(data)
    if mcp_data:
        result["mcp"] = mcp_data

    return result


def _extract_project(data: dict[str, Any]) -> dict[str, Any]:
    """Extract project fields into wizard-compatible format."""
    project_section = data.get("project", {})
    if not isinstance(project_section, dict):
        project_section = {}

    result: dict[str, Any] = {
        "name": project_section.get("name", ""),
        "slug": project_section.get("slug", ""),
        "goal": project_section.get("primary_goal", ""),
        "preset": project_section.get("preset", "default"),
        "coverage_target": project_section.get("coverage_target", 80),
    }

    description = project_section.get("description")
    if description:
        result["description"] = description

    return result


def _extract_enforcement(data: dict[str, Any]) -> dict[str, Any]:
    """Extract enforcement fields into wizard-compatible format."""
    enforcement_section = data.get("enforcement", {})
    if not isinstance(enforcement_section, dict):
        enforcement_section = {}

    result: dict[str, Any] = {
        "preset": enforcement_section.get("preset", "balanced"),
        "ac_verification": enforcement_section.get("ac_verification", True),
        "state_machine": enforcement_section.get("state_machine", True),
        "bypass_audit": enforcement_section.get("bypass_audit", True),
    }

    # Merge protected paths from containment section
    containment = data.get("containment", {})
    if isinstance(containment, dict):
        paths = containment.get("protected_paths")
        if paths:
            result["protected_paths"] = paths

    return result


def _extract_trello(data: dict[str, Any]) -> dict[str, Any]:
    """Extract Trello settings into wizard-compatible format."""
    trello_section = data.get("trello", {})
    if not isinstance(trello_section, dict):
        return {}

    result: dict[str, Any] = {}
    for key in ("board_id", "board_name", "enabled"):
        val = trello_section.get(key)
        if val is not None:
            result[key] = val

    # Flatten defaults sub-section into wizard field names
    defaults = trello_section.get("defaults", {})
    if isinstance(defaults, dict):
        if defaults.get("project"):
            result["default_project"] = defaults["project"]
        if defaults.get("stack"):
            result["default_stack"] = defaults["stack"]
        if defaults.get("repo_url"):
            result["repo_url"] = defaults["repo_url"]

    return result


def _extract_budget(data: dict[str, Any]) -> dict[str, Any]:
    """Extract budget/model settings into wizard-compatible format."""
    result: dict[str, Any] = {}

    token_budget = data.get("token_budget", {})
    if isinstance(token_budget, dict):
        for key in ("warning_threshold", "critical_threshold"):
            val = token_budget.get(key)
            if val is not None:
                result[key] = val

    models = data.get("models", {})
    if isinstance(models, dict):
        if models.get("navigator"):
            result["navigator_model"] = models["navigator"]
        if models.get("driver"):
            result["driver_model"] = models["driver"]
        if models.get("reviewer"):
            result["reviewer_model"] = models["reviewer"]

    return result


def _extract_mcp(data: dict[str, Any]) -> dict[str, Any]:
    """Extract MCP settings into wizard-compatible format."""
    mcp_section = data.get("mcp", {})
    if not isinstance(mcp_section, dict):
        return {}

    result: dict[str, Any] = {}
    for key in ("enabled", "port"):
        val = mcp_section.get(key)
        if val is not None:
            result[key] = val

    return result
