"""
Unified Gap Classifier - Classifies gaps as skills, subagents, or ambiguous.

This module provides classification logic to determine whether detected
gaps should become skills, subagents, or both. It uses a scoring system
based on multiple factors:

- Portability: Higher = skill (cross-platform value)
- Isolation: Higher = subagent (context separation needed)
- Persona: Higher = subagent (specialized role/voice)
- Resumability: Higher = subagent (multi-session state)
- Simplicity: Higher = skill (simple command sequences)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .gap_detector import SkillGap
from .subagent_detector import SubagentGap


class GapType(Enum):
    """Classification result for a gap."""

    SKILL = "skill"
    SUBAGENT = "subagent"
    AMBIGUOUS = "ambiguous"  # Could be either, user decides


@dataclass
class ClassificationScores:
    """Scores used for gap classification."""

    portability: float = 0.0  # Higher = skill
    isolation: float = 0.0  # Higher = subagent
    persona: float = 0.0  # Higher = subagent
    resumability: float = 0.0  # Higher = subagent
    simplicity: float = 0.0  # Higher = skill


@dataclass
class SkillRecommendation:
    """Skill-specific recommendation details."""

    suggested_name: str  # gerund form
    allowed_tools: Optional[List[str]] = None
    estimated_portability: List[str] = field(
        default_factory=lambda: ["claude-code", "cursor", "continue"]
    )


@dataclass
class SubagentRecommendation:
    """Subagent-specific recommendation details."""

    suggested_name: str  # kebab-case
    suggested_model: Optional[str] = None
    suggested_tools: Optional[List[str]] = None
    persona_hint: Optional[str] = None


@dataclass
class ClassifiedGap:
    """A gap that has been classified as skill, subagent, or ambiguous."""

    id: str
    gap_type: GapType
    confidence: float
    reasoning: str  # Human-readable explanation

    # Original gap data
    suggested_name: str
    description: str
    source_commands: List[str] = field(default_factory=list)
    occurrence_count: int = 0

    # Classification factors (scores 0-1)
    portability_score: float = 0.0
    isolation_score: float = 0.0
    persona_score: float = 0.0
    resumability_score: float = 0.0
    simplicity_score: float = 0.0

    # Recommendations
    skill_recommendation: Optional[SkillRecommendation] = None
    subagent_recommendation: Optional[SubagentRecommendation] = None

    # Metadata
    classified_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "gap_type": self.gap_type.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "suggested_name": self.suggested_name,
            "description": self.description,
            "source_commands": self.source_commands,
            "occurrence_count": self.occurrence_count,
            "scores": {
                "portability": self.portability_score,
                "isolation": self.isolation_score,
                "persona": self.persona_score,
                "resumability": self.resumability_score,
                "simplicity": self.simplicity_score,
            },
            "classified_at": self.classified_at,
        }

        if self.skill_recommendation:
            result["skill_recommendation"] = {
                "suggested_name": self.skill_recommendation.suggested_name,
                "allowed_tools": self.skill_recommendation.allowed_tools,
                "estimated_portability": self.skill_recommendation.estimated_portability,
            }

        if self.subagent_recommendation:
            result["subagent_recommendation"] = {
                "suggested_name": self.subagent_recommendation.suggested_name,
                "suggested_model": self.subagent_recommendation.suggested_model,
                "suggested_tools": self.subagent_recommendation.suggested_tools,
                "persona_hint": self.subagent_recommendation.persona_hint,
            }

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClassifiedGap":
        """Create ClassifiedGap from dictionary."""
        scores = data.get("scores", {})

        skill_rec = None
        if "skill_recommendation" in data:
            rec = data["skill_recommendation"]
            skill_rec = SkillRecommendation(
                suggested_name=rec.get("suggested_name", ""),
                allowed_tools=rec.get("allowed_tools"),
                estimated_portability=rec.get(
                    "estimated_portability", ["claude-code"]
                ),
            )

        subagent_rec = None
        if "subagent_recommendation" in data:
            rec = data["subagent_recommendation"]
            subagent_rec = SubagentRecommendation(
                suggested_name=rec.get("suggested_name", ""),
                suggested_model=rec.get("suggested_model"),
                suggested_tools=rec.get("suggested_tools"),
                persona_hint=rec.get("persona_hint"),
            )

        return cls(
            id=data.get("id", ""),
            gap_type=GapType(data.get("gap_type", "skill")),
            confidence=data.get("confidence", 0.0),
            reasoning=data.get("reasoning", ""),
            suggested_name=data.get("suggested_name", ""),
            description=data.get("description", ""),
            source_commands=data.get("source_commands", []),
            occurrence_count=data.get("occurrence_count", 0),
            portability_score=scores.get("portability", 0.0),
            isolation_score=scores.get("isolation", 0.0),
            persona_score=scores.get("persona", 0.0),
            resumability_score=scores.get("resumability", 0.0),
            simplicity_score=scores.get("simplicity", 0.0),
            skill_recommendation=skill_rec,
            subagent_recommendation=subagent_rec,
            classified_at=data.get("classified_at", datetime.now().isoformat()),
        )


@dataclass
class AllGaps:
    """Container for both skill and subagent gaps."""

    skills: List[SkillGap] = field(default_factory=list)
    subagents: List[SubagentGap] = field(default_factory=list)


class GapClassifier:
    """Classifies gaps as skills, subagents, or ambiguous."""

    # Thresholds for classification
    SKILL_THRESHOLD = 0.6  # Above this = likely skill
    SUBAGENT_THRESHOLD = 0.6  # Above this = likely subagent
    AMBIGUOUS_MARGIN = 0.2  # If within margin, mark ambiguous

    # Keywords indicating portability value
    PORTABLE_KEYWORDS = [
        "format",
        "lint",
        "test",
        "build",
        "deploy",
        "commit",
        "review",
        "document",
    ]

    def __init__(
        self,
        existing_skills: Optional[List[str]] = None,
        existing_subagents: Optional[List[str]] = None,
    ):
        """Initialize classifier.

        Args:
            existing_skills: List of existing skill names
            existing_subagents: List of existing subagent names
        """
        self.existing_skills = [s.lower() for s in (existing_skills or [])]
        self.existing_subagents = [s.lower() for s in (existing_subagents or [])]

    def classify(self, gap: Union[SkillGap, SubagentGap]) -> ClassifiedGap:
        """Classify a single gap.

        Args:
            gap: Either a SkillGap or SubagentGap

        Returns:
            ClassifiedGap with type determination and recommendations
        """
        scores = self._calculate_scores(gap)
        gap_type = self._determine_type(scores)
        confidence = self._calculate_confidence(scores, gap_type)
        reasoning = self._generate_reasoning(gap, scores, gap_type)

        # Extract common fields
        if isinstance(gap, SkillGap):
            gap_id = f"skill-{gap.suggested_name}"
            description = f"Pattern: {' → '.join(gap.pattern[:3])}"
            source_commands = gap.pattern
            occurrence_count = gap.frequency
        else:
            gap_id = gap.id
            description = gap.description
            source_commands = gap.source_commands
            occurrence_count = gap.occurrence_count

        # Build recommendations
        skill_rec = None
        subagent_rec = None

        if gap_type in [GapType.SKILL, GapType.AMBIGUOUS]:
            skill_rec = self._build_skill_recommendation(gap, scores)

        if gap_type in [GapType.SUBAGENT, GapType.AMBIGUOUS]:
            subagent_rec = self._build_subagent_recommendation(gap, scores)

        return ClassifiedGap(
            id=gap_id,
            gap_type=gap_type,
            confidence=confidence,
            reasoning=reasoning,
            suggested_name=gap.suggested_name,
            description=description,
            source_commands=source_commands,
            occurrence_count=occurrence_count,
            portability_score=scores.portability,
            isolation_score=scores.isolation,
            persona_score=scores.persona,
            resumability_score=scores.resumability,
            simplicity_score=scores.simplicity,
            skill_recommendation=skill_rec,
            subagent_recommendation=subagent_rec,
        )

    def classify_all(self, gaps: AllGaps) -> List[ClassifiedGap]:
        """Classify all detected gaps, deduplicating overlaps.

        Args:
            gaps: Container with skill and subagent gaps

        Returns:
            List of classified gaps
        """
        # Merge overlapping gaps
        merged = self._merge_overlapping_gaps(gaps)

        # Classify each
        classified = [self.classify(g) for g in merged]

        # Sort by confidence descending
        classified.sort(key=lambda g: g.confidence, reverse=True)

        return classified

    def _calculate_scores(
        self, gap: Union[SkillGap, SubagentGap]
    ) -> ClassificationScores:
        """Calculate factor scores for classification.

        Args:
            gap: The gap to score

        Returns:
            ClassificationScores with all factors
        """
        scores = ClassificationScores()

        if isinstance(gap, SkillGap):
            # Skill gaps lean toward skills by default
            scores.portability = 0.7
            scores.simplicity = 0.6

            # Check for portable keywords in pattern
            pattern_str = " ".join(gap.pattern).lower()
            for keyword in self.PORTABLE_KEYWORDS:
                if keyword in pattern_str:
                    scores.portability = min(scores.portability + 0.1, 0.95)

            # Shorter patterns are simpler
            if len(gap.pattern) <= 2:
                scores.simplicity = 0.8
            elif len(gap.pattern) >= 5:
                scores.simplicity = 0.4

        else:
            # SubagentGap has explicit indicators
            if gap.needs_context_isolation:
                scores.isolation = 0.8

            if gap.needs_resumability:
                scores.resumability = 0.8

            if gap.suggested_persona:
                scores.persona = 0.8

            if "persona_request" in gap.indicators:
                scores.persona = max(scores.persona, 0.7)

            if "context_isolation" in gap.indicators:
                scores.isolation = max(scores.isolation, 0.7)

            if "resumability" in gap.indicators:
                scores.resumability = max(scores.resumability, 0.7)

            if gap.suggested_tools:
                # Tool restrictions don't necessarily mean subagent
                # Could be skill with allowed-tools
                if len(gap.suggested_tools) <= 3:
                    scores.portability = 0.5
                else:
                    scores.isolation = 0.5

        return scores

    def _determine_type(self, scores: ClassificationScores) -> GapType:
        """Determine gap type from scores.

        Args:
            scores: Classification scores

        Returns:
            GapType classification
        """
        # Calculate aggregate scores
        skill_score = (scores.portability + scores.simplicity) / 2
        subagent_score = (scores.isolation + scores.persona + scores.resumability) / 3

        # Handle edge case where both are near zero
        if skill_score < 0.2 and subagent_score < 0.2:
            return GapType.SKILL  # Default to skill

        # Check for ambiguity
        if abs(skill_score - subagent_score) < self.AMBIGUOUS_MARGIN:
            return GapType.AMBIGUOUS
        elif skill_score > subagent_score:
            return GapType.SKILL
        else:
            return GapType.SUBAGENT

    def _calculate_confidence(
        self, scores: ClassificationScores, gap_type: GapType
    ) -> float:
        """Calculate confidence in the classification.

        Args:
            scores: Classification scores
            gap_type: Determined type

        Returns:
            Confidence score (0.0 to 1.0)
        """
        skill_score = (scores.portability + scores.simplicity) / 2
        subagent_score = (scores.isolation + scores.persona + scores.resumability) / 3

        if gap_type == GapType.SKILL:
            return min(skill_score + 0.2, 0.95)
        elif gap_type == GapType.SUBAGENT:
            return min(subagent_score + 0.2, 0.95)
        else:
            # Ambiguous - lower confidence
            return max(skill_score, subagent_score) * 0.7

    def _generate_reasoning(
        self,
        gap: Union[SkillGap, SubagentGap],
        scores: ClassificationScores,
        gap_type: GapType,
    ) -> str:
        """Generate human-readable reasoning for classification.

        Args:
            gap: The gap being classified
            scores: Classification scores
            gap_type: Determined type

        Returns:
            Human-readable explanation
        """
        reasons = []

        if scores.portability > 0.5:
            reasons.append("Pattern would be useful across different AI tools")

        if scores.isolation > 0.5:
            reasons.append("Pattern benefits from separate context window")

        if scores.persona > 0.5:
            reasons.append("Pattern involves specialized persona or role")

        if scores.resumability > 0.5:
            reasons.append("Pattern needs state preservation across sessions")

        if scores.simplicity > 0.7:
            reasons.append("Pattern is a simple, repeatable command sequence")

        if not reasons:
            reasons.append("Default classification based on pattern structure")

        type_label = gap_type.value.upper()
        return f"Classified as {type_label}: " + "; ".join(reasons)

    def _build_skill_recommendation(
        self, gap: Union[SkillGap, SubagentGap], scores: ClassificationScores
    ) -> SkillRecommendation:
        """Build skill recommendation.

        Args:
            gap: The gap
            scores: Classification scores

        Returns:
            SkillRecommendation
        """
        # Convert to gerund form if needed
        name = gap.suggested_name
        if not any(name.startswith(v) for v in ["managing", "testing", "reviewing"]):
            # Already in gerund form or close enough
            pass

        # Determine allowed tools if applicable
        allowed_tools = None
        if isinstance(gap, SubagentGap) and gap.suggested_tools:
            allowed_tools = gap.suggested_tools

        # Estimate portability
        portability = ["claude-code"]
        if scores.portability > 0.6:
            portability.extend(["cursor", "continue", "windsurf"])

        return SkillRecommendation(
            suggested_name=name,
            allowed_tools=allowed_tools,
            estimated_portability=portability,
        )

    def _build_subagent_recommendation(
        self, gap: Union[SkillGap, SubagentGap], scores: ClassificationScores
    ) -> SubagentRecommendation:
        """Build subagent recommendation.

        Args:
            gap: The gap
            scores: Classification scores

        Returns:
            SubagentRecommendation
        """
        suggested_model = None
        suggested_tools = None
        persona_hint = None

        if isinstance(gap, SubagentGap):
            suggested_model = gap.suggested_model
            suggested_tools = gap.suggested_tools
            persona_hint = gap.suggested_persona

        # Default model based on complexity
        if not suggested_model:
            if scores.persona > 0.7 or scores.isolation > 0.7:
                suggested_model = "sonnet"  # Good balance

        return SubagentRecommendation(
            suggested_name=gap.suggested_name,
            suggested_model=suggested_model,
            suggested_tools=suggested_tools,
            persona_hint=persona_hint,
        )

    def _merge_overlapping_gaps(
        self, gaps: AllGaps
    ) -> List[Union[SkillGap, SubagentGap]]:
        """Merge overlapping skill and subagent gaps.

        Args:
            gaps: Container with both gap types

        Returns:
            Deduplicated list
        """
        merged: Dict[str, Union[SkillGap, SubagentGap]] = {}

        # Add skill gaps
        for gap in gaps.skills:
            key = gap.suggested_name.lower()
            if key not in merged:
                merged[key] = gap
            elif gap.confidence > merged[key].confidence:
                merged[key] = gap

        # Add subagent gaps, preferring them over skills for overlaps
        for gap in gaps.subagents:
            key = gap.suggested_name.lower()
            if key not in merged:
                merged[key] = gap
            elif isinstance(merged[key], SkillGap):
                # SubagentGap has more specific info, prefer it
                merged[key] = gap
            elif gap.confidence > merged[key].confidence:
                merged[key] = gap

        return list(merged.values())


def detect_and_classify_all(
    history_dir: Path,
    skills_dir: Optional[Path] = None,
    subagents_dir: Optional[Path] = None,
) -> List[ClassifiedGap]:
    """Detect and classify all gaps from history.

    High-level function that runs both skill and subagent detection,
    then classifies all results.

    Args:
        history_dir: Path to history directory
        skills_dir: Path to skills directory
        subagents_dir: Path to subagents directory

    Returns:
        List of classified gaps
    """
    from .gap_detector import detect_gaps_from_history
    from .subagent_detector import detect_subagent_gaps

    # Detect gaps
    skill_gaps = detect_gaps_from_history(history_dir, skills_dir)
    subagent_gaps = detect_subagent_gaps(history_dir, subagents_dir)

    # Get existing names
    existing_skills = []
    if skills_dir and skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                existing_skills.append(skill_dir.name)

    existing_subagents = []
    if subagents_dir and subagents_dir.exists():
        for agent_file in subagents_dir.glob("*.md"):
            existing_subagents.append(agent_file.stem)

    # Also check .claude/agents/
    claude_agents = history_dir.parent.parent / ".claude" / "agents"
    if claude_agents.exists():
        for agent_file in claude_agents.glob("*.md"):
            existing_subagents.append(agent_file.stem)

    # Classify
    classifier = GapClassifier(
        existing_skills=existing_skills,
        existing_subagents=existing_subagents,
    )

    all_gaps = AllGaps(skills=skill_gaps, subagents=subagent_gaps)
    return classifier.classify_all(all_gaps)


def format_classification_report(gaps: List[ClassifiedGap]) -> str:
    """Format a classification report.

    Args:
        gaps: List of classified gaps

    Returns:
        Formatted report string
    """
    if not gaps:
        return "No gaps detected."

    lines = [
        "Gap Classification Report",
        "=" * 40,
        "",
    ]

    # Group by type
    skills = [g for g in gaps if g.gap_type == GapType.SKILL]
    subagents = [g for g in gaps if g.gap_type == GapType.SUBAGENT]
    ambiguous = [g for g in gaps if g.gap_type == GapType.AMBIGUOUS]

    if skills:
        lines.append(f"SKILLS ({len(skills)}):")
        for gap in skills:
            lines.append(f"  - {gap.suggested_name} ({gap.confidence:.0%})")
        lines.append("")

    if subagents:
        lines.append(f"SUBAGENTS ({len(subagents)}):")
        for gap in subagents:
            lines.append(f"  - {gap.suggested_name} ({gap.confidence:.0%})")
        lines.append("")

    if ambiguous:
        lines.append(f"AMBIGUOUS ({len(ambiguous)}):")
        for gap in ambiguous:
            lines.append(f"  - {gap.suggested_name} ({gap.confidence:.0%})")
            lines.append("    (Could be skill or subagent - user decision needed)")
        lines.append("")

    lines.append(f"Total: {len(gaps)} gaps classified")

    return "\n".join(lines)
