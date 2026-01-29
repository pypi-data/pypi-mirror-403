"""Metrics reporting and analytics."""

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from io import StringIO
from typing import List, Dict, Any, Optional

from .collector import MetricsCollector, MetricsEvent


@dataclass
class MetricsSummary:
    """Summary of metrics for a time period."""
    period: str
    start_date: str
    end_date: str
    total_events: int
    successful_events: int
    failed_events: int
    total_tokens: int
    input_tokens: int
    output_tokens: int
    total_cost_usd: float
    total_duration_ms: int
    by_agent: Dict[str, Dict[str, Any]]
    by_task: Dict[str, Dict[str, Any]]
    by_model: Dict[str, Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "period": self.period,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "total_events": self.total_events,
            "successful_events": self.successful_events,
            "failed_events": self.failed_events,
            "tokens": {
                "total": self.total_tokens,
                "input": self.input_tokens,
                "output": self.output_tokens,
            },
            "cost_usd": self.total_cost_usd,
            "duration_ms": self.total_duration_ms,
            "by_agent": self.by_agent,
            "by_task": self.by_task,
            "by_model": self.by_model,
        }


class MetricsReporter:
    """Generates reports from collected metrics."""

    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    def _aggregate_events(self, events: List[MetricsEvent]) -> Dict[str, Any]:
        """Aggregate basic stats from events."""
        total_input = sum(e.tokens.input for e in events)
        total_output = sum(e.tokens.output for e in events)
        total_cost = sum(e.cost_usd for e in events)
        total_duration = sum(e.duration_ms for e in events)
        successful = sum(1 for e in events if e.success)

        return {
            "events": len(events),
            "successful": successful,
            "failed": len(events) - successful,
            "tokens": {
                "input": total_input,
                "output": total_output,
                "total": total_input + total_output,
            },
            "cost_usd": round(total_cost, 4),
            "duration_ms": total_duration,
        }

    def _group_by_field(self, events: List[MetricsEvent],
                        field: str) -> Dict[str, Dict[str, Any]]:
        """Group events by a field and aggregate."""
        grouped: Dict[str, List[MetricsEvent]] = defaultdict(list)

        for event in events:
            key = getattr(event, field) or "unknown"
            grouped[key].append(event)

        return {k: self._aggregate_events(v) for k, v in grouped.items()}

    def get_summary(self, period: str = "daily",
                    date: Optional[datetime] = None) -> MetricsSummary:
        """Get metrics summary for a period."""
        date = date or datetime.now()

        if period == "daily":
            start = datetime(date.year, date.month, date.day)
            end = start + timedelta(days=1) - timedelta(seconds=1)
            period_label = date.strftime("%Y-%m-%d")
        elif period == "weekly":
            # Start of week (Monday)
            start = date - timedelta(days=date.weekday())
            start = datetime(start.year, start.month, start.day)
            end = start + timedelta(days=7) - timedelta(seconds=1)
            period_label = f"Week of {start.strftime('%Y-%m-%d')}"
        elif period == "monthly":
            start = datetime(date.year, date.month, 1)
            # End of month
            if date.month == 12:
                end = datetime(date.year + 1, 1, 1) - timedelta(seconds=1)
            else:
                end = datetime(date.year, date.month + 1, 1) - timedelta(seconds=1)
            period_label = date.strftime("%Y-%m")
        else:
            raise ValueError(f"Unknown period: {period}")

        events = self.collector.load_events(start, end)
        agg = self._aggregate_events(events)

        return MetricsSummary(
            period=period_label,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            total_events=agg["events"],
            successful_events=agg["successful"],
            failed_events=agg["failed"],
            total_tokens=agg["tokens"]["total"],
            input_tokens=agg["tokens"]["input"],
            output_tokens=agg["tokens"]["output"],
            total_cost_usd=agg["cost_usd"],
            total_duration_ms=agg["duration_ms"],
            by_agent=self._group_by_field(events, "agent"),
            by_task=self._group_by_field(events, "task_id"),
            by_model=self._group_by_field(events, "model"),
        )

    def get_breakdown(self, by: str = "agent",
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> Dict[str, Dict[str, Any]]:
        """Get metrics breakdown by a specific dimension."""
        events = self.collector.load_events(start_date, end_date)
        return self._group_by_field(events, by)

    def get_task_metrics(self, task_id: str) -> Dict[str, Any]:
        """Get metrics for a specific task."""
        events = self.collector.get_task_events(task_id)
        metrics = self._aggregate_events(events)
        metrics["task_id"] = task_id
        metrics["by_agent"] = self._group_by_field(events, "agent")
        return metrics

    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get metrics for a specific session."""
        events = self.collector.get_session_events(session_id)
        metrics = self._aggregate_events(events)
        metrics["session_id"] = session_id
        return metrics

    def export_csv(self, start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> str:
        """Export metrics to CSV format."""
        events = self.collector.load_events(start_date, end_date)

        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "timestamp", "session_id", "task_id", "agent", "model",
            "operation", "input_tokens", "output_tokens", "total_tokens",
            "cost_usd", "duration_ms", "success", "error"
        ])

        # Data
        for event in events:
            writer.writerow([
                event.timestamp,
                event.session_id or "",
                event.task_id or "",
                event.agent,
                event.model,
                event.operation,
                event.tokens.input,
                event.tokens.output,
                event.tokens.total,
                event.cost_usd,
                event.duration_ms,
                event.success,
                event.error or "",
            ])

        return output.getvalue()

    def format_summary_report(self, summary: MetricsSummary) -> str:
        """Format summary as human-readable report."""
        lines = [
            f"Metrics Summary: {summary.period}",
            "=" * 50,
            "",
            f"Total Tokens:     {summary.total_tokens:,} ({summary.input_tokens:,} input / {summary.output_tokens:,} output)",
            f"Total Cost:       ${summary.total_cost_usd:.2f}",
            f"Total Operations: {summary.total_events} ({summary.successful_events} success, {summary.failed_events} failed)",
            f"Total Duration:   {summary.total_duration_ms / 1000:.1f}s",
            "",
        ]

        if summary.by_agent:
            lines.append("By Agent:")
            total_cost = sum(v["cost_usd"] for v in summary.by_agent.values())
            for agent, stats in sorted(summary.by_agent.items()):
                pct = (stats["cost_usd"] / total_cost * 100) if total_cost > 0 else 0
                lines.append(f"  {agent}: ${stats['cost_usd']:.2f} ({pct:.0f}%)")
            lines.append("")

        if summary.by_task:
            # Only show top 5 tasks
            lines.append("By Task (top 5):")
            sorted_tasks = sorted(
                summary.by_task.items(),
                key=lambda x: x[1]["cost_usd"],
                reverse=True
            )[:5]
            total_cost = sum(v["cost_usd"] for v in summary.by_task.values())
            for task, stats in sorted_tasks:
                if task != "unknown":
                    pct = (stats["cost_usd"] / total_cost * 100) if total_cost > 0 else 0
                    lines.append(f"  {task}: ${stats['cost_usd']:.2f} ({pct:.0f}%)")
            lines.append("")

        return "\n".join(lines)
