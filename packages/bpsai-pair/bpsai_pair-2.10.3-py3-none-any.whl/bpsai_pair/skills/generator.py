"""
Skill Generator - Automatically generates skill drafts from detected gaps.

This module transforms pattern detection into actionable skills by:
- Analyzing detected patterns from SkillGap
- Generating SKILL.md structure following Anthropic spec
- Including observed commands in workflow
- Adding placeholders for user customization
- Validating generated skills before saving
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .gap_detector import SkillGap
from .validator import SkillValidator
from .suggestion import BLOCKED_SKILL_NAMES

logger = logging.getLogger(__name__)


class SkillGeneratorError(Exception):
    """Error during skill generation."""
    pass


@dataclass
class GeneratedSkill:
    """Represents a generated skill draft."""

    name: str
    content: str
    source_pattern: List[str]
    requires_review: bool = True
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "content": self.content,
            "source_pattern": self.source_pattern,
            "requires_review": self.requires_review,
            "generated_at": self.generated_at,
        }


class SkillGenerator:
    """Generates skill drafts from detected gaps."""

    # Template for generated SKILL.md
    TEMPLATE = '''---
name: {name}
description: {description}
---

# {title}

## Overview

{overview}

## Trigger

Activates when performing {trigger_context}.

## Workflow

{workflow_steps}

## Notes

{notes}

---
*Auto-generated from session patterns. Review and customize before use.*
'''

    # Verb mappings for generating descriptions
    VERB_DESCRIPTIONS = {
        "testing": "Manages testing workflows",
        "debugging": "Guides debugging processes",
        "managing": "Handles management tasks",
        "reviewing": "Facilitates review processes",
        "building": "Orchestrates build operations",
        "deploying": "Coordinates deployment tasks",
        "searching": "Assists with search operations",
        "fixing": "Guides fix implementation",
        "creating": "Helps with creation tasks",
        "updating": "Manages update operations",
        "running": "Coordinates execution tasks",
        "committing": "Handles commit workflows",
        "formatting": "Manages formatting tasks",
        "linting": "Coordinates linting operations",
    }

    def __init__(self, validator: Optional[SkillValidator] = None):
        """Initialize generator.

        Args:
            validator: Optional SkillValidator for validation
        """
        self.validator = validator

    def generate_from_gap(self, gap: SkillGap) -> GeneratedSkill:
        """Generate a skill draft from a detected gap.

        Args:
            gap: The skill gap to generate from

        Returns:
            GeneratedSkill with content ready for review
        """
        name = gap.suggested_name
        pattern = gap.pattern

        # Generate content parts
        description = self._generate_description(name, pattern)
        title = self._generate_title(name)
        overview = self._generate_overview(pattern, gap)
        trigger_context = self._generate_trigger(pattern)
        workflow_steps = self._generate_workflow(pattern)
        notes = self._generate_notes(gap)

        # Build full content
        content = self.TEMPLATE.format(
            name=name,
            description=description,
            title=title,
            overview=overview,
            trigger_context=trigger_context,
            workflow_steps=workflow_steps,
            notes=notes,
        )

        return GeneratedSkill(
            name=name,
            content=content,
            source_pattern=pattern,
            requires_review=True,
        )

    def _generate_description(self, name: str, pattern: List[str]) -> str:
        """Generate a third-person description.

        Args:
            name: Skill name
            pattern: Command pattern

        Returns:
            Description string (under 1024 chars)
        """
        # Extract the verb from the name
        parts = name.split("-")
        verb = parts[0] if parts else "managing"

        # Get base description
        base = self.VERB_DESCRIPTIONS.get(verb, "Automates workflow tasks")

        # Add pattern context
        pattern_keywords = set()
        for cmd in pattern[:3]:
            words = re.findall(r"[a-z]+", cmd.lower())
            pattern_keywords.update(w for w in words if len(w) > 2)

        if pattern_keywords:
            context_words = list(pattern_keywords)[:3]
            context = ", ".join(context_words)
            desc = f"{base} involving {context}."
        else:
            desc = f"{base} based on observed patterns."

        # Ensure under 1024 chars
        if len(desc) > 1000:
            desc = desc[:997] + "..."

        return desc

    def _generate_title(self, name: str) -> str:
        """Generate a title from the skill name.

        Args:
            name: Skill name (kebab-case)

        Returns:
            Title Case string
        """
        return " ".join(word.capitalize() for word in name.split("-"))

    def _generate_overview(self, pattern: List[str], gap: SkillGap) -> str:
        """Generate an overview section.

        Args:
            pattern: Command pattern
            gap: The skill gap

        Returns:
            Overview text
        """
        lines = [
            f"This skill was generated from a workflow pattern detected {gap.frequency} times.",
            "",
            "**Detected Pattern:**",
        ]

        for i, cmd in enumerate(pattern[:5], 1):
            # Escape special chars for markdown
            cmd_escaped = cmd.replace("`", "\\`")
            lines.append(f"{i}. `{cmd_escaped}`")

        if len(pattern) > 5:
            lines.append(f"   ... and {len(pattern) - 5} more steps")

        lines.extend([
            "",
            f"**Estimated Time Savings:** {gap.time_saved_estimate}",
            "",
            "[Customize this overview to describe the skill's purpose]",
        ])

        return "\n".join(lines)

    def _generate_trigger(self, pattern: List[str]) -> str:
        """Generate trigger context from pattern.

        Args:
            pattern: Command pattern

        Returns:
            Trigger description
        """
        if not pattern:
            return "the related workflow"

        first_cmd = pattern[0].lower()

        # Identify trigger from first command
        if "test" in first_cmd or "pytest" in first_cmd:
            return "testing or debugging test failures"
        elif "git" in first_cmd:
            return "git operations and version control tasks"
        elif "grep" in first_cmd or "search" in first_cmd:
            return "codebase search and exploration"
        elif "build" in first_cmd or "npm" in first_cmd:
            return "build or package operations"
        elif "deploy" in first_cmd:
            return "deployment tasks"
        else:
            return f"`{pattern[0]}` and related operations"

    def _generate_workflow(self, pattern: List[str]) -> str:
        """Generate workflow steps from pattern.

        Args:
            pattern: Command pattern

        Returns:
            Workflow markdown
        """
        lines = []

        for i, cmd in enumerate(pattern, 1):
            # Clean up command for display
            cmd_clean = cmd.strip()
            cmd_escaped = cmd_clean.replace("`", "\\`")

            lines.append(f"### Step {i}: {self._step_title(cmd_clean)}")
            lines.append("")

            if self._looks_like_command(cmd_clean):
                lines.append("```bash")
                lines.append(cmd_escaped)
                lines.append("```")
            else:
                lines.append(f"Execute: `{cmd_escaped}`")

            lines.append("")
            lines.append("[Add context or decision points here]")
            lines.append("")

        return "\n".join(lines)

    def _step_title(self, cmd: str) -> str:
        """Generate a step title from a command.

        Args:
            cmd: Command string

        Returns:
            Step title
        """
        cmd_lower = cmd.lower()

        # Extract verb from command
        if cmd_lower.startswith("pytest") or "test" in cmd_lower:
            return "Run Tests"
        elif cmd_lower.startswith("git "):
            action = cmd.split()[1] if len(cmd.split()) > 1 else "operation"
            return f"Git {action.capitalize()}"
        elif "grep" in cmd_lower or "search" in cmd_lower:
            return "Search Codebase"
        elif "edit" in cmd_lower or "vim" in cmd_lower or "nano" in cmd_lower:
            return "Edit File"
        elif "read" in cmd_lower or "cat" in cmd_lower:
            return "Read Content"
        elif "fix" in cmd_lower:
            return "Apply Fix"
        else:
            # Use first word capitalized
            first_word = cmd.split()[0] if cmd.split() else "Execute"
            return first_word.capitalize()

    def _looks_like_command(self, cmd: str) -> bool:
        """Check if string looks like a shell command.

        Args:
            cmd: String to check

        Returns:
            True if looks like command
        """
        # Commands typically start with lowercase and contain no spaces at start
        if not cmd:
            return False

        # Check for common command patterns
        cmd_starters = [
            "git", "pytest", "python", "npm", "yarn", "pip", "grep", "find",
            "cat", "head", "tail", "vim", "nano", "cd", "ls", "mkdir", "rm",
            "cp", "mv", "docker", "kubectl", "make", "cargo", "go", "ruby",
        ]

        first_word = cmd.split()[0].lower() if cmd.split() else ""
        return first_word in cmd_starters or cmd.startswith("./")

    def _generate_notes(self, gap: SkillGap) -> str:
        """Generate notes section.

        Args:
            gap: The skill gap

        Returns:
            Notes markdown
        """
        lines = [
            f"- **Confidence:** {gap.confidence:.0%}",
            f"- **Observed:** {gap.frequency} times",
            f"- **Pattern detected:** {gap.detected_at[:10]}",
            "",
            "**Customization suggestions:**",
            "- Add error handling for edge cases",
            "- Include validation steps",
            "- Add rollback instructions if applicable",
        ]

        return "\n".join(lines)


def save_generated_skill(
    skill: GeneratedSkill,
    skills_dir: Path,
    force: bool = False,
    auto_approve: bool = False,
) -> Dict[str, Any]:
    """Save a generated skill to the skills directory.

    Args:
        skill: The generated skill
        skills_dir: Path to skills directory
        force: Overwrite existing skill
        auto_approve: Skip confirmation (same as saving directly)

    Returns:
        Result dict with success status

    Raises:
        SkillGeneratorError: If skill exists and force=False
    """
    # Check blocked skill names (permanent blocklist)
    if skill.name.lower() in BLOCKED_SKILL_NAMES:
        raise SkillGeneratorError(
            f"Skill name '{skill.name}' is permanently blocked. "
            f"This pattern is too trivial to be a skill."
        )

    skill_dir = skills_dir / skill.name
    skill_file = skill_dir / "SKILL.md"

    # Check if exists
    if skill_dir.exists() and not force:
        raise SkillGeneratorError(
            f"Skill '{skill.name}' already exists. Use --force to overwrite."
        )

    # Create directory and write file
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(skill.content, encoding="utf-8")

    # Validate the generated skill
    validator = SkillValidator(skills_dir)
    validation = validator.validate_skill(skill_dir)

    if not validation["valid"]:
        # Try to fix common issues
        validator.fix_skill(skill_dir)
        validation = validator.validate_skill(skill_dir)

    return {
        "success": True,
        "path": str(skill_file),
        "name": skill.name,
        "validation": validation,
        "requires_review": skill.requires_review,
    }


def generate_skill_from_gap_id(
    gap_id: int,
    history_dir: Path,
    skills_dir: Path,
    force: bool = False,
    auto_approve: bool = False,
) -> Dict[str, Any]:
    """Generate a skill from a gap ID.
    ...
    """
    from .gap_detector import GapPersistence
    from .gates import evaluate_gap_quality, GateStatus

    # Load gaps
    persistence = GapPersistence(history_dir=history_dir)
    gaps = persistence.load_gaps()

    if not gaps:
        raise SkillGeneratorError("No skill gaps found. Run `skill gaps --analyze` first.")

    if gap_id < 1 or gap_id > len(gaps):
        raise SkillGeneratorError(f"Invalid gap ID: {gap_id}. Valid range: 1-{len(gaps)}")

    gap = gaps[gap_id - 1]

    # ENFORCEMENT: Run quality gates before generation
    gate_result = evaluate_gap_quality(gap, skills_dir=skills_dir)

    if not gate_result.can_generate and not force:
        blocked_gates = [g.gate_name for g in gate_result.gate_results
                         if g.status == GateStatus.BLOCK]
        raise SkillGeneratorError(
            f"Quality gates blocked generation: {', '.join(blocked_gates)}. "
            f"Reason: {gate_result.recommendation}\n"
            f"Use --force to override (not recommended)."
        )

    if gate_result.overall_status == GateStatus.WARN and not force:
        # Log warning but proceed
        logger.warning(f"Quality gate warnings for '{gap.suggested_name}': {gate_result.recommendation}")

    # Generate skill
    generator = SkillGenerator()
    generated = generator.generate_from_gap(gap)

    # Save if auto_approve
    if auto_approve:
        return save_generated_skill(generated, skills_dir, force=force, auto_approve=True)

    # Return generated content for review
    return {
        "success": True,
        "generated": generated,
        "preview": generated.content,
        "requires_confirmation": True,
    }
