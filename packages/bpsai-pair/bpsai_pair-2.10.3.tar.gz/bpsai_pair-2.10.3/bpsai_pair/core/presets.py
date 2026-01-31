"""
Configuration presets for PairCoder initialization.

Provides pre-built configurations for different project types,
making it easy to bootstrap new projects with sensible defaults.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import yaml

from .config_defaults import CURRENT_CONFIG_VERSION


@dataclass
class Preset:
    """A configuration preset for a specific project type."""

    name: str
    description: str
    project_type: str

    # Project settings
    coverage_target: int = 80

    # Workflow settings
    default_branch_type: str = "feature"
    main_branch: str = "main"

    # Pack excludes (project-type specific)
    pack_excludes: List[str] = field(default_factory=list)

    # CI settings
    python_formatter: str = "ruff"
    node_formatter: str = "prettier"
    ci_type: str = "fullstack"  # "node", "python", or "fullstack"

    # Flow settings
    enabled_flows: List[str] = field(default_factory=lambda: [
        "design-plan-implement",
        "tdd-implement",
        "review",
        "finish-branch"
    ])

    # Model routing (optional complexity-based routing)
    model_routing: Optional[Dict[str, Any]] = None

    # Trello configuration (optional)
    trello_config: Optional[Dict[str, Any]] = None

    # Hooks configuration (optional)
    hooks_config: Optional[Dict[str, Any]] = None

    # Estimation configuration (optional)
    estimation_config: Optional[Dict[str, Any]] = None

    # Metrics configuration (optional)
    metrics_config: Optional[Dict[str, Any]] = None

    # Security configuration (optional)
    security_config: Optional[Dict[str, Any]] = None

    def to_config_dict(
        self, project_name: str, primary_goal: str, description: str = ""
    ) -> Dict[str, Any]:
        """Convert preset to a config dictionary.

        Args:
            project_name: Name of the project
            primary_goal: Primary goal for the project
            description: Optional project description

        Returns:
            Config dictionary ready for YAML serialization (v2.9.3 format)
        """
        config: Dict[str, Any] = {
            "version": CURRENT_CONFIG_VERSION,
            "project": {
                "name": project_name,
                "description": description or f"{project_name} project",
                "primary_goal": primary_goal,
                "coverage_target": self.coverage_target,
            },
            "workflow": {
                "default_branch_type": self.default_branch_type,
                "main_branch": self.main_branch,
                "context_dir": ".paircoder/context",
                "plans_dir": ".paircoder/plans",
                "tasks_dir": ".paircoder/tasks",
            },
            "pack": {
                "default_name": "agent_pack.tgz",
                "excludes": self.pack_excludes,
            },
        }

        # Add models section (v2.9.3)
        config["models"] = {
            "navigator": "claude-opus-4-5",
            "driver": "claude-sonnet-4-5",
            "reviewer": "claude-sonnet-4-5",
            "providers": {
                "anthropic": {
                    "models": [
                        "claude-opus-4-5",
                        "claude-sonnet-4-5",
                        "claude-haiku-4-5",
                    ],
                    "default_effort": "medium",
                },
            },
        }

        # Add model routing (with defaults if not specified)
        config["routing"] = self.model_routing or {
            "by_complexity": {
                "trivial": {"max_score": 20, "model": "claude-haiku-4-5"},
                "simple": {"max_score": 40, "model": "claude-haiku-4-5"},
                "moderate": {"max_score": 60, "model": "claude-sonnet-4-5"},
                "complex": {"max_score": 80, "model": "claude-opus-4-5"},
                "epic": {"max_score": 100, "model": "claude-opus-4-5"},
            },
            "overrides": {
                "security": "claude-opus-4-5",
                "architecture": "claude-opus-4-5",
            },
        }

        # Add Trello configuration (v2.9.3 format)
        if self.trello_config:
            # Use preset's custom config but ensure v2.9.3 structure
            config["trello"] = self._convert_trello_config(self.trello_config)
        else:
            config["trello"] = {
                "enabled": False,
                "board_id": "",
                "board_name": "",
                "defaults": {
                    "project": project_name,
                    "stack": "Worker/Function",
                    "repo_url": "",
                },
                "board_structure": {
                    "lists": [
                        {"name": "Intake/Backlog", "maps_to_status": ["pending", "backlog"]},
                        {"name": "Planned/Ready", "maps_to_status": ["ready", "planned"]},
                        {"name": "In Progress", "maps_to_status": ["in_progress"]},
                        {"name": "Review/Testing", "maps_to_status": ["review", "testing"]},
                        {"name": "Deployed/Done", "maps_to_status": ["done", "deployed"]},
                        {"name": "Issues/Tech Debt", "maps_to_status": ["blocked", "issue"]},
                    ],
                },
                "custom_fields": {
                    "project": {
                        "type": "dropdown",
                        "options": ["--", project_name],
                        "default": project_name,
                    },
                    "stack": {
                        "type": "dropdown",
                        "options": ["--", "React", "Flask", "Worker/Function", "Infra", "Collection"],
                        "mapping": {
                            "cli": "Worker/Function",
                            "python": "Flask",
                            "backend": "Flask",
                            "frontend": "React",
                            "ui": "React",
                            "worker": "Worker/Function",
                            "function": "Worker/Function",
                            "infra": "Infra",
                            "deploy": "Infra",
                            "ci": "Infra",
                            "docs": "Collection",
                            "documentation": "Collection",
                        },
                        "default": "Worker/Function",
                    },
                    "status": {
                        "type": "dropdown",
                        "options": ["--", "Planning", "In progress", "Testing", "Done", "Enqueued", "Waiting", "Blocked"],
                        "mapping": {
                            "pending": "Planning",
                            "ready": "Enqueued",
                            "in_progress": "In progress",
                            "review": "Testing",
                            "testing": "Testing",
                            "done": "Done",
                            "blocked": "Blocked",
                            "waiting": "Waiting",
                        },
                        "default": "Planning",
                    },
                    "effort": {
                        "type": "dropdown",
                        "options": ["--", "S", "M", "L"],
                        "mapping": {"0-30": "S", "31-60": "M", "61-100": "L"},
                        "default": "M",
                    },
                    "agent_task": {"type": "checkbox", "default": False},
                },
                "labels": [
                    {"name": "Frontend", "color": "green", "matches": ["react", "ui", "frontend", "css"]},
                    {"name": "Backend", "color": "blue", "matches": ["flask", "api", "backend", "python"]},
                    {"name": "Worker / Function", "color": "purple", "matches": ["worker", "function", "background", "async", "cli"]},
                    {"name": "Deployment", "color": "red", "matches": ["deploy", "ci", "cd", "infra", "config"]},
                    {"name": "Bug / Issue", "color": "orange", "matches": ["bug", "fix", "issue", "error"]},
                    {"name": "Documentation", "color": "sky", "matches": ["docs", "documentation", "readme", "guide"]},
                ],
                "automation": {
                    "on_task_ready": {"move_to_list": "Planned/Ready", "set_status": "Enqueued"},
                    "on_task_start": {"move_to_list": "In Progress", "set_status": "In progress"},
                    "on_task_review": {"move_to_list": "Review/Testing", "set_status": "Testing"},
                    "on_task_complete": {"move_to_list": "Deployed/Done", "set_status": "Done"},
                    "on_task_block": {"move_to_list": "Issues/Tech Debt", "set_status": "Blocked"},
                },
            }

        # Add estimation configuration (v2.9.3 format with lowercase keys)
        config["estimation"] = self.estimation_config or {
            "complexity_to_hours": {
                "xs": {"range": [0, 15], "hours": [0.5, 1.0, 2.0]},
                "s": {"range": [16, 30], "hours": [1.0, 2.0, 4.0]},
                "m": {"range": [31, 50], "hours": [2.0, 4.0, 8.0]},
                "l": {"range": [51, 75], "hours": [4.0, 8.0, 16.0]},
                "xl": {"range": [76, 100], "hours": [8.0, 16.0, 32.0]},
            },
        }

        # Add token_estimates as top-level (v2.9.3)
        config["token_estimates"] = {
            "base_context": 15000,
            "per_complexity_point": 500,
            "per_file_touched": 2000,
            "by_task_type": {
                "feature": 1.2,
                "bugfix": 0.8,
                "docs": 0.6,
                "refactor": 1.5,
                "chore": 0.9,
            },
        }

        # Add token_budget section (v2.9.3)
        config["token_budget"] = {
            "warning_threshold": 75,
            "critical_threshold": 90,
        }

        # Add metrics configuration (with defaults if not specified)
        config["metrics"] = self.metrics_config or {
            "enabled": True,
            "store_path": ".paircoder/history/metrics.jsonl",
        }

        # Add hooks configuration (v2.9.3 with new events)
        config["hooks"] = self.hooks_config or {
            "enabled": True,
            "on_task_ready": [
                "sync_trello",
                "update_state",
            ],
            "on_task_start": [
                "check_token_budget",
                "start_timer",
                "sync_trello",
                "update_state",
            ],
            "on_task_review": [
                "sync_trello",
                "update_state",
            ],
            "on_task_complete": [
                "stop_timer",
                "record_task_completion",
                "record_metrics",
                "record_velocity",
                "sync_trello",
                "update_state",
                "check_unblocked",
            ],
            "on_task_block": [
                "sync_trello",
                "update_state",
            ],
        }

        # Add containment configuration (v2.9.3 format)
        config["containment"] = {
            "enabled": False,
            "mode": "strict",
            "auto_checkpoint": True,
            "rollback_on_violation": False,
            "blocked_directories": [],
            "blocked_files": [
                ".env",
                ".env.local",
                ".env.production",
                "credentials.json",
                "secrets.yaml",
            ],
            "readonly_directories": [
                ".claude/agents",
                ".claude/commands",
                ".claude/skills",
            ],
            "readonly_files": [
                "CLAUDE.md",
                "AGENTS.md",
            ],
            "allow_network": [
                "api.anthropic.com",
                "api.trello.com",
                "github.com",
                "pypi.org",
            ],
        }

        return config

    def _convert_trello_config(self, trello_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Trello config to v2.9.3 format if needed."""
        result: Dict[str, Any] = {
            "enabled": trello_config.get("enabled", True),
            "board_id": trello_config.get("board_id", ""),
            "board_name": trello_config.get("board_name", ""),
        }

        # Add defaults
        result["defaults"] = trello_config.get("defaults", {
            "project": "",
            "stack": "Worker/Function",
            "repo_url": "",
        })

        # Convert lists to board_structure format
        if "lists" in trello_config:
            old_lists = trello_config["lists"]
            result["board_structure"] = {
                "lists": [
                    {"name": old_lists.get("backlog", "Intake/Backlog"), "maps_to_status": ["pending", "backlog"]},
                    {"name": old_lists.get("ready", "Planned/Ready"), "maps_to_status": ["ready", "planned"]},
                    {"name": old_lists.get("in_progress", "In Progress"), "maps_to_status": ["in_progress"]},
                    {"name": old_lists.get("review", "Review/Testing"), "maps_to_status": ["review", "testing"]},
                    {"name": old_lists.get("done", "Deployed/Done"), "maps_to_status": ["done", "deployed"]},
                    {"name": old_lists.get("blocked", "Issues/Tech Debt"), "maps_to_status": ["blocked", "issue"]},
                ],
            }
        elif "board_structure" in trello_config:
            result["board_structure"] = trello_config["board_structure"]
        else:
            result["board_structure"] = {
                "lists": [
                    {"name": "Intake/Backlog", "maps_to_status": ["pending", "backlog"]},
                    {"name": "Planned/Ready", "maps_to_status": ["ready", "planned"]},
                    {"name": "In Progress", "maps_to_status": ["in_progress"]},
                    {"name": "Review/Testing", "maps_to_status": ["review", "testing"]},
                    {"name": "Deployed/Done", "maps_to_status": ["done", "deployed"]},
                    {"name": "Issues/Tech Debt", "maps_to_status": ["blocked", "issue"]},
                ],
            }

        # Copy over other fields if present
        for key in ["custom_fields", "labels", "automation"]:
            if key in trello_config:
                result[key] = trello_config[key]

        return result

    def to_yaml(
        self, project_name: str, primary_goal: str, description: str = ""
    ) -> str:
        """Convert preset to YAML string.

        Args:
            project_name: Name of the project
            primary_goal: Primary goal for the project
            description: Optional project description

        Returns:
            YAML string
        """
        config = self.to_config_dict(project_name, primary_goal, description)
        return yaml.dump(config, default_flow_style=False, sort_keys=False)


