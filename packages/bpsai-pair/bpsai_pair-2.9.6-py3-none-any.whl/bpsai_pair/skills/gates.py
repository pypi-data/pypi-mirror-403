"""
Gap Quality Gates - Pre-generation quality checks for skill/subagent gaps.

This module provides quality gates that run BEFORE auto-skill generation
to prevent low-value skills from being created. The gates check:

1. Redundancy: Does this overlap with existing skills?
2. Novelty: Are these just generic commands everyone knows?
3. Complexity: Is this complex enough to warrant a skill?
4. Time Value: Does automation save meaningful time?

A gap must pass all gates to be eligible for auto-generation.
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .gap_detector import SkillGap
from .subagent_detector import SubagentGap
from .classifier import ClassifiedGap


class GateStatus(Enum):
    """Result status for a quality gate."""

    PASS = "pass"
    WARN = "warn"  # Passes but with warnings
    BLOCK = "block"  # Hard rejection


@dataclass
class GateResult:
    """Result from evaluating a single gate."""

    gate_name: str
    status: GateStatus
    score: float  # 0.0 to 1.0
    reason: str
    details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gate_name": self.gate_name,
            "status": self.status.value,
            "score": self.score,
            "reason": self.reason,
            "details": self.details,
        }


@dataclass
class QualityGateResult:
    """Combined result from all quality gates."""

    gap_id: str
    gap_name: str
    overall_status: GateStatus
    gate_results: List[GateResult]
    recommendation: str
    can_generate: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gap_id": self.gap_id,
            "gap_name": self.gap_name,
            "overall_status": self.overall_status.value,
            "gate_results": [g.to_dict() for g in self.gate_results],
            "recommendation": self.recommendation,
            "can_generate": self.can_generate,
        }


# Generic commands that shouldn't form the basis of a skill alone
GENERIC_COMMANDS = {
    # Testing
    "pytest",
    "npm test",
    "npm run test",
    "yarn test",
    "make test",
    "go test",
    "cargo test",
    "ruby test",
    "jest",
    "mocha",
    "rspec",
    # Git basics
    "git add",
    "git commit",
    "git push",
    "git pull",
    "git status",
    "git diff",
    "git log",
    "git checkout",
    "git branch",
    "git merge",
    "git stash",
    # Package management
    "pip install",
    "npm install",
    "yarn add",
    "brew install",
    "apt install",
    "cargo add",
    # Build basics
    "npm run build",
    "make",
    "make build",
    "cargo build",
    "go build",
    # Vague action words (too generic)
    "fix",
    "edit",
    "update",
    "change",
    "modify",
    "check",
    "run",
    "start",
    "stop",
}

# Pattern pairs that are always blocked (too simple to be skills)
TRIVIAL_PATTERN_PAIRS = [
    # test + fix is just development, not a skill
    ({"pytest", "test", "jest", "mocha", "npm test", "yarn test"}, {"fix", "edit", "update"}),
    # basic git workflow
    ({"git add"}, {"git commit"}),
    ({"git commit"}, {"git push"}),
    # install + run
    ({"pip install", "npm install", "yarn add"}, {"python", "npm run", "yarn run"}),
]

# Patterns that indicate generic commands
GENERIC_PATTERNS = [
    r"^(pip|npm|yarn|cargo|go)\s+(install|add|get)",
    r"^git\s+(add|commit|push|pull|status|diff|log)",
    r"^(pytest|jest|mocha|rspec|cargo test|go test)",
    r"^make\s*$",
    r"^(npm|yarn)\s+run\s+(test|build|start)",
]


class GapQualityGate:
    """Quality gate for evaluating gaps before skill generation."""

    # Thresholds for gate decisions
    REDUNDANCY_THRESHOLD = 0.4  # Below this = blocked
    NOVELTY_THRESHOLD = 0.4  # Below this = blocked
    COMPLEXITY_THRESHOLD = 0.4  # Below this = blocked
    TIME_VALUE_THRESHOLD = 0.4  # Below this = blocked

    # Minimum requirements
    MIN_COMMANDS = 3  # Minimum distinct commands for complexity
    MIN_PATTERN_LENGTH = 3  # Block 2-step patterns entirely
    MIN_TIME_SAVINGS_MINUTES = 5  # Minimum time savings value
    MIN_OCCURRENCES = 5  # Require more evidence

    def __init__(
        self,
        existing_skills: Optional[List[str]] = None,
        skills_dir: Optional[Path] = None,
    ):
        """Initialize gate.

        Args:
            existing_skills: List of existing skill names
            skills_dir: Path to skills directory for loading skill content
        """
        self.existing_skills = [s.lower() for s in (existing_skills or [])]
        self.skills_dir = skills_dir
        self._skill_content_cache: Dict[str, str] = {}

    def evaluate(
        self,
        gap: Union[SkillGap, SubagentGap, ClassifiedGap],
    ) -> QualityGateResult:
        """Evaluate a gap against all quality gates."""
        # Extract common fields
        if isinstance(gap, ClassifiedGap):
            gap_id = gap.id
            gap_name = gap.suggested_name
            source_commands = gap.source_commands
            occurrence_count = gap.occurrence_count
        elif isinstance(gap, SkillGap):
            gap_id = f"skill-{gap.suggested_name}"
            gap_name = gap.suggested_name
            source_commands = gap.pattern
            occurrence_count = gap.frequency
        else:  # SubagentGap
            gap_id = gap.id
            gap_name = gap.suggested_name
            source_commands = gap.source_commands
            occurrence_count = gap.occurrence_count

        # EARLY REJECTION: Check for trivial patterns before running full gates
        trivial_result = self._check_trivial_pattern(source_commands)
        if trivial_result:
            return QualityGateResult(
                gap_id=gap_id,
                gap_name=gap_name,
                overall_status=GateStatus.BLOCK,
                gate_results=[trivial_result],
                recommendation=f"BLOCKED: {trivial_result.reason}. Pattern too simple to be a skill.",
                can_generate=False,
            )

        # EARLY REJECTION: Check minimum pattern length
        if len(source_commands) < self.MIN_PATTERN_LENGTH:
            return QualityGateResult(
                gap_id=gap_id,
                gap_name=gap_name,
                overall_status=GateStatus.BLOCK,
                gate_results=[GateResult(
                    gate_name="pattern_length",
                    status=GateStatus.BLOCK,
                    score=0.0,
                    reason=f"Pattern has only {len(source_commands)} steps (min: {self.MIN_PATTERN_LENGTH})",
                    details="2-step patterns are too simple to warrant skills",
                )],
                recommendation="BLOCKED: Pattern too short. Skills need 3+ distinct steps.",
                can_generate=False,
            )

        # EARLY REJECTION: Check minimum occurrences
        if occurrence_count < self.MIN_OCCURRENCES:
            return QualityGateResult(
                gap_id=gap_id,
                gap_name=gap_name,
                overall_status=GateStatus.BLOCK,
                gate_results=[GateResult(
                    gate_name="occurrence_count",
                    status=GateStatus.BLOCK,
                    score=0.0,
                    reason=f"Only {occurrence_count} occurrences (min: {self.MIN_OCCURRENCES})",
                    details="Need more evidence before creating a skill",
                )],
                recommendation=f"BLOCKED: Pattern only seen {occurrence_count} times. Need {self.MIN_OCCURRENCES}+ occurrences.",
                can_generate=False,
            )

        # Run all gates
        gate_results = [
            self._check_redundancy(gap_name, source_commands),
            self._check_novelty(source_commands),
            self._check_complexity(source_commands),
            self._check_time_value(source_commands, occurrence_count),
        ]

        # Determine overall status
        if any(g.status == GateStatus.BLOCK for g in gate_results):
            overall_status = GateStatus.BLOCK
            can_generate = False
        elif any(g.status == GateStatus.WARN for g in gate_results):
            overall_status = GateStatus.WARN
            can_generate = True
        else:
            overall_status = GateStatus.PASS
            can_generate = True

        # Generate recommendation
        recommendation = self._generate_recommendation(gate_results, overall_status)

        return QualityGateResult(
            gap_id=gap_id,
            gap_name=gap_name,
            overall_status=overall_status,
            gate_results=gate_results,
            recommendation=recommendation,
            can_generate=can_generate,
        )

    def _check_trivial_pattern(self, source_commands: List[str]) -> Optional[GateResult]:
        """Check if pattern matches a known trivial pattern pair.

        Args:
            source_commands: Commands in the pattern

        Returns:
            GateResult if blocked, None if ok
        """
        if len(source_commands) < 2:
            return None

        # Normalize commands
        normalized = [cmd.lower().strip() for cmd in source_commands]

        # For 2-step patterns, check against trivial pairs
        if len(normalized) == 2:
            first, second = normalized[0], normalized[1]

            for first_set, second_set in TRIVIAL_PATTERN_PAIRS:
                first_matches = any(f in first or first in f for f in first_set)
                second_matches = any(s in second or second in s for s in second_set)

                if first_matches and second_matches:
                    return GateResult(
                        gate_name="trivial_pattern",
                        status=GateStatus.BLOCK,
                        score=0.0,
                        reason=f"Trivial pattern: '{first}' + '{second}'",
                        details="This is just normal development workflow, not a skill",
                    )

        # Check for "test + fix" pattern regardless of length
        test_cmds = {"pytest", "test", "jest", "mocha", "npm test", "yarn test", "cargo test", "go test"}
        fix_cmds = {"fix", "edit", "update", "change", "modify", "patch"}

        has_test = any(any(t in cmd for t in test_cmds) for cmd in normalized)
        has_fix = any(any(f in cmd for f in fix_cmds) for cmd in normalized)

        # If pattern is ONLY test + fix with nothing else meaningful, block it
        if has_test and has_fix and len(normalized) == 2:
            return GateResult(
                gate_name="trivial_pattern",
                status=GateStatus.BLOCK,
                score=0.0,
                reason="Pattern is just 'test + fix' - basic development, not a skill",
                details="Running tests and fixing failures is universal developer knowledge",
            )

        return None

    def _check_redundancy(
        self, gap_name: str, source_commands: List[str]
    ) -> GateResult:
        """Check if gap overlaps with existing skills.

        Args:
            gap_name: Suggested skill name
            source_commands: Commands in the pattern

        Returns:
            GateResult for redundancy check
        """
        if not self.existing_skills:
            return GateResult(
                gate_name="redundancy",
                status=GateStatus.PASS,
                score=1.0,
                reason="No existing skills to compare",
            )

        # Check name overlap
        gap_words = set(gap_name.lower().split("-"))
        max_overlap = 0.0
        overlapping_skill = None

        for skill in self.existing_skills:
            skill_words = set(skill.split("-"))
            if gap_words & skill_words:
                overlap = len(gap_words & skill_words) / max(
                    len(gap_words), len(skill_words)
                )
                if overlap > max_overlap:
                    max_overlap = overlap
                    overlapping_skill = skill

        # Check command overlap with skill content
        if self.skills_dir and overlapping_skill:
            skill_content = self._get_skill_content(overlapping_skill)
            if skill_content:
                command_overlap = self._calculate_command_overlap(
                    source_commands, skill_content
                )
                max_overlap = max(max_overlap, command_overlap)

        # Calculate score (inverse of overlap)
        score = 1.0 - max_overlap

        if score < self.REDUNDANCY_THRESHOLD:
            return GateResult(
                gate_name="redundancy",
                status=GateStatus.BLOCK,
                score=score,
                reason=f"High overlap with '{overlapping_skill}'",
                details=f"Overlap: {max_overlap:.0%}. Consider extending existing skill instead.",
            )
        elif score < 0.6:
            return GateResult(
                gate_name="redundancy",
                status=GateStatus.WARN,
                score=score,
                reason=f"Partial overlap with '{overlapping_skill}'",
                details="May duplicate existing functionality",
            )
        else:
            return GateResult(
                gate_name="redundancy",
                status=GateStatus.PASS,
                score=score,
                reason="No significant overlap with existing skills",
            )

    def _check_novelty(self, source_commands: List[str]) -> GateResult:
        """Check if commands are novel (not just generic).

        Args:
            source_commands: Commands in the pattern

        Returns:
            GateResult for novelty check
        """
        if not source_commands:
            return GateResult(
                gate_name="novelty",
                status=GateStatus.BLOCK,
                score=0.0,
                reason="No commands to analyze",
            )

        # Check each command against generic list
        generic_count = 0
        total_commands = len(source_commands)

        for cmd in source_commands:
            cmd_lower = cmd.lower().strip()

            # Check exact match
            if cmd_lower in GENERIC_COMMANDS:
                generic_count += 1
                continue

            # Check word match
            cmd_words = set(cmd_lower.split())
            if cmd_words & GENERIC_COMMANDS:
                generic_count += 0.5
                continue

            # Check pattern match
            for pattern in GENERIC_PATTERNS:
                if re.match(pattern, cmd_lower):
                    generic_count += 0.7
                    break

        # Calculate novelty score
        generic_ratio = generic_count / total_commands
        score = 1.0 - generic_ratio

        if score < self.NOVELTY_THRESHOLD:
            return GateResult(
                gate_name="novelty",
                status=GateStatus.BLOCK,
                score=score,
                reason="Pattern contains only generic commands",
                details=f"{generic_count:.0f}/{total_commands} commands are generic developer knowledge",
            )
        elif score < 0.5:
            return GateResult(
                gate_name="novelty",
                status=GateStatus.WARN,
                score=score,
                reason="Pattern contains mostly generic commands",
                details="Consider whether this adds unique value",
            )
        else:
            return GateResult(
                gate_name="novelty",
                status=GateStatus.PASS,
                score=score,
                reason="Pattern contains novel/specialized commands",
            )

    def _check_complexity(self, source_commands: List[str]) -> GateResult:
        """Check if pattern is complex enough for a skill.

        Args:
            source_commands: Commands in the pattern

        Returns:
            GateResult for complexity check
        """
        # Count distinct commands
        distinct_commands = len(set(cmd.strip().lower() for cmd in source_commands))

        # Calculate score based on command count
        if distinct_commands >= 5:
            score = 1.0
        elif distinct_commands >= self.MIN_COMMANDS:
            score = 0.5 + (distinct_commands - self.MIN_COMMANDS) * 0.25
        else:
            score = distinct_commands / self.MIN_COMMANDS * 0.3

        if score < self.COMPLEXITY_THRESHOLD:
            return GateResult(
                gate_name="complexity",
                status=GateStatus.BLOCK,
                score=score,
                reason=f"Only {distinct_commands} distinct commands (min: {self.MIN_COMMANDS})",
                details="Pattern too simple to warrant a skill",
            )
        elif score < 0.5:
            return GateResult(
                gate_name="complexity",
                status=GateStatus.WARN,
                score=score,
                reason=f"{distinct_commands} commands - borderline complexity",
                details="Consider if more steps should be included",
            )
        else:
            return GateResult(
                gate_name="complexity",
                status=GateStatus.PASS,
                score=score,
                reason=f"{distinct_commands} distinct commands - good complexity",
            )

    def _check_time_value(
        self, source_commands: List[str], occurrence_count: int
    ) -> GateResult:
        """Check if pattern provides meaningful time savings.

        Args:
            source_commands: Commands in the pattern
            occurrence_count: How often the pattern occurs

        Returns:
            GateResult for time value check
        """
        # Estimate time savings
        # Assume: 30 seconds per command for context switching
        # Automation saves ~20 seconds per command
        seconds_per_command = 20
        commands_count = len(source_commands)
        savings_per_use = commands_count * seconds_per_command  # seconds
        total_savings = savings_per_use * occurrence_count  # seconds
        minutes_saved = total_savings / 60

        # Calculate score
        if minutes_saved >= 10:
            score = 1.0
        elif minutes_saved >= self.MIN_TIME_SAVINGS_MINUTES:
            score = 0.5 + (minutes_saved - self.MIN_TIME_SAVINGS_MINUTES) * 0.1
        else:
            score = minutes_saved / self.MIN_TIME_SAVINGS_MINUTES * 0.3

        if score < self.TIME_VALUE_THRESHOLD:
            return GateResult(
                gate_name="time_value",
                status=GateStatus.BLOCK,
                score=score,
                reason=f"Only ~{minutes_saved:.1f} min saved (min: {self.MIN_TIME_SAVINGS_MINUTES})",
                details="Automation overhead exceeds time savings",
            )
        elif score < 0.5:
            return GateResult(
                gate_name="time_value",
                status=GateStatus.WARN,
                score=score,
                reason=f"~{minutes_saved:.1f} min saved - marginal value",
                details="Consider if pattern frequency will increase",
            )
        else:
            return GateResult(
                gate_name="time_value",
                status=GateStatus.PASS,
                score=score,
                reason=f"~{minutes_saved:.1f} min saved - good time value",
            )

    def _get_skill_content(self, skill_name: str) -> Optional[str]:
        """Get content of an existing skill.

        Args:
            skill_name: Skill name

        Returns:
            Skill content or None
        """
        if skill_name in self._skill_content_cache:
            return self._skill_content_cache[skill_name]

        if not self.skills_dir:
            return None

        skill_file = self.skills_dir / skill_name / "SKILL.md"
        if skill_file.exists():
            try:
                content = skill_file.read_text(encoding="utf-8")
                self._skill_content_cache[skill_name] = content
                return content
            except (OSError, IOError):
                pass

        return None

    def _calculate_command_overlap(
        self, commands: List[str], skill_content: str
    ) -> float:
        """Calculate overlap between commands and skill content.

        Args:
            commands: List of commands
            skill_content: Skill file content

        Returns:
            Overlap ratio (0.0 to 1.0)
        """
        content_lower = skill_content.lower()
        matches = 0

        for cmd in commands:
            # Check if command or key words appear in skill
            cmd_lower = cmd.lower()
            if cmd_lower in content_lower:
                matches += 1
            else:
                # Check individual words
                words = cmd_lower.split()
                word_matches = sum(1 for w in words if w in content_lower and len(w) > 3)
                if word_matches >= len(words) * 0.5:
                    matches += 0.5

        return matches / len(commands) if commands else 0.0

    def _generate_recommendation(
        self, gate_results: List[GateResult], overall_status: GateStatus
    ) -> str:
        """Generate a recommendation based on gate results.

        Args:
            gate_results: All gate results
            overall_status: Overall status

        Returns:
            Human-readable recommendation
        """
        if overall_status == GateStatus.PASS:
            return "Ready for auto-generation. Pattern meets all quality criteria."

        blocked = [g for g in gate_results if g.status == GateStatus.BLOCK]
        warnings = [g for g in gate_results if g.status == GateStatus.WARN]

        if blocked:
            reasons = [g.reason for g in blocked]
            return f"BLOCKED: {'; '.join(reasons)}. Use --force to override."

        if warnings:
            reasons = [g.reason for g in warnings]
            return f"WARNINGS: {'; '.join(reasons)}. Review before generating."

        return "Evaluation complete."


def evaluate_gap_quality(
    gap: Union[SkillGap, SubagentGap, ClassifiedGap],
    skills_dir: Optional[Path] = None,
) -> QualityGateResult:
    """High-level function to evaluate gap quality.

    Args:
        gap: The gap to evaluate
        skills_dir: Path to skills directory

    Returns:
        QualityGateResult
    """
    # Get existing skills
    existing_skills = []
    if skills_dir and skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                existing_skills.append(skill_dir.name)

    gate = GapQualityGate(
        existing_skills=existing_skills,
        skills_dir=skills_dir,
    )

    return gate.evaluate(gap)


def format_gate_result(result: QualityGateResult) -> str:
    """Format gate result for CLI display.

    Args:
        result: The gate result

    Returns:
        Formatted string
    """
    # Status indicator
    if result.overall_status == GateStatus.PASS:
        status_icon = "✅"
        status_text = "PASS"
    elif result.overall_status == GateStatus.WARN:
        status_icon = "⚠️"
        status_text = "WARN"
    else:
        status_icon = "❌"
        status_text = "BLOCKED"

    lines = [
        f"Quality Gate Results: {result.gap_name}",
        "=" * 50,
        f"Overall: {status_icon} {status_text}",
        "",
        "Gate Results:",
    ]

    for gate in result.gate_results:
        if gate.status == GateStatus.PASS:
            icon = "✅"
        elif gate.status == GateStatus.WARN:
            icon = "⚠️"
        else:
            icon = "❌"

        score_bar = "█" * int(gate.score * 10) + "░" * (10 - int(gate.score * 10))
        lines.append(f"  {icon} {gate.gate_name:12} [{score_bar}] {gate.score:.2f}")
        lines.append(f"     {gate.reason}")
        if gate.details:
            lines.append(f"     [dim]{gate.details}[/dim]")

    lines.extend(["", f"Recommendation: {result.recommendation}"])

    return "\n".join(lines)
