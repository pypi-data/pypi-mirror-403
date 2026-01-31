"""
Skill Gap Detector - Detects when users need skills that don't exist.

This module monitors session patterns to proactively suggest skill creation
when repeated manual workflows are detected.

Detection signals:
- Repeated command sequences (3+ occurrences)
- Manual workarounds
- Error patterns handled the same way
"""

import json
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Trivial patterns that should never become skills
TRIVIAL_PATTERNS = [
    ("pytest", "fix"),
    ("npm test", "fix"),
    ("yarn test", "fix"),
    ("make test", "fix"),
    ("git add", "git commit"),
    ("git commit", "git push"),
    ("pip install", "python"),
    ("npm install", "npm run"),
    ("cargo build", "cargo run"),
]

logger = logging.getLogger(__name__)


@dataclass
class SkillGap:
    """Represents a detected skill gap."""

    pattern: List[str]
    suggested_name: str
    confidence: float  # 0.0 to 1.0
    frequency: int
    time_saved_estimate: str
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "pattern": self.pattern,
            "suggested_name": self.suggested_name,
            "confidence": self.confidence,
            "frequency": self.frequency,
            "time_saved_estimate": self.time_saved_estimate,
            "detected_at": self.detected_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillGap":
        """Create SkillGap from dictionary."""
        return cls(
            pattern=data.get("pattern", []),
            suggested_name=data.get("suggested_name", ""),
            confidence=data.get("confidence", 0.0),
            frequency=data.get("frequency", 0),
            time_saved_estimate=data.get("time_saved_estimate", ""),
            detected_at=data.get("detected_at", datetime.now().isoformat()),
        )


