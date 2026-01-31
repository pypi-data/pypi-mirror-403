"""
Skill Scorer - Post-creation quality scoring for skills.

This module scores existing skills on multiple quality dimensions
to identify improvement opportunities and rank for discovery.

Dimensions:
1. Token Efficiency (25%): Lines / information density
2. Trigger Clarity (20%): How clear is when to use
3. Completeness (20%): Covers full workflow
4. Usage Frequency (20%): How often invoked (if tracked)
5. Portability (15%): Cross-platform compatibility
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class DimensionScore:
    """Score for a single quality dimension."""

    name: str
    weight: float
    score: float  # 0.0 to 1.0
    reason: str
    recommendations: List[str] = field(default_factory=list)

    @property
    def weighted_score(self) -> float:
        """Get weighted contribution to overall score."""
        return self.score * self.weight

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "weight": self.weight,
            "score": self.score,
            "weighted_score": self.weighted_score,
            "reason": self.reason,
            "recommendations": self.recommendations,
        }


@dataclass
class SkillScore:
    """Complete quality score for a skill."""

    skill_name: str
    skill_path: Path
    overall_score: int  # 0-100
    dimensions: List[DimensionScore]
    recommendations: List[str]
    grade: str  # A, B, C, D, F

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill_name": self.skill_name,
            "skill_path": str(self.skill_path),
            "overall_score": self.overall_score,
            "grade": self.grade,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "recommendations": self.recommendations,
        }


class SkillScorer:
    """Scores skills on multiple quality dimensions."""

    # Dimension weights (must sum to 1.0)
    WEIGHTS = {
        "token_efficiency": 0.25,
        "trigger_clarity": 0.20,
        "completeness": 0.20,
        "usage_frequency": 0.20,
        "portability": 0.15,
    }

    # Trigger keywords that indicate clear invocation points
    TRIGGER_KEYWORDS = [
        "when",
        "use when",
        "trigger",
        "activated by",
        "invoke when",
        "start when",
        "run when",
    ]

    # Completeness indicators
    COMPLETENESS_SECTIONS = [
        "trigger",
        "workflow",
        "steps",
        "process",
        "example",
        "output",
    ]

    # Platform-specific patterns that reduce portability
    PLATFORM_SPECIFIC_PATTERNS = [
        r"bpsai-pair",
        r"\.paircoder",
        r"claude\s+code",
        r"Task\s+tool",
        r"subagent",
    ]

    def __init__(self, skills_dir: Path, usage_data: Optional[Dict[str, int]] = None):
        """Initialize scorer.

        Args:
            skills_dir: Path to skills directory
            usage_data: Optional dict mapping skill names to usage counts
        """
        self.skills_dir = skills_dir
        self.usage_data = usage_data or {}

    def score_skill(self, skill_name: str) -> Optional[SkillScore]:
        """Score a single skill.

        Args:
            skill_name: Name of skill to score

        Returns:
            SkillScore or None if skill not found
        """
        skill_path = self.skills_dir / skill_name / "SKILL.md"
        if not skill_path.exists():
            return None

        content = skill_path.read_text(encoding="utf-8")
        frontmatter, body = self._parse_frontmatter(content)

        # Score each dimension
        dimensions = [
            self._score_token_efficiency(content, body),
            self._score_trigger_clarity(frontmatter, body),
            self._score_completeness(body),
            self._score_usage_frequency(skill_name),
            self._score_portability(content),
        ]

        # Calculate overall score
        overall = sum(d.weighted_score for d in dimensions) * 100
        overall_score = int(min(max(overall, 0), 100))

        # Determine grade
        grade = self._calculate_grade(overall_score)

        # Collect recommendations
        recommendations = []
        for dim in dimensions:
            recommendations.extend(dim.recommendations)

        return SkillScore(
            skill_name=skill_name,
            skill_path=skill_path,
            overall_score=overall_score,
            dimensions=dimensions,
            recommendations=recommendations[:5],  # Top 5 recommendations
            grade=grade,
        )

    def score_all(self) -> List[SkillScore]:
        """Score all skills in the directory.

        Returns:
            List of SkillScore sorted by overall score
        """
        scores = []

        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                score = self.score_skill(skill_dir.name)
                if score:
                    scores.append(score)

        # Sort by overall score descending
        scores.sort(key=lambda s: s.overall_score, reverse=True)
        return scores

    def _parse_frontmatter(self, content: str) -> tuple:
        """Parse YAML frontmatter from skill content.

        Args:
            content: Full skill file content

        Returns:
            Tuple of (frontmatter_dict, body_str)
        """
        pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
        match = pattern.match(content)

        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                frontmatter = {}
            body = match.group(2).strip()
            return frontmatter, body

        return {}, content

    def _score_token_efficiency(self, content: str, body: str) -> DimensionScore:
        """Score token efficiency.

        Args:
            content: Full skill content
            body: Skill body without frontmatter

        Returns:
            DimensionScore for token efficiency
        """
        lines = content.strip().split("\n")
        total_lines = len(lines)

        # Calculate information density
        # Count headings, code blocks, and meaningful content
        headings = len(re.findall(r"^#{1,3}\s+", content, re.MULTILINE))
        code_blocks = len(re.findall(r"```", content))
        bullet_points = len(re.findall(r"^[-*]\s+", content, re.MULTILINE))

        # Information items
        info_items = headings + (code_blocks // 2) + bullet_points

        # Density = info items per 10 lines
        density = (info_items / total_lines * 10) if total_lines > 0 else 0

        # Score based on optimal range (0.5 to 2.0 density is good)
        if 0.5 <= density <= 2.0:
            score = 0.8 + (min(density, 1.5) - 0.5) * 0.2
        elif density < 0.5:
            score = density / 0.5 * 0.5
        else:
            score = 0.7  # Too dense might be hard to read

        # Penalize very long skills
        if total_lines > 300:
            score *= 0.8
        elif total_lines > 500:
            score *= 0.6

        recommendations = []
        if total_lines > 300:
            recommendations.append("Consider splitting into smaller skills")
        if density < 0.5:
            recommendations.append("Add more structure (headings, lists, code examples)")

        return DimensionScore(
            name="token_efficiency",
            weight=self.WEIGHTS["token_efficiency"],
            score=min(score, 1.0),
            reason=f"{total_lines} lines, {info_items} info items (density: {density:.2f})",
            recommendations=recommendations,
        )

    def _score_trigger_clarity(
        self, frontmatter: Dict, body: str
    ) -> DimensionScore:
        """Score trigger clarity.

        Args:
            frontmatter: Parsed frontmatter
            body: Skill body

        Returns:
            DimensionScore for trigger clarity
        """
        description = frontmatter.get("description", "")
        body_lower = body.lower()

        # Check for trigger keywords in body
        trigger_keyword_count = 0
        for keyword in self.TRIGGER_KEYWORDS:
            if keyword in body_lower:
                trigger_keyword_count += 1

        # Check for dedicated trigger section
        has_trigger_section = bool(
            re.search(r"^#{1,3}\s*(trigger|when to use)", body, re.MULTILINE | re.IGNORECASE)
        )

        # Check description contains trigger hints
        desc_has_triggers = any(
            kw in description.lower()
            for kw in ["when", "for", "helps", "guides", "use"]
        )

        # Calculate score
        score = 0.0
        if has_trigger_section:
            score += 0.5
        if trigger_keyword_count >= 2:
            score += 0.3
        elif trigger_keyword_count >= 1:
            score += 0.15
        if desc_has_triggers:
            score += 0.2

        recommendations = []
        if not has_trigger_section:
            recommendations.append("Add a 'Trigger' or 'When to Use' section")
        if not desc_has_triggers:
            recommendations.append("Include usage context in description")

        return DimensionScore(
            name="trigger_clarity",
            weight=self.WEIGHTS["trigger_clarity"],
            score=min(score, 1.0),
            reason=f"{'Has' if has_trigger_section else 'Missing'} trigger section, {trigger_keyword_count} trigger keywords",
            recommendations=recommendations,
        )

    def _score_completeness(self, body: str) -> DimensionScore:
        """Score workflow completeness.

        Args:
            body: Skill body

        Returns:
            DimensionScore for completeness
        """
        body_lower = body.lower()

        # Check for expected sections
        sections_found = 0
        for section in self.COMPLETENESS_SECTIONS:
            if section in body_lower:
                sections_found += 1

        # Check for numbered steps or checklists
        has_numbered_steps = bool(re.search(r"^\d+\.", body, re.MULTILINE))
        has_checklist = bool(re.search(r"^[-*]\s*\[[ x]\]", body, re.MULTILINE))

        # Check for code examples
        has_code = "```" in body

        # Calculate score
        section_score = sections_found / len(self.COMPLETENESS_SECTIONS)
        step_bonus = 0.2 if (has_numbered_steps or has_checklist) else 0
        code_bonus = 0.1 if has_code else 0

        score = section_score * 0.7 + step_bonus + code_bonus

        recommendations = []
        if not has_numbered_steps and not has_checklist:
            recommendations.append("Add numbered steps or checklist for workflow")
        if not has_code:
            recommendations.append("Add code examples for clarity")
        if sections_found < 3:
            recommendations.append(
                f"Add more sections (found {sections_found}/{len(self.COMPLETENESS_SECTIONS)})"
            )

        return DimensionScore(
            name="completeness",
            weight=self.WEIGHTS["completeness"],
            score=min(score, 1.0),
            reason=f"{sections_found} sections, {'has' if has_numbered_steps else 'no'} steps, {'has' if has_code else 'no'} code",
            recommendations=recommendations,
        )

    def _score_usage_frequency(self, skill_name: str) -> DimensionScore:
        """Score based on usage frequency.

        Args:
            skill_name: Name of skill

        Returns:
            DimensionScore for usage frequency
        """
        usage_count = self.usage_data.get(skill_name, 0)

        # Score based on usage
        if usage_count >= 10:
            score = 1.0
        elif usage_count >= 5:
            score = 0.8
        elif usage_count >= 2:
            score = 0.5
        elif usage_count >= 1:
            score = 0.3
        else:
            score = 0.1  # Never used gets low but not zero

        recommendations = []
        if usage_count == 0:
            recommendations.append("Skill has no recorded usage - verify triggers work")

        return DimensionScore(
            name="usage_frequency",
            weight=self.WEIGHTS["usage_frequency"],
            score=score,
            reason=f"{usage_count} recorded uses",
            recommendations=recommendations,
        )

    def _score_portability(self, content: str) -> DimensionScore:
        """Score cross-platform portability.

        Args:
            content: Full skill content

        Returns:
            DimensionScore for portability
        """
        content_lower = content.lower()

        # Check for platform-specific patterns
        platform_hits = 0
        found_patterns = []
        for pattern in self.PLATFORM_SPECIFIC_PATTERNS:
            if re.search(pattern, content_lower):
                platform_hits += 1
                found_patterns.append(pattern)

        # Calculate score (fewer hits = more portable)
        if platform_hits == 0:
            score = 1.0
        elif platform_hits == 1:
            score = 0.7
        elif platform_hits == 2:
            score = 0.4
        else:
            score = 0.2

        recommendations = []
        if platform_hits > 0:
            recommendations.append(
                f"Contains {platform_hits} platform-specific references - may not port to other tools"
            )

        return DimensionScore(
            name="portability",
            weight=self.WEIGHTS["portability"],
            score=score,
            reason=f"{platform_hits} platform-specific patterns found",
            recommendations=recommendations,
        )

    def _calculate_grade(self, score: int) -> str:
        """Calculate letter grade from score.

        Args:
            score: Overall score (0-100)

        Returns:
            Letter grade
        """
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"


def score_skills(skills_dir: Path) -> List[SkillScore]:
    """High-level function to score all skills.

    Args:
        skills_dir: Path to skills directory

    Returns:
        List of SkillScore sorted by overall score
    """
    scorer = SkillScorer(skills_dir)
    return scorer.score_all()


def format_skill_score(score: SkillScore) -> str:
    """Format skill score for CLI display.

    Args:
        score: SkillScore to format

    Returns:
        Formatted string
    """
    # Grade color
    grade_colors = {
        "A": "green",
        "B": "cyan",
        "C": "yellow",
        "D": "red",
        "F": "red",
    }
    grade_color = grade_colors.get(score.grade, "white")

    lines = [
        f"Skill: {score.skill_name}",
        "=" * 50,
        f"Overall Score: {score.overall_score}/100 (Grade: [{grade_color}]{score.grade}[/{grade_color}])",
        "",
        "Dimension Scores:",
    ]

    for dim in score.dimensions:
        score_bar = "█" * int(dim.score * 10) + "░" * (10 - int(dim.score * 10))
        weight_pct = int(dim.weight * 100)
        lines.append(f"  {dim.name:18} [{score_bar}] {dim.score:.2f} (weight: {weight_pct}%)")
        lines.append(f"    {dim.reason}")

    if score.recommendations:
        lines.extend(["", "Recommendations:"])
        for i, rec in enumerate(score.recommendations, 1):
            lines.append(f"  {i}. {rec}")

    return "\n".join(lines)


def format_score_table(scores: List[SkillScore]) -> str:
    """Format scores as a table.

    Args:
        scores: List of scores

    Returns:
        Formatted table string
    """
    lines = [
        "Skill Quality Report",
        "=" * 70,
        "",
        f"{'Skill':<30} {'Score':>6} {'Grade':>6} {'Token':>6} {'Trigger':>7} {'Complete':>8}",
        "-" * 70,
    ]

    for score in scores:
        token = next((d for d in score.dimensions if d.name == "token_efficiency"), None)
        trigger = next((d for d in score.dimensions if d.name == "trigger_clarity"), None)
        complete = next((d for d in score.dimensions if d.name == "completeness"), None)

        token_score = f"{int(token.score * 100)}" if token else "-"
        trigger_score = f"{int(trigger.score * 100)}" if trigger else "-"
        complete_score = f"{int(complete.score * 100)}" if complete else "-"

        lines.append(
            f"{score.skill_name:<30} {score.overall_score:>6} {score.grade:>6} "
            f"{token_score:>6} {trigger_score:>7} {complete_score:>8}"
        )

    lines.extend([
        "-" * 70,
        f"Total: {len(scores)} skills scored",
    ])

    return "\n".join(lines)
