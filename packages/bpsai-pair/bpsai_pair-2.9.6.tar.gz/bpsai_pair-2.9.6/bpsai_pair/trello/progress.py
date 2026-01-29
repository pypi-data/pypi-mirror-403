"""
Progress reporter for Trello card comments.

Enables agents to post progress updates to Trello cards as they work on tasks.
"""

from datetime import datetime
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


# Progress comment templates
PROGRESS_TEMPLATES = {
    "started": "[{agent}] Started working on this task at {timestamp}",
    "progress": "[{agent}] Progress update: {message}",
    "completed_step": "[{agent}] Completed: {step_description}",
    "blocked": "[{agent}] Encountered issue: {issue}",
    "waiting": "[{agent}] Waiting for: {dependency}",
    "completed": "[{agent}] Task completed at {timestamp}\n\nSummary:\n{summary}",
    "review": "[{agent}] Submitted for review at {timestamp}",
}


class ProgressReporter:
    """Manages progress reporting to Trello cards."""

    def __init__(
        self,
        trello_service: Any,
        card_id: Optional[str] = None,
        task_id: Optional[str] = None,
        agent_name: str = "claude"
    ):
        """Initialize progress reporter.

        Args:
            trello_service: TrelloService instance
            card_id: Trello card ID (optional if task_id provided)
            task_id: Task ID to find card by prefix (optional if card_id provided)
            agent_name: Name of the agent making reports
        """
        self.service = trello_service
        self.agent = agent_name
        self.card = None
        self._card_id = card_id
        self._task_id = task_id

    def _get_card(self) -> Optional[Any]:
        """Get the card object, finding it if needed."""
        if self.card:
            return self.card

        if self._card_id:
            self.card, _ = self.service.find_card(self._card_id)
        elif self._task_id:
            self.card, _ = self.service.find_card_with_prefix(self._task_id)

        return self.card

    def _format_timestamp(self) -> str:
        """Get formatted current timestamp."""
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    def _post_comment(self, template_key: str, **kwargs) -> bool:
        """Post a comment using a template.

        Args:
            template_key: Key in PROGRESS_TEMPLATES
            **kwargs: Template variables

        Returns:
            True if comment was posted successfully
        """
        card = self._get_card()
        if not card:
            logger.warning("Could not find card for progress report")
            return False

        template = PROGRESS_TEMPLATES.get(template_key, "{message}")

        # Add common variables
        kwargs.setdefault("agent", self.agent)
        kwargs.setdefault("timestamp", self._format_timestamp())

        try:
            comment = template.format(**kwargs)
            self.service.add_comment(card, comment)
            logger.info(f"Posted progress comment: {template_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to post comment: {e}")
            return False

    def report_start(self) -> bool:
        """Report task start.

        Returns:
            True if comment was posted
        """
        return self._post_comment("started")

    def report_progress(self, message: str) -> bool:
        """Report progress update.

        Args:
            message: Progress message

        Returns:
            True if comment was posted
        """
        return self._post_comment("progress", message=message)

    def report_step_complete(self, step: str) -> bool:
        """Report completion of a step.

        Args:
            step: Description of completed step

        Returns:
            True if comment was posted
        """
        return self._post_comment("completed_step", step_description=step)

    def report_blocked(self, issue: str) -> bool:
        """Report a blocking issue.

        Args:
            issue: Description of the blocking issue

        Returns:
            True if comment was posted
        """
        return self._post_comment("blocked", issue=issue)

    def report_waiting(self, dependency: str) -> bool:
        """Report waiting for a dependency.

        Args:
            dependency: What we're waiting for

        Returns:
            True if comment was posted
        """
        return self._post_comment("waiting", dependency=dependency)

    def report_completion(self, summary: str) -> bool:
        """Report task completion with summary.

        Args:
            summary: Summary of what was accomplished

        Returns:
            True if comment was posted
        """
        return self._post_comment("completed", summary=summary)

    def report_review(self) -> bool:
        """Report task submitted for review.

        Returns:
            True if comment was posted
        """
        return self._post_comment("review")


def _load_config(paircoder_dir) -> dict:
    """Load configuration from config.yaml."""
    import yaml
    from pathlib import Path

    config_path = Path(paircoder_dir) / "config.yaml"
    if config_path.exists():
        return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return {}


def create_progress_reporter(
    paircoder_dir,
    task_id: str,
    agent_name: str = "claude"
) -> Optional[ProgressReporter]:
    """Factory to create a ProgressReporter for a task.

    Args:
        paircoder_dir: Path to .paircoder directory
        task_id: Task ID (e.g., 'TASK-001')
        agent_name: Name of the reporting agent

    Returns:
        ProgressReporter instance or None if Trello not configured
    """
    try:
        from .auth import load_token
        from .client import TrelloService

        token_data = load_token()
        if not token_data:
            logger.warning("Trello not connected")
            return None

        config = _load_config(paircoder_dir)
        trello_config = config.get("trello", {})
        board_id = trello_config.get("board_id")

        if not board_id:
            logger.warning("No Trello board configured")
            return None

        service = TrelloService(
            api_key=token_data["api_key"],
            token=token_data["token"]
        )
        service.set_board(board_id)

        return ProgressReporter(
            trello_service=service,
            task_id=task_id,
            agent_name=agent_name
        )

    except Exception as e:
        logger.error(f"Failed to create progress reporter: {e}")
        return None
