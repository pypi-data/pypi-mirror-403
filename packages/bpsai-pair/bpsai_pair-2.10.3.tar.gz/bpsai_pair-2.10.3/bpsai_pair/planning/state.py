"""
State Management

Manages project state including active plan, current tasks, and status tracking.
Reads from and writes to .paircoder/context/state.md
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Plan, Task, TaskStatus
from .parser import PlanParser, TaskParser


@dataclass
class ProjectState:
    """
    Represents the current project state.
    
    Parsed from .paircoder/context/state.md
    """
    active_plan_id: Optional[str] = None
    active_sprint_id: Optional[str] = None
    last_updated: Optional[datetime] = None
    what_was_done: list[str] = field(default_factory=list)
    whats_next: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    source_path: Optional[Path] = None
    
    @classmethod
    def from_state_md(cls, content: str, source_path: Optional[Path] = None) -> "ProjectState":
        """
        Parse state from state.md content.
        
        This is a best-effort parser that extracts key information from
        the Markdown-formatted state file.
        """
        state = cls(source_path=source_path)
        
        # Extract last updated
        updated_match = re.search(r"Last updated:\s*(\d{4}-\d{2}-\d{2})", content)
        if updated_match:
            try:
                state.last_updated = datetime.strptime(updated_match.group(1), "%Y-%m-%d")
            except ValueError:
                pass
        
        # Extract active plan ID
        # Support both formats: **Plan:** `plan-id` and **Plan:** plan-id
        # Exclude "None" as it indicates no plan
        plan_match = re.search(r"\*\*Plan:\*\*\s*`?([^\s`]+)`?", content)
        if plan_match:
            plan_id = plan_match.group(1)
            # "None" is not a valid plan ID - it means no plan
            if plan_id.lower() != "none":
                state.active_plan_id = plan_id
        
        # Extract current sprint
        sprint_match = re.search(r"\*\*Current Sprint:\*\*\s*(\S+)", content)
        if sprint_match:
            state.active_sprint_id = sprint_match.group(1)
        
        # Extract "What Was Just Done" section
        done_match = re.search(
            r"## What Was Just Done\s*\n(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL
        )
        if done_match:
            lines = done_match.group(1).strip().split("\n")
            state.what_was_done = [
                line.lstrip("- ✅•").strip()
                for line in lines
                if line.strip() and not line.startswith("#")
            ]
        
        # Extract "What's Next" section
        next_match = re.search(
            r"## What'?s Next\s*\n(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL
        )
        if next_match:
            lines = next_match.group(1).strip().split("\n")
            state.whats_next = [
                line.lstrip("- 0123456789.•").strip()
                for line in lines
                if line.strip() and not line.startswith("#")
            ]
        
        # Extract blockers
        blockers_match = re.search(
            r"## Blockers\s*\n(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL
        )
        if blockers_match:
            text = blockers_match.group(1).strip()
            if text.lower() not in ("none", "none.", "none currently", "none currently."):
                lines = text.split("\n")
                state.blockers = [
                    line.lstrip("- •").strip()
                    for line in lines
                    if line.strip() and not line.startswith("#")
                ]
        
        return state


class StateManager:
    """
    Manages project state for PairCoder v2.
    
    Coordinates between state.md, plans, and tasks to provide
    a unified view of project status.
    """
    
    def __init__(self, paircoder_dir: Path):
        """
        Initialize state manager.
        
        Args:
            paircoder_dir: Path to .paircoder/ directory
        """
        self.paircoder_dir = Path(paircoder_dir)
        self.context_dir = self.paircoder_dir / "context"
        self.state_path = self.context_dir / "state.md"
        self.plan_parser = PlanParser(self.paircoder_dir / "plans")
        self.task_parser = TaskParser(self.paircoder_dir / "tasks")
        
        self._state: Optional[ProjectState] = None
        self._active_plan: Optional[Plan] = None
    
    @property
    def state(self) -> ProjectState:
        """Get current project state, loading if necessary."""
        if self._state is None:
            self._state = self.load_state()
        return self._state
    
    @property
    def active_plan(self) -> Optional[Plan]:
        """Get the active plan, loading if necessary."""
        if self._active_plan is None and self.state.active_plan_id:
            self._active_plan = self.plan_parser.get_plan_by_id(self.state.active_plan_id)
        return self._active_plan
    
    def load_state(self) -> ProjectState:
        """Load state from state.md file."""
        if self.state_path.exists():
            content = self.state_path.read_text(encoding="utf-8")
            return ProjectState.from_state_md(content, source_path=self.state_path)
        return ProjectState(source_path=self.state_path)
    
    def reload(self) -> None:
        """Reload state from disk."""
        self._state = None
        self._active_plan = None
    
    def get_status_summary(self) -> dict:
        """
        Get a summary of current project status.
        
        Returns dict with:
        - active_plan: Plan info or None
        - current_sprint: Sprint info or None
        - task_counts: Dict of status -> count
        - blockers: List of blockers
        - whats_next: List of next items
        """
        summary = {
            "active_plan": None,
            "current_sprint": None,
            "task_counts": {
                "pending": 0,
                "in_progress": 0,
                "done": 0,
                "blocked": 0,
            },
            "blockers": self.state.blockers,
            "whats_next": self.state.whats_next,
        }
        
        plan = self.active_plan
        if plan:
            summary["active_plan"] = {
                "id": plan.id,
                "title": plan.title,
                "status": plan.status.value,
                "type": plan.type.value,
            }
            
            # Get sprint info
            if self.state.active_sprint_id:
                sprint = plan.get_sprint_by_id(self.state.active_sprint_id)
                if sprint:
                    summary["current_sprint"] = {
                        "id": sprint.id,
                        "title": sprint.title,
                        "goal": sprint.goal,
                        "task_count": len(sprint.task_ids),
                    }
            
            # Count tasks by status
            tasks = self.task_parser.parse_all(plan.slug)
            for task in tasks:
                status_key = task.status.value
                if status_key in summary["task_counts"]:
                    summary["task_counts"][status_key] += 1
        
        return summary
    
    def get_tasks_by_status(self, status: Optional[TaskStatus] = None) -> list[Task]:
        """
        Get tasks filtered by status.
        
        Args:
            status: Filter to this status, or None for all tasks
            
        Returns:
            List of Task objects
        """
        plan = self.active_plan
        if not plan:
            return []
        
        tasks = self.task_parser.parse_all(plan.slug)
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        return tasks
    
    def get_next_task(self) -> Optional[Task]:
        """
        Get the next task to work on.

        Prioritizes in-progress tasks, then pending tasks by priority.
        If an active plan is set, searches within that plan first.
        Falls back to searching all tasks if no active plan is set.
        """
        plan = self.active_plan

        # Get tasks - from active plan if set, otherwise all tasks
        if plan:
            tasks = self.task_parser.parse_all(plan.slug)
        else:
            tasks = self.task_parser.parse_all(None)

        # First check for in-progress tasks
        in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        if in_progress:
            return in_progress[0]

        # Then get highest priority pending task
        pending = [t for t in tasks if t.status == TaskStatus.PENDING]
        if pending:
            # Sort by priority (P0 > P1 > P2)
            pending.sort(key=lambda t: t.priority)
            return pending[0]

        return None
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """
        Update a task's status.
        
        Args:
            task_id: Task ID to update
            status: New status
            
        Returns:
            True if updated successfully
        """
        plan = self.active_plan
        plan_slug = plan.slug if plan else None
        
        return self.task_parser.update_status(
            task_id,
            status.value,
            plan_slug
        )
    
    def get_active_plan_id(self) -> Optional[str]:
        """
        Get the active plan ID from state.

        Returns:
            Plan ID or None if no active plan
        """
        return self.state.active_plan_id

    def set_active_plan(self, plan_id: str) -> bool:
        """
        Set the active plan and update state.md.
        
        Args:
            plan_id: Plan ID to set as active
            
        Returns:
            True if successful
        """
        plan = self.plan_parser.get_plan_by_id(plan_id)
        if not plan:
            return False
        
        self._active_plan = plan
        self.state.active_plan_id = plan_id
        
        # Set first sprint as active if available
        if plan.sprints:
            self.state.active_sprint_id = plan.sprints[0].id
        
        # Note: Full state.md update should be done separately
        return True
    
    def format_status_report(self) -> str:
        """
        Format a human-readable status report.
        
        Returns:
            Formatted status string
        """
        summary = self.get_status_summary()
        
        lines = ["# Project Status", ""]
        
        # Plan info
        if summary["active_plan"]:
            plan = summary["active_plan"]
            lines.append(f"**Active Plan:** `{plan['id']}`")
            lines.append(f"**Title:** {plan['title']}")
            lines.append(f"**Status:** {plan['status']}")
            lines.append("")
        else:
            lines.append("**No active plan.**")
            lines.append("")
        
        # Sprint info
        if summary["current_sprint"]:
            sprint = summary["current_sprint"]
            lines.append(f"**Current Sprint:** {sprint['id']} - {sprint['title']}")
            if sprint["goal"]:
                lines.append(f"**Goal:** {sprint['goal']}")
            lines.append("")
        
        # Task counts
        counts = summary["task_counts"]
        total = sum(counts.values())
        if total > 0:
            lines.append("## Task Progress")
            lines.append("")
            lines.append(f"- ✅ Done: {counts['done']}")
            lines.append(f"- 🔄 In Progress: {counts['in_progress']}")
            lines.append(f"- ⏳ Pending: {counts['pending']}")
            lines.append(f"- 🚫 Blocked: {counts['blocked']}")
            lines.append("")
            
            # Progress bar
            done_pct = int((counts['done'] / total) * 100) if total > 0 else 0
            lines.append(f"**Progress:** {done_pct}% ({counts['done']}/{total} tasks)")
            lines.append("")
        
        # Blockers
        if summary["blockers"]:
            lines.append("## Blockers")
            lines.append("")
            for blocker in summary["blockers"]:
                lines.append(f"- 🚫 {blocker}")
            lines.append("")
        
        # What's next
        if summary["whats_next"]:
            lines.append("## What's Next")
            lines.append("")
            for item in summary["whats_next"][:5]:  # Limit to 5 items
                lines.append(f"- {item}")
            lines.append("")
        
        return "\n".join(lines)
