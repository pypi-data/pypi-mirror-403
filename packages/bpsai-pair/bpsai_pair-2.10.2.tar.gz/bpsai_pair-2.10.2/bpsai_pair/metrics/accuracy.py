"""Estimation accuracy analysis and reporting."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Complexity band definitions (matching estimation.py)
COMPLEXITY_BANDS = {
    "XS": (0, 15),
    "S": (16, 30),
    "M": (31, 50),
    "L": (51, 75),
    "XL": (76, 100),
}


@dataclass
class AccuracyStats:
    """Overall estimation accuracy statistics."""

    total_tasks: int
    overall_accuracy: float  # Percentage (0-100)
    bias_direction: str  # "optimistic", "pessimistic", or "neutral"
    bias_percent: float  # How much bias as percentage
    avg_variance_percent: float  # Average variance from estimates

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_tasks": self.total_tasks,
            "overall_accuracy": round(self.overall_accuracy, 1),
            "bias_direction": self.bias_direction,
            "bias_percent": round(self.bias_percent, 1),
            "avg_variance_percent": round(self.avg_variance_percent, 1),
        }


@dataclass
class TaskTypeAccuracy:
    """Accuracy breakdown for a specific task type."""

    task_type: str
    count: int
    accuracy_percent: float
    bias_direction: str
    bias_percent: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_type": self.task_type,
            "count": self.count,
            "accuracy_percent": round(self.accuracy_percent, 1),
            "bias_direction": self.bias_direction,
            "bias_percent": round(self.bias_percent, 1),
        }


@dataclass
class ComplexityBandAccuracy:
    """Accuracy breakdown for a complexity band."""

    band: str
    complexity_range: str
    count: int
    accuracy_percent: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "band": self.band,
            "complexity_range": self.complexity_range,
            "count": self.count,
            "accuracy_percent": round(self.accuracy_percent, 1),
        }


class AccuracyAnalyzer:
    """Analyzes estimation accuracy from historical task data."""

    def __init__(self, history_dir: Path):
        """Initialize accuracy analyzer.

        Args:
            history_dir: Directory containing task completion history
        """
        self.history_dir = Path(history_dir)
        self._completions_path = self.history_dir / "task-completions.jsonl"

    def load_completions(self) -> List[Dict[str, Any]]:
        """Load task completion records.

        Returns:
            List of completion records with estimated vs actual data
        """
        completions = []

        if not self._completions_path.exists():
            return completions

        try:
            with open(self._completions_path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            completions.append(data)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse completion line: {e}")
        except Exception as e:
            logger.warning(f"Failed to load completions: {e}")

        return completions

    def _get_complexity_band(self, complexity: int) -> str:
        """Map complexity score to band name.

        Args:
            complexity: Complexity score (0-100)

        Returns:
            Band name: XS, S, M, L, or XL
        """
        complexity = max(0, min(100, complexity))

        for band, (low, high) in COMPLEXITY_BANDS.items():
            if low <= complexity <= high:
                return band

        return "M"  # Default fallback

    def _calculate_accuracy_from_variance(self, variance_percent: float) -> float:
        """Calculate accuracy percentage from variance.

        Accuracy is 100% when variance is 0, and decreases with variance.

        Args:
            variance_percent: Variance as percentage (can be negative)

        Returns:
            Accuracy percentage (0-100)
        """
        # Use absolute value of variance
        abs_variance = abs(variance_percent)
        # Cap variance at 100% for accuracy calculation
        abs_variance = min(abs_variance, 100.0)
        return 100.0 - abs_variance

    def _determine_bias(self, avg_variance: float) -> tuple[str, float]:
        """Determine bias direction and magnitude.

        Args:
            avg_variance: Average variance percentage (positive = took longer)

        Returns:
            Tuple of (direction, percentage)
        """
        abs_variance = abs(avg_variance)

        if abs_variance < 5.0:
            return "neutral", abs_variance

        if avg_variance > 0:
            # Took longer than estimated = optimistic estimates
            return "optimistic", abs_variance
        else:
            # Finished faster than estimated = pessimistic estimates
            return "pessimistic", abs_variance

    def get_accuracy_stats(self) -> AccuracyStats:
        """Get overall accuracy statistics.

        Returns:
            AccuracyStats with overall metrics
        """
        completions = self.load_completions()

        if not completions:
            return AccuracyStats(
                total_tasks=0,
                overall_accuracy=100.0,
                bias_direction="neutral",
                bias_percent=0.0,
                avg_variance_percent=0.0,
            )

        # Calculate average variance
        variances = [c.get("variance_percent", 0.0) for c in completions]
        avg_variance = sum(variances) / len(variances)

        # Calculate accuracy from average absolute variance
        abs_variances = [abs(v) for v in variances]
        avg_abs_variance = sum(abs_variances) / len(abs_variances)
        overall_accuracy = self._calculate_accuracy_from_variance(avg_abs_variance)

        # Determine bias
        bias_direction, bias_percent = self._determine_bias(avg_variance)

        return AccuracyStats(
            total_tasks=len(completions),
            overall_accuracy=overall_accuracy,
            bias_direction=bias_direction,
            bias_percent=bias_percent,
            avg_variance_percent=avg_variance,
        )

    def get_accuracy_by_task_type(self) -> List[TaskTypeAccuracy]:
        """Get accuracy breakdown by task type.

        Returns:
            List of TaskTypeAccuracy for each task type
        """
        completions = self.load_completions()

        if not completions:
            return []

        # Group by task type
        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for c in completions:
            task_type = c.get("task_type", "unknown")
            if task_type not in by_type:
                by_type[task_type] = []
            by_type[task_type].append(c)

        result = []
        for task_type, tasks in by_type.items():
            variances = [t.get("variance_percent", 0.0) for t in tasks]
            avg_variance = sum(variances) / len(variances)

            abs_variances = [abs(v) for v in variances]
            avg_abs_variance = sum(abs_variances) / len(abs_variances)
            accuracy = self._calculate_accuracy_from_variance(avg_abs_variance)

            bias_direction, bias_percent = self._determine_bias(avg_variance)

            result.append(
                TaskTypeAccuracy(
                    task_type=task_type,
                    count=len(tasks),
                    accuracy_percent=accuracy,
                    bias_direction=bias_direction,
                    bias_percent=bias_percent,
                )
            )

        # Sort by task type name
        result.sort(key=lambda x: x.task_type)
        return result

    def get_accuracy_by_complexity_band(self) -> List[ComplexityBandAccuracy]:
        """Get accuracy breakdown by complexity band.

        Returns:
            List of ComplexityBandAccuracy for each band with data
        """
        completions = self.load_completions()

        if not completions:
            return []

        # Group by complexity band
        by_band: Dict[str, List[Dict[str, Any]]] = {}
        for c in completions:
            complexity = c.get("complexity", 30)  # Default to medium
            band = self._get_complexity_band(complexity)
            if band not in by_band:
                by_band[band] = []
            by_band[band].append(c)

        result = []
        for band in ["XS", "S", "M", "L", "XL"]:
            if band not in by_band:
                continue

            tasks = by_band[band]
            variances = [t.get("variance_percent", 0.0) for t in tasks]
            abs_variances = [abs(v) for v in variances]
            avg_abs_variance = sum(abs_variances) / len(abs_variances)
            accuracy = self._calculate_accuracy_from_variance(avg_abs_variance)

            low, high = COMPLEXITY_BANDS[band]
            result.append(
                ComplexityBandAccuracy(
                    band=band,
                    complexity_range=f"{low}-{high}",
                    count=len(tasks),
                    accuracy_percent=accuracy,
                )
            )

        return result

    def get_recommendation(self) -> str:
        """Generate an actionable recommendation based on accuracy data.

        Returns:
            Recommendation string
        """
        stats = self.get_accuracy_stats()

        if stats.total_tasks == 0:
            return "No historical data available. Complete some tasks to get recommendations."

        if stats.bias_direction == "neutral":
            return "Your estimates are well-calibrated. Keep up the good work!"

        if stats.bias_direction == "optimistic":
            buffer_pct = int(stats.bias_percent)
            return f"Add {buffer_pct}% buffer to estimates to improve accuracy."

        # Pessimistic
        buffer_pct = int(stats.bias_percent)
        return f"Your estimates are {buffer_pct}% pessimistic. Consider reducing estimates."

    def generate_report(self) -> Dict[str, Any]:
        """Generate a full accuracy report.

        Returns:
            Dictionary with all accuracy data
        """
        stats = self.get_accuracy_stats()
        by_type = self.get_accuracy_by_task_type()
        by_band = self.get_accuracy_by_complexity_band()
        recommendation = self.get_recommendation()

        return {
            "stats": stats.to_dict(),
            "by_task_type": [t.to_dict() for t in by_type],
            "by_complexity_band": [b.to_dict() for b in by_band],
            "recommendation": recommendation,
        }
