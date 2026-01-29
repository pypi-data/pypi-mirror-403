"""
Subagent Gap Detector - Detects patterns that would benefit from Claude Code subagents.

This module extends the skill gap detection system to identify patterns where
subagents would be more appropriate than skills. Subagents are preferred when:
- Context isolation is needed
- A specialized persona is beneficial
- Resumable workflows are required
- Specific tool restrictions apply
- Different model capabilities are needed

Key distinction:
- Skills: Portable instructions, model-invoked, cross-platform
- Subagents: Context-isolated personas, Claude Code specific, resumable
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SubagentGap:
    """Detected pattern suggesting a subagent would be beneficial."""

    id: str
    suggested_name: str  # kebab-case, e.g., "security-reviewer"
    description: str
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 0.0  # 0.0 to 1.0

    # Subagent-specific fields
    indicators: List[str] = field(default_factory=list)  # Which indicators triggered
    suggested_tools: Optional[List[str]] = None  # Tool restrictions if any
    suggested_model: Optional[str] = None  # "opus", "sonnet", "haiku", or None
    needs_context_isolation: bool = False
    needs_resumability: bool = False
    suggested_persona: Optional[str] = None  # System prompt suggestion

    # Source patterns
    source_commands: List[str] = field(default_factory=list)
    occurrence_count: int = 0
    estimated_context_savings: Optional[int] = None  # Tokens saved by isolation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "suggested_name": self.suggested_name,
            "description": self.description,
            "detected_at": self.detected_at,
            "confidence": self.confidence,
            "indicators": self.indicators,
            "suggested_tools": self.suggested_tools,
            "suggested_model": self.suggested_model,
            "needs_context_isolation": self.needs_context_isolation,
            "needs_resumability": self.needs_resumability,
            "suggested_persona": self.suggested_persona,
            "source_commands": self.source_commands,
            "occurrence_count": self.occurrence_count,
            "estimated_context_savings": self.estimated_context_savings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubagentGap":
        """Create SubagentGap from dictionary."""
        return cls(
            id=data.get("id", ""),
            suggested_name=data.get("suggested_name", ""),
            description=data.get("description", ""),
            detected_at=data.get("detected_at", datetime.now().isoformat()),
            confidence=data.get("confidence", 0.0),
            indicators=data.get("indicators", []),
            suggested_tools=data.get("suggested_tools"),
            suggested_model=data.get("suggested_model"),
            needs_context_isolation=data.get("needs_context_isolation", False),
            needs_resumability=data.get("needs_resumability", False),
            suggested_persona=data.get("suggested_persona"),
            source_commands=data.get("source_commands", []),
            occurrence_count=data.get("occurrence_count", 0),
            estimated_context_savings=data.get("estimated_context_savings"),
        )


class SubagentGapDetector:
    """Detects patterns that suggest subagent creation."""

    # Keywords indicating persona-based work
    PERSONA_KEYWORDS = [
        "act as",
        "you are a",
        "pretend to be",
        "role of",
        "reviewer",
        "analyst",
        "expert",
        "specialist",
        "advocate",
        "critic",
        "auditor",
    ]

    # Keywords indicating context isolation need
    ISOLATION_KEYWORDS = [
        "separately",
        "in parallel",
        "don't mix",
        "fresh context",
        "new conversation",
        "isolated",
        "independent",
        "aside",
        "background",
        "concurrent",
    ]

    # Keywords indicating resumability need
    RESUMABLE_KEYWORDS = [
        "continue",
        "pick up where",
        "resume",
        "last time",
        "remember when",
        "earlier we",
        "back to",
        "follow up",
        "next session",
        "later",
    ]

    # Keywords indicating model preference
    MODEL_KEYWORDS = {
        "opus": [
            "complex",
            "difficult",
            "nuanced",
            "thorough analysis",
            "deep reasoning",
        ],
        "haiku": [
            "quick",
            "fast",
            "simple",
            "straightforward",
            "just",
            "briefly",
        ],
    }

    # Tool restriction patterns (read-only operations suggest restricted tools)
    READ_ONLY_PATTERNS = [
        "review",
        "analyze",
        "check",
        "audit",
        "inspect",
        "examine",
        "scan",
        "look at",
        "read through",
    ]

    def __init__(
        self,
        existing_subagents: Optional[List[str]] = None,
        confidence_threshold: float = 0.3,
    ):
        """Initialize detector.

        Args:
            existing_subagents: List of existing subagent names
            confidence_threshold: Minimum confidence to report a gap
        """
        self.existing_subagents = [s.lower() for s in (existing_subagents or [])]
        self.confidence_threshold = confidence_threshold

    def detect_from_history(
        self,
        history_path: Path,
        existing_subagents: Optional[List[str]] = None,
    ) -> List[SubagentGap]:
        """Analyze session history for subagent patterns.

        Args:
            history_path: Path to history directory
            existing_subagents: Override existing subagents list

        Returns:
            List of detected subagent gaps
        """
        if existing_subagents is not None:
            self.existing_subagents = [s.lower() for s in existing_subagents]

        # Load session data from history
        sessions = self._load_sessions(history_path)

        if not sessions:
            return []

        gaps: List[SubagentGap] = []

        # Detect different pattern types
        gaps.extend(self._detect_persona_patterns(sessions))
        gaps.extend(self._detect_isolation_patterns(sessions))
        gaps.extend(self._detect_resumable_patterns(sessions))
        gaps.extend(self._detect_tool_restriction_patterns(sessions))

        # Deduplicate and merge similar gaps
        gaps = self._merge_similar_gaps(gaps)

        # Filter by confidence threshold
        gaps = [g for g in gaps if g.confidence >= self.confidence_threshold]

        # Reduce confidence for overlaps with existing subagents
        for gap in gaps:
            if self._overlaps_existing(gap.suggested_name):
                gap.confidence *= 0.3
                gap.indicators.append("overlaps_existing_subagent")

        # Sort by confidence
        gaps.sort(key=lambda g: g.confidence, reverse=True)

        return gaps

    def _load_sessions(self, history_path: Path) -> List[Dict[str, Any]]:
        """Load session data from history files.

        Args:
            history_path: Path to history directory

        Returns:
            List of session entries with content and metadata
        """
        sessions = []

        if not history_path.exists():
            return sessions

        # Try to load from changes.log
        changes_log = history_path / "changes.log"
        if changes_log.exists():
            try:
                content = changes_log.read_text(encoding="utf-8")
                for line in content.strip().split("\n")[-200:]:  # Last 200 entries
                    if line:
                        sessions.append({
                            "type": "command",
                            "content": line,
                        })
            except Exception as e:
                logger.warning(f"Error reading changes log: {e}")

        # Try to load from session files
        for session_file in history_path.glob("session-*.jsonl"):
            try:
                content = session_file.read_text(encoding="utf-8")
                for line in content.strip().split("\n"):
                    if line:
                        try:
                            data = json.loads(line)
                            sessions.append(data)
                        except json.JSONDecodeError:
                            sessions.append({"type": "text", "content": line})
            except Exception as e:
                logger.warning(f"Error reading session file {session_file}: {e}")

        return sessions

    def _detect_persona_patterns(
        self, sessions: List[Dict[str, Any]]
    ) -> List[SubagentGap]:
        """Find patterns where user requested specific personas.

        Args:
            sessions: Session data

        Returns:
            List of persona-based subagent gaps
        """
        gaps = []
        persona_matches: Dict[str, List[str]] = {}

        for session in sessions:
            content = session.get("content", "").lower()

            for keyword in self.PERSONA_KEYWORDS:
                if keyword in content:
                    # Extract potential persona name
                    persona = self._extract_persona_name(content, keyword)
                    if persona:
                        if persona not in persona_matches:
                            persona_matches[persona] = []
                        persona_matches[persona].append(content[:100])

        # Create gaps for repeated personas
        for persona, occurrences in persona_matches.items():
            if len(occurrences) >= 2:
                gap_id = f"persona-{persona.replace(' ', '-')}"
                confidence = self._calculate_confidence(
                    indicators=["persona_request"],
                    occurrences=len(occurrences),
                )

                gaps.append(SubagentGap(
                    id=gap_id,
                    suggested_name=self._to_kebab_case(persona),
                    description=f"Specialized {persona} for focused analysis",
                    confidence=confidence,
                    indicators=["persona_request"],
                    suggested_persona=f"You are a {persona}. Focus on...",
                    source_commands=occurrences[:5],
                    occurrence_count=len(occurrences),
                    needs_context_isolation=True,
                ))

        return gaps

    def _detect_isolation_patterns(
        self, sessions: List[Dict[str, Any]]
    ) -> List[SubagentGap]:
        """Find patterns where context isolation would help.

        Args:
            sessions: Session data

        Returns:
            List of isolation-based subagent gaps
        """
        gaps = []
        isolation_matches: List[str] = []

        for session in sessions:
            content = session.get("content", "").lower()

            for keyword in self.ISOLATION_KEYWORDS:
                if keyword in content:
                    isolation_matches.append(content[:100])
                    break

        if len(isolation_matches) >= 2:
            confidence = self._calculate_confidence(
                indicators=["context_isolation"],
                occurrences=len(isolation_matches),
            )

            gaps.append(SubagentGap(
                id="context-isolated-worker",
                suggested_name="isolated-analyzer",
                description="Context-isolated worker for parallel analysis",
                confidence=confidence,
                indicators=["context_isolation_requested"],
                needs_context_isolation=True,
                source_commands=isolation_matches[:5],
                occurrence_count=len(isolation_matches),
                estimated_context_savings=5000,  # Rough estimate
            ))

        return gaps

    def _detect_resumable_patterns(
        self, sessions: List[Dict[str, Any]]
    ) -> List[SubagentGap]:
        """Find patterns where resumability is needed.

        Args:
            sessions: Session data

        Returns:
            List of resumability-based subagent gaps
        """
        gaps = []
        resume_matches: List[str] = []

        for session in sessions:
            content = session.get("content", "").lower()

            for keyword in self.RESUMABLE_KEYWORDS:
                if keyword in content:
                    resume_matches.append(content[:100])
                    break

        if len(resume_matches) >= 2:
            confidence = self._calculate_confidence(
                indicators=["resumability"],
                occurrences=len(resume_matches),
            )

            gaps.append(SubagentGap(
                id="resumable-task-worker",
                suggested_name="persistent-task-handler",
                description="Resumable worker for multi-session tasks",
                confidence=confidence,
                indicators=["resumability_requested"],
                needs_resumability=True,
                source_commands=resume_matches[:5],
                occurrence_count=len(resume_matches),
            ))

        return gaps

    def _detect_tool_restriction_patterns(
        self, sessions: List[Dict[str, Any]]
    ) -> List[SubagentGap]:
        """Find patterns with consistent tool subsets.

        Args:
            sessions: Session data

        Returns:
            List of tool-restriction-based subagent gaps
        """
        gaps = []
        read_only_matches: List[str] = []

        for session in sessions:
            content = session.get("content", "").lower()

            for pattern in self.READ_ONLY_PATTERNS:
                if pattern in content:
                    read_only_matches.append(content[:100])
                    break

        if len(read_only_matches) >= 3:
            confidence = self._calculate_confidence(
                indicators=["tool_restriction"],
                occurrences=len(read_only_matches),
            )

            gaps.append(SubagentGap(
                id="read-only-reviewer",
                suggested_name="code-reviewer",
                description="Read-only reviewer that cannot modify files",
                confidence=confidence,
                indicators=["read_only_pattern"],
                suggested_tools=["Read", "Grep", "Glob", "Bash"],
                needs_context_isolation=True,
                source_commands=read_only_matches[:5],
                occurrence_count=len(read_only_matches),
            ))

        return gaps

    def _extract_persona_name(self, content: str, keyword: str) -> Optional[str]:
        """Extract persona name from content near keyword.

        Args:
            content: Text content
            keyword: Matched keyword

        Returns:
            Extracted persona name or None
        """
        # Find text after the keyword
        idx = content.find(keyword)
        if idx == -1:
            return None

        after = content[idx + len(keyword):].strip()

        # Extract words that form the persona
        words = re.findall(r"[a-z]+", after[:50])
        if not words:
            return None

        # Take first 2-3 meaningful words
        persona_words = []
        for word in words[:3]:
            if word not in {"a", "an", "the", "and", "or", "for", "to", "be"}:
                persona_words.append(word)
            if len(persona_words) >= 2:
                break

        if persona_words:
            return " ".join(persona_words)
        return None

    def _to_kebab_case(self, text: str) -> str:
        """Convert text to kebab-case.

        Args:
            text: Input text

        Returns:
            Kebab-case version
        """
        # Replace spaces and underscores with hyphens
        result = re.sub(r"[\s_]+", "-", text.lower())
        # Remove non-alphanumeric except hyphens
        result = re.sub(r"[^a-z0-9-]", "", result)
        # Remove multiple consecutive hyphens
        result = re.sub(r"-+", "-", result)
        return result.strip("-")

    def _calculate_confidence(
        self,
        indicators: List[str],
        occurrences: int,
    ) -> float:
        """Calculate confidence score for a gap.

        Args:
            indicators: List of detected indicators
            occurrences: Number of pattern occurrences

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Base confidence from indicators
        # Single indicator: 0.3-0.5
        # Two indicators: 0.5-0.7
        # Three+ indicators: 0.7-0.9
        indicator_score = min(len(indicators) * 0.2 + 0.2, 0.6)

        # Occurrence bonus
        occurrence_score = min(occurrences / 10, 0.3)

        return min(indicator_score + occurrence_score, 0.95)

    def _overlaps_existing(self, name: str) -> bool:
        """Check if name overlaps with existing subagent.

        Args:
            name: Proposed subagent name

        Returns:
            True if overlaps with existing
        """
        name_words = set(name.lower().split("-"))

        for existing in self.existing_subagents:
            existing_words = set(existing.split("-"))
            if name_words & existing_words:
                return True

        return False

    def _merge_similar_gaps(self, gaps: List[SubagentGap]) -> List[SubagentGap]:
        """Merge gaps with similar names.

        Args:
            gaps: List of gaps

        Returns:
            Deduplicated list
        """
        if not gaps:
            return gaps

        merged: Dict[str, SubagentGap] = {}

        for gap in gaps:
            key = gap.suggested_name

            if key in merged:
                # Merge: keep higher confidence, combine indicators
                existing = merged[key]
                if gap.confidence > existing.confidence:
                    existing.confidence = gap.confidence
                existing.indicators = list(set(existing.indicators + gap.indicators))
                existing.occurrence_count += gap.occurrence_count
                existing.source_commands.extend(gap.source_commands[:3])
            else:
                merged[key] = gap

        return list(merged.values())


