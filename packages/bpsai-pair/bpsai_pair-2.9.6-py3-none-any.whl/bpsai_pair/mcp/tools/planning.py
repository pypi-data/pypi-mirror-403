"""
MCP Planning Tools

Implements plan management tools:
- paircoder_plan_status: Get plan status with sprint breakdown
- paircoder_plan_list: List available plans
"""

from pathlib import Path
from typing import Any, Optional

from ...planning.parser import PlanParser, TaskParser
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


def register_planning_tools(server: Any) -> None:
    """Register planning tools with the MCP server."""

    @server.tool()
    async def paircoder_plan_status(
        plan_id: Optional[str] = None,
    ) -> dict:
        """
        Get plan status with sprint/task breakdown.

        Args:
            plan_id: Plan ID or None for active plan

        Returns:
            Plan status dictionary with progress info
        """
        try:
            paircoder_dir = find_paircoder_dir()
            state_manager = StateManager(paircoder_dir)
            plan_parser = PlanParser(paircoder_dir / "plans")
            task_parser = TaskParser(paircoder_dir / "tasks")

            # Get plan
            if plan_id:
                plan = plan_parser.get_plan_by_id(plan_id)
            else:
                plan_id = state_manager.get_active_plan_id()
                if plan_id:
                    plan = plan_parser.get_plan_by_id(plan_id)
                else:
                    plan = None

            if not plan:
                return {"error": {"code": "PLAN_NOT_FOUND", "message": f"Plan not found: {plan_id or 'active'}"}}

            # Get tasks for plan
            tasks = task_parser.get_tasks_for_plan(plan.id)

            # Calculate task counts by status
            task_counts = {
                "pending": 0,
                "in_progress": 0,
                "done": 0,
                "blocked": 0,
            }
            for task in tasks:
                status_key = task.status.value
                if status_key in task_counts:
                    task_counts[status_key] += 1

            total_tasks = sum(task_counts.values())
            done_count = task_counts["done"]
            progress_pct = int((done_count / total_tasks * 100)) if total_tasks > 0 else 0

            # Calculate sprint progress
            sprint_progress = []
            for sprint in plan.sprints:
                sprint_tasks = [t for t in tasks if t.sprint == sprint.id]
                sprint_done = sum(1 for t in sprint_tasks if t.status == TaskStatus.DONE)
                sprint_total = len(sprint_tasks)
                sprint_pct = int((sprint_done / sprint_total * 100)) if sprint_total > 0 else 0

                sprint_progress.append({
                    "id": sprint.id,
                    "title": sprint.title,
                    "done": sprint_done,
                    "total": sprint_total,
                    "percent": sprint_pct,
                })

            # Find blockers
            blockers = []
            for task in tasks:
                if task.status == TaskStatus.BLOCKED:
                    blockers.append({
                        "task_id": task.id,
                        "title": task.title,
                        "blocked_by": task.depends_on,
                    })

            return {
                "plan": {
                    "id": plan.id,
                    "title": plan.title,
                    "status": plan.status.value,
                    "type": plan.type.value,
                },
                "goals": plan.goals,
                "task_counts": task_counts,
                "total_tasks": total_tasks,
                "progress_percent": progress_pct,
                "sprint_progress": sprint_progress,
                "blockers": blockers,
            }
        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}

    @server.tool()
    async def paircoder_plan_list() -> list[dict]:
        """
        List available plans.

        Returns:
            List of plan dictionaries
        """
        try:
            paircoder_dir = find_paircoder_dir()
            plan_parser = PlanParser(paircoder_dir / "plans")
            state_manager = StateManager(paircoder_dir)

            plans = plan_parser.parse_all()
            active_plan_id = state_manager.get_active_plan_id()

            return [
                {
                    "id": p.id,
                    "title": p.title,
                    "status": p.status.value,
                    "type": p.type.value,
                    "is_active": p.id == active_plan_id,
                    "sprint_count": len(p.sprints),
                }
                for p in plans
            ]
        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}
