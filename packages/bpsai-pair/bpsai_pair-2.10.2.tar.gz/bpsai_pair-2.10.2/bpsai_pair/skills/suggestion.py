"""
Skill Suggestion Module - Analyzes session patterns to suggest new skills.

This module provides:
- Pattern detection from session history
- Skill suggestion generation
- Skill draft creation from suggestions
- Integration with the existing skill validator
"""

import re
import logging
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .validator import SkillValidator

logger = logging.getLogger(__name__)

# Trivial patterns that should never become skills
# These are basic development workflows that don't need skill automation
TRIVIAL_PATTERNS = [
    ("pytest", "fix"),
    ("npm test", "fix"),
    ("yarn test", "fix"),
    ("make test", "fix"),
    ("jest", "fix"),
    ("mocha", "fix"),
    ("test", "fix"),
    ("test", "edit"),
    ("test", "update"),
    ("git add", "git commit"),
    ("git commit", "git push"),
    ("pip install", "python"),
    ("npm install", "npm run"),
    ("cargo build", "cargo run"),
]

# Generic commands that shouldn't form the basis of a skill
GENERIC_COMMANDS = {
    "pytest", "npm test", "yarn test", "make test", "go test", "cargo test",
    "jest", "mocha", "rspec",
    "git add", "git commit", "git push", "git pull", "git status", "git diff",
    "fix", "edit", "update", "change", "modify", "check", "run", "start", "stop",
}

# Skill names that are permanently blocked from creation
# These represent trivial patterns that should never become skills
BLOCKED_SKILL_NAMES = {
    "testing-fixes",
    "test-fix",
    "test-and-fix",
    "pytest-fix",
    "git-add-commit",
    "git-commit-push",
    "install-run",
}


class SkillSuggestionError(Exception):
    """Error during skill suggestion operations."""
    pass


class HistoryParser:
    """Parses session history files to extract command patterns."""

    def __init__(self, history_dir: Optional[Path] = None):
        """Initialize parser.

        Args:
            history_dir: Path to history directory. If None, uses default.
        """
        self.history_dir = history_dir

    def get_sessions(self) -> List[Dict[str, Any]]:
        """Get list of sessions from session log.

        Returns:
            List of session dicts with id and timestamps
        """
        if not self.history_dir or not self.history_dir.exists():
            return []

        sessions_log = self.history_dir / "sessions.log"
        if not sessions_log.exists():
            return []

        sessions = []
        try:
            content = sessions_log.read_text(encoding="utf-8")
            for line in content.strip().split("\n"):
                if not line:
                    continue
                # Parse: 2025-12-23T10:00:00 session_start id=abc123
                match = re.match(r"(\S+)\s+session_start\s+id=(\S+)", line)
                if match:
                    sessions.append({
                        "timestamp": match.group(1),
                        "id": match.group(2),
                    })
        except Exception as e:
            logger.warning(f"Error parsing sessions log: {e}")

        return sessions

    def get_changes(self) -> List[Dict[str, Any]]:
        """Get list of changes from changes log.

        Returns:
            List of change entries
        """
        if not self.history_dir or not self.history_dir.exists():
            return []

        changes_log = self.history_dir / "changes.log"
        if not changes_log.exists():
            return []

        changes = []
        try:
            content = changes_log.read_text(encoding="utf-8")
            for line in content.strip().split("\n"):
                if not line:
                    continue
                # Parse timestamp
                parts = line.split()
                if parts:
                    changes.append({
                        "timestamp": parts[0],
                        "data": " ".join(parts[1:]) if len(parts) > 1 else "",
                    })
        except Exception as e:
            logger.warning(f"Error parsing changes log: {e}")

        return changes

    def get_command_history(self) -> List[Dict[str, Any]]:
        """Get command history for pattern analysis.

        This is a simplified version - in a real implementation,
        this would parse more detailed command logs.

        Returns:
            List of command entries
        """
        # In a full implementation, this would parse detailed command logs
        # For now, return empty as we don't have detailed command history
        return []


