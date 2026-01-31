"""
Planning Models

Data classes for plans, tasks, and sprints.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..metrics.estimation import HoursEstimate, TokenEstimate


# Regex to parse AC items from markdown: - [ ] or - [x]
AC_ITEM_PATTERN = re.compile(r'^[-*]\s+\[([ xX])\]\s+(.+)$', re.MULTILINE)


@dataclass
class AcceptanceCriteriaItem:
    """A single acceptance criteria item."""
    text: str
    checked: bool = False

    def to_markdown(self) -> str:
        """Convert to markdown checkbox format."""
        check = "x" if self.checked else " "
        return f"- [{check}] {self.text}"


class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class PlanStatus(str, Enum):
    """Status of a plan."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    ARCHIVED = "archived"


class PlanType(str, Enum):
    """Type of plan."""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    CHORE = "chore"


@dataclass
class Task:
    """
    Represents a single task within a plan.

    Tasks are stored as .task.md files with YAML frontmatter.
    """
    id: str
    title: str
    plan_id: str
    type: str = "feature"
    priority: str = "P1"
    complexity: int = 50
    status: TaskStatus = TaskStatus.PENDING
    sprint: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    description: str = ""
    body: str = ""  # Markdown body content
    files_touched: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)  # Task IDs this task depends on
    source_path: Optional[Path] = None
    due_date: Optional[datetime] = None

    @property
    def status_emoji(self) -> str:
        """Return emoji for current status."""
        return {
            TaskStatus.PENDING: "⏳",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.REVIEW: "📝",
            TaskStatus.DONE: "✅",
            TaskStatus.BLOCKED: "🚫",
            TaskStatus.CANCELLED: "❌",
        }.get(self.status, "❓")

    @property
    def estimated_hours(self) -> "HoursEstimate":
        """Get estimated hours based on complexity.

        Returns:
            HoursEstimate with min, expected, and max hours
        """
        from ..metrics.estimation import EstimationService
        service = EstimationService()
        return service.estimate_hours(self.complexity)

    @property
    def estimated_hours_str(self) -> str:
        """Get formatted estimated hours string.

        Returns:
            String like "2.0h (S)"
        """
        estimate = self.estimated_hours
        return f"{estimate.expected_hours:.1f}h ({estimate.size_band.upper()})"

    @property
    def estimated_tokens(self) -> "TokenEstimate":
        """Get estimated token usage based on complexity, type, and files.

        Returns:
            TokenEstimate with breakdown and total
        """
        from ..metrics.estimation import TokenEstimator
        estimator = TokenEstimator()
        return estimator.estimate_for_task(self)

    @property
    def estimated_tokens_str(self) -> str:
        """Get formatted estimated tokens string.

        Returns:
            String like "~45K tokens"
        """
        return str(self.estimated_tokens)

    @property
    def acceptance_criteria(self) -> List[AcceptanceCriteriaItem]:
        """Parse acceptance criteria from the markdown body.

        Looks for an "# Acceptance Criteria" section and parses checkbox items.
        Supports both `- [ ]` and `* [ ]` formats.

        Returns:
            List of AcceptanceCriteriaItem objects
        """
        if not self.body:
            return []

        # Find the Acceptance Criteria section
        ac_section_match = re.search(
            r'#\s*Acceptance\s+Criteria\s*\n(.*?)(?=\n#|\Z)',
            self.body,
            re.IGNORECASE | re.DOTALL
        )
        if not ac_section_match:
            return []

        ac_section = ac_section_match.group(1)
        items = []

        for match in AC_ITEM_PATTERN.finditer(ac_section):
            checked = match.group(1).lower() == 'x'
            text = match.group(2).strip()
            items.append(AcceptanceCriteriaItem(text=text, checked=checked))

        return items

    @property
    def unchecked_ac(self) -> List[AcceptanceCriteriaItem]:
        """Get all unchecked acceptance criteria items.

        Returns:
            List of unchecked AcceptanceCriteriaItem objects
        """
        return [ac for ac in self.acceptance_criteria if not ac.checked]

    @property
    def actual_hours(self) -> Optional[float]:
        """Get actual hours from time tracking entries.

        Note: This property returns None as it requires a paircoder_dir.
        Use get_actual_hours(paircoder_dir) for actual values.

        Returns:
            None (use get_actual_hours instead)
        """
        return None

    def get_actual_hours(self, paircoder_dir: Path) -> Optional[float]:
        """Get actual hours spent from time tracking cache.

        Args:
            paircoder_dir: Path to .paircoder directory (or parent containing cache)

        Returns:
            Total hours spent on task, or None if no time tracking data
        """
        try:
            from ..integrations.time_tracking import LocalTimeCache

            # Look for time tracking cache
            cache_path = paircoder_dir / "time-tracking-cache.json"
            if not cache_path.exists():
                # Try direct path (for testing)
                cache_path = paircoder_dir / "time-cache.json"
                if not cache_path.exists():
                    return None

            cache = LocalTimeCache(cache_path)
            total = cache.get_total(self.id)

            if total.total_seconds() == 0:
                return None

            return total.total_seconds() / 3600  # Convert to hours

        except Exception:
            return None

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        result = {
            "id": self.id,
            "title": self.title,
            "plan": self.plan_id,
            "type": self.type,
            "priority": self.priority,
            "complexity": self.complexity,
            "status": self.status.value,
            "sprint": self.sprint,
            "tags": self.tags,
            "depends_on": self.depends_on,
        }
        if self.due_date is not None:
            result["due_date"] = self.due_date.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: dict, body: str = "", source_path: Optional[Path] = None) -> "Task":
        """Create Task from dictionary (parsed YAML frontmatter)."""
        status = data.get("status", "pending")
        if isinstance(status, str):
            try:
                status = TaskStatus(status)
            except ValueError:
                status = TaskStatus.PENDING

        # Parse due_date if present
        due_date = data.get("due_date")
        if isinstance(due_date, str):
            try:
                due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            except ValueError:
                due_date = None

        return cls(
            id=data.get("id", "UNKNOWN"),
            title=data.get("title", "Untitled Task"),
            plan_id=data.get("plan", ""),
            type=data.get("type", "feature"),
            priority=data.get("priority", "P1"),
            complexity=data.get("complexity", data.get("complexity_hint", 50)),
            status=status,
            sprint=data.get("sprint"),
            tags=data.get("tags", []),
            description=data.get("description", ""),
            body=body,
            files_touched=data.get("files_touched", []),
            verification=data.get("verification", []),
            depends_on=data.get("depends_on", []),
            source_path=source_path,
            due_date=due_date,
        )


