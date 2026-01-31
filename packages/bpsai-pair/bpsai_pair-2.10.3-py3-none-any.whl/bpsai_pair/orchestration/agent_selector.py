"""
Agent Selection Logic for Multi-Agent Orchestration.

Routes tasks to appropriate specialized agents based on:
- Task type (design, review, implement, etc.)
- Task tags (security, auth, etc.)
- Complexity level
- Agent capabilities from .claude/agents/

Selection rules:
- Design/plan tasks -> planner agent
- Review/PR tasks -> reviewer agent
- Security/auth tasks -> security agent
- High complexity -> claude-code (full agent)
- Default -> claude-code
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .invoker import AgentDefinition, AgentInvoker

logger = logging.getLogger(__name__)

# Default agent when no specialized agent matches
DEFAULT_AGENT = "claude-code"

# Keywords for routing
DESIGN_KEYWORDS = ["design", "plan", "architecture", "architect", "proposal"]
REVIEW_KEYWORDS = ["review", "pr", "check", "audit", "inspect"]
SECURITY_KEYWORDS = ["security", "auth", "credential", "token", "secret", "password"]
SECURITY_TAGS = ["security", "auth", "authentication", "authorization"]


@dataclass
class AgentMatch:
    """
    Result of agent selection with scoring details.

    Attributes:
        agent_name: Name of the selected agent
        score: Confidence score (0.0 to 1.0)
        reasons: List of reasons for selection
        permission_mode: Permission mode for the agent
    """

    agent_name: str
    score: float
    reasons: list[str] = field(default_factory=list)
    permission_mode: str = "auto"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "score": self.score,
            "reasons": self.reasons,
            "permission_mode": self.permission_mode,
        }


@dataclass
class SelectionCriteria:
    """
    Criteria for agent selection.

    Can be created directly or from TaskCharacteristics.
    Automatically detects requirements from title and tags.
    """

    task_type: str = ""
    task_title: str = ""
    task_tags: list[str] = field(default_factory=list)
    complexity: int = 50  # 0-100 scale
    requires_review: bool = False
    requires_security: bool = False
    preferred_agent: Optional[str] = None

    def __post_init__(self):
        """Auto-detect requirements from title and tags."""
        title_lower = self.task_title.lower()
        tags_lower = [t.lower() for t in self.task_tags]

        # Detect review requirement
        if not self.requires_review:
            if any(kw in title_lower for kw in REVIEW_KEYWORDS):
                self.requires_review = True
            if "review" in tags_lower:
                self.requires_review = True

        # Detect security requirement
        if not self.requires_security:
            if any(kw in title_lower for kw in SECURITY_KEYWORDS):
                self.requires_security = True
            if any(tag in tags_lower for tag in SECURITY_TAGS):
                self.requires_security = True

    @classmethod
    def from_task_characteristics(
        cls,
        task: Any,  # TaskCharacteristics
        task_title: str = "",
        task_tags: Optional[list[str]] = None,
    ) -> "SelectionCriteria":
        """
        Create from TaskCharacteristics.

        Args:
            task: TaskCharacteristics from orchestrator
            task_title: Task title for keyword matching
            task_tags: Task tags for routing

        Returns:
            SelectionCriteria for agent selection
        """
        # Map TaskComplexity to numeric
        complexity_map = {
            "LOW": 25,
            "MEDIUM": 50,
            "HIGH": 75,
        }

        return cls(
            task_type=task.task_type.value.upper() if hasattr(task.task_type, "value") else str(task.task_type),
            task_title=task_title or task.description[:100] if hasattr(task, "description") else "",
            task_tags=task_tags or [],
            complexity=complexity_map.get(
                task.complexity.value.upper() if hasattr(task.complexity, "value") else "MEDIUM",
                50,
            ),
            requires_review=task.task_type.value.upper() == "REVIEW" if hasattr(task.task_type, "value") else False,
        )


class AgentSelector:
    """
    Selects the best agent for a task based on criteria.

    Loads available agents from .claude/agents/ and scores
    each against the selection criteria.

    Example:
        >>> selector = AgentSelector()
        >>> criteria = SelectionCriteria(
        ...     task_type="design",
        ...     task_title="Design auth system",
        ... )
        >>> match = selector.select(criteria)
        >>> print(f"Selected: {match.agent_name} (score: {match.score})")
    """

    def __init__(
        self,
        agents_dir: Optional[Path] = None,
        working_dir: Optional[Path] = None,
    ):
        """
        Initialize the agent selector.

        Args:
            agents_dir: Directory containing agent definitions
            working_dir: Working directory for agent invocation
        """
        self.agents_dir = agents_dir or Path(".claude/agents")
        self.working_dir = working_dir or Path.cwd()
        self._agents: dict[str, AgentDefinition] = {}
        self._load_agents()

    def _load_agents(self) -> None:
        """Load available agent definitions."""
        if not self.agents_dir.is_absolute():
            full_path = self.working_dir / self.agents_dir
        else:
            full_path = self.agents_dir

        if not full_path.exists():
            logger.warning(f"Agents directory not found: {full_path}")
            return

        invoker = AgentInvoker(
            agents_dir=full_path,
            working_dir=self.working_dir,
        )

        try:
            agents = invoker.list_agents()
            for agent in agents:
                self._agents[agent.name] = agent
        except Exception as e:
            logger.warning(f"Failed to load agents: {e}")

    @property
    def available_agents(self) -> list[str]:
        """Get list of available agent names."""
        return list(self._agents.keys())

    def get_available_agents(self) -> list[str]:
        """Get list of available agent names."""
        return self.available_agents

    def select(self, criteria: SelectionCriteria) -> AgentMatch:
        """
        Select the best agent for the given criteria.

        Selection priority:
        1. Explicitly requested agent
        2. Security agent for security/auth tasks
        3. Reviewer agent for review/PR tasks
        4. Planner agent for design/plan tasks
        5. Claude-code for high complexity
        6. Default agent

        Args:
            criteria: Selection criteria

        Returns:
            AgentMatch with selected agent and reasoning
        """
        # Check for explicitly requested agent
        if criteria.preferred_agent:
            if criteria.preferred_agent in self._agents:
                agent_def = self._agents[criteria.preferred_agent]
                return AgentMatch(
                    agent_name=criteria.preferred_agent,
                    score=1.0,
                    reasons=["Explicitly requested"],
                    permission_mode=agent_def.permission_mode,
                )
            else:
                # Fall back if requested agent not available
                logger.warning(f"Requested agent not found: {criteria.preferred_agent}")

        # Get all matches and select the best
        matches = self.get_all_matches(criteria)

        if matches:
            return matches[0]

        # Fallback to default
        return AgentMatch(
            agent_name=DEFAULT_AGENT,
            score=0.1,
            reasons=["Fallback to default agent"],
            permission_mode="auto",
        )

    def get_all_matches(self, criteria: SelectionCriteria) -> list[AgentMatch]:
        """
        Get all agents scored against criteria.

        Args:
            criteria: Selection criteria

        Returns:
            List of AgentMatch sorted by score descending
        """
        matches: list[AgentMatch] = []
        title_lower = criteria.task_title.lower()
        type_lower = criteria.task_type.lower()

        for agent_name, agent_def in self._agents.items():
            score = 0.0
            reasons = []

            # Check for security match
            if agent_name == "security":
                if criteria.requires_security:
                    score += 0.5
                    reasons.append("Task requires security review")
                if any(kw in title_lower for kw in SECURITY_KEYWORDS):
                    score += 0.3
                    reasons.append("Security keyword in title")
                if any(tag.lower() in SECURITY_TAGS for tag in criteria.task_tags):
                    score += 0.2
                    reasons.append("Security tag present")

            # Check for reviewer match
            if agent_name == "reviewer":
                if criteria.requires_review:
                    score += 0.5
                    reasons.append("Task requires review")
                if type_lower == "review":
                    score += 0.3
                    reasons.append("Task type is review")
                if any(kw in title_lower for kw in REVIEW_KEYWORDS):
                    score += 0.2
                    reasons.append("Review keyword in title")

            # Check for planner match
            if agent_name == "planner":
                if type_lower == "design":
                    score += 0.5
                    reasons.append("Task type is design")
                if any(kw in title_lower for kw in DESIGN_KEYWORDS):
                    score += 0.3
                    reasons.append("Design keyword in title")

            # Check description match
            desc_lower = agent_def.description.lower() if agent_def.description else ""
            if type_lower and type_lower in desc_lower:
                score += 0.1
                reasons.append(f"Agent description matches '{type_lower}'")

            # Complexity adjustment
            if criteria.complexity > 60:
                # High complexity prefers more capable agents
                if agent_name in ["planner", "claude-code"]:
                    score += 0.1
                    reasons.append("Agent suitable for high complexity")

            # Only add if we have reasons (agent is relevant)
            if reasons:
                matches.append(AgentMatch(
                    agent_name=agent_name,
                    score=min(1.0, score),  # Cap at 1.0
                    reasons=reasons,
                    permission_mode=agent_def.permission_mode,
                ))

        # Add default agent if no matches
        if not matches:
            matches.append(AgentMatch(
                agent_name=DEFAULT_AGENT,
                score=0.5,
                reasons=["Default agent for generic tasks"],
                permission_mode="auto",
            ))

        # Sort by score descending
        matches.sort(key=lambda m: m.score, reverse=True)

        return matches

    def score_agent(
        self,
        agent_def: AgentDefinition,
        criteria: SelectionCriteria,
    ) -> tuple[float, list[str]]:
        """
        Score an agent against criteria.

        Args:
            agent_def: Agent definition
            criteria: Selection criteria

        Returns:
            Tuple of (score, reasons)
        """
        score = 0.0
        reasons = []

        title_lower = criteria.task_title.lower()
        type_lower = criteria.task_type.lower()
        desc_lower = agent_def.description.lower() if agent_def.description else ""

        # Type match (40%)
        if type_lower:
            if type_lower in desc_lower:
                score += 0.4
                reasons.append(f"Agent handles '{type_lower}' tasks")
            elif agent_def.name == "planner" and type_lower == "design":
                score += 0.4
                reasons.append("Planner for design tasks")
            elif agent_def.name == "reviewer" and type_lower == "review":
                score += 0.4
                reasons.append("Reviewer for review tasks")

        # Keyword match (30%)
        if agent_def.name == "security":
            if any(kw in title_lower for kw in SECURITY_KEYWORDS):
                score += 0.3
                reasons.append("Security keywords detected")
        elif agent_def.name == "reviewer":
            if any(kw in title_lower for kw in REVIEW_KEYWORDS):
                score += 0.3
                reasons.append("Review keywords detected")
        elif agent_def.name == "planner":
            if any(kw in title_lower for kw in DESIGN_KEYWORDS):
                score += 0.3
                reasons.append("Design keywords detected")

        # Tag match (20%)
        if agent_def.name == "security":
            if any(tag.lower() in SECURITY_TAGS for tag in criteria.task_tags):
                score += 0.2
                reasons.append("Security tags present")

        # Complexity match (10%)
        if criteria.complexity > 60:
            if agent_def.name in ["planner", "claude-code"]:
                score += 0.1
                reasons.append("High complexity handled")

        return score, reasons


def select_agent_for_task(
    task_type: str = "",
    task_title: str = "",
    task_tags: Optional[list[str]] = None,
    complexity: int = 50,
    preferred_agent: Optional[str] = None,
    agents_dir: Optional[Path] = None,
    working_dir: Optional[Path] = None,
) -> AgentMatch:
    """
    Convenience function to select an agent for a task.

    Args:
        task_type: Type of task (design, implement, review, etc.)
        task_title: Title of the task
        task_tags: Tags associated with the task
        complexity: Complexity score (0-100)
        preferred_agent: Explicitly preferred agent name
        agents_dir: Directory containing agent definitions
        working_dir: Working directory

    Returns:
        AgentMatch with selected agent

    Example:
        >>> match = select_agent_for_task(
        ...     task_type="design",
        ...     task_title="Design authentication system",
        ... )
        >>> print(f"Use agent: {match.agent_name}")
    """
    selector = AgentSelector(
        agents_dir=agents_dir,
        working_dir=working_dir,
    )

    criteria = SelectionCriteria(
        task_type=task_type,
        task_title=task_title,
        task_tags=task_tags or [],
        complexity=complexity,
        preferred_agent=preferred_agent,
    )

    return selector.select(criteria)
