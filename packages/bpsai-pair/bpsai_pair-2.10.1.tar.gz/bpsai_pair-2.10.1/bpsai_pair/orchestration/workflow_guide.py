"""
Workflow Guide for PairCoder Agents.

This module codifies the standard workflow process that all agents
must follow when working with tasks and Trello boards.

Workflow Stages:
1. INTAKE - New tasks arrive in "Intake/Backlog"
2. PLANNED - Tasks with full implementation plans move to "Planned/Ready"
3. IN_PROGRESS - Active development work
4. REVIEW - Testing and verification
5. DONE - Completed and verified
6. BLOCKED - Issues or tech debt requiring attention
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """Standard workflow stages for task lifecycle."""

    INTAKE = "intake"           # New tasks, not yet planned
    PLANNED = "planned"         # Fully planned, ready to work
    IN_PROGRESS = "in_progress" # Active development
    REVIEW = "review"           # Testing and verification
    DONE = "done"               # Completed and verified
    BLOCKED = "blocked"         # Issues or blockers


# Map workflow stages to Trello list names
STAGE_TO_LIST: Dict[WorkflowStage, str] = {
    WorkflowStage.INTAKE: "Intake/Backlog",
    WorkflowStage.PLANNED: "Planned/Ready",
    WorkflowStage.IN_PROGRESS: "In Progress",
    WorkflowStage.REVIEW: "Review/Testing",
    WorkflowStage.DONE: "Deployed/Done",
    WorkflowStage.BLOCKED: "Issues/Tech Debt",
}

# Map Trello list names to workflow stages
LIST_TO_STAGE: Dict[str, WorkflowStage] = {
    "Intake/Backlog": WorkflowStage.INTAKE,
    "Backlog": WorkflowStage.INTAKE,
    "Planned/Ready": WorkflowStage.PLANNED,
    "Ready": WorkflowStage.PLANNED,
    "In Progress": WorkflowStage.IN_PROGRESS,
    "Review/Testing": WorkflowStage.REVIEW,
    "Review": WorkflowStage.REVIEW,
    "Testing": WorkflowStage.REVIEW,
    "Deployed/Done": WorkflowStage.DONE,
    "Done": WorkflowStage.DONE,
    "Issues/Tech Debt": WorkflowStage.BLOCKED,
    "Blocked": WorkflowStage.BLOCKED,
}

# Map task status to workflow stage
STATUS_TO_STAGE: Dict[str, WorkflowStage] = {
    "pending": WorkflowStage.INTAKE,
    "backlog": WorkflowStage.INTAKE,
    "ready": WorkflowStage.PLANNED,
    "planned": WorkflowStage.PLANNED,
    "in_progress": WorkflowStage.IN_PROGRESS,
    "review": WorkflowStage.REVIEW,
    "testing": WorkflowStage.REVIEW,
    "done": WorkflowStage.DONE,
    "deployed": WorkflowStage.DONE,
    "blocked": WorkflowStage.BLOCKED,
    "issue": WorkflowStage.BLOCKED,
}


@dataclass
class WorkflowRequirement:
    """Requirements for a task to be in a workflow stage."""

    stage: WorkflowStage
    required_fields: List[str]
    optional_fields: List[str]
    description: str


# Requirements for each workflow stage
STAGE_REQUIREMENTS: Dict[WorkflowStage, WorkflowRequirement] = {
    WorkflowStage.INTAKE: WorkflowRequirement(
        stage=WorkflowStage.INTAKE,
        required_fields=["id", "title"],
        optional_fields=["description", "type"],
        description="New task with basic info. Needs planning before work begins.",
    ),
    WorkflowStage.PLANNED: WorkflowRequirement(
        stage=WorkflowStage.PLANNED,
        required_fields=["id", "title", "objective", "implementation_plan", "acceptance_criteria"],
        optional_fields=["depends_on", "complexity", "priority"],
        description="Fully planned task ready for implementation. Has clear objective, plan, and acceptance criteria.",
    ),
    WorkflowStage.IN_PROGRESS: WorkflowRequirement(
        stage=WorkflowStage.IN_PROGRESS,
        required_fields=["id", "title", "objective", "implementation_plan", "acceptance_criteria"],
        optional_fields=["current_step", "agent"],
        description="Task being actively worked on. Agent assigned and making progress.",
    ),
    WorkflowStage.REVIEW: WorkflowRequirement(
        stage=WorkflowStage.REVIEW,
        required_fields=["id", "title", "implementation_summary", "verification_steps"],
        optional_fields=["test_results", "pr_link"],
        description="Implementation complete. Under review or testing before final completion.",
    ),
    WorkflowStage.DONE: WorkflowRequirement(
        stage=WorkflowStage.DONE,
        required_fields=["id", "title", "implementation_summary", "verification"],
        optional_fields=["pr_link", "deployed_at"],
        description="Task completed, verified, and deployed if applicable.",
    ),
    WorkflowStage.BLOCKED: WorkflowRequirement(
        stage=WorkflowStage.BLOCKED,
        required_fields=["id", "title", "block_reason"],
        optional_fields=["blocked_by", "unblock_steps"],
        description="Task blocked by an issue. Needs attention to resolve blocker.",
    ),
}


class WorkflowGuide:
    """
    Guide for managing task workflow.

    This class provides methods to:
    - Check if a task meets requirements for a stage
    - Determine valid stage transitions
    - Get guidance for moving tasks between stages
    - Ensure agents follow the correct workflow
    """

    # Valid stage transitions
    VALID_TRANSITIONS = {
        WorkflowStage.INTAKE: [WorkflowStage.PLANNED, WorkflowStage.BLOCKED],
        WorkflowStage.PLANNED: [WorkflowStage.IN_PROGRESS, WorkflowStage.BLOCKED, WorkflowStage.INTAKE],
        WorkflowStage.IN_PROGRESS: [WorkflowStage.REVIEW, WorkflowStage.BLOCKED, WorkflowStage.PLANNED],
        WorkflowStage.REVIEW: [WorkflowStage.DONE, WorkflowStage.IN_PROGRESS, WorkflowStage.BLOCKED],
        WorkflowStage.DONE: [],  # Terminal state
        WorkflowStage.BLOCKED: [WorkflowStage.INTAKE, WorkflowStage.PLANNED, WorkflowStage.IN_PROGRESS],
    }

    def __init__(self, paircoder_dir: Optional[Path] = None):
        """Initialize workflow guide.

        Args:
            paircoder_dir: Path to .paircoder directory
        """
        self.paircoder_dir = paircoder_dir

    def get_stage_for_status(self, status: str) -> WorkflowStage:
        """Get workflow stage for a task status.

        Args:
            status: Task status string

        Returns:
            Corresponding workflow stage
        """
        return STATUS_TO_STAGE.get(status.lower(), WorkflowStage.INTAKE)

    def get_list_for_stage(self, stage: WorkflowStage) -> str:
        """Get Trello list name for a workflow stage.

        Args:
            stage: Workflow stage

        Returns:
            Trello list name
        """
        return STAGE_TO_LIST[stage]

    def get_stage_for_list(self, list_name: str) -> Optional[WorkflowStage]:
        """Get workflow stage for a Trello list name.

        Args:
            list_name: Trello list name

        Returns:
            Workflow stage or None if unknown
        """
        return LIST_TO_STAGE.get(list_name)

    def can_transition(self, from_stage: WorkflowStage, to_stage: WorkflowStage) -> bool:
        """Check if a stage transition is valid.

        Args:
            from_stage: Current stage
            to_stage: Target stage

        Returns:
            True if transition is valid
        """
        return to_stage in self.VALID_TRANSITIONS.get(from_stage, [])

    def get_valid_transitions(self, current_stage: WorkflowStage) -> List[WorkflowStage]:
        """Get valid transitions from current stage.

        Args:
            current_stage: Current workflow stage

        Returns:
            List of valid target stages
        """
        return self.VALID_TRANSITIONS.get(current_stage, [])

    def get_requirements(self, stage: WorkflowStage) -> WorkflowRequirement:
        """Get requirements for a workflow stage.

        Args:
            stage: Workflow stage

        Returns:
            Requirements for the stage
        """
        return STAGE_REQUIREMENTS[stage]

    def check_requirements(self, task: Any, stage: WorkflowStage) -> tuple[bool, List[str]]:
        """Check if a task meets requirements for a stage.

        Args:
            task: Task object to check
            stage: Target stage

        Returns:
            Tuple of (passes, list of missing fields)
        """
        requirements = STAGE_REQUIREMENTS[stage]
        missing = []

        for field in requirements.required_fields:
            value = getattr(task, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(field)

        return len(missing) == 0, missing

    def get_guidance(self, from_stage: WorkflowStage, to_stage: WorkflowStage) -> str:
        """Get guidance for transitioning between stages.

        Args:
            from_stage: Current stage
            to_stage: Target stage

        Returns:
            Guidance text
        """
        guidance_map = {
            (WorkflowStage.INTAKE, WorkflowStage.PLANNED): """
