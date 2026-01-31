"""
Hook System for Task State Changes

Automatically triggers actions when task state changes:
- Timer start/stop
- Metrics recording
- Trello sync
- State updates
- Dependency checking
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class HookContext:
    """Context passed to hook handlers."""

    task_id: str
    task: Any  # Task object
    event: str  # on_task_start, on_task_complete, on_task_block
    agent: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HookResult:
    """Result of a hook execution."""

    hook: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        d = {"hook": self.hook, "success": self.success}
        if self.result:
            d["result"] = self.result
        if self.error:
            d["error"] = self.error
        return d


class HookRunner:
    """Runs configured hooks on events."""

    def __init__(self, config: dict, paircoder_dir: Path):
        """
        Initialize hook runner.

        Args:
            config: Configuration dict (from config.yaml)
            paircoder_dir: Path to .paircoder directory
        """
        self.config = config
        self.paircoder_dir = Path(paircoder_dir)
        self._handlers: Dict[str, Callable] = {
            "start_timer": self._start_timer,
            "stop_timer": self._stop_timer,
            "record_metrics": self._record_metrics,
            "sync_trello": self._sync_trello,
            "update_state": self._update_state,
            "check_unblocked": self._check_unblocked,
            "log_trello_activity": self._log_trello_activity,
            "record_task_completion": self._record_task_completion,
            "record_velocity": self._record_velocity,
            "record_token_usage": self._record_token_usage,
            "check_token_budget": self._check_token_budget,
        }

    @property
    def enabled(self) -> bool:
        """Check if hooks are enabled."""
        return self.config.get("hooks", {}).get("enabled", True)

    def get_hooks_for_event(self, event: str) -> List[str]:
        """Get list of hooks configured for an event."""
        return self.config.get("hooks", {}).get(event, [])

    def run_hooks(self, event: str, context: HookContext) -> List[HookResult]:
        """
        Run all hooks for an event.

        Args:
            event: Event name (on_task_start, on_task_complete, on_task_block)
            context: Hook context with task info

        Returns:
            List of hook results
        """
        if not self.enabled:
            logger.debug("Hooks disabled, skipping")
            return []

        hooks = self.get_hooks_for_event(event)
        if not hooks:
            logger.debug(f"No hooks configured for {event}")
            return []

        results = []

        for hook_name in hooks:
            result = self._run_single_hook(hook_name, context)
            results.append(result)

        return results

    def _run_single_hook(self, hook_name: str, context: HookContext) -> HookResult:
        """Run a single hook."""
        handler = self._handlers.get(hook_name)

        if not handler:
            logger.warning(f"Unknown hook: {hook_name}")
            return HookResult(
                hook=hook_name,
                success=False,
                error=f"Unknown hook: {hook_name}",
            )

        try:
            result = handler(context)
            logger.info(f"Hook {hook_name} completed for {context.task_id}")
            return HookResult(hook=hook_name, success=True, result=result)
        except Exception as e:
            logger.error(f"Hook {hook_name} failed: {e}")
            return HookResult(hook=hook_name, success=False, error=str(e))

    def _start_timer(self, ctx: HookContext) -> dict:
        """Start time tracking for task."""
        try:
            from ..integrations.time_tracking import (
                TimeTrackingManager,
                TimeTrackingConfig,
            )

            # Get task title from task object if available
            task_title = getattr(ctx.task, "title", ctx.task_id) if ctx.task else ctx.task_id

            # Load time tracking config from config.yaml
            time_config = self.config.get("time_tracking", {})
            config = TimeTrackingConfig(
                provider=time_config.get("provider", "none"),
                auto_start=time_config.get("auto_start", True),
                auto_stop=time_config.get("auto_stop", True),
                task_pattern=time_config.get("task_pattern", "{task_id}: {task_title}"),
            )

            cache_path = self.paircoder_dir / "time-tracking-cache.json"
            manager = TimeTrackingManager(config, cache_path)
            timer_id = manager.start_task(ctx.task_id, task_title)

            if timer_id:
                return {"timer_started": True, "timer_id": timer_id}
            return {"timer_started": False, "reason": "auto_start disabled"}
        except Exception as e:
            logger.warning(f"Timer start failed: {e}")
            return {"timer_started": False, "error": str(e)}

    def _stop_timer(self, ctx: HookContext) -> dict:
        """Stop time tracking and get duration."""
        try:
            from ..integrations.time_tracking import (
                TimeTrackingManager,
                TimeTrackingConfig,
                LocalTimeCache,
            )

            cache_path = self.paircoder_dir / "time-tracking-cache.json"

            # Check if there's an active timer
            cache = LocalTimeCache(cache_path)
            active = cache.get_active_timer()

            if not active:
                return {"timer_stopped": False, "reason": "No active timer"}

            # Verify the active timer is for this task
            if active.get("task_id") != ctx.task_id:
                return {
                    "timer_stopped": False,
                    "reason": f"Active timer is for {active.get('task_id')}, not {ctx.task_id}",
                }

            # Load config and create manager
            time_config = self.config.get("time_tracking", {})
            config = TimeTrackingConfig(
                provider=time_config.get("provider", "none"),
                auto_start=time_config.get("auto_start", True),
                auto_stop=time_config.get("auto_stop", True),
                task_pattern=time_config.get("task_pattern", "{task_id}: {task_title}"),
            )

            manager = TimeTrackingManager(config, cache_path)
            entry = manager.stop_task(active["timer_id"])

            if entry:
                duration_seconds = entry.duration.total_seconds() if entry.duration else 0
                total = manager.get_task_time(ctx.task_id)
                return {
                    "timer_stopped": True,
                    "duration_seconds": duration_seconds,
                    "total_seconds": total.total_seconds(),
                    "formatted_duration": manager.format_duration(entry.duration) if entry.duration else "0m",
                    "formatted_total": manager.format_duration(total),
                }
            return {"timer_stopped": False, "reason": "Failed to stop timer"}
        except Exception as e:
            logger.warning(f"Timer stop failed: {e}")
            return {"timer_stopped": False, "error": str(e)}

    def _record_metrics(self, ctx: HookContext) -> dict:
        """Record metrics from context.extra."""
        try:
            from ..metrics import MetricsCollector

            history_dir = self.paircoder_dir / "history"
            history_dir.mkdir(exist_ok=True)

            collector = MetricsCollector(history_dir)

            extra = ctx.extra or {}
            event = collector.record_invocation(
                agent=ctx.agent or "unknown",
                model=extra.get("model", "unknown"),
                input_tokens=extra.get("input_tokens", 0),
                output_tokens=extra.get("output_tokens", 0),
                duration_ms=int(extra.get("duration_seconds", 0) * 1000),
                success=True,
                task_id=ctx.task_id,
                operation=extra.get("action_type", "coding"),
            )
            return {"metrics_recorded": True, "cost": f"${event.cost_usd:.4f}"}
        except Exception as e:
            logger.warning(f"Metrics recording failed: {e}")
            return {"metrics_recorded": False, "error": str(e)}

    def _sync_trello(self, ctx: HookContext) -> dict:
        """Sync task state to Trello card."""
        try:
            from ..trello.auth import load_token
            from ..trello.client import TrelloService

            token_data = load_token()
            if not token_data:
                return {"trello_synced": False, "reason": "Not connected to Trello"}

            # Get board_id from config
            trello_config = self.config.get("trello", {})
            board_id = trello_config.get("board_id")
            if not board_id:
                return {"trello_synced": False, "reason": "No board_id configured"}

            service = TrelloService(
                api_key=token_data["api_key"], token=token_data["token"]
            )
            service.set_board(board_id)

            # Get automation config for target lists
            # Check multiple locations for backwards compatibility
            automation = trello_config.get("automation", {})
            if not automation:
                # Also check card_format.automation (older config structure)
                automation = trello_config.get("card_format", {}).get("automation", {})

            # Map event to target list and comment
            event_config = {
                "on_task_start": automation.get("on_task_start", {}),
                "on_task_complete": automation.get("on_task_complete", {}),
                "on_task_block": automation.get("on_task_block", {}),
            }
            config = event_config.get(ctx.event, {})
            target_list = config.get("move_to_list")
            comment_template = config.get("add_comment")

            if not target_list:
                return {"trello_synced": False, "reason": f"No target list for {ctx.event}"}

            # Find card by task ID in title (e.g., "[TASK-001] Title")
            card = None
            for lst in service.board.all_lists():
                for c in lst.list_cards():
                    if f"[{ctx.task_id}]" in c.name:
                        card = c
                        break
                if card:
                    break

            if not card:
                # Also check trello_card_id if available
                trello_card_id = getattr(ctx.task, "trello_card_id", None)
                if trello_card_id:
                    card, _ = service.find_card(trello_card_id)

            if not card:
                return {"trello_synced": False, "reason": f"Card not found for {ctx.task_id}"}

            # Move card to target list
            service.move_card(card, target_list)

            # Add comment if configured
            if comment_template:
                comment = comment_template.format(
                    agent=ctx.agent or "Agent",
                    summary=ctx.extra.get("summary", "Task updated"),
                    reason=ctx.extra.get("reason", "No reason provided"),
                )
                service.add_comment(card, comment)

            logger.info(f"Moved card for {ctx.task_id} to '{target_list}'")
            return {
                "trello_synced": True,
                "action": ctx.event,
                "target_list": target_list,
                "card_name": card.name,
            }
        except ImportError:
            return {"trello_synced": False, "reason": "py-trello not installed"}
        except Exception as e:
            logger.warning(f"Trello sync failed: {e}")
            return {"trello_synced": False, "error": str(e)}

    def _update_state(self, ctx: HookContext) -> dict:
        """Update state.md with current focus."""
        try:
            from ..planning.state import StateManager

            manager = StateManager(self.paircoder_dir)

            # Just reload state - actual state file updates would be manual
            manager.reload()
            return {"state_updated": True, "task_id": ctx.task_id}
        except Exception as e:
            logger.warning(f"State update failed: {e}")
            return {"state_updated": False, "error": str(e)}

    def _check_unblocked(self, ctx: HookContext) -> dict:
        """Check if completing this task unblocks others."""
        try:
            from ..planning.parser import TaskParser
            from ..planning.models import TaskStatus

            parser = TaskParser(self.paircoder_dir / "tasks")
            all_tasks = parser.parse_all()

            unblocked = []
            for task in all_tasks:
                # Use getattr for backwards compatibility with old task objects
                # that may not have depends_on attribute
                depends_on = getattr(task, 'depends_on', None) or []
                if not depends_on:
                    continue

                if ctx.task_id in depends_on:
                    # Check if all dependencies are now complete
                    all_done = True
                    for dep_id in depends_on:
                        dep_task = parser.get_task_by_id(dep_id)
                        if dep_task and dep_task.status != TaskStatus.DONE:
                            all_done = False
                            break

                    if all_done and task.status == TaskStatus.BLOCKED:
                        unblocked.append(task.id)
                        logger.info(f"Task {task.id} unblocked by {ctx.task_id}")

            return {"unblocked_tasks": unblocked, "count": len(unblocked)}
        except Exception as e:
            logger.warning(f"Unblock check failed: {e}")
            return {"unblocked_tasks": [], "error": str(e)}

    def _log_trello_activity(self, ctx: HookContext) -> dict:
        """Log activity to Trello card as a comment.

        Logs appropriate event based on hook context:
        - on_task_start → TASK_STARTED
        - on_task_complete → TASK_COMPLETED
        - on_task_block → TASK_BLOCKED
        """
        try:
            from ..trello.auth import load_token
            from ..trello.activity import TrelloActivityLogger, ActivityEvent
            from ..trello.client import TrelloService

            token_data = load_token()
            if not token_data:
                return {"activity_logged": False, "reason": "Not connected to Trello"}

            trello_config = self.config.get("trello", {})
            board_id = trello_config.get("board_id")
            if not board_id:
                return {"activity_logged": False, "reason": "No board_id configured"}

            service = TrelloService(
                api_key=token_data["api_key"], token=token_data["token"]
            )
            service.set_board(board_id)
            activity_logger = TrelloActivityLogger(service)

            # Map hook event to activity event
            event_mapping = {
                "on_task_start": ActivityEvent.TASK_STARTED,
                "on_task_complete": ActivityEvent.TASK_COMPLETED,
                "on_task_block": ActivityEvent.TASK_BLOCKED,
            }

            activity_event = event_mapping.get(ctx.event)
            if not activity_event:
                return {"activity_logged": False, "reason": f"Unknown event: {ctx.event}"}

            extra = ctx.extra or {}

            # Log appropriate event
            if activity_event == ActivityEvent.TASK_STARTED:
                success = activity_logger.log_task_started(
                    ctx.task_id,
                    agent=ctx.agent or "Agent"
                )
            elif activity_event == ActivityEvent.TASK_COMPLETED:
                success = activity_logger.log_task_completed(
                    ctx.task_id,
                    summary=extra.get("summary", "Task completed")
                )
            elif activity_event == ActivityEvent.TASK_BLOCKED:
                success = activity_logger.log_task_blocked(
                    ctx.task_id,
                    reason=extra.get("reason", "No reason provided")
                )
            else:
                success = False

            if success:
                logger.info(f"Logged activity for {ctx.task_id}: {activity_event.value}")
                return {"activity_logged": True, "event": activity_event.value}
            else:
                return {"activity_logged": False, "reason": "Card not found"}

        except ImportError as e:
            return {"activity_logged": False, "reason": f"Import error: {e}"}
        except Exception as e:
            logger.warning(f"Activity logging failed: {e}")
            return {"activity_logged": False, "error": str(e)}

    def _record_task_completion(self, ctx: HookContext) -> dict:
        """Record task completion with estimated vs actual hours comparison.

        Records to history/task-completions.jsonl for historical tracking.
        """
        try:
            from ..metrics import MetricsCollector
            from ..integrations.time_tracking import LocalTimeCache

            # Get actual hours from time tracking cache
            cache_path = self.paircoder_dir / "time-tracking-cache.json"
            if not cache_path.exists():
                return {
                    "comparison_recorded": False,
                    "reason": "No time tracking cache found",
                }

            cache = LocalTimeCache(cache_path)
            total_time = cache.get_total(ctx.task_id)
            actual_hours = total_time.total_seconds() / 3600

            if actual_hours == 0:
                return {
                    "comparison_recorded": False,
                    "reason": "No time tracked for task",
                }

            # Get estimated hours from task
            if not ctx.task:
                return {
                    "comparison_recorded": False,
                    "reason": "No task object in context",
                }

            estimated_hours = ctx.task.estimated_hours.expected_hours

            # Record the completion
            history_dir = self.paircoder_dir / "history"
            history_dir.mkdir(exist_ok=True)

            collector = MetricsCollector(history_dir)
            data = collector.record_task_completion(
                task_id=ctx.task_id,
                estimated_hours=estimated_hours,
                actual_hours=actual_hours,
            )

            return {
                "comparison_recorded": True,
                "estimated_hours": data["estimated_hours"],
                "actual_hours": data["actual_hours"],
                "variance_hours": data["variance_hours"],
                "variance_percent": data["variance_percent"],
            }

        except Exception as e:
            logger.warning(f"Task completion recording failed: {e}")
            return {"comparison_recorded": False, "error": str(e)}

    def _record_velocity(self, ctx: HookContext) -> dict:
        """Record task completion for velocity tracking.

        Records complexity points to velocity-completions.jsonl for velocity metrics.
        """
        try:
            from ..metrics import VelocityTracker

            # Get task details
            if not ctx.task:
                return {
                    "velocity_recorded": False,
                    "reason": "No task object in context",
                }

            complexity = ctx.task.complexity
            sprint = ctx.task.sprint or ""

            # Record the completion
            history_dir = self.paircoder_dir / "history"
            history_dir.mkdir(exist_ok=True)

            tracker = VelocityTracker(history_dir)
            record = tracker.record_completion(
                task_id=ctx.task_id,
                complexity=complexity,
                sprint=sprint,
            )

            return {
                "velocity_recorded": True,
                "task_id": record.task_id,
                "complexity": record.complexity,
                "sprint": record.sprint,
            }

        except Exception as e:
            logger.warning(f"Velocity recording failed: {e}")
            return {"velocity_recorded": False, "error": str(e)}

    def _record_token_usage(self, ctx: HookContext) -> dict:
        """Record token usage comparison for feedback loop.

        Records estimated vs actual tokens for improving token estimation accuracy.
        Requires actual_tokens to be present in context.extra.
        """
        try:
            from ..metrics import TokenFeedbackTracker

            # Get task details
            if not ctx.task:
                return {
                    "token_usage_recorded": False,
                    "reason": "No task object in context",
                }

            # Get actual tokens from context extra
            extra = ctx.extra or {}
            actual_tokens = extra.get("actual_tokens")

            if actual_tokens is None:
                # Try to calculate from metrics events
                actual_tokens = extra.get("total_tokens", 0)

            if not actual_tokens:
                return {
                    "token_usage_recorded": False,
                    "reason": "No actual_tokens in context",
                }

            # Get estimated tokens from task
            estimated = ctx.task.estimated_tokens.total_tokens
            task_type = ctx.task.type
            complexity = ctx.task.complexity

            # Record the comparison
            history_dir = self.paircoder_dir / "history"
            history_dir.mkdir(exist_ok=True)

            tracker = TokenFeedbackTracker(history_dir)
            data = tracker.record_usage(
                task_id=ctx.task_id,
                estimated_tokens=estimated,
                actual_tokens=actual_tokens,
                task_type=task_type,
                complexity=complexity,
            )

            return {
                "token_usage_recorded": True,
                "task_id": ctx.task_id,
                "estimated_tokens": estimated,
                "actual_tokens": actual_tokens,
                "ratio": data.get("ratio", 1.0),
            }

        except Exception as e:
            logger.warning(f"Token usage recording failed: {e}")
            return {"token_usage_recorded": False, "error": str(e)}

    def _check_token_budget(self, ctx: HookContext) -> dict:
        """Check token budget before starting a task.

        Warns if estimated tokens exceed the warning threshold.
        Non-blocking in CI environments (no TTY).
        """
        import sys

        try:
            from ..tokens import (
                estimate_from_task_file,
                get_budget_status,
                THRESHOLDS,
            )

            # Find task file
            task_file = None
            tasks_dir = self.paircoder_dir / "tasks"
            for pattern in [f"{ctx.task_id}.task.md", f"TASK-{ctx.task_id}.task.md"]:
                path = tasks_dir / pattern
                if path.exists():
                    task_file = path
                    break

            if not task_file:
                return {
                    "budget_checked": False,
                    "reason": f"Task file not found for {ctx.task_id}",
                }

            estimate = estimate_from_task_file(task_file)
            if not estimate:
                return {
                    "budget_checked": False,
                    "reason": "Could not estimate tokens",
                }

            # Get threshold from config or use default
            budget_config = self.config.get("token_budget", {})
            warning_threshold = budget_config.get("warning_threshold", THRESHOLDS["warning"])

            status = get_budget_status(estimate.total)
            over_threshold = estimate.budget_percent >= warning_threshold

            result = {
                "budget_checked": True,
                "task_id": ctx.task_id,
                "estimated_tokens": estimate.total,
                "budget_percent": estimate.budget_percent,
                "threshold": warning_threshold,
                "over_threshold": over_threshold,
                "status": status.status,
            }

            if over_threshold:
                # Check if running interactively
                is_interactive = sys.stdout.isatty() and sys.stdin.isatty()

                # Check if force flag is set in context
                force = ctx.extra.get("force", False)

                if force:
                    result["action"] = "continued_with_force"
                    logger.warning(
                        f"Token budget warning bypassed with --force for {ctx.task_id}"
                    )
                elif is_interactive:
                    # Print warning and prompt
                    print("\n\u26a0\ufe0f  TOKEN BUDGET WARNING")
                    print(f"Task {ctx.task_id} estimated at {estimate.total:,} tokens ({estimate.budget_percent}% of budget)")
                    print(f"Threshold: {warning_threshold}%")
                    print("\nBreakdown:")
                    print(f"  Base context:  {estimate.base_context:,}")
                    print(f"  Task file:     {estimate.task_file:,}")
                    print(f"  Source files:  {estimate.source_files:,}")
                    print(f"  Est. output:   {estimate.estimated_output:,}")
                    print(f"  Total:         {estimate.total:,}")
                    print("\nConsider breaking into smaller subtasks.")

                    try:
                        response = input("\nContinue anyway? [y/N]: ").strip().lower()
                        if response == 'y':
                            result["action"] = "user_continued"
                            logger.info(f"User chose to continue despite budget warning for {ctx.task_id}")
                        else:
                            result["action"] = "user_aborted"
                            result["aborted"] = True
                            logger.info(f"User aborted task {ctx.task_id} due to budget warning")
                    except (EOFError, KeyboardInterrupt):
                        result["action"] = "user_aborted"
                        result["aborted"] = True
                else:
                    # Non-interactive - just warn
                    result["action"] = "warned"
                    logger.warning(
                        f"Token budget warning for {ctx.task_id}: "
                        f"{estimate.total:,} tokens ({estimate.budget_percent}%)"
                    )
            else:
                result["action"] = "passed"

            return result

        except ImportError as e:
            logger.warning(f"Token budget check failed: {e}")
            return {"budget_checked": False, "error": f"Import error: {e}"}
        except Exception as e:
            logger.warning(f"Token budget check failed: {e}")
            return {"budget_checked": False, "error": str(e)}


def load_config(paircoder_dir: Path) -> dict:
    """Load configuration from config.yaml."""
    import yaml

    config_path = paircoder_dir / "config.yaml"
    if config_path.exists():
        return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return {}


def get_hook_runner(paircoder_dir: Path) -> HookRunner:
    """Get a HookRunner instance for the project."""
    config = load_config(paircoder_dir)
    return HookRunner(config, paircoder_dir)