# Common pack excludes shared across presets
COMMON_EXCLUDES = [
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "*.log",
    "*.bak",
]


# Pre-defined presets
PRESETS: Dict[str, Preset] = {
    "python-cli": Preset(
        name="python-cli",
        description="Python CLI application with Click/Typer",
        project_type="Python CLI",
        coverage_target=80,
        python_formatter="ruff",
        ci_type="python",
        pack_excludes=COMMON_EXCLUDES + [
            "*.egg-info",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
            ".coverage",
        ],
    ),

    "python-api": Preset(
        name="python-api",
        description="Python REST API with Flask/FastAPI",
        project_type="Python API",
        coverage_target=85,
        python_formatter="ruff",
        ci_type="python",
        pack_excludes=COMMON_EXCLUDES + [
            "*.egg-info",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
            ".coverage",
            "instance/",
            "*.db",
            "*.sqlite",
        ],
    ),

    "react": Preset(
        name="react",
        description="React/Next.js frontend application",
        project_type="React App",
        coverage_target=75,
        node_formatter="prettier",
        ci_type="node",
        pack_excludes=COMMON_EXCLUDES + [
            ".next",
            ".cache",
            "coverage",
            "*.tsbuildinfo",
            ".turbo",
        ],
    ),

    "fullstack": Preset(
        name="fullstack",
        description="Full-stack application (Python backend + React frontend)",
        project_type="Full-Stack App",
        coverage_target=80,
        python_formatter="ruff",
        node_formatter="prettier",
        ci_type="fullstack",
        pack_excludes=COMMON_EXCLUDES + [
            "*.egg-info",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
            ".coverage",
            ".next",
            ".cache",
            "coverage",
            "*.tsbuildinfo",
        ],
    ),

    "library": Preset(
        name="library",
        description="Python library/package for distribution",
        project_type="Python Library",
        coverage_target=90,
        python_formatter="ruff",
        ci_type="python",
        pack_excludes=COMMON_EXCLUDES + [
            "*.egg-info",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
            ".coverage",
            "dist/",
            "build/",
            "*.whl",
            "*.tar.gz",
        ],
    ),

    "minimal": Preset(
        name="minimal",
        description="Minimal configuration with essential defaults only",
        project_type="Project",
        coverage_target=70,
        ci_type="fullstack",  # Keep both for flexibility
        pack_excludes=COMMON_EXCLUDES,
        enabled_flows=["tdd-implement", "review"],
    ),

    "autonomous": Preset(
        name="autonomous",
        description="Full autonomy configuration with Trello integration",
        project_type="Autonomous Project",
        coverage_target=80,
        ci_type="python",
        pack_excludes=COMMON_EXCLUDES + [
            "*.egg-info",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
            ".coverage",
        ],
        enabled_flows=[
            "design-plan-implement",
            "tdd-implement",
            "review",
            "finish-branch",
        ],
        model_routing={
            "by_complexity": {
                "trivial": {"max_score": 20, "model": "claude-haiku-4-5"},
                "simple": {"max_score": 40, "model": "claude-haiku-4-5"},
                "moderate": {"max_score": 60, "model": "claude-sonnet-4-5"},
                "complex": {"max_score": 80, "model": "claude-opus-4-5"},
                "epic": {"max_score": 100, "model": "claude-opus-4-5"},
            }
        },
    ),

    "bps": Preset(
        name="bps",
        description="BPS AI Software preset with 7-list Trello workflow",
        project_type="BPS Project",
        coverage_target=80,
        ci_type="python",
        pack_excludes=COMMON_EXCLUDES + [
            "*.egg-info",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "htmlcov",
            ".coverage",
        ],
        enabled_flows=[
            "design-plan-implement",
            "tdd-implement",
            "review",
            "finish-branch",
        ],
        model_routing={
            "by_complexity": {
                "trivial": {"max_score": 20, "model": "claude-haiku-4-5"},
                "simple": {"max_score": 40, "model": "claude-haiku-4-5"},
                "moderate": {"max_score": 60, "model": "claude-sonnet-4-5"},
                "complex": {"max_score": 80, "model": "claude-opus-4-5"},
                "epic": {"max_score": 100, "model": "claude-opus-4-5"},
            }
        },
        trello_config={
            # BPS 7-list structure per TRELLO_GUIDELINES.md
            "lists": {
                "backlog": "Intake / Backlog",
                "ready": "Planned / Ready",
                "in_progress": "In Progress",
                "review": "Review / Testing",
                "done": "Deployed / Done",
                "blocked": "Issues / Tech Debt",
                "notes": "Notes / Ops Log",
            },
            # Card title format: [Stack] Title
            "card_format": "[{stack}] {title}",
            # Label colors per BPS guidelines
            "labels": {
                "frontend": {"name": "Frontend", "color": "green"},
                "backend": {"name": "Backend", "color": "blue"},
                "worker": {"name": "Worker / Function", "color": "purple"},
                "deployment": {"name": "Deployment", "color": "red"},
                "bug": {"name": "Bug / Issue", "color": "orange"},
                "security": {"name": "Security / Admin", "color": "yellow"},
                "docs": {"name": "Documentation", "color": "sky"},
                "ai": {"name": "AI / ML Integration", "color": "black"},
            },
            # Custom fields
            "custom_fields": {
                "project": "Project",
                "stack": "Stack",
                "status": "Status",
                "effort": "Effort",
                "deployment_tag": "Deployment Tag",
            },
            # Automation mappings
            "automation": {
                "on_task_start": {
                    "move_to_list": "In Progress",
                    "add_comment": "🤖 {agent} started working on this task",
                },
                "on_task_complete": {
                    "move_to_list": "Deployed / Done",
                    "add_comment": "✅ Task completed by {agent}\n\n{summary}",
                },
                "on_task_block": {
                    "move_to_list": "Issues / Tech Debt",
                    "add_comment": "⚠️ Task blocked: {reason}",
                },
                "on_task_review": {
                    "move_to_list": "Review / Testing",
                    "add_comment": "🔍 {agent} submitted for review",
                },
            },
            # Status mapping for webhook sync
            "status_mapping": {
                "Intake / Backlog": "pending",
                "Planned / Ready": "pending",
                "In Progress": "in_progress",
                "Review / Testing": "in_progress",
                "Deployed / Done": "done",
                "Issues / Tech Debt": "blocked",
            },
        },
        hooks_config={
            "enabled": True,
            "on_task_start": ["start_timer", "sync_trello", "update_state"],
            "on_task_complete": [
                "stop_timer",
                "record_metrics",
                "record_velocity",
                "record_token_usage",
                "sync_trello",
                "update_state",
                "check_unblocked",
            ],
            "on_task_block": ["sync_trello", "update_state"],
        },
    ),
}


