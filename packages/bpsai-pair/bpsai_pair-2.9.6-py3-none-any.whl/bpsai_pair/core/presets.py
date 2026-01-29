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

    def to_config_dict(self, project_name: str, primary_goal: str) -> Dict[str, Any]:
        """Convert preset to a config dictionary.

        Args:
            project_name: Name of the project
            primary_goal: Primary goal for the project

        Returns:
            Config dictionary ready for YAML serialization
        """
        config = {
            "version": CURRENT_CONFIG_VERSION,
            "project": {
                "name": project_name,
                "primary_goal": primary_goal,
                "coverage_target": self.coverage_target,
            },
            "workflow": {
                "default_branch_type": self.default_branch_type,
                "main_branch": self.main_branch,
                "context_dir": ".paircoder/context",
                "flows_dir": ".paircoder/flows",
            },
            "pack": {
                "default_name": "agent_pack.tgz",
                "excludes": self.pack_excludes,
            },
            "flows": {
                "enabled": self.enabled_flows,
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
            }
        }

        # Add Trello configuration (with placeholder if not specified)
        config["trello"] = self.trello_config or {
            "board_id": "",  # Set via: bpsai-pair trello use-board <id>
            "board_name": "",
            "sync": {
                "default_list": "Planned/Ready",
                "use_butler_workflow": True,
                "preserve_manual_edits": True,
            },
            "list_mappings": {
                "pending": "Planned/Ready",
                "in_progress": "In Progress",
                "blocked": "Blocked",
                "review": "In Review",
                "done": "Deployed/Done",
            },
        }

        # Add estimation configuration (with defaults if not specified)
        config["estimation"] = self.estimation_config or {
            "complexity_to_hours": {
                "XS": [0.5, 1, 2],    # [min, expected, max] hours
                "S": [1, 2, 4],
                "M": [2, 4, 8],
                "L": [4, 8, 16],
                "XL": [8, 16, 32],
            },
            "token_estimates": {
                "base_context": 15000,
                "per_complexity_point": 500,
                "per_file_touched": 2000,
                "by_task_type": {
                    "feature": 1.2,
                    "bugfix": 0.8,
                    "docs": 0.6,
                    "refactor": 1.5,
                },
            },
        }

        # Add metrics configuration (with defaults if not specified)
        config["metrics"] = self.metrics_config or {
            "enabled": True,
            "store_path": ".paircoder/history/metrics.jsonl",
        }

        # Add hooks configuration (with Sprint 17 defaults if not specified)
        config["hooks"] = self.hooks_config or {
            "enabled": True,
            "on_task_start": [
                "start_timer",
                "sync_trello",
                "update_state",
            ],
            "on_task_complete": [
                "stop_timer",
                "record_metrics",
                "record_velocity",
                "record_token_usage",
                "sync_trello",
                "update_state",
                "check_unblocked",
            ],
            "on_task_block": [
                "sync_trello",
                "update_state",
            ],
        }

        # Add security configuration (with defaults if not specified)
        config["security"] = self.security_config or {
            "allowlist_path": ".paircoder/security/allowlist.yaml",
            "secrets_allowlist_path": ".paircoder/security/secret-allowlist.yaml",
            "sandbox": {
                "enabled": False,
                "config_path": ".paircoder/security/sandbox.yaml",
            },
        }

        # Add containment configuration (contained autonomy mode)
        config["containment"] = {
            "enabled": False,
            "locked_directories": [
                ".claude/agents/",
                ".claude/commands/",
                ".claude/skills/",
            ],
            "locked_files": [
                "CLAUDE.md",
                "AGENTS.md",
            ],
            "allow_network": [
                "api.anthropic.com",
                "api.trello.com",
                "github.com",
                "pypi.org",
            ],
            "auto_checkpoint": True,
            "rollback_on_violation": False,
        }

        return config

    def to_yaml(self, project_name: str, primary_goal: str) -> str:
        """Convert preset to YAML string.

        Args:
            project_name: Name of the project
            primary_goal: Primary goal for the project

        Returns:
            YAML string
        """
        config = self.to_config_dict(project_name, primary_goal)
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