class SubagentGapPersistence:
    """Handles persisting detected subagent gaps to history."""

    def __init__(self, history_dir: Path):
        """Initialize persistence.

        Args:
            history_dir: Path to history directory
        """
        self.history_dir = history_dir
        self.gap_file = history_dir / "subagent-gaps.jsonl" if history_dir else None

    def save_gap(self, gap: SubagentGap) -> None:
        """Save a gap to history.

        Args:
            gap: Gap to save
        """
        if not self.gap_file:
            return

        self.history_dir.mkdir(parents=True, exist_ok=True)

        # Load existing gaps to check for duplicates
        existing_gaps = self.load_gaps()

        # Check for duplicate (same id)
        updated = False
        for i, existing in enumerate(existing_gaps):
            if existing.id == gap.id:
                # Update with higher confidence
                if gap.confidence > existing.confidence:
                    existing_gaps[i] = gap
                updated = True
                break

        if not updated:
            existing_gaps.append(gap)

        # Write all gaps
        with open(self.gap_file, "w", encoding="utf-8") as f:
            for g in existing_gaps:
                f.write(json.dumps(g.to_dict()) + "\n")

    def load_gaps(self) -> List[SubagentGap]:
        """Load gaps from history.

        Returns:
            List of subagent gaps
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
                        gaps.append(SubagentGap.from_dict(data))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.warning(f"Error loading subagent gaps: {e}")

        return gaps

    def clear_gaps(self) -> None:
        """Clear all gaps from history."""
        if self.gap_file and self.gap_file.exists():
            self.gap_file.write_text("", encoding="utf-8")


def detect_subagent_gaps(
    history_dir: Path,
    subagents_dir: Optional[Path] = None,
) -> List[SubagentGap]:
    """High-level function to detect subagent gaps from history.

    Args:
        history_dir: Path to history directory
        subagents_dir: Path to subagents directory for overlap detection

    Returns:
        List of detected subagent gaps
    """
    # Get existing subagent names
    existing_subagents = []
    if subagents_dir and subagents_dir.exists():
        for agent_file in subagents_dir.glob("*.md"):
            existing_subagents.append(agent_file.stem)

    # Also check .claude/agents/ if it exists
    claude_agents = history_dir.parent.parent / ".claude" / "agents"
    if claude_agents.exists():
        for agent_file in claude_agents.glob("*.md"):
            existing_subagents.append(agent_file.stem)

    detector = SubagentGapDetector(existing_subagents=existing_subagents)
    return detector.detect_from_history(history_dir)


def format_subagent_gap_notification(gap: SubagentGap) -> str:
    """Format a subagent gap notification message.

    Args:
        gap: The subagent gap

    Returns:
        Formatted notification string
    """
    lines = [
        "Subagent Gap Detected",
        "",
        f"Pattern suggests a '{gap.suggested_name}' subagent:",
    ]

    if gap.indicators:
        lines.append(f"  Indicators: {', '.join(gap.indicators)}")

    if gap.suggested_persona:
        lines.append(f"  Persona: {gap.suggested_persona[:50]}...")

    if gap.suggested_tools:
        lines.append(f"  Tools: {', '.join(gap.suggested_tools)}")

    if gap.suggested_model:
        lines.append(f"  Model: {gap.suggested_model}")

    lines.extend([
        "",
        "Would you like to create this subagent?",
        f"Confidence: {gap.confidence:.0%}",
    ])

    if gap.estimated_context_savings:
        lines.append(f"Est. context savings: ~{gap.estimated_context_savings} tokens")

    return "\n".join(lines)
