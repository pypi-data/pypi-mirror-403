"""Task lifecycle states and transitions."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..core.constants import TASK_ID_PATTERN, TASK_FILE_GLOBS


class TaskState(Enum):
    """Task lifecycle states."""
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    REVIEW = "review"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


# Valid state transitions
VALID_TRANSITIONS: Dict[TaskState, List[TaskState]] = {
    TaskState.PENDING: [TaskState.IN_PROGRESS, TaskState.CANCELLED],
    TaskState.IN_PROGRESS: [TaskState.REVIEW, TaskState.COMPLETED, TaskState.BLOCKED, TaskState.CANCELLED],
    TaskState.REVIEW: [TaskState.COMPLETED, TaskState.IN_PROGRESS, TaskState.BLOCKED],
    TaskState.COMPLETED: [TaskState.ARCHIVED],
    TaskState.BLOCKED: [TaskState.IN_PROGRESS, TaskState.CANCELLED],
    TaskState.CANCELLED: [TaskState.ARCHIVED],
    TaskState.ARCHIVED: [],  # Terminal state
}


@dataclass
class TaskTransition:
    """Record of a task state transition."""
    from_state: TaskState
    to_state: TaskState
    timestamp: datetime
    reason: Optional[str] = None


@dataclass
class TaskMetadata:
    """Task metadata for lifecycle tracking."""
    id: str
    title: str
    status: TaskState
    sprint: Optional[str] = None
    plan: Optional[str] = None
    priority: Optional[str] = None
    complexity: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    pr: Optional[str] = None
    changelog_entry: Optional[str] = None
    transitions: List[TaskTransition] = field(default_factory=list)


class TaskLifecycle:
    """Manages task lifecycle state transitions."""

    def __init__(self, tasks_dir: Path):
        self.tasks_dir = tasks_dir

    def can_transition(self, from_state: TaskState, to_state: TaskState) -> bool:
        """Check if transition is valid."""
        return to_state in VALID_TRANSITIONS.get(from_state, [])

    def transition(self, task: TaskMetadata, new_state: TaskState,
                   reason: Optional[str] = None) -> TaskMetadata:
        """Transition task to new state."""
        if not self.can_transition(task.status, new_state):
            raise ValueError(
                f"Invalid transition: {task.status.value} -> {new_state.value}"
            )

        transition = TaskTransition(
            from_state=task.status,
            to_state=new_state,
            timestamp=datetime.now(),
            reason=reason
        )
        task.transitions.append(transition)
        task.status = new_state

        # Update completion timestamp
        if new_state == TaskState.COMPLETED:
            task.completed_at = datetime.now()
        elif new_state == TaskState.ARCHIVED:
            task.archived_at = datetime.now()

        return task

    def load_task(self, task_path: Path) -> TaskMetadata:
        """Load task metadata from file."""
        content = task_path.read_text(encoding="utf-8")

        # Parse YAML frontmatter from markdown
        metadata = self._parse_metadata(content)

        # Helper to get value with fallback to lowercase key
        def get_value(key: str, default=None):
            return metadata.get(key, metadata.get(key.lower(), default))

        # Parse tags - handle both string and list formats
        tags_raw = get_value("Tags", [])
        if isinstance(tags_raw, str):
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        elif isinstance(tags_raw, list):
            tags = tags_raw
        else:
            tags = []

        return TaskMetadata(
            id=get_value("ID", metadata.get("id", task_path.stem.replace(".task", ""))),
            title=get_value("Title", metadata.get("title", "")),
            status=self._parse_status(get_value("Status", "pending")),
            sprint=get_value("Sprint"),
            plan=get_value("Plan"),
            priority=get_value("Priority"),
            complexity=get_value("Complexity"),
            tags=tags,
            created_at=self._parse_date(get_value("Created")),
            changelog_entry=get_value("changelog_entry"),
        )

    def _parse_metadata(self, content: str) -> Dict[str, Any]:
        """Parse metadata from task markdown file.

        Supports both YAML frontmatter (---delimited) and markdown ## Metadata sections.
        """
        metadata = {}

        # Try YAML frontmatter first (more common in current codebase)
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    frontmatter = yaml.safe_load(parts[1])
                    if isinstance(frontmatter, dict):
                        # Map YAML keys to expected metadata keys (case-insensitive)
                        for key, value in frontmatter.items():
                            # Capitalize key for consistency with old format
                            cap_key = key.capitalize() if key.islower() else key
                            metadata[cap_key] = value
                            # Also store lowercase for direct access
                            metadata[key] = value
                        return metadata
                except Exception:
                    pass  # Fall through to markdown parsing

        # Fall back to ## Metadata markdown section
        in_metadata = False
        for line in content.split("\n"):
            line_stripped = line.strip()
            # Extract title from H1 heading: "# TASK-XXX: Title" or "# T18.1: Title"
            task_heading_match = re.match(rf"# {TASK_ID_PATTERN}: (.+)", line_stripped)
            if task_heading_match:
                title_parts = line_stripped.split(": ", 1)
                if len(title_parts) == 2:
                    metadata["title"] = title_parts[1]
            if line_stripped.startswith("## Metadata"):
                in_metadata = True
                continue
            if in_metadata:
                if line_stripped.startswith("## "):
                    break
                if line_stripped.startswith("- **"):
                    # Parse "- **Key**: Value"
                    parts = line_stripped[4:].split("**:", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        metadata[key] = value

        return metadata

    def _parse_status(self, status_str: str) -> TaskState:
        """Parse status string to TaskState."""
        status_map = {
            "pending": TaskState.PENDING,
            "in-progress": TaskState.IN_PROGRESS,
            "in_progress": TaskState.IN_PROGRESS,
            "review": TaskState.REVIEW,
            "completed": TaskState.COMPLETED,
            "done": TaskState.COMPLETED,
            "blocked": TaskState.BLOCKED,
            "cancelled": TaskState.CANCELLED,
            "archived": TaskState.ARCHIVED,
        }
        return status_map.get(status_str.lower(), TaskState.PENDING)

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return None

    def get_tasks_by_status(self, plan_dir: Path,
                            statuses: List[TaskState]) -> List[TaskMetadata]:
        """Get all tasks with specified statuses."""
        tasks = []
        for glob_pattern in TASK_FILE_GLOBS:
            for task_file in plan_dir.glob(glob_pattern):
                task = self.load_task(task_file)
                if task.status in statuses:
                    tasks.append(task)
        return sorted(tasks, key=lambda t: t.id)

    def get_tasks_by_sprint(self, plan_dir: Path,
                            sprints: List[str]) -> List[TaskMetadata]:
        """Get all tasks in specified sprints."""
        tasks = []
        for glob_pattern in TASK_FILE_GLOBS:
            for task_file in plan_dir.glob(glob_pattern):
                task = self.load_task(task_file)
                if task.sprint in sprints:
                    tasks.append(task)
        return sorted(tasks, key=lambda t: t.id)