class PatternDetector:
    """Detects repeated patterns in command sequences."""

    def __init__(self, min_occurrences: int = 3, max_sequence_length: int = 5):
        """Initialize detector.

        Args:
            min_occurrences: Minimum times a pattern must occur
            max_sequence_length: Maximum length of sequences to detect
        """
        self.min_occurrences = min_occurrences
        self.max_sequence_length = max_sequence_length

    def detect_patterns(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns in command history.

        Args:
            history: List of command entries with 'command' and 'timestamp' keys

        Returns:
            List of detected patterns with confidence scores
        """
        if not history:
            return []

        # Extract command sequence
        commands = [entry.get("command", "") for entry in history if entry.get("command")]

        if len(commands) < self.min_occurrences:
            return []

        patterns = []

        # Detect n-gram patterns for various sequence lengths
        for n in range(2, min(self.max_sequence_length + 1, len(commands) + 1)):
            ngram_counts = self._count_ngrams(commands, n)

            for ngram, count in ngram_counts.items():
                if count >= self.min_occurrences:
                    confidence = self._calculate_confidence(count, len(commands), n)
                    patterns.append({
                        "sequence": list(ngram),
                        "occurrences": count,
                        "confidence": confidence,
                        "sequence_length": n,
                    })

        # Sort by confidence, then by occurrences
        patterns.sort(key=lambda p: (p["confidence"], p["occurrences"]), reverse=True)

        # Remove overlapping/redundant patterns
        patterns = self._deduplicate_patterns(patterns)

        # Filter out trivial patterns (test+fix, git add+commit, etc.)
        patterns = [p for p in patterns if not self._is_trivial_pattern(p["sequence"])]

        return patterns

    def _is_trivial_pattern(self, sequence: List[str]) -> bool:
        """Check if a pattern is too trivial to become a skill.

        Args:
            sequence: Command sequence

        Returns:
            True if pattern is trivial and should be blocked
        """
        if not sequence:
            return True

        # Normalize commands for comparison
        normalized = [cmd.lower().strip() for cmd in sequence]

        # Check exact matches in trivial patterns list
        for trivial in TRIVIAL_PATTERNS:
            if len(normalized) == len(trivial):
                # Check if all elements match (allowing partial matches)
                matches = all(
                    t in n or n in t
                    for t, n in zip(trivial, normalized)
                )
                if matches:
                    logger.debug(f"Blocked trivial pattern: {sequence}")
                    return True

        # Define test and fix command sets
        test_words = {"pytest", "test", "npm test", "yarn test", "jest", "mocha", "go test", "cargo test"}
        fix_words = {"fix", "edit", "update", "change", "modify"}

        # Block any 2-step pattern that's just "test" + "fix/edit/update"
        if len(normalized) == 2:
            first_is_test = any(tw in normalized[0] for tw in test_words)
            second_is_fix = any(fw in normalized[1] for fw in fix_words)

            if first_is_test and second_is_fix:
                logger.debug(f"Blocked test+fix pattern: {sequence}")
                return True

        # Block patterns where ALL unique commands are just test+fix commands
        # e.g., ["pytest", "fix", "pytest", "fix"] has unique set {"pytest", "fix"}
        unique_commands = set(normalized)
        is_all_test = all(any(tw in cmd for tw in test_words) for cmd in unique_commands)
        is_all_fix = all(any(fw in cmd for fw in fix_words) for cmd in unique_commands)
        is_mixed_test_fix = (
            all(
                any(tw in cmd for tw in test_words) or any(fw in cmd for fw in fix_words)
                for cmd in unique_commands
            )
            and any(any(tw in cmd for tw in test_words) for cmd in unique_commands)
            and any(any(fw in cmd for fw in fix_words) for cmd in unique_commands)
        )

        if is_mixed_test_fix:
            logger.debug(f"Blocked test+fix repetition pattern: {sequence}")
            return True

        # Block patterns where all commands are generic (too basic)
        generic_count = sum(1 for cmd in normalized if any(g in cmd for g in GENERIC_COMMANDS))
        if generic_count == len(normalized) and len(normalized) <= 2:
            logger.debug(f"Blocked all-generic pattern: {sequence}")
            return True

        return False

    def _count_ngrams(self, commands: List[str], n: int) -> Counter:
        """Count n-gram occurrences in command sequence.

        Args:
            commands: List of commands
            n: N-gram length

        Returns:
            Counter of n-gram tuples
        """
        ngrams = []
        for i in range(len(commands) - n + 1):
            ngram = tuple(commands[i:i + n])
            ngrams.append(ngram)
        return Counter(ngrams)

    def _calculate_confidence(self, count: int, total_commands: int, sequence_length: int) -> int:
        """Calculate confidence score for a pattern.

        Args:
            count: Number of occurrences
            total_commands: Total commands in history
            sequence_length: Length of the pattern

        Returns:
            Confidence score (0-100)
        """
        # Base confidence from frequency
        frequency_score = min(count / self.min_occurrences * 50, 50)

        # Bonus for longer sequences (more specific patterns)
        length_bonus = min((sequence_length - 1) * 10, 30)

        # Penalty for very short histories
        coverage_score = min(count * sequence_length / total_commands * 20, 20)

        return min(int(frequency_score + length_bonus + coverage_score), 100)

    def _deduplicate_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove redundant patterns (subsets of longer patterns).

        Args:
            patterns: List of patterns sorted by confidence

        Returns:
            Deduplicated list
        """
        if len(patterns) <= 1:
            return patterns

        result = []
        seen_sequences = set()

        for pattern in patterns:
            seq_tuple = tuple(pattern["sequence"])

            # Check if this is a subset of an already-added pattern
            is_subset = False
            for seen in seen_sequences:
                if len(seq_tuple) < len(seen):
                    # Check if seq_tuple is contained in seen
                    seen_str = " ".join(seen)
                    seq_str = " ".join(seq_tuple)
                    if seq_str in seen_str:
                        is_subset = True
                        break

            if not is_subset:
                result.append(pattern)
                seen_sequences.add(seq_tuple)

        return result


class SkillSuggester:
    """Generates skill suggestions from detected patterns."""

    # Mapping of command types to gerund verbs
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
    }

    def __init__(self, skills_dir: Optional[Path] = None):
        """Initialize suggester.

        Args:
            skills_dir: Path to existing skills directory for overlap detection
        """
        self.skills_dir = skills_dir
        self._existing_skills = self._load_existing_skills()

    def _load_existing_skills(self) -> Dict[str, str]:
        """Load existing skill names and descriptions.

        Returns:
            Dict mapping skill name to description
        """
        skills = {}
        if not self.skills_dir or not self.skills_dir.exists():
            return skills

        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    try:
                        content = skill_file.read_text(encoding="utf-8")
                        # Parse frontmatter
                        if content.startswith("---"):
                            end_idx = content.find("---", 3)
                            if end_idx > 0:
                                yaml_content = content[3:end_idx]
                                fm = yaml.safe_load(yaml_content) or {}
                                skills[skill_dir.name] = fm.get("description", "")
                    except Exception as e:
                        logger.warning(f"Error loading skill {skill_dir.name}: {e}")

        return skills

    def generate_suggestions(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate skill suggestions from patterns.

        Args:
            patterns: List of detected patterns

        Returns:
            List of skill suggestions
        """
        suggestions = []

        for pattern in patterns:
            suggestion = self._pattern_to_suggestion(pattern)
            if suggestion:
                # Check for overlap with existing skills
                overlaps = self._check_overlap(suggestion)
                if overlaps:
                    suggestion["overlaps_with"] = overlaps

                suggestions.append(suggestion)

        return suggestions

    def _pattern_to_suggestion(self, pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert a pattern to a skill suggestion.

        Args:
            pattern: Detected pattern

        Returns:
            Skill suggestion dict or None
        """
        sequence = pattern.get("sequence", [])
        if not sequence:
            return None

        # Generate name from pattern
        name = self._generate_name(sequence)

        # Generate description
        description = self._generate_description(sequence, pattern)

        # Estimate time savings (simple heuristic)
        estimated_savings = self._estimate_savings(pattern)

        return {
            "name": name,
            "description": description,
            "confidence": pattern.get("confidence", 0),
            "pattern": sequence,
            "occurrences": pattern.get("occurrences", 0),
            "estimated_savings": estimated_savings,
        }

    def _generate_name(self, sequence: List[str]) -> str:
        """Generate a skill name from a command sequence.

        Args:
            sequence: Command sequence

        Returns:
            Skill name in gerund-noun format
        """
        # Find the primary action verb
        primary_verb = None
        for cmd in sequence:
            cmd_lower = cmd.lower()
            for key, verb in self.COMMAND_VERBS.items():
                if key in cmd_lower:
                    primary_verb = verb
                    break
            if primary_verb:
                break

        if not primary_verb:
            primary_verb = "managing"

        # Find the object/context
        context_words = []
        for cmd in sequence:
            cmd_lower = cmd.lower()
            # Extract meaningful words
            words = re.findall(r"[a-z]+", cmd_lower)
            for word in words:
                if word not in self.COMMAND_VERBS and len(word) > 2:
                    context_words.append(word)

        # Build name
        if context_words:
            # Use the most common context word
            context = Counter(context_words).most_common(1)[0][0]
            name = f"{primary_verb}-{context}"
        else:
            name = f"{primary_verb}-workflows"

        return name.lower()

    def _generate_description(self, sequence: List[str], pattern: Dict[str, Any]) -> str:
        """Generate a description for the skill.

        Args:
            sequence: Command sequence
            pattern: Pattern data

        Returns:
            Skill description in 3rd person
        """
        # Describe the workflow
        action_words = []
        for cmd in sequence[:3]:  # First 3 commands
            cmd_lower = cmd.lower()
            for key, verb in self.COMMAND_VERBS.items():
                if key in cmd_lower:
                    action_words.append(verb.replace("-", " "))
                    break

        if action_words:
            actions = ", ".join(action_words[:-1])
            if len(action_words) > 1:
                actions += f", and {action_words[-1]}"
            else:
                actions = action_words[0]
            return f"Automates {actions} workflows for improved efficiency."

        return "Automates a repeated workflow pattern."

    def _estimate_savings(self, pattern: Dict[str, Any]) -> str:
        """Estimate time savings from automating this pattern.

        Args:
            pattern: Pattern data

        Returns:
            Human-readable savings estimate
        """
        occurrences = pattern.get("occurrences", 0)
        sequence_length = pattern.get("sequence_length", 2)

        # Estimate: each command takes ~30 seconds of context switching
        # Automation could save ~20 seconds per command
        estimated_seconds = occurrences * sequence_length * 20

        if estimated_seconds < 60:
            return f"~{estimated_seconds} seconds per cycle"
        else:
            minutes = estimated_seconds // 60
            return f"~{minutes} minutes per cycle"

    def _check_overlap(self, suggestion: Dict[str, Any]) -> List[str]:
        """Check if suggestion overlaps with existing skills.

        Args:
            suggestion: Skill suggestion

        Returns:
            List of overlapping skill names
        """
        overlaps = []
        suggestion_name = suggestion.get("name", "").lower()
        suggestion_pattern = suggestion.get("pattern", [])

        for skill_name, skill_desc in self._existing_skills.items():
            # Check name similarity
            if self._names_similar(suggestion_name, skill_name):
                overlaps.append(skill_name)
                continue

            # Check if pattern keywords appear in existing skill description
            pattern_keywords = set()
            for cmd in suggestion_pattern:
                pattern_keywords.update(re.findall(r"[a-z]+", cmd.lower()))

            desc_lower = skill_desc.lower()
            matching_keywords = sum(1 for kw in pattern_keywords if kw in desc_lower)
            if matching_keywords >= len(pattern_keywords) * 0.5:  # 50% overlap
                overlaps.append(skill_name)

        return overlaps

    def _names_similar(self, name1: str, name2: str) -> bool:
        """Check if two skill names are similar.

        Args:
            name1: First name
            name2: Second name

        Returns:
            True if names are similar
        """
        # Extract words
        words1 = set(name1.split("-"))
        words2 = set(name2.split("-"))

        # Check overlap
        common = words1 & words2
        if len(common) >= min(len(words1), len(words2)) * 0.5:
            return True

        return False


class SkillDraftCreator:
    """Creates skill draft files from suggestions."""

    TEMPLATE = '''---
name: {name}
description: {description}
---

# {title}

## Overview

This skill was auto-generated based on detected workflow patterns.

## Pattern Detected

{pattern_description}

## Usage

Activated when performing {activation_context}.

## Workflow

{workflow_steps}

## Notes

- Confidence: {confidence}%
- Based on {occurrences} observed occurrences
- Estimated savings: {estimated_savings}

---
*This is a draft skill. Review and customize before use.*
'''

    def __init__(self, skills_dir: Path):
        """Initialize creator.

        Args:
            skills_dir: Path to skills directory
        """
        self.skills_dir = skills_dir
        self.validator = SkillValidator(skills_dir)

    def create_draft(self, suggestion: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
        """Create a skill draft from a suggestion.

        Args:
            suggestion: Skill suggestion dict
            force: Overwrite existing skill

        Returns:
            Result dict with success status and path

        Raises:
            SkillSuggestionError: If skill exists and force=False
        """
        name = suggestion.get("name", "")
        if not name:
            raise SkillSuggestionError("Suggestion missing 'name' field")

        # Check blocked skill names (permanent blocklist)
        if name.lower() in BLOCKED_SKILL_NAMES:
            raise SkillSuggestionError(
                f"Skill name '{name}' is permanently blocked. "
                f"This pattern is too trivial to be a skill."
            )

        skill_dir = self.skills_dir / name
        skill_file = skill_dir / "SKILL.md"

        # Check if exists
        if skill_dir.exists() and not force:
            raise SkillSuggestionError(f"Skill '{name}' already exists. Use --force to overwrite.")

        # Generate content
        content = self._generate_content(suggestion)

        # Create directory and file
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(content, encoding="utf-8")

        # Validate
        validation = self.validator.validate_skill(skill_dir)
        if not validation["valid"]:
            # Try to fix
            self.validator.fix_skill(skill_dir)
            validation = self.validator.validate_skill(skill_dir)

        return {
            "success": True,
            "path": str(skill_file),
            "validation": validation,
        }

    def _generate_content(self, suggestion: Dict[str, Any]) -> str:
        """Generate SKILL.md content from suggestion.

        Args:
            suggestion: Skill suggestion

        Returns:
            SKILL.md content
        """
        name = suggestion.get("name", "unknown")
        description = suggestion.get("description", "Auto-generated skill.")
        pattern = suggestion.get("pattern", [])
        confidence = suggestion.get("confidence", 0)
        occurrences = suggestion.get("occurrences", 0)
        estimated_savings = suggestion.get("estimated_savings", "unknown")

        # Generate title (convert kebab-case to Title Case)
        title = " ".join(word.capitalize() for word in name.split("-"))

        # Pattern description
        pattern_description = " → ".join(pattern) if pattern else "No pattern data"

        # Activation context
        if pattern:
            activation_context = pattern[0].lower()
        else:
            activation_context = "the related workflow"

        # Workflow steps
        workflow_steps = ""
        for i, cmd in enumerate(pattern, 1):
            workflow_steps += f"{i}. Execute `{cmd}`\n"
        if not workflow_steps:
            workflow_steps = "1. (Define workflow steps)"

        return self.TEMPLATE.format(
            name=name,
            description=description,
            title=title,
            pattern_description=pattern_description,
            activation_context=activation_context,
            workflow_steps=workflow_steps.strip(),
            confidence=confidence,
            occurrences=occurrences,
            estimated_savings=estimated_savings,
        )


def suggest_skills(
    history_dir: Optional[Path] = None,
    skills_dir: Optional[Path] = None,
    min_occurrences: int = 3,
) -> List[Dict[str, Any]]:
    """High-level function to analyze history and suggest skills.

    Args:
        history_dir: Path to history directory
        skills_dir: Path to skills directory
        min_occurrences: Minimum pattern occurrences

    Returns:
        List of skill suggestions
    """
    # Parse history
    parser = HistoryParser(history_dir=history_dir)
    history = parser.get_command_history()

    # Detect patterns
    detector = PatternDetector(min_occurrences=min_occurrences)
    patterns = detector.detect_patterns(history)

    # Generate suggestions
    suggester = SkillSuggester(skills_dir=skills_dir)
    suggestions = suggester.generate_suggestions(patterns)

    return suggestions
