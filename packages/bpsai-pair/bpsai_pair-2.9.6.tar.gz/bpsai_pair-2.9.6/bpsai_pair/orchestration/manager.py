"""
Handoff manager for creating and extracting handoff packages.

This module provides the HandoffManager class that orchestrates the
creation and extraction of handoff tarballs for agent context transfer.

Classes:
    HandoffManager: Main orchestrator for pack/unpack operations

Extracted from handoff.py as part of EPIC-005 module decomposition.
"""

from __future__ import annotations

import json
import logging
import tarfile
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

from .package_builder import AgentType, HandoffPackage

logger = logging.getLogger(__name__)


class HandoffManager:
    """
    Manages creation and extraction of handoff packages.

    Handles context packaging for agent transfers, including
    agent-specific formatting and token estimation.

    Attributes:
        project_root: Root directory of the project
        CHARS_PER_TOKEN: Approximate characters per token for estimation
    """

    # Token estimates per character (rough approximation)
    CHARS_PER_TOKEN = 4

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the handoff manager.

        Args:
            project_root: Root directory of the project. Defaults to cwd.
        """
        self.project_root = project_root or Path.cwd()

    def pack(
        self,
        task_id: str,
        target_agent: AgentType = "generic",
        source_agent: AgentType = "claude",
        include_files: Optional[list[Path]] = None,
        exclude_patterns: Optional[list[str]] = None,
        conversation_summary: str = "",
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Create a handoff package for the specified task.

        Args:
            task_id: ID of the task being handed off
            target_agent: Target agent type
            source_agent: Source agent type
            include_files: Specific files to include
            exclude_patterns: Patterns to exclude (default excludes common dirs)
            conversation_summary: Summary of work done
            output_path: Path for output file

        Returns:
            Path to the created handoff package
        """
        exclude_patterns = exclude_patterns or [
            "__pycache__",
            ".git",
            "node_modules",
            ".venv",
            "*.pyc",
        ]

        # Load task details
        task_info = self._load_task(task_id)

        # Determine files to include
        files_to_include = include_files or self._detect_relevant_files(task_id)

        # Calculate token estimate
        token_estimate = self._estimate_tokens(files_to_include)

        # Create package
        package = HandoffPackage(
            task_id=task_id,
            source_agent=source_agent,
            target_agent=target_agent,
            token_estimate=token_estimate,
            files_included=[str(f) for f in files_to_include],
            conversation_summary=conversation_summary,
            task_description=task_info.get("description", ""),
            current_state=task_info.get("state", ""),
            instructions=self._generate_instructions(target_agent, task_info),
        )

        # Determine output path
        if output_path is None:
            output_path = self.project_root / f"handoff-{task_id}-{target_agent}.tgz"

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create the tarball
        self._create_tarball(package, files_to_include, output_path)

        logger.info(
            f"Created handoff package: {output_path} "
            f"({token_estimate} tokens, {len(files_to_include)} files)"
        )

        return output_path

    def unpack(
        self,
        package_path: Path,
        target_dir: Optional[Path] = None,
    ) -> HandoffPackage:
        """
        Extract and validate a handoff package.

        Args:
            package_path: Path to the handoff package
            target_dir: Directory to extract into

        Returns:
            HandoffPackage with metadata
        """
        if target_dir is None:
            target_dir = self.project_root / ".paircoder" / "incoming"

        target_dir.mkdir(parents=True, exist_ok=True)

        with tarfile.open(package_path, "r:gz") as tar:
            tar.extractall(target_dir, filter="data")

        # Load metadata
        metadata_path = target_dir / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {}

        package = HandoffPackage(
            task_id=metadata.get("task_id", "unknown"),
            source_agent=metadata.get("source_agent", "unknown"),
            target_agent=metadata.get("target_agent", "generic"),
            token_estimate=metadata.get("token_estimate", 0),
            files_included=metadata.get("files_included", []),
            conversation_summary=metadata.get("conversation_summary", ""),
        )

        logger.info(f"Unpacked handoff: {package.task_id} from {package.source_agent}")

        return package

    def _load_task(self, task_id: str) -> dict[str, Any]:
        """Load task details from task file.

        Args:
            task_id: The task identifier

        Returns:
            Dictionary with task description, state, and acceptance_criteria
        """
        # Search for task file
        task_dirs = [
            self.project_root / ".paircoder" / "tasks",
        ]

        for task_dir in task_dirs:
            if not task_dir.exists():
                continue

            # Search recursively for task file
            for task_file in task_dir.rglob(f"{task_id}*.md"):
                content = task_file.read_text(encoding="utf-8")
                return {
                    "description": self._extract_section(content, "Description", "Objective"),
                    "state": self._extract_section(content, "Current State", "Status"),
                    "acceptance_criteria": self._extract_section(content, "Acceptance Criteria"),
                }

        return {"description": f"Task {task_id}", "state": "In progress"}

    def _extract_section(self, content: str, *section_names: str) -> str:
        """Extract a section from markdown content.

        Args:
            content: The markdown content
            *section_names: Section names to try (in order)

        Returns:
            The section content, or empty string if not found
        """
        for name in section_names:
            marker = f"## {name}"
            if marker in content:
                start = content.find(marker) + len(marker)
                # Find next section or end
                next_section = content.find("\n## ", start)
                if next_section == -1:
                    return content[start:].strip()
                return content[start:next_section].strip()
        return ""

    def _detect_relevant_files(self, task_id: str) -> list[Path]:
        """Auto-detect files relevant to the task.

        Args:
            task_id: The task identifier

        Returns:
            List of relevant file paths (limited to 20)
        """
        relevant = []

        # Include task file itself
        task_dirs = self.project_root / ".paircoder" / "tasks"
        if task_dirs.exists():
            for task_file in task_dirs.rglob(f"{task_id}*.md"):
                relevant.append(task_file)

        # Include state file
        state_file = self.project_root / ".paircoder" / "context" / "state.md"
        if state_file.exists():
            relevant.append(state_file)

        # Include recently modified files from git
        try:
            import subprocess

            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~5"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        file_path = self.project_root / line
                        if file_path.exists() and file_path not in relevant:
                            relevant.append(file_path)
        except Exception:
            pass

        return relevant[:20]  # Limit to 20 files

    def _estimate_tokens(self, files: list[Path]) -> int:
        """Estimate token count for files.

        Args:
            files: List of file paths

        Returns:
            Estimated token count
        """
        total_chars = 0
        for file_path in files:
            try:
                if file_path.exists() and file_path.is_file():
                    total_chars += len(file_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        return total_chars // self.CHARS_PER_TOKEN

    def _generate_instructions(self, target_agent: AgentType, task_info: dict) -> str:
        """Generate agent-specific instructions.

        Args:
            target_agent: The target agent type
            task_info: Dictionary with task information

        Returns:
            Instructions string for the agent
        """
        base_instructions = task_info.get("acceptance_criteria", "Complete the task as described.")

        agent_specifics = {
            "claude": "Use your skills in `.claude/skills/` if applicable. Update task status when done.",
            "codex": "Follow AGENTS.md conventions. Use full-auto mode for implementation.",
            "cursor": "Work interactively in the IDE. Reference .cursorrules if present.",
            "generic": "Follow project conventions. Update state when done.",
        }

        return f"{base_instructions}\n\n**Agent-specific:** {agent_specifics.get(target_agent, '')}"

    def _create_tarball(
        self,
        package: HandoffPackage,
        files: list[Path],
        output_path: Path,
    ) -> None:
        """Create the handoff tarball.

        Args:
            package: The handoff package with metadata
            files: List of files to include
            output_path: Where to write the tarball
        """
        with tarfile.open(output_path, "w:gz") as tar:
            # Add HANDOFF.md
            handoff_content = package.generate_handoff_md().encode("utf-8")
            handoff_info = tarfile.TarInfo(name="HANDOFF.md")
            handoff_info.size = len(handoff_content)
            tar.addfile(handoff_info, BytesIO(handoff_content))

            # Add metadata.json
            metadata_content = json.dumps(package.to_metadata(), indent=2).encode("utf-8")
            metadata_info = tarfile.TarInfo(name="metadata.json")
            metadata_info.size = len(metadata_content)
            tar.addfile(metadata_info, BytesIO(metadata_content))

            # Add context files
            for file_path in files:
                if file_path.exists() and file_path.is_file():
                    try:
                        rel_path = file_path.relative_to(self.project_root)
                        arcname = f"context/{rel_path}"
                        tar.add(file_path, arcname=arcname)
                    except ValueError:
                        # File outside project root
                        tar.add(file_path, arcname=f"context/{file_path.name}")
