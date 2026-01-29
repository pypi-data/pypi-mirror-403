"""
MCP Task Tools

Implements task management tools:
- paircoder_task_list: List tasks with filters
- paircoder_task_next: Get next recommended task
- paircoder_task_start: Start a task
- paircoder_task_complete: Complete a task
"""

from pathlib import Path
from typing import Any, Optional

from ...planning.parser import TaskParser
from ...planning.state import StateManager
from ...planning.models import TaskStatus


def find_paircoder_dir() -> Path:
    """Find the .paircoder directory."""
    from ...core.ops import find_paircoder_dir as _find_paircoder_dir, ProjectRootNotFoundError
    try:
        paircoder_dir = _find_paircoder_dir()
    except ProjectRootNotFoundError:
        raise FileNotFoundError("No .paircoder directory found")
    if not paircoder_dir.exists():
        raise FileNotFoundError("No .paircoder directory found")
    return paircoder_dir


def register_task_tools(server: Any) -> None:
    """Register task tools with the MCP server."""

    @server.tool()
    async def paircoder_task_list(
        status: str = "all",
        plan: Optional[str] = None,
        sprint: Optional[str] = None,
    ) -> list[dict]:
        """
        List tasks with optional filters.

        Args:
            status: Filter by status (all, pending, in_progress, done, blocked)
            plan: Filter by plan ID
            sprint: Filter by sprint ID

        Returns:
            List of task dictionaries
        """
        try:
            paircoder_dir = find_paircoder_dir()
            task_parser = TaskParser(paircoder_dir / "tasks")

            # Get tasks for plan if specified
            if plan:
                tasks = task_parser.get_tasks_for_plan(plan)
            else:
                tasks = task_parser.parse_all()

            # Filter by status
            if status != "all":
                try:
                    status_filter = TaskStatus(status)
                    tasks = [t for t in tasks if t.status == status_filter]
                except ValueError:
                    pass  # Invalid status, return all

            # Filter by sprint
            if sprint:
                tasks = [t for t in tasks if t.sprint == sprint]

            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status.value,
                    "priority": t.priority,
                    "complexity": t.complexity,
                    "sprint": t.sprint,
                    "plan": t.plan,
                    "depends_on": t.depends_on,
                }
                for t in tasks
            ]
        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}

    @server.tool()
    async def paircoder_task_next() -> dict:
        """
        Get the next recommended task to work on.

        Prioritizes in-progress tasks, then pending tasks by priority.

        Returns:
            Task dictionary or error if no tasks available
        """
        try:
            paircoder_dir = find_paircoder_dir()
            state_manager = StateManager(paircoder_dir)

            task = state_manager.get_next_task()
            if not task:
                return {"error": {"code": "NO_TASKS", "message": "No pending tasks found"}}

            return {
                "id": task.id,
                "title": task.title,
                "status": task.status.value,
                "priority": task.priority,
                "complexity": task.complexity,
                "sprint": task.sprint,
                "plan": task.plan,
                "objective": task.objective,
            }
        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}

    @server.tool()
    async def paircoder_task_start(
        task_id: str,
        agent: Optional[str] = None,
    ) -> dict:
        """
        Start a task - updates status to in_progress and triggers hooks.

        Args:
            task_id: Task ID to start
            agent: Agent starting the task (optional)

        Returns:
            Status update result with hook execution info
        """
        try:
            paircoder_dir = find_paircoder_dir()
            state_manager = StateManager(paircoder_dir)
            task_parser = TaskParser(paircoder_dir / "tasks")

            # Get task first (for hooks)
            task = task_parser.get_task_by_id(task_id)
            if not task:
                return {"error": {"code": "TASK_NOT_FOUND", "message": f"Task {task_id} not found"}}

            # Update status
            success = state_manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)
            if not success:
                return {"error": {"code": "UPDATE_FAILED", "message": f"Failed to update {task_id}"}}

            # Run hooks
            hooks_executed = []
            try:
                from ...core.hooks import get_hook_runner, HookContext

                hook_runner = get_hook_runner(paircoder_dir)
                ctx = HookContext(
                    task_id=task_id,
                    task=task,
                    event="on_task_start",
                    agent=agent,
                )
                results = hook_runner.run_hooks("on_task_start", ctx)
                hooks_executed = [r.to_dict() for r in results]
            except ImportError:
                pass  # Hooks module not available

            return {
                "status": "started",
                "task_id": task_id,
                "agent": agent,
                "hooks": hooks_executed,
            }
        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}

    @server.tool()
    async def paircoder_task_complete(
        task_id: str,
        summary: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> dict:
        """
        Complete a task - updates status to done and triggers hooks.

        Args:
            task_id: Task ID to complete
            summary: Summary of what was done (optional)
            input_tokens: Input tokens used (for metrics)
            output_tokens: Output tokens used (for metrics)
            model: Model used (for metrics)
            agent: Agent completing the task (for metrics)

        Returns:
            Status update result with hook execution info
        """
        try:
            paircoder_dir = find_paircoder_dir()
            state_manager = StateManager(paircoder_dir)
            task_parser = TaskParser(paircoder_dir / "tasks")

            # Get task first (for hooks)
            task = task_parser.get_task_by_id(task_id)
            if not task:
                return {"error": {"code": "TASK_NOT_FOUND", "message": f"Task {task_id} not found"}}

            # Update status
            success = state_manager.update_task_status(task_id, TaskStatus.DONE)
            if not success:
                return {"error": {"code": "UPDATE_FAILED", "message": f"Failed to update {task_id}"}}

            # Run hooks
            hooks_executed = []
            try:
                from ...core.hooks import get_hook_runner, HookContext

                hook_runner = get_hook_runner(paircoder_dir)
                ctx = HookContext(
                    task_id=task_id,
                    task=task,
                    event="on_task_complete",
                    agent=agent,
                    extra={
                        "summary": summary,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "model": model,
                    },
                )
                results = hook_runner.run_hooks("on_task_complete", ctx)
                hooks_executed = [r.to_dict() for r in results]
            except ImportError:
                pass  # Hooks module not available

            return {
                "status": "completed",
                "task_id": task_id,
                "summary": summary,
                "hooks": hooks_executed,
            }
        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}