class SkillGapDetector:
    """Detects potential skill gaps from session logs."""

    # Mapping of command keywords to gerund verbs for name generation
    COMMAND_VERBS = {
        "pytest": "testing",
        "test": "testing",
        "git": "managing-git",
        "commit": "committing",
        "diff": "reviewing",
        "review": "reviewing",
        "read": "reading",
        "edit": "editing",
        "debug": "debugging",
        "fix": "fixing",
        "build": "building",
        "deploy": "deploying",
        "lint": "linting",
        "format": "formatting",
        "search": "searching",
        "grep": "searching",
        "find": "finding",
        "create": "creating",
        "delete": "deleting",
        "update": "updating",
        "install": "installing",
        "run": "running",
    }

    def __init__(
        self,
        existing_skills: List[str],
        pattern_threshold: int = 5,
        max_sequence_length: int = 5,
        min_sequence_length: int = 3,
    ):
        """Initialize detector.

        Args:
            existing_skills: List of existing skill names
            pattern_threshold: Minimum occurrences to detect as gap (default: 5)
            max_sequence_length: Maximum length of command sequences to detect
            min_sequence_length: Minimum length (2-step patterns blocked)
        """
        self.existing_skills = [s.lower() for s in existing_skills]
        self.pattern_threshold = pattern_threshold
        self.max_sequence_length = max_sequence_length
        self.min_sequence_length = min_sequence_length

    def analyze_session(self, session_log: List[Dict[str, Any]]) -> List[SkillGap]:
        """Analyze session log for potential skill gaps.

        Args:
            session_log: List of session messages with 'type' and 'content' keys

        Returns:
            List of detected skill gaps
        """
        if not session_log:
            return []

        # Extract commands from session
        commands = self._extract_commands(session_log)

        if len(commands) < self.pattern_threshold:
            return []

        # Detect patterns
        patterns = self._detect_patterns(commands)

        # Convert patterns to skill gaps
        gaps = []
        for pattern_tuple, count in patterns.items():
            pattern_list = list(pattern_tuple)

            # Generate suggested name
            suggested_name = self._generate_name(pattern_list)

            # Calculate confidence
            confidence = self._calculate_confidence(count, pattern_list)

            # Check for overlap with existing skills
            if self._has_matching_skill(pattern_list, suggested_name):
                confidence *= 0.3  # Significantly reduce confidence for overlaps

            # Estimate time savings
            time_estimate = self._estimate_time_savings(count, len(pattern_list))

            gaps.append(SkillGap(
                pattern=pattern_list,
                suggested_name=suggested_name,
                confidence=confidence,
                frequency=count,
                time_saved_estimate=time_estimate,
            ))

        # Sort by confidence descending
        gaps.sort(key=lambda g: g.confidence, reverse=True)

        return gaps

    def _extract_commands(self, session_log: List[Dict[str, Any]]) -> List[str]:
        """Extract command strings from session log.

        Args:
            session_log: Session messages

        Returns:
            List of command strings
        """
        commands = []
        for msg in session_log:
            if msg.get("type") == "command":
                content = msg.get("content", "")
                if content:
                    commands.append(content.strip())
        return commands

    def _detect_patterns(self, commands: List[str]) -> Dict[tuple, int]:
        """Detect repeated command patterns."""
        pattern_counts: Dict[tuple, int] = Counter()

        # Detect n-grams for various sequence lengths
        # Start from min_sequence_length (not 2) to block trivial patterns
        for n in range(self.min_sequence_length, min(self.max_sequence_length + 1, len(commands) + 1)):
            for i in range(len(commands) - n + 1):
                pattern = tuple(commands[i:i + n])
                pattern_counts[pattern] += 1

        # Filter by threshold AND exclude trivial patterns
        return {
            p: c for p, c in pattern_counts.items()
            if c >= self.pattern_threshold and not self._is_trivial_pattern(p)
        }

    def _is_trivial_pattern(self, pattern: tuple) -> bool:
        """Check if pattern is in the trivial blocklist.

        Args:
            pattern: Tuple of commands

        Returns:
            True if pattern is trivial and should be blocked
        """
        # Normalize pattern for comparison
        normalized = tuple(cmd.lower().strip() for cmd in pattern)

        # Check exact matches in blocklist
        for trivial in TRIVIAL_PATTERNS:
            if len(normalized) == len(trivial):
                # Check if all elements match (allowing partial matches)
                matches = all(
                    t in n or n in t
                    for t, n in zip(trivial, normalized)
                )
                if matches:
                    return True

        # Block any 2-step pattern that's just "test" + "fix"
        if len(normalized) == 2:
            test_words = {"pytest", "test", "npm test", "yarn test", "jest", "mocha"}
            fix_words = {"fix", "edit", "update", "change", "modify"}

            first_is_test = any(tw in normalized[0] for tw in test_words)
            second_is_fix = any(fw in normalized[1] for fw in fix_words)

            if first_is_test and second_is_fix:
                return True

        return False

    def _generate_name(self, pattern: List[str]) -> str:
        """Generate a skill name from a command pattern.

        Args:
            pattern: List of commands

        Returns:
            Skill name in gerund form
        """
        # Find the primary action verb
        primary_verb = None
        for cmd in pattern:
            cmd_lower = cmd.lower()
            for key, verb in self.COMMAND_VERBS.items():
                if key in cmd_lower:
                    primary_verb = verb
                    break
            if primary_verb:
                break

        if not primary_verb:
            primary_verb = "managing"

        # Extract context words
        context_words = []
        for cmd in pattern:
            words = re.findall(r"[a-z]+", cmd.lower())
            for word in words:
                if word not in self.COMMAND_VERBS and len(word) > 2:
                    context_words.append(word)

        # Build name
        if context_words:
            context = Counter(context_words).most_common(1)[0][0]
            name = f"{primary_verb}-{context}"
        else:
            name = f"{primary_verb}-workflows"

        return name.lower()

    def _calculate_confidence(self, frequency: int, pattern: List[str]) -> float:
        """Calculate confidence score for a gap.

        Args:
            frequency: Number of occurrences
            pattern: The command pattern

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Base confidence from frequency
        freq_score = min(frequency / 10, 0.5)

        # Bonus for longer patterns (more specific)
        length_bonus = min((len(pattern) - 1) * 0.1, 0.3)

        # Combined score
        return min(freq_score + length_bonus + 0.2, 1.0)

    def _has_matching_skill(self, pattern: List[str], suggested_name: str) -> bool:
        """Check if pattern matches an existing skill.

        Args:
            pattern: Command pattern
            suggested_name: Generated skill name

        Returns:
            True if overlaps with existing skill
        """
        name_words = set(suggested_name.split("-"))

        for skill in self.existing_skills:
            skill_words = set(skill.split("-"))

            # Check name overlap
            common = name_words & skill_words
            if len(common) >= min(len(name_words), len(skill_words)) * 0.5:
                return True

            # Check if pattern keywords are in skill name
            pattern_keywords = set()
            for cmd in pattern:
                pattern_keywords.update(re.findall(r"[a-z]+", cmd.lower()))

            if pattern_keywords & skill_words:
                return True

        return False

    def _estimate_time_savings(self, frequency: int, pattern_length: int) -> str:
        """Estimate time savings from automating this pattern.

        Args:
            frequency: Number of occurrences
            pattern_length: Number of commands in pattern

        Returns:
            Human-readable estimate
        """
        # Estimate: each command takes ~30 seconds context switching
        # Automation saves ~20 seconds per command
        estimated_seconds = frequency * pattern_length * 20

        if estimated_seconds < 60:
            return f"~{estimated_seconds} seconds per cycle"
        else:
            minutes = estimated_seconds // 60
            return f"~{minutes} min per cycle"


class GapPersistence:
    """Handles persisting detected gaps to history."""

    def __init__(self, history_dir: Path):
        """Initialize persistence.

        Args:
            history_dir: Path to history directory
        """
        self.history_dir = history_dir
        self.gap_file = history_dir / "skill-gaps.jsonl" if history_dir else None

    def save_gap(self, gap: SkillGap) -> None:
        """Save a gap to history.

        Args:
            gap: Gap to save
        """
        if not self.gap_file:
            return

        self.history_dir.mkdir(parents=True, exist_ok=True)

        # Load existing gaps to check for duplicates
        existing_gaps = self.load_gaps()

        # Check for duplicate (same pattern)
        updated = False
        for i, existing in enumerate(existing_gaps):
            if existing.pattern == gap.pattern:
                # Update existing gap with higher confidence
                if gap.confidence > existing.confidence:
                    existing_gaps[i] = gap
                updated = True
                break

        if not updated:
            existing_gaps.append(gap)

        # Write all gaps back
        with open(self.gap_file, "w", encoding="utf-8") as f:
            for g in existing_gaps:
                f.write(json.dumps(g.to_dict()) + "\n")

    def load_gaps(self) -> List[SkillGap]:
        """Load gaps from history.

        Returns:
            List of skill gaps
        """
        if not self.gap_file or not self.gap_file.exists():
            return []

        gaps = []
        try:
            content = self.gap_file.read_text(encoding="utf-8")
            for line in content.strip().split("\n"):
                if line:
                    try:
                        data = json.loads(line)
                        gaps.append(SkillGap.from_dict(data))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.warning(f"Error loading gaps: {e}")

        return gaps

    def clear_gaps(self) -> None:
        """Clear all gaps from history."""
        if self.gap_file and self.gap_file.exists():
            self.gap_file.write_text("", encoding="utf-8")


def format_gap_notification(gap: SkillGap) -> str:
    """Format a gap notification message.

    Args:
        gap: The skill gap

    Returns:
        Formatted notification string
    """
    lines = [
        "Skill Gap Detected",
        "",
        f"You've performed this workflow {gap.frequency} times this session:",
    ]

    for i, cmd in enumerate(gap.pattern, 1):
        lines.append(f"  {i}. {cmd}")

    lines.extend([
        "",
        f"Would you like to create a \"{gap.suggested_name}\" skill?",
        f"Confidence: {gap.confidence:.0%}",
        f"Estimated savings: {gap.time_saved_estimate}",
    ])

    return "\n".join(lines)


def detect_gaps_from_history(
    history_dir: Path,
    skills_dir: Optional[Path] = None,
    pattern_threshold: int = 5,
) -> List[SkillGap]:
    """High-level function to detect gaps from history files.

    Args:
        history_dir: Path to history directory
        skills_dir: Path to skills directory for overlap detection
        pattern_threshold: Minimum pattern occurrences

    Returns:
        List of detected skill gaps
    """
    # Get existing skill names
    existing_skills = []
    if skills_dir and skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                existing_skills.append(skill_dir.name)

    # Load session log from changes.log or other sources
    session_log = []
    changes_log = history_dir / "changes.log" if history_dir else None

    if changes_log and changes_log.exists():
        try:
            content = changes_log.read_text(encoding="utf-8")
            for line in content.strip().split("\n")[-100:]:  # Last 100 entries
                if line:
                    # Parse as command-like entry
                    session_log.append({
                        "type": "command",
                        "content": line.split(" ", 1)[-1] if " " in line else line,
                    })
        except Exception as e:
            logger.warning(f"Error reading changes log: {e}")

    # Detect gaps
    detector = SkillGapDetector(
        existing_skills=existing_skills,
        pattern_threshold=pattern_threshold,
    )

    return detector.analyze_session(session_log)
