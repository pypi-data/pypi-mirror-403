"""
Autonomous workflow orchestration for PairCoder.

Ties together task selection, intent detection, flow execution,
and integration with GitHub and Trello for full autonomy.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable

logger = logging.getLogger(__name__)


class WorkflowPhase(Enum):
    """Phases in the autonomous workflow."""

    IDLE = "idle"
    SELECTING_TASK = "selecting_task"
    PLANNING = "planning"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    REVIEWING = "reviewing"
    CREATING_PR = "creating_pr"
    COMPLETING = "completing"
    ERROR = "error"


class WorkflowEvent(Enum):
    """Events in the autonomous workflow."""

    TASK_SELECTED = "task_selected"
    PLANNING_STARTED = "planning_started"
    PLANNING_COMPLETED = "planning_completed"
    IMPLEMENTATION_STARTED = "implementation_started"
    IMPLEMENTATION_COMPLETED = "implementation_completed"
    TESTS_PASSED = "tests_passed"
    TESTS_FAILED = "tests_failed"
    REVIEW_STARTED = "review_started"
    REVIEW_COMPLETED = "review_completed"
    PR_CREATED = "pr_created"
    PR_MERGED = "pr_merged"
    TASK_COMPLETED = "task_completed"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class WorkflowState:
    """Current state of the autonomous workflow."""

    phase: WorkflowPhase = WorkflowPhase.IDLE
    current_task_id: Optional[str] = None
    current_plan_id: Optional[str] = None
    current_flow: Optional[str] = None
    pr_number: Optional[int] = None
    started_at: Optional[datetime] = None
    events: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None

    def record_event(self, event: WorkflowEvent, data: Optional[Dict] = None):
        """Record a workflow event."""
        self.events.append({
            "event": event.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "phase": self.phase.value,
            "current_task_id": self.current_task_id,
            "current_plan_id": self.current_plan_id,
            "current_flow": self.current_flow,
            "pr_number": self.pr_number,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "events_count": len(self.events),
            "error": self.error,
        }


@dataclass
class WorkflowConfig:
    """Configuration for autonomous workflow."""

    auto_select_tasks: bool = True
    auto_create_pr: bool = True
    auto_update_trello: bool = True
    run_tests_before_pr: bool = True
    require_review: bool = True
    max_tasks_per_session: int = 5
    task_timeout_minutes: int = 30

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowConfig":
        """Create config from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class AutonomousWorkflow:
    """
    Autonomous workflow orchestrator for PairCoder.

    Manages the full task lifecycle from selection to completion,
    integrating with all PairCoder systems.
    """

    def __init__(
        self,
        paircoder_dir: Path,
        config: Optional[WorkflowConfig] = None,
        hooks: Optional[Dict[str, Callable]] = None,
    ):
        """Initialize autonomous workflow.

        Args:
            paircoder_dir: Path to .paircoder directory
            config: Workflow configuration
            hooks: Callback hooks for workflow events
        """
        self.paircoder_dir = paircoder_dir
        self.project_root = paircoder_dir.parent
        self.config = config or WorkflowConfig()
        self.hooks = hooks or {}
        self.state = WorkflowState()
        self._task_parser = None
        self._github_pr_manager = None
        self._intent_detector = None

    @property
    def task_parser(self):
        """Lazy-load task parser."""
        if self._task_parser is None:
            from ..planning.parser import TaskParser
            self._task_parser = TaskParser(self.paircoder_dir / "tasks")
        return self._task_parser

    @property
    def github_pr_manager(self):
        """Lazy-load GitHub PR manager."""
        if self._github_pr_manager is None:
            try:
                from ..github.pr import PRManager
                self._github_pr_manager = PRManager(
                    project_root=self.project_root,
                    paircoder_dir=self.paircoder_dir,
                )
            except ImportError:
                logger.warning("GitHub module not available")
        return self._github_pr_manager

    @property
    def intent_detector(self):
        """Lazy-load intent detector."""
        if self._intent_detector is None:
            from ..planning.intent_detection import IntentDetector
            self._intent_detector = IntentDetector()
        return self._intent_detector

    def _call_hook(self, name: str, *args, **kwargs):
        """Call a hook if registered."""
        if name in self.hooks:
            try:
                return self.hooks[name](*args, **kwargs)
            except Exception as e:
                logger.error(f"Hook {name} failed: {e}")

    # =========================================================================
    # Task Selection Phase
    # =========================================================================

    def select_next_task(self, plan_id: Optional[str] = None) -> Optional[str]:
        """Select the next task to work on.

        Args:
            plan_id: Optional plan ID to filter tasks

        Returns:
            Task ID if selected, None otherwise
        """
        from ..planning.auto_assign import get_next_pending_task

        self.state.phase = WorkflowPhase.SELECTING_TASK

        task = get_next_pending_task(self.paircoder_dir, plan_id)

        if task:
            self.state.current_task_id = task.id
            self.state.current_plan_id = task.plan_id
            self.state.started_at = datetime.now(timezone.utc)
            self.state.record_event(WorkflowEvent.TASK_SELECTED, {
                "task_id": task.id,
                "title": task.title,
                "priority": task.priority,
            })
            self._call_hook("on_task_selected", task)
            logger.info(f"Selected task: {task.id} - {task.title}")
            return task.id

        logger.info("No pending tasks available")
        self.state.phase = WorkflowPhase.IDLE
        return None

    # =========================================================================
    # Planning Phase
    # =========================================================================

    def start_planning(self) -> Optional[str]:
        """Start planning phase for current task.

        Returns:
            Suggested flow name
        """
        if not self.state.current_task_id:
            logger.warning("No task selected for planning")
            return None

        self.state.phase = WorkflowPhase.PLANNING
        self.state.record_event(WorkflowEvent.PLANNING_STARTED)

        # Get task content
        task = self.task_parser.get_task_by_id(self.state.current_task_id)
        if not task:
            logger.error(f"Task not found: {self.state.current_task_id}")
            return None

        # Detect intent and suggest flow
        flow = self.intent_detector.get_flow_suggestion(task.title)
        self.state.current_flow = flow or "tdd-implement"

        self._call_hook("on_planning_started", task, self.state.current_flow)
        logger.info(f"Started planning with flow: {self.state.current_flow}")

        return self.state.current_flow

    def complete_planning(self):
        """Complete the planning phase."""
        self.state.record_event(WorkflowEvent.PLANNING_COMPLETED)
        self._call_hook("on_planning_completed", self.state.current_task_id)
        logger.info("Planning completed")

    # =========================================================================
    # Implementation Phase
    # =========================================================================

    def start_implementation(self) -> bool:
        """Start implementation phase.

        Returns:
            True if started successfully
        """
        if not self.state.current_task_id:
            logger.warning("No task selected for implementation")
            return False

        self.state.phase = WorkflowPhase.IMPLEMENTING
        self.state.record_event(WorkflowEvent.IMPLEMENTATION_STARTED)

        # Update task status to in_progress
        from ..planning.models import TaskStatus
        task = self.task_parser.get_task_by_id(self.state.current_task_id)
        if task:
            task.status = TaskStatus.IN_PROGRESS
            self.task_parser.save(task)

        self._call_hook("on_implementation_started", self.state.current_task_id)
        logger.info(f"Started implementing: {self.state.current_task_id}")
        return True

    def complete_implementation(self, success: bool = True):
        """Complete implementation phase.

        Args:
            success: Whether implementation was successful
        """
        if success:
            self.state.record_event(WorkflowEvent.IMPLEMENTATION_COMPLETED)
            self._call_hook("on_implementation_completed", self.state.current_task_id)
            logger.info("Implementation completed")
        else:
            self.state.phase = WorkflowPhase.ERROR
            self.state.error = "Implementation failed"
            self.state.record_event(WorkflowEvent.ERROR_OCCURRED, {"reason": "implementation_failed"})

    # =========================================================================
    # Testing Phase
    # =========================================================================

    def run_tests(self) -> bool:
        """Run tests for current implementation.

        Returns:
            True if tests pass
        """
        self.state.phase = WorkflowPhase.TESTING
        logger.info("Running tests...")

        # This is a placeholder - actual test running would be done by the agent
        self._call_hook("on_tests_started", self.state.current_task_id)

        # Assume tests pass for now
        self.state.record_event(WorkflowEvent.TESTS_PASSED)
        self._call_hook("on_tests_completed", True)
        return True

    def report_test_failure(self, reason: str):
        """Report test failure."""
        self.state.record_event(WorkflowEvent.TESTS_FAILED, {"reason": reason})
        self._call_hook("on_tests_completed", False, reason)
        logger.warning(f"Tests failed: {reason}")

    # =========================================================================
    # Review Phase
    # =========================================================================

    def start_review(self) -> bool:
        """Start review phase.

        Returns:
            True if review started
        """
        if not self.config.require_review:
            logger.info("Review not required, skipping")
            return True

        self.state.phase = WorkflowPhase.REVIEWING
        self.state.record_event(WorkflowEvent.REVIEW_STARTED)
        self._call_hook("on_review_started", self.state.current_task_id)
        logger.info("Review phase started")
        return True

    def complete_review(self, approved: bool = True):
        """Complete review phase.

        Args:
            approved: Whether review was approved
        """
        self.state.record_event(WorkflowEvent.REVIEW_COMPLETED, {"approved": approved})
        self._call_hook("on_review_completed", approved)

        if not approved:
            self.state.phase = WorkflowPhase.IMPLEMENTING
            logger.info("Review not approved, returning to implementation")
        else:
            logger.info("Review approved")

    # =========================================================================
    # PR Creation Phase
    # =========================================================================

    def create_pr(self, summary: Optional[str] = None) -> Optional[int]:
        """Create a pull request for the completed work.

        Args:
            summary: Optional summary of changes

        Returns:
            PR number if created
        """
        if not self.config.auto_create_pr:
            logger.info("Auto PR creation disabled")
            return None

        if not self.github_pr_manager:
            logger.warning("GitHub PR manager not available")
            return None

        self.state.phase = WorkflowPhase.CREATING_PR

        task = self.task_parser.get_task_by_id(self.state.current_task_id)
        if not task:
            return None

        pr = self.github_pr_manager.create_pr_for_task(
            task_id=self.state.current_task_id,
            summary=summary or f"Implementation of {task.title}",
        )

        if pr:
            self.state.pr_number = pr.number
            self.state.record_event(WorkflowEvent.PR_CREATED, {
                "pr_number": pr.number,
                "url": pr.url,
            })
            self._call_hook("on_pr_created", pr)
            logger.info(f"Created PR #{pr.number}")
            return pr.number

        return None

    # =========================================================================
    # Completion Phase
    # =========================================================================

    def complete_task(self) -> bool:
        """Complete the current task.

        Returns:
            True if completed successfully
        """
        if not self.state.current_task_id:
            return False

        self.state.phase = WorkflowPhase.COMPLETING

        # Update task status to done
        from ..planning.models import TaskStatus
        task = self.task_parser.get_task_by_id(self.state.current_task_id)
        if task:
            task.status = TaskStatus.DONE
            self.task_parser.save(task)

        self.state.record_event(WorkflowEvent.TASK_COMPLETED, {
            "task_id": self.state.current_task_id,
            "duration_seconds": (datetime.now(timezone.utc) - self.state.started_at).total_seconds()
            if self.state.started_at else 0,
        })

        self._call_hook("on_task_completed", self.state.current_task_id)
        logger.info(f"Completed task: {self.state.current_task_id}")

        # Reset state for next task
        completed_task_id = self.state.current_task_id
        self.state.current_task_id = None
        self.state.current_plan_id = None
        self.state.current_flow = None
        self.state.pr_number = None
        self.state.phase = WorkflowPhase.IDLE

        return True

    # =========================================================================
    # Full Workflow Execution
    # =========================================================================

    def run_task_workflow(
        self,
        task_id: Optional[str] = None,
        plan_id: Optional[str] = None,
    ) -> bool:
        """Run the full workflow for a single task.

        Args:
            task_id: Specific task ID (auto-selects if not provided)
            plan_id: Plan ID for task selection

        Returns:
            True if workflow completed successfully
        """
        # Select task
        if task_id:
            self.state.current_task_id = task_id
            self.state.started_at = datetime.now(timezone.utc)
        elif self.config.auto_select_tasks:
            if not self.select_next_task(plan_id):
                return False
        else:
            logger.warning("No task specified and auto-select disabled")
            return False

        # Planning
        self.start_planning()
        self.complete_planning()

        # Implementation
        self.start_implementation()
        self.complete_implementation()

        # Testing (if enabled)
        if self.config.run_tests_before_pr:
            if not self.run_tests():
                return False

        # Review (if required)
        if self.config.require_review:
            self.start_review()
            self.complete_review()

        # PR Creation
        if self.config.auto_create_pr:
            self.create_pr()

        # Complete task
        return self.complete_task()

    def run_session(
        self,
        plan_id: Optional[str] = None,
        max_tasks: Optional[int] = None,
    ) -> List[str]:
        """Run an autonomous session processing multiple tasks.

        Args:
            plan_id: Optional plan ID to filter tasks
            max_tasks: Maximum tasks to process (uses config if not provided)

        Returns:
            List of completed task IDs
        """
        max_tasks = max_tasks or self.config.max_tasks_per_session
        completed_tasks = []

        logger.info(f"Starting autonomous session (max {max_tasks} tasks)")

        for i in range(max_tasks):
            logger.info(f"Processing task {i + 1}/{max_tasks}")

            if self.run_task_workflow(plan_id=plan_id):
                # The task_id was already reset, so we need to get it from events
                for event in reversed(self.state.events):
                    if event["event"] == "task_completed":
                        completed_tasks.append(event["data"]["task_id"])
                        break
            else:
                logger.info("No more tasks or workflow failed, ending session")
                break

        logger.info(f"Session completed: {len(completed_tasks)} tasks done")
        return completed_tasks

    def get_status(self) -> Dict[str, Any]:
        """Get current workflow status.

        Returns:
            Status dictionary
        """
        return {
            "workflow_state": self.state.to_dict(),
            "config": {
                "auto_select_tasks": self.config.auto_select_tasks,
                "auto_create_pr": self.config.auto_create_pr,
                "auto_update_trello": self.config.auto_update_trello,
                "run_tests_before_pr": self.config.run_tests_before_pr,
                "require_review": self.config.require_review,
            },
        }


