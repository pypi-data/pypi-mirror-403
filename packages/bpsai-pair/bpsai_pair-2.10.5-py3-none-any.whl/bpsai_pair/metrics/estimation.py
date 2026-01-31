"""Estimation service for complexity-to-hours and token estimation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from pathlib import Path
import json
import yaml
import logging

if TYPE_CHECKING:
    from ..planning.models import Task

logger = logging.getLogger(__name__)


# Default complexity-to-hours mapping
# Format: complexity_range -> (min_hours, expected_hours, max_hours)
DEFAULT_COMPLEXITY_TO_HOURS = {
    "xs": {"range": (0, 15), "hours": (0.5, 1.0, 2.0)},      # XS - under 2 hours
    "s": {"range": (16, 30), "hours": (1.0, 2.0, 4.0)},      # S - half day
    "m": {"range": (31, 50), "hours": (2.0, 4.0, 8.0)},      # M - full day
    "l": {"range": (51, 75), "hours": (4.0, 8.0, 16.0)},     # L - 1-2 days
    "xl": {"range": (76, 100), "hours": (8.0, 16.0, 32.0)},  # XL - 2-4 days
}


@dataclass
class HoursEstimate:
    """Estimated hours for a task."""
    min_hours: float
    expected_hours: float
    max_hours: float
    complexity: int
    size_band: str  # xs, s, m, l, xl

    def __str__(self) -> str:
        return f"{self.expected_hours:.1f}h ({self.size_band.upper()})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_hours": self.min_hours,
            "expected_hours": self.expected_hours,
            "max_hours": self.max_hours,
            "complexity": self.complexity,
            "size_band": self.size_band,
        }


@dataclass
class TaskComparison:
    """Comparison of estimated vs actual hours for a task."""

    task_id: str
    estimated_hours: float
    actual_hours: float
    completed_at: Optional[datetime] = None

    @property
    def variance_hours(self) -> float:
        """Calculate variance (actual - estimated). Negative means under estimate."""
        return self.actual_hours - self.estimated_hours

    @property
    def variance_percent(self) -> float:
        """Calculate variance as percentage of estimated hours."""
        if self.estimated_hours == 0:
            return 0.0
        return (self.variance_hours / self.estimated_hours) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for metrics JSONL storage."""
        return {
            "task_id": self.task_id,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "variance_hours": self.variance_hours,
            "variance_percent": self.variance_percent,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_task(
        cls, task: "Task", actual_hours: float, completed_at: Optional[datetime] = None
    ) -> "TaskComparison":
        """Create comparison from task object and actual hours."""
        return cls(
            task_id=task.id,
            estimated_hours=task.estimated_hours.expected_hours,
            actual_hours=actual_hours,
            completed_at=completed_at or datetime.now(),
        )


@dataclass
class EstimationConfig:
    """Configuration for estimation service."""
    complexity_to_hours: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: DEFAULT_COMPLEXITY_TO_HOURS.copy()
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EstimationConfig":
        """Create from dictionary (e.g., from config.yaml)."""
        mapping = data.get("complexity_to_hours", {})
        if not mapping:
            return cls()

        # Convert from config format to internal format
        converted = {}
        for key, value in mapping.items():
            if isinstance(value, dict):
                converted[key.lower()] = value
            else:
                # Handle simplified format: "xs": [0.5, 1, 2]
                if isinstance(value, list) and len(value) == 3:
                    converted[key.lower()] = {"hours": tuple(value)}

        # Merge with defaults to fill in missing bands
        result = DEFAULT_COMPLEXITY_TO_HOURS.copy()
        for key, value in converted.items():
            if key in result:
                result[key].update(value)
            else:
                result[key] = value

        return cls(complexity_to_hours=result)


class EstimationService:
    """Service for estimating task hours from complexity points."""

    def __init__(self, config: Optional[EstimationConfig] = None):
        self.config = config or EstimationConfig()

    @classmethod
    def from_config_file(cls, config_path: Path) -> "EstimationService":
        """Load estimation config from a YAML file."""
        if not config_path.exists():
            return cls()

        try:
            with open(config_path, encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            estimation_data = data.get("estimation", {})
            config = EstimationConfig.from_dict(estimation_data)
            return cls(config)
        except Exception as e:
            logger.warning(f"Failed to load estimation config: {e}")
            return cls()

    def get_size_band(self, complexity: int) -> str:
        """Determine the size band for a complexity score.

        Args:
            complexity: Complexity score (0-100)

        Returns:
            Size band: 'xs', 's', 'm', 'l', or 'xl'
        """
        # Clamp to valid range
        complexity = max(0, min(100, complexity))

        for band, info in self.config.complexity_to_hours.items():
            range_tuple = info.get("range", (0, 0))
            if range_tuple[0] <= complexity <= range_tuple[1]:
                return band

        # Fallback based on standard bands if no range defined
        if complexity <= 15:
            return "xs"
        elif complexity <= 30:
            return "s"
        elif complexity <= 50:
            return "m"
        elif complexity <= 75:
            return "l"
        else:
            return "xl"

    def estimate_hours(self, complexity: int) -> HoursEstimate:
        """Estimate hours from complexity score.

        Args:
            complexity: Complexity score (0-100)

        Returns:
            HoursEstimate with min, expected, and max hours
        """
        # Clamp to valid range
        complexity = max(0, min(100, complexity))

        size_band = self.get_size_band(complexity)
        band_info = self.config.complexity_to_hours.get(
            size_band, DEFAULT_COMPLEXITY_TO_HOURS.get(size_band, {"hours": (1.0, 2.0, 4.0)})
        )
        hours = band_info.get("hours", (1.0, 2.0, 4.0))

        return HoursEstimate(
            min_hours=hours[0],
            expected_hours=hours[1],
            max_hours=hours[2],
            complexity=complexity,
            size_band=size_band,
        )

    def estimate_hours_for_tasks(self, tasks: List[Any]) -> Dict[str, HoursEstimate]:
        """Estimate hours for multiple tasks.

        Args:
            tasks: List of Task objects with 'id' and 'complexity' attributes

        Returns:
            Dict mapping task_id to HoursEstimate
        """
        estimates = {}
        for task in tasks:
            task_id = getattr(task, "id", str(task))
            complexity = getattr(task, "complexity", 30)  # Default to medium
            estimates[task_id] = self.estimate_hours(complexity)
        return estimates

    def get_total_hours(self, tasks: List[Any]) -> Tuple[float, float, float]:
        """Get total estimated hours for a list of tasks.

        Args:
            tasks: List of Task objects with 'complexity' attribute

        Returns:
            Tuple of (min_total, expected_total, max_total) hours
        """
        estimates = self.estimate_hours_for_tasks(tasks)

        min_total = sum(e.min_hours for e in estimates.values())
        expected_total = sum(e.expected_hours for e in estimates.values())
        max_total = sum(e.max_hours for e in estimates.values())

        return min_total, expected_total, max_total

    def format_estimate(self, estimate: HoursEstimate) -> str:
        """Format an estimate for display.

        Args:
            estimate: HoursEstimate to format

        Returns:
            Formatted string like "2.0h (S) [1.0h - 4.0h]"
        """
        return (
            f"{estimate.expected_hours:.1f}h ({estimate.size_band.upper()}) "
            f"[{estimate.min_hours:.1f}h - {estimate.max_hours:.1f}h]"
        )

    def create_comparison(
        self, task: Any, actual_hours: float, completed_at: Optional[datetime] = None
    ) -> TaskComparison:
        """Create a comparison between estimated and actual hours.

        Args:
            task: Task object with 'id' and 'complexity' attributes
            actual_hours: Actual hours spent on the task
            completed_at: Optional completion timestamp

        Returns:
            TaskComparison with variance calculations
        """
        task_id = getattr(task, "id", str(task))
        complexity = getattr(task, "complexity", 30)
        estimate = self.estimate_hours(complexity)

        return TaskComparison(
            task_id=task_id,
            estimated_hours=estimate.expected_hours,
            actual_hours=actual_hours,
            completed_at=completed_at or datetime.now(),
        )

    def format_comparison(self, comparison: TaskComparison) -> str:
        """Format a comparison for display.

        Args:
            comparison: TaskComparison to format

        Returns:
            Formatted string like "Est: 4.0h | Act: 3.5h (-12.5%)"
        """
        sign = "+" if comparison.variance_percent > 0 else ""
        return (
            f"Est: {comparison.estimated_hours:.1f}h | "
            f"Act: {comparison.actual_hours:.1f}h "
            f"({sign}{comparison.variance_percent:.1f}%)"
        )


# ============================================================================
# Token Estimation
# ============================================================================

# Default token estimation coefficients
DEFAULT_TOKEN_ESTIMATES = {
    "base_context": 15000,  # Skills, state, project context
    "per_complexity_point": 500,  # Rough: 50 complexity = 25k tokens
    "by_task_type": {
        "feature": 1.2,  # More back-and-forth
        "bugfix": 0.8,   # Usually focused
        "docs": 0.6,     # Less code generation
        "refactor": 1.5,  # Lots of reading existing code
        "chore": 0.9,    # Moderate complexity
    },
    "per_file_touched": 2000,  # Each file adds context
}


@dataclass
class TokenEstimate:
    """Estimated token usage for a task."""

    base_tokens: int
    complexity_tokens: int
    type_multiplier: float
    file_tokens: int
    total_tokens: int
    task_type: str

    def __str__(self) -> str:
        """Return formatted string like '~45K tokens'."""
        if self.total_tokens >= 1000:
            return f"~{self.total_tokens // 1000}K tokens"
        return f"~{self.total_tokens} tokens"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "base_tokens": self.base_tokens,
            "complexity_tokens": self.complexity_tokens,
            "type_multiplier": self.type_multiplier,
            "file_tokens": self.file_tokens,
            "total_tokens": self.total_tokens,
            "task_type": self.task_type,
        }


@dataclass
class TokenEstimationConfig:
    """Configuration for token estimation."""

    base_context: int = DEFAULT_TOKEN_ESTIMATES["base_context"]
    per_complexity_point: int = DEFAULT_TOKEN_ESTIMATES["per_complexity_point"]
    by_task_type: Dict[str, float] = field(
        default_factory=lambda: DEFAULT_TOKEN_ESTIMATES["by_task_type"].copy()
    )
    per_file_touched: int = DEFAULT_TOKEN_ESTIMATES["per_file_touched"]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenEstimationConfig":
        """Create from dictionary (e.g., from config.yaml).

        Args:
            data: Dictionary with token estimation config

        Returns:
            TokenEstimationConfig with merged values
        """
        defaults = DEFAULT_TOKEN_ESTIMATES.copy()

        return cls(
            base_context=data.get("base_context", defaults["base_context"]),
            per_complexity_point=data.get("per_complexity_point", defaults["per_complexity_point"]),
            by_task_type={
                **defaults["by_task_type"],
                **data.get("by_task_type", {}),
            },
            per_file_touched=data.get("per_file_touched", defaults["per_file_touched"]),
        )


class TokenEstimator:
    """Estimates token usage for tasks based on complexity, type, and file count.

    Formula:
        tokens = base_context +
                 (complexity * per_complexity_point) * type_multiplier +
                 (file_count * per_file_touched)
    """

    def __init__(self, config: Optional[TokenEstimationConfig] = None):
        """Initialize token estimator.

        Args:
            config: Optional configuration, uses defaults if not provided
        """
        self.config = config or TokenEstimationConfig()

    @classmethod
    def from_config_file(cls, config_path: Path) -> "TokenEstimator":
        """Load token estimation config from a YAML file.

        Args:
            config_path: Path to config.yaml

        Returns:
            TokenEstimator with loaded configuration
        """
        if not config_path.exists():
            return cls()

        try:
            with open(config_path, encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            token_data = data.get("token_estimates", {})
            config = TokenEstimationConfig.from_dict(token_data)
            return cls(config)
        except Exception as e:
            logger.warning(f"Failed to load token estimation config: {e}")
            return cls()

    def estimate_tokens(
        self,
        complexity: int,
        task_type: str,
        file_count: int,
    ) -> TokenEstimate:
        """Estimate token usage for a task.

        Args:
            complexity: Complexity score (0-100)
            task_type: Type of task (feature, bugfix, docs, refactor, etc.)
            file_count: Number of files touched by the task

        Returns:
            TokenEstimate with breakdown and total
        """
        # Get type multiplier, default to 1.0 for unknown types
        type_multiplier = self.config.by_task_type.get(task_type.lower(), 1.0)

        # Calculate components
        base_tokens = self.config.base_context
        raw_complexity_tokens = complexity * self.config.per_complexity_point
        complexity_tokens = int(raw_complexity_tokens * type_multiplier)
        file_tokens = file_count * self.config.per_file_touched

        # Total
        total_tokens = base_tokens + complexity_tokens + file_tokens

        return TokenEstimate(
            base_tokens=base_tokens,
            complexity_tokens=complexity_tokens,
            type_multiplier=type_multiplier,
            file_tokens=file_tokens,
            total_tokens=total_tokens,
            task_type=task_type,
        )

    def estimate_for_task(self, task: Any) -> TokenEstimate:
        """Estimate tokens from a Task object.

        Args:
            task: Task object with complexity, type, and files_touched attributes

        Returns:
            TokenEstimate for the task
        """
        complexity = getattr(task, "complexity", 50)
        task_type = getattr(task, "type", "feature")
        files_touched = getattr(task, "files_touched", [])
        file_count = len(files_touched) if files_touched else 0

        return self.estimate_tokens(complexity, task_type, file_count)


# ============================================================================
# Token Feedback Loop
# ============================================================================

# Bounds for coefficient learning
MIN_MULTIPLIER = 0.3  # Don't go below 30% of base
MAX_MULTIPLIER = 3.0  # Don't go above 3x of base
LEARNING_RATE = 0.1   # How quickly to adjust (10% per iteration)


@dataclass
class TokenComparison:
    """Comparison of estimated vs actual tokens for a task."""

    task_id: str
    estimated_tokens: int
    actual_tokens: int
    task_type: str
    complexity: int
    completed_at: Optional[datetime] = None

    @property
    def ratio(self) -> float:
        """Calculate ratio (actual/estimated). 1.0 = perfect estimate."""
        if self.estimated_tokens == 0:
            return 1.0
        return self.actual_tokens / self.estimated_tokens

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSONL storage."""
        return {
            "task_id": self.task_id,
            "estimated_tokens": self.estimated_tokens,
            "actual_tokens": self.actual_tokens,
            "ratio": self.ratio,
            "task_type": self.task_type,
            "complexity": self.complexity,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class TokenFeedbackTracker:
    """Tracks token estimation accuracy and enables learning.

    The feedback loop works as follows:
    1. Record estimated vs actual tokens on task completion
    2. Calculate accuracy statistics by task type and complexity
    3. Recommend coefficient adjustments based on historical data
    4. Apply learning to improve future estimates
    """

    def __init__(self, history_dir: Path):
        """Initialize token feedback tracker.

        Args:
            history_dir: Directory for storing token comparison data
        """
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self._comparisons_path = self.history_dir / "token-comparisons.jsonl"

    def record_usage(
        self,
        task_id: str,
        estimated_tokens: int,
        actual_tokens: int,
        task_type: str,
        complexity: int,
        completed_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Record a token usage comparison.

        Args:
            task_id: Task identifier
            estimated_tokens: Tokens estimated before task
            actual_tokens: Actual tokens used
            task_type: Type of task (feature, bugfix, etc.)
            complexity: Complexity score (0-100)
            completed_at: Optional completion timestamp

        Returns:
            Dictionary with comparison data
        """
        comparison = TokenComparison(
            task_id=task_id,
            estimated_tokens=estimated_tokens,
            actual_tokens=actual_tokens,
            task_type=task_type,
            complexity=complexity,
            completed_at=completed_at or datetime.now(),
        )

        data = comparison.to_dict()

        try:
            with open(self._comparisons_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data) + "\n")
        except Exception as e:
            logger.warning(f"Failed to record token comparison: {e}")

        return data

    def load_comparisons(self) -> List[Dict[str, Any]]:
        """Load all token comparisons.

        Returns:
            List of comparison dictionaries
        """
        comparisons = []

        if not self._comparisons_path.exists():
            return comparisons

        try:
            with open(self._comparisons_path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            comparisons.append(data)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse token comparison: {e}")
        except Exception as e:
            logger.warning(f"Failed to load token comparisons: {e}")

        return comparisons

    def get_accuracy_stats(self) -> Dict[str, Any]:
        """Get token accuracy statistics.

        Returns:
            Dictionary with:
            - total_tasks: Number of completed tasks
            - avg_ratio: Average actual/estimated ratio
            - by_task_type: Breakdown by task type
        """
        comparisons = self.load_comparisons()

        if not comparisons:
            return {
                "total_tasks": 0,
                "avg_ratio": 1.0,
                "by_task_type": {},
            }

        # Calculate overall average ratio
        ratios = [c.get("ratio", 1.0) for c in comparisons]
        avg_ratio = sum(ratios) / len(ratios)

        # Group by task type
        by_type: Dict[str, List[float]] = {}
        for c in comparisons:
            task_type = c.get("task_type", "unknown")
            if task_type not in by_type:
                by_type[task_type] = []
            by_type[task_type].append(c.get("ratio", 1.0))

        # Calculate stats per type
        by_type_stats = {}
        for task_type, type_ratios in by_type.items():
            by_type_stats[task_type] = {
                "count": len(type_ratios),
                "avg_ratio": sum(type_ratios) / len(type_ratios),
            }

        return {
            "total_tasks": len(comparisons),
            "avg_ratio": avg_ratio,
            "by_task_type": by_type_stats,
        }

    def get_recommended_adjustments(self, min_samples: int = 2) -> Dict[str, float]:
        """Get recommended coefficient adjustments based on data.

        Args:
            min_samples: Minimum samples needed to recommend adjustment

        Returns:
            Dictionary mapping task_type to recommended multiplier adjustment
            (value > 1.0 means increase multiplier, < 1.0 means decrease)
        """
        stats = self.get_accuracy_stats()
        by_type = stats.get("by_task_type", {})

        adjustments = {}
        for task_type, type_stats in by_type.items():
            if type_stats["count"] >= min_samples:
                # If avg_ratio > 1.0, we're underestimating (need higher multiplier)
                # If avg_ratio < 1.0, we're overestimating (need lower multiplier)
                adjustments[task_type] = type_stats["avg_ratio"]

        return adjustments

    def apply_learning(
        self,
        config: TokenEstimationConfig,
        min_samples: int = 2,
    ) -> TokenEstimationConfig:
        """Apply learning to adjust config coefficients.

        Uses a conservative learning approach:
        new_multiplier = old_multiplier * (1 + LEARNING_RATE * (avg_ratio - 1))

        Args:
            config: Current token estimation config
            min_samples: Minimum samples required per task type

        Returns:
            New TokenEstimationConfig with adjusted multipliers
        """
        adjustments = self.get_recommended_adjustments(min_samples)

        if not adjustments:
            return config

        # Copy current multipliers
        new_multipliers = dict(config.by_task_type)

        for task_type, avg_ratio in adjustments.items():
            if task_type in new_multipliers:
                old_mult = new_multipliers[task_type]
                # Conservative adjustment: move 10% toward the observed ratio
                adjustment_factor = 1 + LEARNING_RATE * (avg_ratio - 1)
                new_mult = old_mult * adjustment_factor

                # Clamp to reasonable bounds
                new_mult = max(MIN_MULTIPLIER, min(MAX_MULTIPLIER, new_mult))
                new_multipliers[task_type] = new_mult

        return TokenEstimationConfig(
            base_context=config.base_context,
            per_complexity_point=config.per_complexity_point,
            by_task_type=new_multipliers,
            per_file_touched=config.per_file_touched,
        )

    def generate_report(self) -> Dict[str, Any]:
        """Generate a token accuracy report.

        Returns:
            Dictionary with stats, breakdown by type, and recommendations
        """
        stats = self.get_accuracy_stats()
        adjustments = self.get_recommended_adjustments()

        # Generate human-readable recommendations
        recommendations = []
        for task_type, adj in adjustments.items():
            if adj > 1.1:
                pct = int((adj - 1) * 100)
                recommendations.append(
                    f"Increase {task_type} multiplier by ~{pct}%"
                )
            elif adj < 0.9:
                pct = int((1 - adj) * 100)
                recommendations.append(
                    f"Decrease {task_type} multiplier by ~{pct}%"
                )

        return {
            "stats": stats,
            "by_task_type": stats.get("by_task_type", {}),
            "recommendations": recommendations,
        }


# Convenience function for quick access
def estimate_hours(complexity: int, config_path: Optional[Path] = None) -> HoursEstimate:
    """Estimate hours for a given complexity score.

    Args:
        complexity: Complexity score (0-100)
        config_path: Optional path to config file

    Returns:
        HoursEstimate with min, expected, and max hours
    """
    if config_path:
        service = EstimationService.from_config_file(config_path)
    else:
        service = EstimationService()

    return service.estimate_hours(complexity)
