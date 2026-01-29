"""Sprint burndown chart data generation."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Protocol

from .velocity import VelocityTracker

logger = logging.getLogger(__name__)


class TaskLike(Protocol):
    """Protocol for task-like objects."""

    id: str
    complexity: int
    sprint: str


@dataclass
class SprintConfig:
    """Configuration for a sprint burndown."""

    sprint_id: str
    start_date: datetime
    end_date: datetime
    total_points: int

    @property
    def duration_days(self) -> int:
        """Calculate sprint duration in days (inclusive)."""
        delta = self.end_date - self.start_date
        return delta.days + 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sprint_id": self.sprint_id,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
            "total_points": self.total_points,
            "duration_days": self.duration_days,
        }


@dataclass
class BurndownDataPoint:
    """A single data point in the burndown chart."""

    date: datetime
    remaining: int
    ideal: float
    completed: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "remaining": self.remaining,
            "ideal": self.ideal,
            "completed": self.completed,
        }


@dataclass
class BurndownData:
    """Complete burndown chart data for a sprint."""

    config: SprintConfig
    data_points: List[BurndownDataPoint]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "sprint": self.config.sprint_id,
            "start_date": self.config.start_date.strftime("%Y-%m-%d"),
            "end_date": self.config.end_date.strftime("%Y-%m-%d"),
            "total_points": self.config.total_points,
            "duration_days": self.config.duration_days,
            "data": [p.to_dict() for p in self.data_points],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class BurndownGenerator:
    """Generates burndown chart data from velocity completions."""

    def __init__(self, history_dir: Path):
        """Initialize burndown generator.

        Args:
            history_dir: Directory containing velocity data
        """
        self.history_dir = Path(history_dir)
        self._velocity_tracker = VelocityTracker(history_dir)

    def generate(self, config: SprintConfig) -> BurndownData:
        """Generate burndown data for a sprint.

        Args:
            config: Sprint configuration

        Returns:
            BurndownData with daily data points
        """
        data_points = []
        today = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)

        # Track cumulative completion
        cumulative_completed = 0

        # Generate data points for each day in the sprint
        current_date = config.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = config.end_date.replace(hour=23, minute=59, second=59, microsecond=0)

        while current_date <= end_date:
            # Don't generate future data points
            if current_date > today:
                break

            # Get completions for this day
            daily_completed = self._get_completions_for_date(
                config.sprint_id,
                current_date,
            )
            cumulative_completed += daily_completed

            # Calculate remaining points
            remaining = config.total_points - cumulative_completed

            # Calculate ideal remaining
            ideal = self._calculate_ideal_remaining(config, current_date)

            data_points.append(BurndownDataPoint(
                date=current_date,
                remaining=remaining,
                ideal=ideal,
                completed=cumulative_completed,
            ))

            current_date += timedelta(days=1)

        return BurndownData(config=config, data_points=data_points)

    def _calculate_ideal_remaining(
        self,
        config: SprintConfig,
        date: datetime,
    ) -> float:
        """Calculate ideal remaining points for a date.

        Ideal burndown is a linear progression from total_points to 0.

        Args:
            config: Sprint configuration
            date: Date to calculate for

        Returns:
            Ideal remaining points
        """
        # Normalize dates to start of day
        start = config.start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = config.end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        current = date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Calculate days elapsed
        total_days = (end - start).days
        if total_days == 0:
            return 0.0

        days_elapsed = (current - start).days

        # Linear burndown
        burn_rate_per_day = config.total_points / total_days
        ideal_remaining = config.total_points - (burn_rate_per_day * days_elapsed)

        return max(0.0, ideal_remaining)

    def _get_completions_for_date(
        self,
        sprint_id: str,
        date: datetime,
    ) -> int:
        """Get total points completed on a specific date.

        Args:
            sprint_id: Sprint ID to filter by
            date: Date to get completions for

        Returns:
            Total points completed on that date
        """
        # Get start and end of day
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)

        completions = self._velocity_tracker.load_completions(
            start_date=day_start,
            end_date=day_end,
        )

        # Filter by sprint and sum complexity
        return sum(
            c.complexity
            for c in completions
            if c.sprint == sprint_id
        )

    def create_config_from_tasks(
        self,
        sprint_id: str,
        tasks: List[TaskLike],
        start_date: datetime,
        end_date: datetime,
    ) -> SprintConfig:
        """Create sprint config from a list of tasks.

        Args:
            sprint_id: Sprint ID
            tasks: List of tasks in the sprint
            start_date: Sprint start date
            end_date: Sprint end date

        Returns:
            SprintConfig with calculated total points
        """
        total_points = sum(t.complexity for t in tasks if t.sprint == sprint_id)

        return SprintConfig(
            sprint_id=sprint_id,
            start_date=start_date,
            end_date=end_date,
            total_points=total_points,
        )
