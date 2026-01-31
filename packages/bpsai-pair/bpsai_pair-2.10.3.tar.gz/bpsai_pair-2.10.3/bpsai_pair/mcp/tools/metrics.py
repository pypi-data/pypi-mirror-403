"""
MCP Metrics Tools

Implements metrics tools:
- paircoder_metrics_record: Record token usage and cost metrics
- paircoder_metrics_summary: Get metrics summary
"""

from pathlib import Path
from typing import Any, Optional


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


def register_metrics_tools(server: Any) -> None:
    """Register metrics tools with the MCP server."""

    @server.tool()
    async def paircoder_metrics_record(
        task_id: str,
        agent: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_seconds: float = 0,
        action_type: str = "coding",
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> dict:
        """
        Record metrics for a completed action.

        Args:
            task_id: Task ID the work was for
            agent: Agent that did the work (claude-code, codex-cli, etc.)
            model: Model used (claude-sonnet-4-5-20250929, etc.)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_seconds: Duration of the action in seconds
            action_type: Type of action (planning, coding, review, testing, docs)
            success: Whether the action succeeded
            error_message: Error message if failed

        Returns:
            Recording confirmation with cost
        """
        try:
            from ...metrics import MetricsCollector

            paircoder_dir = find_paircoder_dir()
            history_dir = paircoder_dir / "history"
            history_dir.mkdir(exist_ok=True)

            collector = MetricsCollector(history_dir)

            # Record the event
            event = collector.record_invocation(
                agent=agent,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=int(duration_seconds * 1000),
                success=success,
                task_id=task_id,
                operation=action_type,
                error=error_message,
            )

            return {
                "recorded": True,
                "task_id": task_id,
                "agent": agent,
                "model": model,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": input_tokens + output_tokens,
                },
                "cost": f"${event.cost_usd:.4f}",
                "duration_seconds": duration_seconds,
            }
        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}

    @server.tool()
    async def paircoder_metrics_summary(
        scope: str = "daily",
        scope_id: Optional[str] = None,
    ) -> dict:
        """
        Get metrics summary.

        Args:
            scope: Scope for summary (daily, weekly, monthly, task, plan)
            scope_id: ID for task/plan scope (optional)

        Returns:
            Metrics summary with totals and breakdowns
        """
        try:
            from ...metrics import MetricsCollector, MetricsReporter

            paircoder_dir = find_paircoder_dir()
            history_dir = paircoder_dir / "history"

            if not history_dir.exists():
                return {
                    "scope": scope,
                    "total_tokens": 0,
                    "total_cost": "$0.00",
                    "total_duration": "0.0h",
                    "events": 0,
                    "by_agent": {},
                    "by_model": {},
                }

            collector = MetricsCollector(history_dir)
            reporter = MetricsReporter(collector)

            # Handle task/plan scope
            if scope == "task" and scope_id:
                task_metrics = reporter.get_task_metrics(scope_id)
                total_duration_hours = task_metrics["duration_ms"] / (1000 * 60 * 60)
                return {
                    "scope": f"task:{scope_id}",
                    "total_tokens": task_metrics["tokens"]["total"],
                    "total_cost": f"${task_metrics['cost_usd']:.2f}",
                    "total_duration": f"{total_duration_hours:.1f}h",
                    "events": task_metrics["events"],
                    "successful": task_metrics["successful"],
                    "failed": task_metrics["failed"],
                    "by_agent": task_metrics.get("by_agent", {}),
                }

            # Handle time-based scopes
            if scope not in ["daily", "weekly", "monthly"]:
                scope = "daily"

            summary = reporter.get_summary(scope)
            total_duration_hours = summary.total_duration_ms / (1000 * 60 * 60)

            return {
                "scope": summary.period,
                "start_date": summary.start_date,
                "end_date": summary.end_date,
                "total_tokens": summary.total_tokens,
                "input_tokens": summary.input_tokens,
                "output_tokens": summary.output_tokens,
                "total_cost": f"${summary.total_cost_usd:.2f}",
                "total_duration": f"{total_duration_hours:.1f}h",
                "events": summary.total_events,
                "successful": summary.successful_events,
                "failed": summary.failed_events,
                "by_agent": summary.by_agent,
                "by_model": summary.by_model,
                "by_task": summary.by_task,
            }
        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}