@dataclass
class Sprint:
    """
    Represents a sprint containing multiple tasks.
    """
    id: str
    title: str
    goal: str = ""
    task_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "goal": self.goal,
            "tasks": self.task_ids,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Sprint":
        """Create Sprint from dictionary."""
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            goal=data.get("goal", ""),
            task_ids=data.get("tasks", []),
        )


@dataclass
class Plan:
    """
    Represents a plan with goals, tasks, and sprints.

    Plans are stored as .plan.yaml files.
    """
    id: str
    title: str
    type: PlanType = PlanType.FEATURE
    status: PlanStatus = PlanStatus.PLANNED
    owner: str = ""
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    skills: list[str] = field(default_factory=list)  # Associated skills (v2.9.1+)
    flows: list[str] = field(default_factory=list)   # DEPRECATED: Use skills instead
    goals: list[str] = field(default_factory=list)
    sprints: list[Sprint] = field(default_factory=list)
    tasks: list[dict] = field(default_factory=list)  # Task summaries in plan file
    acceptance_criteria: dict = field(default_factory=dict)
    source_path: Optional[Path] = None

    @property
    def status_emoji(self) -> str:
        """Return emoji for current status."""
        return {
            PlanStatus.PLANNED: "📋",
            PlanStatus.IN_PROGRESS: "🔄",
            PlanStatus.COMPLETE: "✅",
            PlanStatus.ARCHIVED: "📦",
        }.get(self.status, "❓")

    @property
    def task_ids(self) -> list[str]:
        """Get all task IDs from the plan."""
        return [t.get("id", "") for t in self.tasks if t.get("id")]

    @property
    def slug(self) -> str:
        """Get plan slug from ID (e.g., 'plan-2025-01-feature' -> 'feature')."""
        parts = self.id.split("-")
        if len(parts) > 3:
            return "-".join(parts[3:])
        return self.id

    def get_sprint_by_id(self, sprint_id: str) -> Optional[Sprint]:
        """Get a sprint by ID."""
        for sprint in self.sprints:
            if sprint.id == sprint_id:
                return sprint
        return None

    def get_tasks_for_sprint(self, sprint_id: str) -> list[dict]:
        """Get task summaries for a specific sprint."""
        sprint = self.get_sprint_by_id(sprint_id)
        if not sprint:
            return []
        return [t for t in self.tasks if t.get("id") in sprint.task_ids]

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        result = {
            "id": self.id,
            "title": self.title,
            "type": self.type.value,
            "status": self.status.value,
        }

        if self.owner:
            result["owner"] = self.owner
        if self.created_at:
            result["created_at"] = self.created_at.isoformat()
        if self.completed_at:
            result["completed_at"] = self.completed_at.isoformat()

        # Write skills (new field) - always write if present
        if self.skills:
            result["skills"] = self.skills

        # DEPRECATED: Only write flows for backward compat if no skills
        # This allows old tools to read plans created by new tools
        if self.flows and not self.skills:
            result["flows"] = self.flows

        if self.goals:
            result["goals"] = self.goals
        if self.acceptance_criteria:
            result["acceptance_criteria"] = self.acceptance_criteria
        if self.sprints:
            result["sprints"] = [s.to_dict() for s in self.sprints]
        if self.tasks:
            result["tasks"] = self.tasks

        return result

    @classmethod
    def from_dict(cls, data: dict, source_path: Optional[Path] = None) -> "Plan":
        """Create Plan from dictionary (parsed YAML)."""
        # Parse type
        plan_type = data.get("type", "feature")
        if isinstance(plan_type, str):
            try:
                plan_type = PlanType(plan_type)
            except ValueError:
                plan_type = PlanType.FEATURE

        # Parse status
        status = data.get("status", "planned")
        if isinstance(status, str):
            try:
                status = PlanStatus(status)
            except ValueError:
                status = PlanStatus.PLANNED

        # Parse dates
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                created_at = None

        completed_at = data.get("completed_at")
        if isinstance(completed_at, str):
            try:
                completed_at = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
            except ValueError:
                completed_at = None

        # Parse sprints
        sprints = [
            Sprint.from_dict(s) if isinstance(s, dict) else s
            for s in data.get("sprints", [])
        ]

        # Handle skills vs flows (backward compat)
        # New plans use 'skills', old plans use 'flows'
        skills = data.get("skills", [])
        flows = data.get("flows", [])

        # If no skills but has flows, migrate flows to skills
        if not skills and flows:
            skills = flows

        return cls(
            id=data.get("id", ""),
            title=data.get("title", "Untitled Plan"),
            type=plan_type,
            status=status,
            owner=data.get("owner", ""),
            created_at=created_at,
            completed_at=completed_at,
            skills=skills,
            flows=flows if not skills else [],  # Clear flows if skills present
            goals=data.get("goals", []),
            sprints=sprints,
            tasks=data.get("tasks", []),
            acceptance_criteria=data.get("acceptance_criteria", {}),
            source_path=source_path,
        )
