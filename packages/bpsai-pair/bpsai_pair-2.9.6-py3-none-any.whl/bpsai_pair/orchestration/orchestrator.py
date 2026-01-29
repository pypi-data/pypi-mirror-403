"""
Orchestrator service for multi-agent task routing.

Intelligently routes tasks to the most appropriate AI coding agent
based on task characteristics, agent capabilities, cost, and availability.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional

import yaml

from .handoff import HandoffManager
from .headless import HeadlessSession
from .planner import PlannerAgent, should_trigger_planner
from .reviewer import ReviewerAgent, should_trigger_reviewer

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks for routing decisions."""

    DESIGN = "design"
    IMPLEMENT = "implement"
    REVIEW = "review"
    REFACTOR = "refactor"
    FIX = "fix"
    TEST = "test"
    DOCUMENT = "document"


class TaskComplexity(Enum):
    """Complexity levels for task classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskScope(Enum):
    """Scope of task for routing decisions."""

    SINGLE_FILE = "single-file"
    MULTI_FILE = "multi-file"
    CROSS_MODULE = "cross-module"


AgentName = Literal["claude-code", "cursor"]


@dataclass
class AgentCapabilities:
    """Capabilities of an AI coding agent."""

    name: AgentName
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    cost_per_1k_tokens: float = 0.01
    context_limit: int = 100000
    availability: Literal["local", "optional", "cloud"] = "local"


@dataclass
class TaskCharacteristics:
    """Characteristics of a task for routing decisions."""

    task_id: str
    task_type: TaskType = TaskType.IMPLEMENT
    complexity: TaskComplexity = TaskComplexity.MEDIUM
    scope: TaskScope = TaskScope.SINGLE_FILE
    risk: Literal["low", "medium", "high"] = "medium"
    estimated_tokens: int = 5000
    requires_reasoning: bool = False
    requires_iteration: bool = False
    description: str = ""


@dataclass
class Assignment:
    """An assignment of a task to an agent."""

    task_id: str
    agent: AgentName
    permission_mode: str = "auto"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    result: Optional[Any] = None
    score: float = 0.0
    reasoning: str = ""


@dataclass
class RoutingDecision:
    """A routing decision with scoring details."""

    agent: AgentName
    score: float
    reasoning: list[str] = field(default_factory=list)


class Orchestrator:
    """
    Orchestrates task routing and execution across multiple AI agents.

    Routes tasks to the most appropriate agent based on capabilities,
    manages handoffs between agents, and monitors execution.
    """

    # Default agent capabilities
    DEFAULT_AGENTS: dict[AgentName, AgentCapabilities] = {
        "claude-code": AgentCapabilities(
            name="claude-code",
            strengths=[
                "complex-reasoning",
                "architecture-design",
                "code-review",
                "documentation",
                "planning",
            ],
            weaknesses=["rapid-iteration", "bulk-file-operations"],
            cost_per_1k_tokens=0.015,
            context_limit=200000,
            availability="local",
        ),
        "cursor": AgentCapabilities(
            name="cursor",
            strengths=["ide-integration", "interactive-editing", "ui-development"],
            weaknesses=["headless-operation", "automation"],
            cost_per_1k_tokens=0.012,
            context_limit=100000,
            availability="optional",
        ),
    }

    def __init__(
        self,
        project_root: Optional[Path] = None,
        capabilities_path: Optional[Path] = None,
        available_agents: Optional[list[AgentName]] = None,
        preferences: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            project_root: Root directory of the project
            capabilities_path: Path to capabilities.yaml
            available_agents: List of available agents
            preferences: User preferences for routing
        """
        self.project_root = project_root or Path.cwd()
        self.agents = self._load_capabilities(capabilities_path)
        self.available_agents = available_agents or ["claude-code"]
        self.preferences = preferences or {}
        self.sessions: dict[str, Any] = {}

        # Initialize adapters
        self.handoff_manager = HandoffManager(project_root=self.project_root)

    def _load_capabilities(
        self, path: Optional[Path] = None
    ) -> dict[AgentName, AgentCapabilities]:
        """Load agent capabilities from config or use defaults."""
        if path and path.exists():
            with open(path, encoding='utf-8') as f:
                data = yaml.safe_load(f)
                agents = {}
                for name, caps in data.get("agents", {}).items():
                    agents[name] = AgentCapabilities(
                        name=name,
                        strengths=caps.get("strengths", []),
                        weaknesses=caps.get("weaknesses", []),
                        cost_per_1k_tokens=caps.get("cost_per_1k_tokens", 0.01),
                        context_limit=caps.get("context_limit", 100000),
                        availability=caps.get("availability", "local"),
                    )
                return agents
        return self.DEFAULT_AGENTS.copy()

    def analyze_task(self, task_id: str) -> TaskCharacteristics:
        """
        Analyze a task and determine its characteristics.

        Args:
            task_id: ID of the task to analyze

        Returns:
            TaskCharacteristics for routing
        """
        # Find and load task file
        task_file = self._find_task_file(task_id)

        if not task_file:
            logger.warning(f"Task file not found for {task_id}, using defaults")
            return TaskCharacteristics(task_id=task_id)

        content = task_file.read_text(encoding="utf-8").lower()

        # Determine task type
        task_type = TaskType.IMPLEMENT
        if "design" in content or "architecture" in content:
            task_type = TaskType.DESIGN
        elif "review" in content or "check" in content:
            task_type = TaskType.REVIEW
        elif "refactor" in content:
            task_type = TaskType.REFACTOR
        elif "fix" in content or "bug" in content:
            task_type = TaskType.FIX
        elif "test" in content:
            task_type = TaskType.TEST
        elif "document" in content or "docs" in content:
            task_type = TaskType.DOCUMENT

        # Determine complexity
        complexity = TaskComplexity.MEDIUM
        if "simple" in content or "trivial" in content:
            complexity = TaskComplexity.LOW
        elif "complex" in content or "challenging" in content:
            complexity = TaskComplexity.HIGH

        # Determine scope
        scope = TaskScope.SINGLE_FILE
        if "multiple files" in content or "cross-module" in content:
            scope = TaskScope.CROSS_MODULE
        elif "multi-file" in content or "several files" in content:
            scope = TaskScope.MULTI_FILE

        # Estimate tokens based on content length
        estimated_tokens = len(content) // 4

        return TaskCharacteristics(
            task_id=task_id,
            task_type=task_type,
            complexity=complexity,
            scope=scope,
            estimated_tokens=estimated_tokens,
            requires_reasoning=task_type in [TaskType.DESIGN, TaskType.REVIEW],
            requires_iteration=task_type in [TaskType.IMPLEMENT, TaskType.REFACTOR],
            description=content[:200],
        )

    def select_agent(
        self,
        task: TaskCharacteristics,
        constraints: Optional[dict[str, Any]] = None,
    ) -> RoutingDecision:
        """
        Select the best agent for a task.

        Args:
            task: Task characteristics
            constraints: Optional constraints (max_cost, prefer, etc.)

        Returns:
            RoutingDecision with selected agent and reasoning
        """
        constraints = constraints or {}
        scores: dict[AgentName, RoutingDecision] = {}

        for agent_name in self.available_agents:
            agent = self.agents.get(agent_name)
            if not agent:
                continue

            score = 0.0
            reasoning = []

            # Strength match (40%)
            strength_score = self._calculate_strength_score(task, agent)
            score += strength_score * 0.4
            if strength_score > 0.5:
                reasoning.append(f"Good strength match ({strength_score:.2f})")

            # Cost efficiency (20%)
            cost_score = 1.0 - (agent.cost_per_1k_tokens / 0.02)  # Normalize to 0-1
            score += max(0, cost_score) * 0.2
            if agent.cost_per_1k_tokens < 0.012:
                reasoning.append("Cost efficient")

            # Context fit (20%)
            context_score = 1.0 if task.estimated_tokens < agent.context_limit * 0.8 else 0.5
            score += context_score * 0.2
            if context_score < 1.0:
                reasoning.append("Context may be tight")

            # Availability (10%)
            availability_score = 1.0 if agent.availability == "local" else 0.5
            score += availability_score * 0.1

            # User preference (10%)
            if constraints.get("prefer") == agent_name:
                score += 0.1
                reasoning.append("User preferred")

            scores[agent_name] = RoutingDecision(
                agent=agent_name, score=score, reasoning=reasoning
            )

        # Select best agent
        best = max(scores.values(), key=lambda x: x.score)
        return best

    def _calculate_strength_score(
        self, task: TaskCharacteristics, agent: AgentCapabilities
    ) -> float:
        """Calculate how well agent strengths match task requirements."""
        task_needs = []

        if task.task_type == TaskType.DESIGN:
            task_needs.extend(["architecture-design", "planning", "complex-reasoning"])
        elif task.task_type == TaskType.REVIEW:
            task_needs.extend(["code-review", "complex-reasoning"])
        elif task.task_type == TaskType.REFACTOR:
            task_needs.extend(["refactoring", "file-operations"])
        elif task.task_type == TaskType.IMPLEMENT:
            task_needs.extend(["implementation", "rapid-iteration"])
        elif task.task_type == TaskType.FIX:
            task_needs.extend(["implementation", "rapid-iteration"])

        if task.requires_reasoning:
            task_needs.append("complex-reasoning")
        if task.requires_iteration:
            task_needs.append("rapid-iteration")

        if not task_needs:
            return 0.5

        matches = sum(1 for need in task_needs if need in agent.strengths)
        weaknesses = sum(1 for need in task_needs if need in agent.weaknesses)

        return (matches - weaknesses * 0.5) / len(task_needs)

    def assign_task(
        self,
        task_id: str,
        constraints: Optional[dict[str, Any]] = None,
    ) -> Assignment:
        """
        Analyze a task and assign it to the best agent.

        Args:
            task_id: Task ID to assign
            constraints: Optional routing constraints

        Returns:
            Assignment with selected agent
        """
        task = self.analyze_task(task_id)
        decision = self.select_agent(task, constraints)

        # Determine permission mode based on task type
        permission_mode = "auto"
        if task.task_type in [TaskType.DESIGN, TaskType.REVIEW]:
            permission_mode = "plan"

        assignment = Assignment(
            task_id=task_id,
            agent=decision.agent,
            permission_mode=permission_mode,
            score=decision.score,
            reasoning="; ".join(decision.reasoning),
        )

        logger.info(
            f"Assigned {task_id} to {decision.agent} "
            f"(score: {decision.score:.2f}, mode: {permission_mode})"
        )

        return assignment

    def execute(
        self,
        assignment: Assignment,
        dry_run: bool = False,
    ) -> Assignment:
        """
        Execute a task assignment.

        Args:
            assignment: The assignment to execute
            dry_run: If True, show decision without executing

        Returns:
            Updated assignment with result
        """
        if dry_run:
            logger.info(f"[DRY RUN] Would execute {assignment.task_id} with {assignment.agent}")
            assignment.status = "completed"
            assignment.result = {"dry_run": True}
            return assignment

        assignment.status = "running"

        try:
            # Check if this is a design/planning or review task
            task = self.analyze_task(assignment.task_id)

            use_planner = should_trigger_planner(
                task_type=task.task_type.value.upper(),
                task_title=task.description,
            )
            use_reviewer = should_trigger_reviewer(
                task_type=task.task_type.value.upper(),
                task_title=task.description,
            )

            if use_planner and assignment.permission_mode == "plan":
                result = self._execute_with_planner(assignment)
            elif use_reviewer and assignment.permission_mode == "plan":
                result = self._execute_with_reviewer(assignment)
            elif assignment.agent == "claude-code":
                result = self._execute_with_claude(assignment)
            else:
                raise ValueError(f"Unknown agent: {assignment.agent}")

            assignment.result = result
            assignment.status = "completed" if result.get("success", False) else "failed"

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            assignment.status = "failed"
            assignment.result = {"error": str(e)}

        return assignment

    def _execute_with_claude(self, assignment: Assignment) -> dict[str, Any]:
        """Execute task with Claude Code."""
        session = HeadlessSession(
            permission_mode=assignment.permission_mode,
            working_dir=self.project_root,
        )

        # Load task description
        task = self.analyze_task(assignment.task_id)
        prompt = f"Work on {assignment.task_id}: {task.description}"

        response = session.invoke(prompt)

        return {
            "success": not response.is_error,
            "result": response.result,
            "tokens": response.total_tokens,
            "cost": response.cost_usd,
        }

    def _execute_with_planner(self, assignment: Assignment) -> dict[str, Any]:
        """
        Execute a design/planning task with the planner agent.

        The planner operates in read-only mode and returns structured
        planning output including phases, files, and complexity estimates.

        Args:
            assignment: The task assignment

        Returns:
            Dictionary with planning results
        """
        planner = PlannerAgent(
            agents_dir=self.project_root / ".claude" / "agents",
            working_dir=self.project_root,
        )

        task_dir = self.project_root / ".paircoder"
        context_dir = task_dir / "context"

        plan = planner.plan(
            task_id=assignment.task_id,
            task_dir=task_dir,
            context_dir=context_dir,
        )

        return {
            "success": True,
            "result": plan.raw_output or plan.summary,
            "plan": plan.to_dict(),
            "phases": len(plan.phases),
            "files_to_modify": plan.files_to_modify,
            "complexity": plan.estimated_complexity,
        }

    def _execute_with_reviewer(self, assignment: Assignment) -> dict[str, Any]:
        """
        Execute a code review task with the reviewer agent.

        The reviewer operates in read-only mode and returns structured
        review feedback including items by severity and verdict.

        Args:
            assignment: The task assignment

        Returns:
            Dictionary with review results
        """
        import subprocess

        reviewer = ReviewerAgent(
            agents_dir=self.project_root / ".claude" / "agents",
            working_dir=self.project_root,
        )

        # Get git diff for current changes
        try:
            diff_result = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            diff = diff_result.stdout if diff_result.returncode == 0 else ""

            # Get list of changed files
            files_result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            changed_files = files_result.stdout.strip().split("\n") if files_result.returncode == 0 else []
            changed_files = [f for f in changed_files if f]  # Filter empty strings

        except Exception as e:
            logger.warning(f"Could not get git diff: {e}")
            diff = ""
            changed_files = []

        output = reviewer.review(
            diff=diff,
            changed_files=changed_files,
            include_file_contents=True,
        )

        return {
            "success": True,
            "result": output.raw_output or output.summary,
            "review": output.to_dict(),
            "verdict": output.verdict.value,
            "blockers": output.blocker_count,
            "warnings": output.warning_count,
            "has_blockers": output.has_blockers,
        }

    def _find_task_file(self, task_id: str) -> Optional[Path]:
        """Find the task file for a given task ID."""
        task_dirs = [
            self.project_root / ".paircoder" / "tasks",
        ]

        for task_dir in task_dirs:
            if not task_dir.exists():
                continue
            for task_file in task_dir.rglob(f"{task_id}*.md"):
                return task_file

        return None

    def handoff(
        self,
        assignment: Assignment,
        target_agent: AgentName,
        conversation_summary: str = "",
    ) -> Assignment:
        """
        Hand off a task from one agent to another.

        Args:
            assignment: Current assignment
            target_agent: Target agent for handoff
            conversation_summary: Summary of work done

        Returns:
            New assignment for target agent
        """
        # Create handoff package
        package_path = self.handoff_manager.pack(
            task_id=assignment.task_id,
            source_agent=assignment.agent,
            target_agent=target_agent,
            conversation_summary=conversation_summary,
        )

        logger.info(f"Created handoff package: {package_path}")

        # Create new assignment
        new_assignment = Assignment(
            task_id=assignment.task_id,
            agent=target_agent,
            reasoning=f"Handoff from {assignment.agent}",
        )

        return new_assignment

    def run(
        self,
        task_ids: list[str],
        constraints: Optional[dict[str, Any]] = None,
        dry_run: bool = False,
    ) -> list[Assignment]:
        """
        Execute multiple tasks with optimal routing.

        Args:
            task_ids: List of task IDs to execute
            constraints: Routing constraints
            dry_run: If True, show decisions without executing

        Returns:
            List of assignments with results
        """
        assignments = []

        for task_id in task_ids:
            assignment = self.assign_task(task_id, constraints)
            if not dry_run:
                assignment = self.execute(assignment, dry_run=dry_run)
            assignments.append(assignment)

        return assignments
