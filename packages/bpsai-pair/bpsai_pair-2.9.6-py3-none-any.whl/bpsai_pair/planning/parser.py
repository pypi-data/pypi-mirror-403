"""
Planning Parsers

Handles parsing of plan files (.plan.yaml) and task files (.task.md).
Task files use YAML frontmatter + Markdown body format.
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple

import yaml

from .models import Plan, Task, PlanStatus, TaskStatus


# Regex to match YAML frontmatter (content between --- delimiters)
FRONTMATTER_PATTERN = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n?(.*)$",
    re.DOTALL
)


def parse_frontmatter(content: str) -> Tuple[dict, str]:
    """
    Parse YAML frontmatter from a document.

    Args:
        content: Full file content with optional YAML frontmatter

    Returns:
        Tuple of (frontmatter_dict, body_content)
        If no frontmatter, returns ({}, full_content)
    """
    match = FRONTMATTER_PATTERN.match(content)
    if match:
        frontmatter_str = match.group(1)
        body = match.group(2).strip()
        try:
            frontmatter = yaml.safe_load(frontmatter_str) or {}
        except yaml.YAMLError:
            frontmatter = {}
        return frontmatter, body
    return {}, content


class PlanParser:
    """
    Parser for plan files (.plan.yaml).
    """

    def __init__(self, plans_dir: Path):
        """
        Initialize parser with plans directory.

        Args:
            plans_dir: Path to .paircoder/plans/
        """
        self.plans_dir = Path(plans_dir)

    def list_plans(self) -> list[Path]:
        """List all plan files in the plans directory."""
        if not self.plans_dir.exists():
            return []
        return sorted(self.plans_dir.glob("*.plan.yaml"))

    def parse(self, plan_path: Path) -> Optional[Plan]:
        """
        Parse a single plan file.

        Args:
            plan_path: Path to the plan file

        Returns:
            Plan object or None if parsing fails
        """
        try:
            with open(plan_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                return None
            return Plan.from_dict(data, source_path=plan_path)
        except (yaml.YAMLError, OSError) as e:
            print(f"Error parsing plan {plan_path}: {e}")
            return None

    def parse_all(self) -> list[Plan]:
        """Parse all plans in the directory."""
        plans = []
        for plan_path in self.list_plans():
            plan = self.parse(plan_path)
            if plan:
                plans.append(plan)
        return plans

    def get_plan_by_id(self, plan_id: str) -> Optional[Plan]:
        """
        Find and parse a plan by its ID.

        Args:
            plan_id: Plan ID (e.g., "plan-2025-01-feature-name")

        Returns:
            Plan object or None if not found
        """
        # Try exact filename match first
        exact_path = self.plans_dir / f"{plan_id}.plan.yaml"
        if exact_path.exists():
            return self.parse(exact_path)

        # Search all plans for matching ID
        for plan in self.parse_all():
            if plan.id == plan_id:
                return plan

        # Try partial match (slug)
        for plan_path in self.list_plans():
            if plan_id in plan_path.stem:
                return self.parse(plan_path)

        return None

    def save(self, plan: Plan, filename: Optional[str] = None) -> Path:
        """
        Save a plan to a YAML file.

        Args:
            plan: Plan object to save
            filename: Optional filename (defaults to plan.id)

        Returns:
            Path to saved file
        """
        self.plans_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            filename = f"{plan.id}.plan.yaml"

        plan_path = self.plans_dir / filename

        with open(plan_path, "w", encoding="utf-8") as f:
            yaml.dump(
                plan.to_dict(),
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        plan.source_path = plan_path
        return plan_path

    def update_plan_status(self, plan_id: str, new_status: PlanStatus) -> bool:
        """
        Update a plan's status in its YAML file.

        Args:
            plan_id: Plan ID to update
            new_status: New PlanStatus value

        Returns:
            True if updated successfully, False if plan not found
        """
        plan = self.get_plan_by_id(plan_id)
        if not plan or not plan.source_path:
            return False

        # Read current YAML content
        with open(plan.source_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return False

        # Update status
        data["status"] = new_status.value

        # Write back
        with open(plan.source_path, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        return True

    def check_and_update_plan_status(self, plan_id: str, tasks_dir: Path) -> bool:
        """
        Check task statuses and update plan status accordingly.

        Transitions:
        - planned → in_progress: when any task is in_progress or done
        - in_progress → complete: when all tasks are done or cancelled

        Args:
            plan_id: Plan ID to check
            tasks_dir: Path to tasks directory

        Returns:
            True if plan status was updated, False otherwise
        """
        plan = self.get_plan_by_id(plan_id)
        if not plan:
            return False

        task_parser = TaskParser(tasks_dir)
        tasks = task_parser.get_tasks_for_plan(plan_id)

        if not tasks:
            return False

        # Count task statuses
        done_statuses = {TaskStatus.DONE, TaskStatus.CANCELLED}
        active_statuses = {TaskStatus.IN_PROGRESS, TaskStatus.REVIEW, TaskStatus.BLOCKED}

        total_tasks = len(tasks)
        done_count = sum(1 for t in tasks if t.status in done_statuses)
        active_count = sum(1 for t in tasks if t.status in active_statuses)

        # Determine target plan status
        if done_count == total_tasks:
            # All tasks done or cancelled → plan complete
            target_status = PlanStatus.COMPLETE
        elif done_count > 0 or active_count > 0:
            # Some work has started → plan in progress
            target_status = PlanStatus.IN_PROGRESS
        else:
            # No work started yet → stay planned
            return False

        # Only update if status actually changes
        if plan.status != target_status:
            return self.update_plan_status(plan_id, target_status)

        return False


class TaskParser:
    """
    Parser for task files (.task.md).

    Task files use YAML frontmatter + Markdown body format:

    ```
    ---
    id: TASK-001
    plan: plan-2025-01-feature
    title: Implement feature X
    status: pending
    ---

    # Objective

    Description of what this task accomplishes...

    # Implementation Plan

    - Step 1
    - Step 2
    ```
    """

    def __init__(self, tasks_dir: Path):
        """
        Initialize parser with tasks directory.

        Args:
            tasks_dir: Path to .paircoder/tasks/
        """
        self.tasks_dir = Path(tasks_dir)

    def list_tasks(self, plan_slug: Optional[str] = None) -> List[Path]:
        """List task files, optionally filtered by plan.

        Args:
            plan_slug: If provided, filter to tasks with matching plan_id

        Returns:
            List of task file paths
        """
        if not self.tasks_dir.exists():
            return []

        # Flat storage - all .task.md files directly in tasks/
        all_tasks = list(self.tasks_dir.glob("*.task.md"))

        # Also check subdirectories for backwards compatibility with old structure
        for subdir in self.tasks_dir.iterdir():
            if subdir.is_dir():
                all_tasks.extend(subdir.glob("*.task.md"))

        # Deduplicate and sort
        all_tasks = sorted(set(all_tasks))

        if plan_slug:
            # Filter by parsing each task's plan_id
            filtered = []
            for task_path in all_tasks:
                task = self.parse(task_path)
                if task and task.plan_id and plan_slug in task.plan_id:
                    filtered.append(task_path)
            return filtered

        return all_tasks

    def parse(self, task_path: Path) -> Optional[Task]:
        """
        Parse a single task file.

        Args:
            task_path: Path to the task file

        Returns:
            Task object or None if parsing fails
        """
        try:
            with open(task_path, "r", encoding="utf-8") as f:
                content = f.read()

            frontmatter, body = parse_frontmatter(content)
            if not frontmatter:
                return None

            return Task.from_dict(frontmatter, body=body, source_path=task_path)
        except OSError as e:
            print(f"Error parsing task {task_path}: {e}")
            return None

    def parse_all(self, plan_slug: Optional[str] = None) -> list[Task]:
        """
        Parse all tasks, optionally filtered by plan.

        Args:
            plan_slug: If provided, only parse tasks for this plan

        Returns:
            List of Task objects
        """
        tasks = []
        for task_path in self.list_tasks(plan_slug):
            task = self.parse(task_path)
            if task:
                tasks.append(task)
        return tasks

    def get_task_by_id(self, task_id: str, plan_slug: Optional[str] = None) -> Optional[Task]:
        """
        Find and parse a task by its ID.

        Args:
            task_id: Task ID (e.g., "TASK-001")
            plan_slug: Optional plan slug to narrow search

        Returns:
            Task object or None if not found
        """
        for task in self.parse_all(plan_slug):
            if task.id == task_id:
                return task
        return None

    def get_tasks_for_plan(self, plan_id: str) -> list[Task]:
        """
        Get all tasks belonging to a specific plan.

        Filters tasks by the plan_id field in frontmatter, not by directory.

        Args:
            plan_id: Plan ID to filter by (e.g., "plan-2025-01-paircoder-v2.4-mcp")

        Returns:
            List of Task objects belonging to this plan
        """
        return [t for t in self.parse_all() if t.plan_id == plan_id]

    def save(self, task: Task, _plan_slug: Optional[str] = None) -> Path:
        """
        Save a task to a Markdown file with YAML frontmatter.

        Args:
            task: Task object to save
            _plan_slug: Deprecated - ignored, kept for backwards compatibility

        Returns:
            Path to saved file
        """
        # Flat storage - all tasks in tasks/ directory
        # Plan association tracked via plan_id field in frontmatter
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

        task_path = self.tasks_dir / f"{task.id}.task.md"

        # Build frontmatter
        frontmatter = task.to_dict()

        # Build content
        content = "---\n"
        content += yaml.dump(
            frontmatter,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        content += "---\n\n"
        content += task.body if task.body else self._generate_default_body(task)

        with open(task_path, "w", encoding="utf-8") as f:
            f.write(content)

        task.source_path = task_path
        return task_path

    def _generate_default_body(self, task: Task) -> str:
        """Generate default Markdown body for a new task."""
        body = f"# Objective\n\n{task.description or task.title}\n\n"
        body += "# Implementation Plan\n\n- TODO: Add implementation steps\n\n"
        body += "# Acceptance Criteria\n\n- [ ] TODO: Add acceptance criteria\n\n"
        body += "# Verification\n\n- TODO: Add verification steps\n"
        return body

    def update_status(self, task_id: str, status: str, plan_slug: Optional[str] = None) -> bool:
        """
        Update a task's status.

        Args:
            task_id: Task ID to update
            status: New status value
            plan_slug: Optional plan slug

        Returns:
            True if updated successfully
        """
        task = self.get_task_by_id(task_id, plan_slug)
        if not task or not task.source_path:
            return False

        # Read current content
        with open(task.source_path, "r", encoding="utf-8") as f:
            content = f.read()

        frontmatter, body = parse_frontmatter(content)
        frontmatter["status"] = status

        # Rewrite file
        new_content = "---\n"
        new_content += yaml.dump(
            frontmatter,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        new_content += "---\n\n"
        new_content += body

        with open(task.source_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True

    def update_ac_item(
        self,
        task_id: str,
        item_text: str,
        checked: bool,
        plan_slug: Optional[str] = None
    ) -> bool:
        """
        Update a specific acceptance criteria item's checked state.

        Args:
            task_id: Task ID to update
            item_text: Text of the AC item to update (partial match supported)
            checked: New checked state
            plan_slug: Optional plan slug

        Returns:
            True if updated successfully, False if not found
        """
        task = self.get_task_by_id(task_id, plan_slug)
        if not task or not task.source_path:
            return False

        # Read current content
        with open(task.source_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find and update the AC item
        # Pattern: - [ ] text or - [x] text
        pattern = re.compile(
            rf'^([-*]\s+\[)[ xX](\]\s+.*{re.escape(item_text)}.*?)$',
            re.MULTILINE | re.IGNORECASE
        )

        new_check = "x" if checked else " "
        new_content, count = pattern.subn(rf'\g<1>{new_check}\2', content, count=1)

        if count == 0:
            return False

        # Write back
        with open(task.source_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True

    def check_all_ac_items(self, task_id: str, plan_slug: Optional[str] = None) -> int:
        """
        Check all acceptance criteria items for a task.

        Args:
            task_id: Task ID to update
            plan_slug: Optional plan slug

        Returns:
            Number of items checked
        """
        task = self.get_task_by_id(task_id, plan_slug)
        if not task or not task.source_path:
            return 0

        # Read current content
        with open(task.source_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace all unchecked AC items with checked
        pattern = re.compile(r'^([-*]\s+\[) (\].+)$', re.MULTILINE)
        new_content, count = pattern.subn(r'\1x\2', content)

        if count > 0:
            with open(task.source_path, "w", encoding="utf-8") as f:
                f.write(new_content)

        return count


# Convenience functions

def parse_plan(plan_path: Path) -> Optional[Plan]:
    """Parse a single plan file."""
    parser = PlanParser(plan_path.parent)
    return parser.parse(plan_path)


def parse_task(task_path: Path) -> Optional[Task]:
    """Parse a single task file.

    Args:
        task_path: Path to the task file

    Returns:
        Parsed Task object or None
    """
    # Find tasks_dir - handle both flat and nested structures
    parent = task_path.parent
    if parent.name == "tasks":
        # Flat: tasks/TASK-XXX.task.md
        tasks_dir = parent
    elif parent.parent.name == "tasks":
        # Nested (legacy): tasks/plan-slug/TASK-XXX.task.md
        tasks_dir = parent.parent
    else:
        # Fallback: assume parent is tasks_dir
        tasks_dir = parent

    parser = TaskParser(tasks_dir)
    return parser.parse(task_path)
