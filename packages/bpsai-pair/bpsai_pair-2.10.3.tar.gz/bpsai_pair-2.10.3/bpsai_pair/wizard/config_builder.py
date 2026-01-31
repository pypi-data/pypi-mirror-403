"""Config builder for the setup wizard.

Transforms wizard session data into a full config.yaml dictionary
by using core presets as the base and overlaying wizard form data.
"""

from __future__ import annotations

from typing import Any

from bpsai_pair.core.presets import COMMON_EXCLUDES, Preset

# Extended excludes for wizard-generated configs (includes Python-specific patterns)
WIZARD_EXCLUDES = COMMON_EXCLUDES + [
    "*.egg-info",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    ".coverage",
]

# Map wizard preset names to core Preset instances
WIZARD_PRESET_MAP: dict[str, Preset] = {
    "default": Preset(
        name="default",
        description="Balanced defaults",
        project_type="Project",
        coverage_target=80,
        pack_excludes=WIZARD_EXCLUDES,
    ),
    "strict": Preset(
        name="strict",
        description="Strict enforcement with tight limits",
        project_type="Project",
        coverage_target=90,
        pack_excludes=WIZARD_EXCLUDES,
    ),
    "relaxed": Preset(
        name="relaxed",
        description="Permissive settings for rapid prototyping",
        project_type="Project",
        coverage_target=70,
        pack_excludes=WIZARD_EXCLUDES,
        enabled_flows=["tdd-implement", "review"],
    ),
    "pro-workflow": Preset(
        name="pro-workflow",
        description="Full workflow with Trello integration",
        project_type="Project",
        coverage_target=80,
        pack_excludes=WIZARD_EXCLUDES,
    ),
    "enterprise": Preset(
        name="enterprise",
        description="Enterprise with strict containment",
        project_type="Project",
        coverage_target=90,
        pack_excludes=WIZARD_EXCLUDES,
    ),
}

# Default exclude patterns for architecture checks
_DEFAULT_EXCLUDE_PATTERNS: list[str] = [
    "**/migrations/*",
    "**/__init__.py",
    "**/conftest.py",
    "**/test_fixtures.py",
    "**/*_generated.py",
]

# Architecture limits per wizard preset
_ARCHITECTURE_LIMITS: dict[str, dict[str, Any]] = {
    "default": {
        "enabled": True,
        "max_file_lines": 400,
        "warning_file_lines": 200,
        "max_function_lines": 50,
        "max_functions_per_file": 15,
        "max_imports": 20,
        "exclude_patterns": _DEFAULT_EXCLUDE_PATTERNS,
    },
    "strict": {
        "enabled": True,
        "max_file_lines": 300,
        "warning_file_lines": 150,
        "max_function_lines": 40,
        "max_functions_per_file": 12,
        "max_imports": 15,
        "exclude_patterns": _DEFAULT_EXCLUDE_PATTERNS,
    },
    "relaxed": {
        "enabled": True,
        "max_file_lines": 600,
        "warning_file_lines": 400,
        "max_function_lines": 80,
        "max_functions_per_file": 20,
        "max_imports": 30,
        "exclude_patterns": _DEFAULT_EXCLUDE_PATTERNS,
    },
    "pro-workflow": {
        "enabled": True,
        "max_file_lines": 400,
        "warning_file_lines": 200,
        "max_function_lines": 50,
        "max_functions_per_file": 15,
        "max_imports": 20,
        "exclude_patterns": _DEFAULT_EXCLUDE_PATTERNS,
    },
    "enterprise": {
        "enabled": True,
        "max_file_lines": 300,
        "warning_file_lines": 150,
        "max_function_lines": 40,
        "max_functions_per_file": 12,
        "max_imports": 15,
        "exclude_patterns": _DEFAULT_EXCLUDE_PATTERNS,
    },
}

# Containment overrides per wizard preset
_CONTAINMENT_OVERRIDES: dict[str, dict[str, Any]] = {
    "enterprise": {
        "rollback_on_violation": True,
        "blocked_paths": [
            ".env",
            ".env.local",
            ".env.production",
            "credentials.json",
            "secrets.yaml",
        ],
    },
}

# Secrets that must never appear in config.yaml
_SECRET_KEYS = {"api_key", "token", "secret", "password", "api_token"}