Before moving to Planned / Ready:
1. Write a clear objective describing what the task accomplishes
2. Create a detailed implementation plan with numbered steps
3. Define acceptance criteria (checkboxes) that can verify completion
4. Estimate complexity (optional but recommended)
5. Identify any dependencies on other tasks
""",
            (WorkflowStage.PLANNED, WorkflowStage.IN_PROGRESS): """
Before starting work:
1. Verify all dependencies are complete
2. Review the implementation plan
3. Set up your development environment
4. Create a feature branch if needed
5. Mark the task as in_progress to signal you're working on it
""",
            (WorkflowStage.IN_PROGRESS, WorkflowStage.REVIEW): """
Before moving to Review:
1. Complete all implementation steps
2. Write or update tests
3. Run the test suite and ensure all tests pass
4. Update documentation if needed
5. Add verification steps showing how to test the work
6. Create a PR if applicable
""",
            (WorkflowStage.REVIEW, WorkflowStage.DONE): """
Before marking as Done:
1. Verify all acceptance criteria are met
2. Ensure tests are passing
3. Review is approved (if required)
4. PR is merged (if applicable)
5. Update the task file with completion summary
""",
        }

        return guidance_map.get(
            (from_stage, to_stage),
            f"Transition from {from_stage.value} to {to_stage.value}"
        )


# Singleton instance for easy access
_workflow_guide: Optional[WorkflowGuide] = None


def get_workflow_guide(paircoder_dir: Optional[Path] = None) -> WorkflowGuide:
    """Get the workflow guide instance.

    Args:
        paircoder_dir: Path to .paircoder directory

    Returns:
        WorkflowGuide instance
    """
    global _workflow_guide
    if _workflow_guide is None:
        _workflow_guide = WorkflowGuide(paircoder_dir)
    return _workflow_guide


# Workflow rules as markdown for agent reference
WORKFLOW_RULES = """
# PairCoder Workflow Rules

