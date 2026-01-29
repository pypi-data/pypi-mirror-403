"""Metrics collection for token usage and costs."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


# Default pricing per 1M tokens (as of Jan 2025)
DEFAULT_PRICING = {
    "claude-code": {
        "claude-sonnet-4-5-20250929": {"input_per_1m": 3.00, "output_per_1m": 15.00},
        "claude-opus-4-5-20251101": {"input_per_1m": 15.00, "output_per_1m": 75.00},
        "default": {"input_per_1m": 3.00, "output_per_1m": 15.00},
    },
    "codex-cli": {
        "default": {"input_per_1m": 2.50, "output_per_1m": 10.00},
    },
}


@dataclass
class TokenUsage:
    """Token usage data."""
    input: int = 0
    output: int = 0

    @property
    def total(self) -> int:
        return self.input + self.output


@dataclass
class MetricsEvent:
    """A single metrics event for an agent invocation."""
    timestamp: str
    session_id: Optional[str]
    task_id: Optional[str]
    agent: str
    model: str
    operation: str
    tokens: TokenUsage
    cost_usd: float
    duration_ms: int
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "agent": self.agent,
            "model": self.model,
            "operation": self.operation,
            "tokens": {
                "input": self.tokens.input,
                "output": self.tokens.output,
                "total": self.tokens.total,
            },
            "cost_usd": self.cost_usd,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricsEvent":
        """Create from dictionary."""
        tokens_data = data.get("tokens", {})
        return cls(
            timestamp=data.get("timestamp", ""),
            session_id=data.get("session_id"),
            task_id=data.get("task_id"),
            agent=data.get("agent", "unknown"),
            model=data.get("model", "unknown"),
            operation=data.get("operation", "invoke"),
            tokens=TokenUsage(
                input=tokens_data.get("input", 0),
                output=tokens_data.get("output", 0),
            ),
            cost_usd=data.get("cost_usd", 0.0),
            duration_ms=data.get("duration_ms", 0),
            success=data.get("success", True),
            error=data.get("error"),
        )


@dataclass
class PricingConfig:
    """Pricing configuration."""
    pricing: Dict[str, Dict[str, Dict[str, float]]] = field(default_factory=lambda: DEFAULT_PRICING.copy())

    def get_pricing(self, agent: str, model: str) -> Dict[str, float]:
        """Get pricing for agent/model combination."""
        agent_pricing = self.pricing.get(agent, {})
        return agent_pricing.get(model, agent_pricing.get("default", {"input_per_1m": 3.0, "output_per_1m": 15.0}))


class MetricsCollector:
    """Collects and stores metrics for agent invocations."""

    def __init__(self, history_dir: Path, pricing_config: Optional[PricingConfig] = None):
        self.history_dir = history_dir
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.pricing = pricing_config or PricingConfig()
        self._current_log = self._get_current_log_path()

    def _get_current_log_path(self) -> Path:
        """Get the current month's log file path."""
        now = datetime.now()
        return self.history_dir / f"metrics-{now.strftime('%Y-%m')}.jsonl"

    def record(self, event: MetricsEvent) -> None:
        """Append event to metrics log."""
        try:
            # Ensure we're using current month's log
            self._current_log = self._get_current_log_path()

            with open(self._current_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception as e:
            # Don't block on metrics failures
            logger.warning(f"Failed to record metrics: {e}")

    def calculate_cost(self, agent: str, model: str,
                       input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on pricing config."""
        pricing = self.pricing.get_pricing(agent, model)
        input_cost = (input_tokens / 1_000_000) * pricing.get("input_per_1m", 3.0)
        output_cost = (output_tokens / 1_000_000) * pricing.get("output_per_1m", 15.0)
        return round(input_cost + output_cost, 6)

    def create_event(
        self,
        agent: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int,
        success: bool = True,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        operation: str = "invoke",
        error: Optional[str] = None,
    ) -> MetricsEvent:
        """Create a metrics event with calculated cost."""
        cost = self.calculate_cost(agent, model, input_tokens, output_tokens)

        return MetricsEvent(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            task_id=task_id,
            agent=agent,
            model=model,
            operation=operation,
            tokens=TokenUsage(input=input_tokens, output=output_tokens),
            cost_usd=cost,
            duration_ms=duration_ms,
            success=success,
            error=error,
        )

    def record_invocation(
        self,
        agent: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int,
        success: bool = True,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        operation: str = "invoke",
        error: Optional[str] = None,
    ) -> MetricsEvent:
        """Create and record a metrics event."""
        event = self.create_event(
            agent=agent,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            success=success,
            session_id=session_id,
            task_id=task_id,
            operation=operation,
            error=error,
        )
        self.record(event)
        return event

    def load_events(self, start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> List[MetricsEvent]:
        """Load events from metrics log files."""
        events = []

        for log_file in sorted(self.history_dir.glob("metrics-*.jsonl")):
            # Parse date from filename to filter
            try:
                file_date_str = log_file.stem.replace("metrics-", "")
                file_date = datetime.strptime(file_date_str, "%Y-%m")

                if start_date and file_date < datetime(start_date.year, start_date.month, 1):
                    continue
                if end_date and file_date > datetime(end_date.year, end_date.month, 1):
                    continue
            except ValueError:
                continue

            with open(log_file, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            event = MetricsEvent.from_dict(data)

                            # Filter by exact date if specified
                            event_dt = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00").replace("+00:00", ""))
                            if start_date and event_dt < start_date:
                                continue
                            if end_date and event_dt > end_date:
                                continue

                            events.append(event)
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.warning(f"Failed to parse metrics line: {e}")

        return events

    def get_session_events(self, session_id: str) -> List[MetricsEvent]:
        """Get all events for a specific session."""
        events = self.load_events()
        return [e for e in events if e.session_id == session_id]

    def get_task_events(self, task_id: str) -> List[MetricsEvent]:
        """Get all events for a specific task."""
        events = self.load_events()
        return [e for e in events if e.task_id == task_id]

    def get_daily_totals(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get totals for a specific day."""
        date = date or datetime.now()
        start = datetime(date.year, date.month, date.day)
        end = datetime(date.year, date.month, date.day, 23, 59, 59)

        events = self.load_events(start, end)

        total_input = sum(e.tokens.input for e in events)
        total_output = sum(e.tokens.output for e in events)
        total_cost = sum(e.cost_usd for e in events)

        return {
            "date": date.strftime("%Y-%m-%d"),
            "events": len(events),
            "tokens": {
                "input": total_input,
                "output": total_output,
                "total": total_input + total_output,
            },
            "cost_usd": round(total_cost, 4),
        }

    def _get_task_completions_log_path(self) -> Path:
        """Get the task completions log file path."""
        return self.history_dir / "task-completions.jsonl"

    def record_task_completion(
        self,
        task_id: str,
        estimated_hours: float,
        actual_hours: float,
        variance_hours: Optional[float] = None,
        variance_percent: Optional[float] = None,
        completed_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Record task completion with estimated vs actual comparison.

        Args:
            task_id: The task ID
            estimated_hours: Estimated hours for the task
            actual_hours: Actual hours spent on the task
            variance_hours: Variance in hours (actual - estimated)
            variance_percent: Variance as percentage
            completed_at: Completion timestamp

        Returns:
            The recorded comparison data
        """
        completed_at = completed_at or datetime.now()

        # Calculate variance if not provided
        if variance_hours is None:
            variance_hours = actual_hours - estimated_hours

        if variance_percent is None:
            if estimated_hours > 0:
                variance_percent = (variance_hours / estimated_hours) * 100
            else:
                variance_percent = 0.0

        data = {
            "task_id": task_id,
            "estimated_hours": round(estimated_hours, 2),
            "actual_hours": round(actual_hours, 2),
            "variance_hours": round(variance_hours, 2),
            "variance_percent": round(variance_percent, 1),
            "completed_at": completed_at.isoformat(),
        }

        try:
            log_path = self._get_task_completions_log_path()
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data) + "\n")
            logger.info(f"Recorded task completion for {task_id}")
        except Exception as e:
            logger.warning(f"Failed to record task completion: {e}")

        return data

    def load_task_completions(
        self, task_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Load task completion records.

        Args:
            task_id: Optional task ID to filter by

        Returns:
            List of task completion records
        """
        completions = []
        log_path = self._get_task_completions_log_path()

        if not log_path.exists():
            return completions

        try:
            with open(log_path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            if task_id is None or data.get("task_id") == task_id:
                                completions.append(data)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.warning(f"Failed to load task completions: {e}")

        return completions

    def get_estimation_accuracy(self) -> Dict[str, Any]:
        """Get overall estimation accuracy statistics.

        Returns:
            Dictionary with accuracy metrics
        """
        completions = self.load_task_completions()

        if not completions:
            return {
                "total_tasks": 0,
                "avg_variance_percent": 0.0,
                "under_estimates": 0,
                "over_estimates": 0,
                "accurate": 0,
            }

        total = len(completions)
        variances = [c.get("variance_percent", 0) for c in completions]
        avg_variance = sum(variances) / total if total > 0 else 0

        # Count under/over/accurate (within 10%)
        under = sum(1 for v in variances if v > 10)  # Took longer than estimated
        over = sum(1 for v in variances if v < -10)  # Finished faster
        accurate = total - under - over

        return {
            "total_tasks": total,
            "avg_variance_percent": round(avg_variance, 1),
            "under_estimates": under,
            "over_estimates": over,
            "accurate": accurate,
        }
