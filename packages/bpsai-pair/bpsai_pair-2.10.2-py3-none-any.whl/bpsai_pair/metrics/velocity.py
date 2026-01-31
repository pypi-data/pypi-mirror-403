"""Velocity tracking for project planning."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TaskCompletionRecord:
    """Record of a completed task for velocity tracking."""

    task_id: str
    complexity: int
    sprint: str
    completed_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "complexity": self.complexity,
            "sprint": self.sprint,
            "completed_at": self.completed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskCompletionRecord":
        """Create from dictionary."""
        completed_at = data.get("completed_at", "")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)
        return cls(
            task_id=data.get("task_id", ""),
            complexity=data.get("complexity", 0),
            sprint=data.get("sprint", ""),
            completed_at=completed_at,
        )


@dataclass
class VelocityStats:
    """Velocity statistics for reporting."""

    points_this_week: int = 0
    points_this_sprint: int = 0
    avg_weekly_velocity: float = 0.0
    avg_sprint_velocity: float = 0.0
    weeks_tracked: int = 0
    sprints_tracked: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "points_this_week": self.points_this_week,
            "points_this_sprint": self.points_this_sprint,
            "avg_weekly_velocity": self.avg_weekly_velocity,
            "avg_sprint_velocity": self.avg_sprint_velocity,
            "weeks_tracked": self.weeks_tracked,
            "sprints_tracked": self.sprints_tracked,
        }


class VelocityTracker:
    """Tracks velocity metrics for project planning."""

    def __init__(self, history_dir: Path):
        """Initialize velocity tracker.

        Args:
            history_dir: Directory to store velocity data
        """
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self._velocity_log_path = self.history_dir / "velocity-completions.jsonl"

    def record_completion(
        self,
        task_id: str,
        complexity: int,
        sprint: str,
        completed_at: Optional[datetime] = None,
    ) -> TaskCompletionRecord:
        """Record a task completion for velocity tracking.

        Args:
            task_id: The completed task ID
            complexity: Complexity points for the task
            sprint: Sprint ID for the task
            completed_at: When the task was completed (defaults to now)

        Returns:
            The recorded completion record
        """
        completed_at = completed_at or datetime.now()
        record = TaskCompletionRecord(
            task_id=task_id,
            complexity=complexity,
            sprint=sprint,
            completed_at=completed_at,
        )

        try:
            with open(self._velocity_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict()) + "\n")
        except Exception as e:
            logger.warning(f"Failed to record velocity completion: {e}")

        return record

    def load_completions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[TaskCompletionRecord]:
        """Load task completion records.

        Args:
            start_date: Filter to completions after this date
            end_date: Filter to completions before this date

        Returns:
            List of completion records
        """
        completions = []

        if not self._velocity_log_path.exists():
            return completions

        try:
            with open(self._velocity_log_path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            record = TaskCompletionRecord.from_dict(data)

                            # Apply date filters
                            if start_date and record.completed_at < start_date:
                                continue
                            if end_date and record.completed_at > end_date:
                                continue

                            completions.append(record)
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.warning(f"Failed to parse velocity line: {e}")
        except Exception as e:
            logger.warning(f"Failed to load velocity completions: {e}")

        return completions

    def _get_week_start(self, date: datetime) -> datetime:
        """Get the Monday at the start of the week containing the date."""
        # weekday() returns 0 for Monday, 6 for Sunday
        days_since_monday = date.weekday()
        monday = date - timedelta(days=days_since_monday)
        return monday.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_points_this_week(self) -> int:
        """Get complexity points completed this week (since Monday)."""
        return self.get_points_for_week(datetime.now())

    def get_points_for_week(self, date: datetime) -> int:
        """Get complexity points completed in the week containing the date.

        Args:
            date: Any date within the target week

        Returns:
            Total complexity points for that week
        """
        week_start = self._get_week_start(date)
        week_end = week_start + timedelta(days=7)

        completions = self.load_completions(start_date=week_start, end_date=week_end)
        return sum(c.complexity for c in completions)

    def get_points_for_sprint(self, sprint: str) -> int:
        """Get complexity points completed in a specific sprint.

        Args:
            sprint: Sprint ID

        Returns:
            Total complexity points for that sprint
        """
        completions = self.load_completions()
        return sum(c.complexity for c in completions if c.sprint == sprint)

    def get_weekly_velocity_average(self, weeks: int = 4) -> float:
        """Calculate rolling average weekly velocity.

        Args:
            weeks: Number of weeks to include in average

        Returns:
            Average points per week
        """
        now = datetime.now()
        week_totals = []

        for i in range(weeks):
            week_date = now - timedelta(weeks=i)
            points = self.get_points_for_week(week_date)
            week_totals.append(points)

        if not week_totals:
            return 0.0

        return sum(week_totals) / len(week_totals)

    def get_sprint_velocity_average(self, sprints: int = 3) -> float:
        """Calculate average velocity per sprint.

        Args:
            sprints: Number of recent sprints to include

        Returns:
            Average points per sprint
        """
        completions = self.load_completions()
        sprint_totals: Dict[str, int] = {}

        for c in completions:
            if c.sprint:
                sprint_totals[c.sprint] = sprint_totals.get(c.sprint, 0) + c.complexity

        if not sprint_totals:
            return 0.0

        # Sort sprints by name (assuming format like sprint-17, sprint-16, etc)
        sorted_sprints = sorted(sprint_totals.keys(), reverse=True)
        recent_sprints = sorted_sprints[:sprints]

        if not recent_sprints:
            return 0.0

        total = sum(sprint_totals[s] for s in recent_sprints)
        return total / len(recent_sprints)

    def get_velocity_stats(
        self,
        current_sprint: str = "",
        weeks_for_average: int = 4,
        sprints_for_average: int = 3,
    ) -> VelocityStats:
        """Get comprehensive velocity statistics.

        Args:
            current_sprint: Current sprint ID
            weeks_for_average: Number of weeks for rolling average
            sprints_for_average: Number of sprints for average

        Returns:
            VelocityStats with all metrics
        """
        completions = self.load_completions()

        # Count unique weeks and sprints
        weeks_set = set()
        sprints_set = set()
        for c in completions:
            week_start = self._get_week_start(c.completed_at)
            weeks_set.add(week_start.isoformat())
            if c.sprint:
                sprints_set.add(c.sprint)

        return VelocityStats(
            points_this_week=self.get_points_this_week(),
            points_this_sprint=self.get_points_for_sprint(current_sprint) if current_sprint else 0,
            avg_weekly_velocity=self.get_weekly_velocity_average(weeks_for_average),
            avg_sprint_velocity=self.get_sprint_velocity_average(sprints_for_average),
            weeks_tracked=len(weeks_set),
            sprints_tracked=len(sprints_set),
        )

    def get_weekly_breakdown(self, weeks: int = 4) -> List[Dict[str, Any]]:
        """Get breakdown of velocity by week.

        Args:
            weeks: Number of weeks to include

        Returns:
            List of dicts with week_start and points
        """
        now = datetime.now()
        breakdown = []

        for i in range(weeks):
            week_date = now - timedelta(weeks=i)
            week_start = self._get_week_start(week_date)
            points = self.get_points_for_week(week_date)

            breakdown.append({
                "week_start": week_start.strftime("%Y-%m-%d"),
                "points": points,
            })

        return breakdown

    def get_sprint_breakdown(self) -> Dict[str, int]:
        """Get breakdown of velocity by sprint.

        Returns:
            Dict mapping sprint ID to total points
        """
        completions = self.load_completions()
        sprint_totals: Dict[str, int] = {}

        for c in completions:
            if c.sprint:
                sprint_totals[c.sprint] = sprint_totals.get(c.sprint, 0) + c.complexity

        return sprint_totals
