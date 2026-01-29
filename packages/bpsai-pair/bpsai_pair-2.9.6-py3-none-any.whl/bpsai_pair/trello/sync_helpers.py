"""
Shared helpers and constants for Trello sync operations.

This module contains:
- Label and status mappings
- Stack keywords for inference
- Due date configuration and calculation
- List name normalization utilities
"""
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re


# BPS Label color mapping
BPS_LABELS = {
    "Frontend": "green",
    "Backend": "blue",
    "Worker/Function": "purple",
    "Deployment": "red",
    "Bug/Issue": "orange",
    "Security/Admin": "yellow",
    "Documentation": "sky",
    "AI/ML": "black",
}

# Task status to Trello Status custom field mapping
# Maps local task status values to Trello Status dropdown options
# Valid BPS board options: Planning, Enqueued, In progress, Testing, Done, Waiting, Blocked
TASK_STATUS_TO_TRELLO_STATUS = {
    "pending": "Planning",
    "ready": "Enqueued",
    "planned": "Planning",
    "in_progress": "In progress",
    "review": "Testing",
    "testing": "Testing",
    "blocked": "Blocked",
    "waiting": "Waiting",
    "done": "Done",
    "deployed": "Done",
}

# Trello Status to task status mapping (reverse of above)
# Maps Status custom field dropdown values back to task status
TRELLO_STATUS_TO_TASK_STATUS = {
    "Planning": "pending",
    "Enqueued": "ready",
    "In progress": "in_progress",
    "Testing": "review",
    "Done": "done",
    "Waiting": "blocked",
    "Blocked": "blocked",
    "Not sure": "blocked",
}

# Keywords to infer labels from task title/tags
STACK_KEYWORDS = {
    "Frontend": ["frontend", "ui", "react", "vue", "angular", "css", "html", "component"],
    "Backend": ["backend", "api", "flask", "fastapi", "django", "server", "endpoint"],
    "Worker/Function": ["worker", "function", "lambda", "celery", "task", "job", "queue", "cli"],
    "Deployment": ["deploy", "docker", "k8s", "kubernetes", "ci", "cd", "pipeline"],
    "Bug/Issue": ["bug", "fix", "issue", "error", "crash"],
    "Security/Admin": ["security", "auth", "admin", "permission", "role", "soc2"],
    "Documentation": ["doc", "readme", "guide", "tutorial", "comment"],
    "AI/ML": ["ai", "ml", "model", "llm", "claude", "gpt", "embedding"],
}

# Map inferred labels to valid Stack dropdown values
# Valid Stack values: React, Flask, Worker/Function, Infra, Collection
LABEL_TO_STACK_MAPPING = {
    "Frontend": "React",
    "Backend": "Flask",
    "Worker/Function": "Worker/Function",
    "Deployment": "Infra",
    "Bug/Issue": None,  # Not a stack, just a label
    "Security/Admin": "Infra",
    "Documentation": "Collection",
    "AI/ML": "Worker/Function",
}

# List name to status mapping for reverse sync
# Includes both spaced and non-spaced variants for flexible matching
LIST_TO_STATUS = {
    # Backlog/Pending variants
    "Intake/Backlog": "pending",
    "Intake / Backlog": "pending",
    "Backlog": "pending",
    "Planned/Ready": "pending",
    "Planned / Ready": "pending",
    "Ready": "pending",
    # In Progress variants
    "In Progress": "in_progress",
    # Review variants
    "Review/Testing": "review",
    "Review / Testing": "review",
    "In Review": "review",
    # Done variants
    "Deployed/Done": "done",
    "Deployed / Done": "done",
    "Done": "done",
    # Blocked variants
    "Issues/Tech Debt": "blocked",
    "Issues / Tech Debt": "blocked",
    "Blocked": "blocked",
}


@dataclass
class DueDateConfig:
    """Configuration for calculating due dates from effort levels."""
    # Days to add for each effort level
    effort_days: Dict[str, int] = field(default_factory=lambda: {"S": 1, "M": 2, "L": 4})

    def get_days_for_effort(self, effort: str) -> int:
        """Get the number of days for an effort level.

        Args:
            effort: Effort level (S, M, L) - case insensitive

        Returns:
            Number of days to add, defaults to M (2 days) if unknown
        """
        effort_upper = effort.upper()
        return self.effort_days.get(effort_upper, self.effort_days.get("M", 2))


def calculate_due_date_from_effort(
    effort: str,
    base_date: Optional[datetime] = None,
    config: Optional[DueDateConfig] = None
) -> datetime:
    """Calculate a due date based on effort level.

    Args:
        effort: Effort level (S, M, L)
        base_date: Starting date (defaults to now in UTC)
        config: DueDateConfig instance (uses defaults if not provided)

    Returns:
        Due date as datetime
    """
    if config is None:
        config = DueDateConfig()

    if base_date is None:
        base_date = datetime.now(timezone.utc)

    days = config.get_days_for_effort(effort)
    return base_date + timedelta(days=days)


def normalize_list_name(name: str) -> str:
    """Normalize list name for matching (remove spaces around slashes).

    Args:
        name: List name to normalize

    Returns:
        Normalized list name
    """
    return re.sub(r'\s*/\s*', '/', name).strip()


def get_status_for_list_flexible(list_name: str) -> Optional[str]:
    """Get status for a list name with flexible matching.

    Args:
        list_name: Trello list name

    Returns:
        Status string or None if no match found
    """
    # Try exact match first
    if list_name in LIST_TO_STATUS:
        return LIST_TO_STATUS[list_name]

    # Try normalized match
    normalized = normalize_list_name(list_name)
    for key, status in LIST_TO_STATUS.items():
        if normalize_list_name(key) == normalized:
            return status

    # Try pattern matching
    list_lower = list_name.lower()
    if "done" in list_lower or "deployed" in list_lower:
        return "done"
    if "progress" in list_lower:
        return "in_progress"
    if "review" in list_lower or "testing" in list_lower:
        return "review"
    if "blocked" in list_lower or "issue" in list_lower:
        return "blocked"
    if "backlog" in list_lower or "intake" in list_lower or "ready" in list_lower:
        return "pending"

    return None