class ConfigBuilder:
    """Builds a full config dict from wizard session data."""

    def __init__(self, session_data: dict[str, Any]) -> None:
        self._data = session_data

    def build(self) -> dict[str, Any]:
        """Build the complete config dictionary."""
        project = self._data.get("project", {})
        preset_name = project.get("preset", "default")
        preset = WIZARD_PRESET_MAP.get(preset_name, WIZARD_PRESET_MAP["default"])

        # Base config from preset
        config = preset.to_config_dict(
            project_name=project.get("name", ""),
            primary_goal=project.get("goal", ""),
            description=project.get("description", ""),
        )

        # Override coverage target from wizard
        coverage = project.get("coverage_target")
        if coverage is not None:
            config["project"]["coverage_target"] = coverage

        # Apply overlays
        self._apply_enforcement(config)
        self._apply_architecture(config, preset_name)
        self._apply_containment(config, preset_name)
        self._apply_trello(config)
        self._apply_github(config)
        self._apply_budget(config)
        self._apply_mcp(config)

        return config

    def _apply_enforcement(self, config: dict[str, Any]) -> None:
        """Overlay enforcement settings."""
        enforcement = self._data.get("enforcement")
        if not enforcement:
            return

        config["enforcement"] = {
            "state_machine": enforcement.get("state_machine", True),
            "strict_ac_verification": enforcement.get("ac_verification", True),
            "require_budget_check": True,
        }
        if enforcement.get("bypass_audit") is not None:
            config["enforcement"]["bypass_audit"] = enforcement["bypass_audit"]

    def _apply_architecture(self, config: dict[str, Any], preset_name: str) -> None:
        """Add architecture limits based on preset."""
        limits = _ARCHITECTURE_LIMITS.get(preset_name, _ARCHITECTURE_LIMITS["default"])
        config["architecture"] = dict(limits)

    def _apply_containment(self, config: dict[str, Any], preset_name: str) -> None:
        """Apply containment overrides for the preset."""
        overrides = _CONTAINMENT_OVERRIDES.get(preset_name)
        if not overrides:
            return
        containment = config.get("containment", {})
        containment.update(overrides)
        config["containment"] = containment

    def _apply_trello(self, config: dict[str, Any]) -> None:
        """Overlay Trello integration settings."""
        trello = self._data.get("trello")
        if not trello:
            return

        trello_config = config.get("trello", {})
        trello_config["enabled"] = trello.get("enabled", False)

        if trello.get("board_id"):
            trello_config["board_id"] = trello["board_id"]
        if trello.get("board_name"):
            trello_config["board_name"] = trello["board_name"]

        # Defaults section - merge with existing, fall back to project name
        project_name = self._data.get("project", {}).get("name", "")
        existing_defaults = trello_config.get("defaults", {})
        defaults: dict[str, str] = dict(existing_defaults)

        # Use wizard value if provided, otherwise keep preset default (which uses project_name)
        if trello.get("default_project"):
            defaults["project"] = trello["default_project"]
        elif not defaults.get("project") and project_name:
            defaults["project"] = project_name

        if trello.get("default_stack"):
            defaults["stack"] = trello["default_stack"]
        if trello.get("repo_url"):
            defaults["repo_url"] = trello["repo_url"]

        trello_config["defaults"] = defaults

        # Strip secrets
        for key in list(trello_config.keys()):
            if key in _SECRET_KEYS:
                del trello_config[key]

        config["trello"] = trello_config

    def _apply_github(self, config: dict[str, Any]) -> None:
        """Overlay GitHub settings."""
        github = self._data.get("github")
        if not github:
            return

        repo_url = github.get("repo_url")
        if repo_url:
            config.setdefault("workflow", {})["repo_url"] = repo_url

    def _apply_budget(self, config: dict[str, Any]) -> None:
        """Overlay budget and model settings."""
        budget = self._data.get("budget")
        if not budget:
            return

        # Token budget thresholds
        token_budget: dict[str, Any] = {}
        if budget.get("warning_threshold") is not None:
            token_budget["warning_threshold"] = budget["warning_threshold"]
        if budget.get("critical_threshold") is not None:
            token_budget["critical_threshold"] = budget["critical_threshold"]
        if token_budget:
            config["token_budget"] = token_budget

        # Model assignments - merge with existing models, don't overwrite
        models = config.get("models", {})
        if budget.get("navigator_model"):
            models["navigator"] = budget["navigator_model"]
        if budget.get("driver_model"):
            models["driver"] = budget["driver_model"]
        if budget.get("reviewer_model"):
            models["reviewer"] = budget["reviewer_model"]
        config["models"] = models

    def _apply_mcp(self, config: dict[str, Any]) -> None:
        """Overlay MCP settings."""
        mcp = self._data.get("mcp")
        if not mcp:
            return

        # Session stores as mcp_enabled/mcp_port (from MCP submit handler)
        config["mcp"] = {
            "enabled": mcp.get("mcp_enabled", False),
        }
        if mcp.get("mcp_port") is not None:
            config["mcp"]["port"] = mcp["mcp_port"]
