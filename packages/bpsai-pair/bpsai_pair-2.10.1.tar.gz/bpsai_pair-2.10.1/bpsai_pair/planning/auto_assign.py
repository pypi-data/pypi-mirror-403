"""
Automatic task assignment for PairCoder.

Provides functionality to automatically assign and start the next
highest-priority task when a task is completed.
"""
import logging
from pathlib import Path
from typing import Optional, Callable

from .models import Task, TaskStatus
from .parser import TaskParser

logger = logging.getLogger(__name__)


def get_next_pending_task(
    paircoder_dir: Path,
    plan_id: Optional[str] = None,
) -> Optional[Task]:
    """Get the next pending task by priority.

    Args:
        paircoder_dir: Path to .paircoder directory
        plan_id: Optional plan ID to filter tasks

    Returns:
        Next pending task or None
    """
    task_parser = TaskParser(paircoder_dir / "tasks")

    # Get all tasks
    if plan_id:
        tasks = task_parser.get_tasks_for_plan(plan_id)
    else:
        tasks = task_parser.parse_all()

    # Filter to pending only
    pending = [t for t in tasks if t.status == TaskStatus.PENDING]

    if not pending:
        return None

    # Sort by priority (P0 > P1 > P2) then by complexity (lower first)
    pending.sort(key=lambda t: (t.priority, t.complexity))

    return pending[0]


def auto_assign_next(
    paircoder_dir: Path,
    plan_id: Optional[str] = None,
    trello_callback: Optional[Callable[[Task], None]] = None,
) -> Optional[Task]:
    """Automatically assign the next pending task.

    Args:
        paircoder_dir: Path to .paircoder directory
        plan_id: Optional plan ID to filter tasks
        trello_callback: Optional callback to update Trello card

    Returns:
        The assigned task or None if no tasks available
    """
    task = get_next_pending_task(paircoder_dir, plan_id)

    if not task:
        logger.info("No pending tasks available for auto-assignment")
        return None

    # Update task status to in_progress
    task_parser = TaskParser(paircoder_dir / "tasks")
    task.status = TaskStatus.IN_PROGRESS
    task_parser.save(task)

    logger.info(f"Auto-assigned task: {task.id} - {task.title}")

    # Trigger Trello callback if provided
    if trello_callback:
        try:
            trello_callback(task)
        except Exception as e:
            logger.error(f"Error updating Trello for {task.id}: {e}")

    return task


def create_completion_handler(
    paircoder_dir: Path,
    auto_assign: bool = True,
    api_key: Optional[str] = None,
    token: Optional[str] = None,
) -> Callable[[str], Optional[Task]]:
    """Create a handler for task completion that optionally auto-assigns next task.

    Args:
        paircoder_dir: Path to .paircoder directory
        auto_assign: Whether to auto-assign next task
        api_key: Trello API key (for card updates)
        token: Trello API token (for card updates)

    Returns:
        Completion handler function
    """

    def on_task_complete(completed_task_id: str) -> Optional[Task]:
        """Handle task completion and optionally assign next task.

        Args:
            completed_task_id: ID of the completed task

        Returns:
            Next assigned task or None
        """
        logger.info(f"Task completed: {completed_task_id}")

        if not auto_assign:
            return None

        # Get plan ID from completed task
        task_parser = TaskParser(paircoder_dir / "tasks")
        completed_task = task_parser.get_task_by_id(completed_task_id)
        plan_id = completed_task.plan_id if completed_task else None

        # Create Trello callback if credentials available
        trello_callback = None
        if api_key and token:
            def update_trello_card(task: Task):
                """Move task's Trello card to In Progress."""
                # This would need the card ID from the task
                # For now, just log the intent
                logger.info(f"Would update Trello card for {task.id}")

            trello_callback = update_trello_card

        # Auto-assign next task
        return auto_assign_next(
            paircoder_dir=paircoder_dir,
            plan_id=plan_id,
            trello_callback=trello_callback,
        )

    return on_task_complete


class AutoAssigner:
    """Automatic task assignment manager."""

    def __init__(
        self,
        paircoder_dir: Path,
        enabled: bool = True,
        trello_api_key: Optional[str] = None,
        trello_token: Optional[str] = None,
    ):
        """Initialize auto-assigner.

        Args:
            paircoder_dir: Path to .paircoder directory
            enabled: Whether auto-assignment is enabled
            trello_api_key: Trello API key for card updates
            trello_token: Trello API token for card updates
        """
        self.paircoder_dir = paircoder_dir
        self.enabled = enabled
        self.api_key = trello_api_key
        self.token = trello_token
        self.task_parser = TaskParser(paircoder_dir / "tasks")

    def get_next(self, plan_id: Optional[str] = None) -> Optional[Task]:
        """Get next pending task."""
        return get_next_pending_task(self.paircoder_dir, plan_id)

    def assign_next(self, plan_id: Optional[str] = None) -> Optional[Task]:
        """Assign the next pending task.

        Returns:
            The assigned task or None
        """
        if not self.enabled:
            logger.debug("Auto-assignment disabled")
            return None

        task = self.get_next(plan_id)
        if not task:
            return None

        # Update to in_progress
        task.status = TaskStatus.IN_PROGRESS
        self.task_parser.save(task)

        logger.info(f"Auto-assigned: {task.id} ({task.priority}, complexity {task.complexity})")

        # Update Trello if configured
        if self.api_key and self.token:
            self._update_trello(task)

        return task

    def on_complete(self, task_id: str) -> Optional[Task]:
        """Handle task completion.

        Args:
            task_id: ID of completed task

        Returns:
            Next assigned task or None
        """
        task = self.task_parser.get_task_by_id(task_id)
        plan_id = task.plan_id if task else None

        return self.assign_next(plan_id)

    def _update_trello(self, task: Task) -> None:
        """Update Trello card for assigned task."""

        # Would need card ID mapping from task
        # This is a placeholder for future enhancement
        logger.debug(f"Trello update for {task.id} not implemented yet")