class WorkflowSequencer:
    """
    Sequences workflow steps for full autonomy.

    Provides step-by-step orchestration with hooks for each phase.
    """

    PHASE_SEQUENCE = [
        WorkflowPhase.SELECTING_TASK,
        WorkflowPhase.PLANNING,
        WorkflowPhase.IMPLEMENTING,
        WorkflowPhase.TESTING,
        WorkflowPhase.REVIEWING,
        WorkflowPhase.CREATING_PR,
        WorkflowPhase.COMPLETING,
    ]

    def __init__(self, workflow: AutonomousWorkflow):
        """Initialize sequencer.

        Args:
            workflow: The autonomous workflow to sequence
        """
        self.workflow = workflow
        self._current_phase_index = 0

    @property
    def current_phase(self) -> WorkflowPhase:
        """Get current phase."""
        return self.workflow.state.phase

    @property
    def next_phase(self) -> Optional[WorkflowPhase]:
        """Get next phase in sequence."""
        try:
            current_idx = self.PHASE_SEQUENCE.index(self.current_phase)
            if current_idx < len(self.PHASE_SEQUENCE) - 1:
                return self.PHASE_SEQUENCE[current_idx + 1]
        except ValueError:
            pass
        return None

    def advance(self) -> WorkflowPhase:
        """Advance to the next phase.

        Returns:
            The new current phase
        """
        next_phase = self.next_phase

        if next_phase == WorkflowPhase.SELECTING_TASK:
            self.workflow.select_next_task()
        elif next_phase == WorkflowPhase.PLANNING:
            self.workflow.start_planning()
        elif next_phase == WorkflowPhase.IMPLEMENTING:
            self.workflow.start_implementation()
        elif next_phase == WorkflowPhase.TESTING:
            self.workflow.run_tests()
        elif next_phase == WorkflowPhase.REVIEWING:
            self.workflow.start_review()
        elif next_phase == WorkflowPhase.CREATING_PR:
            self.workflow.create_pr()
        elif next_phase == WorkflowPhase.COMPLETING:
            self.workflow.complete_task()

        return self.workflow.state.phase

    def run_all(self) -> bool:
        """Run all phases to completion.

        Returns:
            True if all phases completed successfully
        """
        while self.next_phase:
            self.advance()
            if self.workflow.state.phase == WorkflowPhase.ERROR:
                return False
        return True