## Stage Definitions

### 1. Intake/Backlog
- **Purpose**: Collection point for new tasks, ideas, bugs
- **Requirements**: Task ID and title only
- **Actions**: Tasks stay here until fully planned
- **Next**: → Planned / Ready (when planned) or → Issues (if blocked)

### 2. Planned/Ready
- **Purpose**: Tasks that are ready to be worked on
- **Requirements**:
  - Clear objective
  - Detailed implementation plan
  - Acceptance criteria
- **Actions**: Pick up and start when ready
- **Next**: → In Progress (when starting work)

### 3. In Progress
- **Purpose**: Tasks currently being worked on
- **Requirements**: An agent actively working on it
- **Actions**: Follow implementation plan, track progress
- **Next**: → Review / Testing (when implementation complete)

### 4. Review/Testing
- **Purpose**: Verification before completion
- **Requirements**:
  - Implementation complete
  - Tests written and passing
  - Verification steps documented
- **Actions**: Run tests, review code, verify acceptance criteria
- **Next**: → Deployed / Done (when verified) or → In Progress (if issues found)

### 5. Deployed/Done
- **Purpose**: Completed work
- **Requirements**:
  - All acceptance criteria met
  - Tests passing
  - PR merged (if applicable)
- **Actions**: None - terminal state

### 6. Issues/Tech Debt
- **Purpose**: Blocked tasks or technical debt items
- **Requirements**: Clear description of blocker
- **Actions**: Resolve blocker, then move back to appropriate stage

## Agent Guidelines

1. **Always check task requirements** before moving to a new stage
2. **Never skip stages** - follow the workflow in order
3. **Update task files** with progress and decisions
4. **Add comments on Trello cards** when moving tasks
5. **Run verification** before marking tasks complete
"""
