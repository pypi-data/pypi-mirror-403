"""
Daily standup summary generation.

Generates a summary of recent task activity for standup meetings.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class StandupSummary:
    """Summary for daily standup."""

    # Tasks completed since last standup (usually yesterday)
    completed: List[Dict[str, Any]] = field(default_factory=list)

    # Tasks currently in progress
    in_progress: List[Dict[str, Any]] = field(default_factory=list)

    # Blocked tasks
    blocked: List[Dict[str, Any]] = field(default_factory=list)

    # Tasks pending (ready to start)
    ready: List[Dict[str, Any]] = field(default_factory=list)

    # Date range for the summary
    since: Optional[datetime] = None
    until: Optional[datetime] = None

    # Statistics
    total_completed: int = 0
    total_in_progress: int = 0
    total_blocked: int = 0

    def to_markdown(self) -> str:
        """Generate markdown summary for standup.

        Returns:
            Formatted markdown string
        """
        lines = []

        # Header
        date_str = datetime.now().strftime("%Y-%m-%d")
        lines.append(f"# Daily Standup - {date_str}")
        lines.append("")

        # Yesterday / Completed
        lines.append("## Completed")
        if self.completed:
            for task in self.completed:
                lines.append(f"- [{task['id']}] {task['title']}")
        else:
            lines.append("- No tasks completed")
        lines.append("")

        # Today / In Progress
        lines.append("## In Progress")
        if self.in_progress:
            for task in self.in_progress:
                lines.append(f"- [{task['id']}] {task['title']}")
        else:
            lines.append("- No tasks in progress")
        lines.append("")

        # Blockers
        if self.blocked:
            lines.append("## Blockers")
            for task in self.blocked:
                reason = task.get('blocked_reason', 'Unknown')
                lines.append(f"- [{task['id']}] {task['title']}")
                lines.append(f"  - Reason: {reason}")
            lines.append("")

        # Up Next
        if self.ready:
            lines.append("## Up Next")
            for task in self.ready[:3]:  # Show top 3
                lines.append(f"- [{task['id']}] {task['title']} (P{task.get('priority', '?')})")
            lines.append("")

        # Stats
        lines.append("---")
        lines.append(f"*Completed: {self.total_completed} | In Progress: {self.total_in_progress} | Blocked: {self.total_blocked}*")

        return "\n".join(lines)

    def to_slack(self) -> str:
        """Generate Slack-formatted summary.

        Returns:
            Slack mrkdwn formatted string
        """
        lines = []

        date_str = datetime.now().strftime("%A, %B %d")
        lines.append(f":sunrise: *Daily Standup - {date_str}*")
        lines.append("")

        # Completed
        lines.append(":white_check_mark: *Completed*")
        if self.completed:
            for task in self.completed:
                lines.append(f"• `{task['id']}` {task['title']}")
        else:
            lines.append("• _No tasks completed_")
        lines.append("")

        # In Progress
        lines.append(":hammer_and_wrench: *In Progress*")
        if self.in_progress:
            for task in self.in_progress:
                lines.append(f"• `{task['id']}` {task['title']}")
        else:
            lines.append("• _No tasks in progress_")
        lines.append("")

        # Blockers
        if self.blocked:
            lines.append(":no_entry: *Blockers*")
            for task in self.blocked:
                reason = task.get('blocked_reason', 'Unknown')
                lines.append(f"• `{task['id']}` {task['title']} - _{reason}_")
            lines.append("")

        return "\n".join(lines)

    def to_trello_comment(self) -> str:
        """Generate comment for Trello weekly summary card.

        Returns:
            Formatted string for Trello comment
        """
        lines = []

        date_str = datetime.now().strftime("%Y-%m-%d")
        lines.append(f"## Standup Update - {date_str}")
        lines.append("")

        if self.completed:
            lines.append("**Completed:**")
            for task in self.completed:
                lines.append(f"- {task['id']}: {task['title']}")
            lines.append("")

        if self.in_progress:
            lines.append("**Working On:**")
            for task in self.in_progress:
                lines.append(f"- {task['id']}: {task['title']}")
            lines.append("")

        if self.blocked:
            lines.append("**Blocked:**")
            for task in self.blocked:
                lines.append(f"- {task['id']}: {task.get('blocked_reason', 'Unknown')}")

        return "\n".join(lines)


class StandupGenerator:
    """Generates daily standup summaries from task data."""

    def __init__(self, paircoder_dir: Path):
        """Initialize generator.

        Args:
            paircoder_dir: Path to .paircoder directory
        """
        self.paircoder_dir = Path(paircoder_dir)
        self.tasks_dir = self.paircoder_dir / "tasks"

    def generate(
        self,
        since_hours: int = 24,
        plan_id: Optional[str] = None,
    ) -> StandupSummary:
        """Generate standup summary.

        Args:
            since_hours: Look back period for completed tasks
            plan_id: Filter by plan ID (optional)

        Returns:
            StandupSummary instance
        """
        from .parser import TaskParser
        from .models import TaskStatus

        parser = TaskParser(self.tasks_dir)
        since = datetime.now() - timedelta(hours=since_hours)

        summary = StandupSummary(since=since, until=datetime.now())

        # Get all tasks
        if plan_id:
            tasks = parser.get_tasks_for_plan(plan_id)
        else:
            tasks = parser.parse_all()

        for task in tasks:
            task_dict = {
                "id": task.id,
                "title": task.title,
                "priority": task.priority,
                "plan_id": task.plan_id,
            }

            if task.status == TaskStatus.DONE:
                # Check if completed recently (if we have completion date)
                completed_at = getattr(task, 'completed_at', None)
                if completed_at and completed_at >= since:
                    summary.completed.append(task_dict)
                elif not completed_at:
                    # No completion date, include all done tasks for now
                    summary.completed.append(task_dict)
                summary.total_completed += 1

            elif task.status == TaskStatus.IN_PROGRESS:
                summary.in_progress.append(task_dict)
                summary.total_in_progress += 1

            elif task.status == TaskStatus.BLOCKED:
                task_dict["blocked_reason"] = getattr(task, 'blocked_reason', None) or "Not specified"
                summary.blocked.append(task_dict)
                summary.total_blocked += 1

            elif task.status == TaskStatus.PENDING:
                # Add to ready if high priority
                if task.priority in ("P0", "P1"):
                    summary.ready.append(task_dict)

        # Sort ready tasks by priority
        summary.ready.sort(key=lambda t: t.get("priority", "P9"))

        return summary

    def generate_for_trello_board(
        self,
        board_id: str,
        since_hours: int = 24,
    ) -> StandupSummary:
        """Generate standup summary from Trello board state.

        Args:
            board_id: Trello board ID
            since_hours: Look back period for completed tasks

        Returns:
            StandupSummary instance
        """
        try:
            from ..trello.auth import load_token
            from ..trello.client import TrelloService

            token_data = load_token()
            if not token_data:
                logger.warning("Trello not connected, using local tasks only")
                return self.generate(since_hours=since_hours)

            service = TrelloService(
                api_key=token_data["api_key"],
                token=token_data["token"]
            )
            service.set_board(board_id)

            summary = StandupSummary(
                since=datetime.now() - timedelta(hours=since_hours),
                until=datetime.now()
            )

            # Map list names to statuses
            list_status_map = {
                "Deployed / Done": "done",
                "Done": "done",
                "In Progress": "in_progress",
                "Issues / Tech Debt": "blocked",
                "Blocked": "blocked",
                "Planned / Ready": "ready",
                "Ready": "ready",
            }

            for list_name, status in list_status_map.items():
                try:
                    cards = service.get_cards_in_list(list_name)
                    for card in cards:
                        task_dict = {
                            "id": card.short_id,
                            "title": card.name,
                            "url": card.url,
                        }

                        if status == "done":
                            summary.completed.append(task_dict)
                            summary.total_completed += 1
                        elif status == "in_progress":
                            summary.in_progress.append(task_dict)
                            summary.total_in_progress += 1
                        elif status == "blocked":
                            summary.blocked.append(task_dict)
                            summary.total_blocked += 1
                        elif status == "ready":
                            summary.ready.append(task_dict)
                except Exception as e:
                    logger.debug(f"Could not get cards from {list_name}: {e}")

            return summary

        except ImportError:
            logger.warning("Trello module not available")
            return self.generate(since_hours=since_hours)
        except Exception as e:
            logger.error(f"Error generating Trello standup: {e}")
            return self.generate(since_hours=since_hours)


def generate_standup(
    paircoder_dir: Optional[Path] = None,
    plan_id: Optional[str] = None,
    since_hours: int = 24,
    format: str = "markdown",
) -> str:
    """Generate a standup summary string.

    Args:
        paircoder_dir: Path to .paircoder directory
        plan_id: Filter by plan ID (optional)
        since_hours: Look back period for completed tasks
        format: Output format (markdown, slack, trello)

    Returns:
        Formatted standup summary string
    """
    if paircoder_dir is None:
        from ..core.ops import find_paircoder_dir
        paircoder_dir = find_paircoder_dir()

    generator = StandupGenerator(paircoder_dir)
    summary = generator.generate(since_hours=since_hours, plan_id=plan_id)

    if format == "slack":
        return summary.to_slack()
    elif format == "trello":
        return summary.to_trello_comment()
    else:
        return summary.to_markdown()
