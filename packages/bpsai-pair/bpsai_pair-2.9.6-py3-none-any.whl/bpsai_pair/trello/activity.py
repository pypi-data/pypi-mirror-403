"""
Trello activity logging module.

Provides structured activity logging as Trello card comments for status changes
and agent activity.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any
import logging

from .client import TrelloService

logger = logging.getLogger(__name__)


class ActivityEvent(str, Enum):
    """Types of activity events that can be logged."""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_BLOCKED = "task_blocked"
    PR_CREATED = "pr_created"
    PR_MERGED = "pr_merged"
    PROGRESS = "progress"


# Comment format templates for each event type
COMMENT_FORMATS = {
    ActivityEvent.TASK_STARTED: "🚀 Started by {agent} at {time}",
    ActivityEvent.TASK_COMPLETED: "✅ Completed: {summary}",
    ActivityEvent.TASK_BLOCKED: "🚫 Blocked: {reason}",
    ActivityEvent.PR_CREATED: "🔗 PR opened: {pr_url}",
    ActivityEvent.PR_MERGED: "🎉 PR merged!",
    ActivityEvent.PROGRESS: "📝 Progress: {note}",
}


def format_activity_comment(
    event: ActivityEvent,
    agent: Optional[str] = None,
    summary: Optional[str] = None,
    reason: Optional[str] = None,
    pr_url: Optional[str] = None,
    note: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> str:
    """Format an activity comment for a given event.

    Args:
        event: Type of activity event
        agent: Agent name (for TASK_STARTED)
        summary: Completion summary (for TASK_COMPLETED)
        reason: Block reason (for TASK_BLOCKED)
        pr_url: Pull request URL (for PR_CREATED)
        note: Progress note (for PROGRESS)
        timestamp: Event timestamp (defaults to now)

    Returns:
        Formatted comment string
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    time_str = timestamp.strftime("%H:%M UTC")

    template = COMMENT_FORMATS.get(event, "📋 Activity: {note}")

    # Build format kwargs
    kwargs = {
        "agent": agent or "Agent",
        "summary": summary or "Task completed",
        "reason": reason or "No reason provided",
        "pr_url": pr_url or "",
        "note": note or "",
        "time": time_str,
    }

    return template.format(**kwargs)


class TrelloActivityLogger:
    """Logs activity events as Trello card comments."""

    def __init__(self, service: TrelloService):
        """Initialize activity logger.

        Args:
            service: Configured TrelloService with board set
        """
        self.service = service

    def _find_card(self, task_id: str) -> Optional[Any]:
        """Find a card by task ID.

        Args:
            task_id: Task ID (e.g., 'TASK-001')

        Returns:
            Card object or None if not found
        """
        card, _ = self.service.find_card_with_prefix(task_id)
        return card

    def log_event(
        self,
        task_id: str,
        event: ActivityEvent,
        **kwargs
    ) -> bool:
        """Log an activity event as a card comment.

        Args:
            task_id: Task ID (e.g., 'TASK-001')
            event: Activity event type
            **kwargs: Event-specific parameters (agent, summary, reason, etc.)

        Returns:
            True if comment was added, False if card not found or error
        """
        card = self._find_card(task_id)
        if not card:
            logger.warning(f"Card not found for task: {task_id}")
            return False

        try:
            comment = format_activity_comment(event, **kwargs)
            self.service.add_comment(card, comment)
            logger.info(f"Logged {event.value} for {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to log activity for {task_id}: {e}")
            return False

    def log_task_started(
        self,
        task_id: str,
        agent: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Log task started event.

        Args:
            task_id: Task ID
            agent: Agent name that started the task
            timestamp: Event timestamp (defaults to now)

        Returns:
            True if comment was added
        """
        return self.log_event(
            task_id,
            ActivityEvent.TASK_STARTED,
            agent=agent,
            timestamp=timestamp
        )

    def log_task_completed(
        self,
        task_id: str,
        summary: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Log task completed event.

        Args:
            task_id: Task ID
            summary: Completion summary
            timestamp: Event timestamp (defaults to now)

        Returns:
            True if comment was added
        """
        return self.log_event(
            task_id,
            ActivityEvent.TASK_COMPLETED,
            summary=summary,
            timestamp=timestamp
        )

    def log_task_blocked(
        self,
        task_id: str,
        reason: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Log task blocked event.

        Args:
            task_id: Task ID
            reason: Block reason
            timestamp: Event timestamp (defaults to now)

        Returns:
            True if comment was added
        """
        return self.log_event(
            task_id,
            ActivityEvent.TASK_BLOCKED,
            reason=reason,
            timestamp=timestamp
        )

    def log_pr_created(
        self,
        task_id: str,
        pr_url: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Log PR created event.

        Args:
            task_id: Task ID
            pr_url: Pull request URL
            timestamp: Event timestamp (defaults to now)

        Returns:
            True if comment was added
        """
        return self.log_event(
            task_id,
            ActivityEvent.PR_CREATED,
            pr_url=pr_url,
            timestamp=timestamp
        )

    def log_pr_merged(
        self,
        task_id: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Log PR merged event.

        Args:
            task_id: Task ID
            timestamp: Event timestamp (defaults to now)

        Returns:
            True if comment was added
        """
        return self.log_event(
            task_id,
            ActivityEvent.PR_MERGED,
            timestamp=timestamp
        )

    def log_progress(
        self,
        task_id: str,
        note: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Log progress event.

        Args:
            task_id: Task ID
            note: Progress note
            timestamp: Event timestamp (defaults to now)

        Returns:
            True if comment was added
        """
        return self.log_event(
            task_id,
            ActivityEvent.PROGRESS,
            note=note,
            timestamp=timestamp
        )


def create_activity_logger(
    api_key: str,
    token: str,
    board_id: str
) -> TrelloActivityLogger:
    """Create a TrelloActivityLogger from credentials.

    Args:
        api_key: Trello API key
        token: Trello API token
        board_id: Board ID to log activity to

    Returns:
        Configured TrelloActivityLogger
    """
    service = TrelloService(api_key, token)
    service.set_board(board_id)
    return TrelloActivityLogger(service)