def get_preset(name: str) -> Optional[Preset]:
    """Get a preset by name.

    Args:
        name: Preset name

    Returns:
        Preset if found, None otherwise
    """
    return PRESETS.get(name)


def list_presets() -> List[Preset]:
    """List all available presets.

    Returns:
        List of all presets
    """
    return list(PRESETS.values())


def get_preset_names() -> List[str]:
    """Get names of all available presets.

    Returns:
        List of preset names
    """
    return list(PRESETS.keys())


class PresetManager:
    """Manager for configuration presets."""

    def __init__(self, custom_presets: Optional[Dict[str, Preset]] = None):
        """Initialize preset manager.

        Args:
            custom_presets: Additional custom presets to include
        """
        self.presets = dict(PRESETS)
        if custom_presets:
            self.presets.update(custom_presets)

    def get(self, name: str) -> Optional[Preset]:
        """Get preset by name."""
        return self.presets.get(name)

    def list(self) -> List[Preset]:
        """List all presets."""
        return list(self.presets.values())

    def names(self) -> List[str]:
        """Get all preset names."""
        return list(self.presets.keys())

    def add(self, preset: Preset) -> None:
        """Add a custom preset.

        Args:
            preset: Preset to add
        """
        self.presets[preset.name] = preset

    def remove(self, name: str) -> bool:
        """Remove a preset.

        Args:
            name: Preset name to remove

        Returns:
            True if removed, False if not found
        """
        if name in self.presets:
            del self.presets[name]
            return True
        return False

    def describe(self, name: str) -> Optional[str]:
        """Get a formatted description of a preset.

        Args:
            name: Preset name

        Returns:
            Formatted description or None
        """
        preset = self.get(name)
        if not preset:
            return None

        return f"""Preset: {preset.name}
Description: {preset.description}
Project Type: {preset.project_type}
Coverage Target: {preset.coverage_target}%
Branch Type: {preset.default_branch_type}
Flows: {', '.join(preset.enabled_flows)}
Pack Excludes: {len(preset.pack_excludes)} patterns"""
