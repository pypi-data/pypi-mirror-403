"""Project creator for the setup wizard.

This module generates file previews, config previews, and creates
project files based on wizard session data.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from bpsai_pair.init_bundled_cli import (
    _find_template_traversable,
    copytree_non_destructive,
)

try:
    from importlib.resources import as_file
except ImportError:
    from importlib_resources import as_file  # py<=3.8 fallback


# Files that will be created in .paircoder/
PREVIEW_FILES = [
    ".paircoder/",
    ".paircoder/config.yaml",
    ".paircoder/capabilities.yaml",
    ".paircoder/context/",
    ".paircoder/context/project.md",
    ".paircoder/context/state.md",
    ".paircoder/context/workflow.md",
    ".paircoder/security/",
    ".paircoder/security/sandbox.yaml",
    ".paircoder/security/allowlist.yaml",
    ".paircoder/plans/",
    ".paircoder/tasks/",
    ".claude/",
    ".claude/settings.json",
    ".claude/skills/",
    ".claude/commands/",
    ".claude/agents/",
    "CLAUDE.md",
]


class ProjectCreator:
    """Creates project files from wizard session data."""

    def __init__(
        self,
        project_data: dict[str, Any] | None = None,
        enforcement_data: dict[str, Any] | None = None,
        session_data: dict[str, Any] | None = None,
    ) -> None:
        if session_data is not None:
            self._session_data = session_data
            self.project = session_data.get("project", {})
            self.enforcement = session_data.get("enforcement", {})
        else:
            self._session_data = {
                "project": project_data or {},
                "enforcement": enforcement_data or {},
            }
            self.project = project_data or {}
            self.enforcement = enforcement_data or {}

    def preview_files(self) -> list[str]:
        """Return list of files that will be created."""
        return list(PREVIEW_FILES)

    def preview_config(self) -> str:
        """Return config.yaml content as a YAML string."""
        config = self._build_config()
        return yaml.dump(config, default_flow_style=False, sort_keys=False)

    def backup_existing(self, target_dir: Path) -> Path | None:
        """Backup existing config files if present."""
        config_file = target_dir / "config.yaml"
        if not config_file.exists():
            return None

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_dir = target_dir.parent / f".paircoder-backup-{timestamp}"
        shutil.copytree(target_dir, backup_dir)
        return backup_dir

    def create(self, target_dir: Path) -> bool:
        """Create all project files in the target directory."""
        target_dir.mkdir(parents=True, exist_ok=True)

        # Write config.yaml
        config_yaml = self.preview_config()
        (target_dir / "config.yaml").write_text(config_yaml)

        # Write capabilities.yaml
        capabilities = self._build_capabilities()
        cap_yaml = yaml.dump(capabilities, default_flow_style=False, sort_keys=False)
        (target_dir / "capabilities.yaml").write_text(cap_yaml)

        # Write context files
        context_dir = target_dir / "context"
        context_dir.mkdir(exist_ok=True)
        self._write_context_files(context_dir)

        # Write .env.example if integrations are enabled
        self._write_env_example(target_dir.parent)

        # Scaffold additional files from bundled template
        self._scaffold_from_template(target_dir.parent)

        return True

    def _build_config(self) -> dict[str, Any]:
        """Build the config.yaml dictionary using ConfigBuilder."""
        from bpsai_pair.wizard.config_builder import ConfigBuilder

        builder = ConfigBuilder(self._session_data)
        return builder.build()

    def _build_capabilities(self) -> dict[str, Any]:
        """Build the capabilities.yaml dictionary."""
        return {
            "version": 1,
            "roles": ["navigator", "driver", "reviewer"],
            "can_read": [".paircoder/", "src/", "tests/", "docs/"],
            "can_write": [".paircoder/context/state.md", ".paircoder/tasks/"],
        }

    def _write_context_files(self, context_dir: Path) -> None:
        """Write context directory files."""
        name = self.project.get("name", "Project")
        goal = self.project.get("goal", "")

        project_md = f"# {name}\n\n{goal}\n"
        (context_dir / "project.md").write_text(project_md)

        state_md = f"# Current State\n\nProject: {name}\nStatus: initialized\n"
        (context_dir / "state.md").write_text(state_md)

        workflow_md = "# Workflow\n\nSee CLAUDE.md for workflow instructions.\n"
        (context_dir / "workflow.md").write_text(workflow_md)

    def _scaffold_from_template(self, project_root: Path) -> int:
        """Copy bundled scaffold files (skills, agents, commands, etc.).

        Uses copytree_non_destructive so wizard-written files are preserved.
        Returns number of files copied, or 0 if template not found.
        """
        template_traversable = _find_template_traversable()
        if template_traversable is None:
            return 0

        try:
            with as_file(template_traversable) as template_root:
                return copytree_non_destructive(template_root, project_root)
        except Exception:
            return 0

    def _write_env_example(self, project_root: Path) -> None:
        """Write .env.example with secret placeholders."""
        lines: list[str] = []

        trello = self._session_data.get("trello", {})
        if trello.get("enabled") or trello.get("board_id"):
            lines.append("# Trello (required for trello sync)")
            lines.append("TRELLO_API_KEY=")
            lines.append("TRELLO_TOKEN=")
            lines.append("")

        github = self._session_data.get("github", {})
        if github.get("repo_url"):
            lines.append("# GitHub (required for auto-PR)")
            lines.append("GITHUB_TOKEN=")
            lines.append("")

        mcp = self._session_data.get("mcp", {})
        if mcp.get("enabled"):
            lines.append("# MCP Server")
            lines.append("MCP_SECRET=")
            lines.append("")

        if not lines:
            return

        env_path = project_root / ".env.example"
        env_path.write_text("\n".join(lines) + "\n")
