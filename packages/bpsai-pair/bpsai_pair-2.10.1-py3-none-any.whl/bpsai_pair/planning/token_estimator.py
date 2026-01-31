"""Plan-level token estimation for batch planning.

Estimates total token usage for a plan and suggests batching
when plans exceed comfortable session limits.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..metrics.estimation import (
    TokenEstimator,
    TokenEstimationConfig,
)


# Default threshold for comfortable session limits (tokens)
DEFAULT_THRESHOLD = 50000


@dataclass
class TaskTokenEstimate:
    """Token estimate for a single task within a plan."""

    task_id: str
    task_type: str
    complexity: int
    file_count: int
    base_tokens: int
    complexity_tokens: int
    type_multiplier: float
    file_tokens: int
    total_tokens: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "type": self.task_type,
            "complexity": self.complexity,
            "file_count": self.file_count,
            "base_tokens": self.base_tokens,
            "complexity_tokens": self.complexity_tokens,
            "type_multiplier": self.type_multiplier,
            "file_tokens": self.file_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class BatchSuggestion:
    """Suggested batch of tasks."""

    batch_number: int
    task_ids: List[str]
    estimated_tokens: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "batch": self.batch_number,
            "tasks": self.task_ids,
            "estimated_tokens": self.estimated_tokens,
        }


@dataclass
class PlanTokenEstimate:
    """Complete token estimate for a plan."""

    plan_id: str
    base_context: int
    task_count: int
    total_task_tokens: int
    total_file_tokens: int
    total_tokens: int
    threshold: int
    exceeds_threshold: bool
    tasks: List[TaskTokenEstimate] = field(default_factory=list)
    suggested_batches: Optional[List[BatchSuggestion]] = None
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        result = {
            "plan_id": self.plan_id,
            "base_context": self.base_context,
            "task_count": self.task_count,
            "total_task_tokens": self.total_task_tokens,
            "total_file_tokens": self.total_file_tokens,
            "total_tokens": self.total_tokens,
            "threshold": self.threshold,
            "exceeds_threshold": self.exceeds_threshold,
            "tasks": [t.to_dict() for t in self.tasks],
            "recommendations": self.recommendations,
        }
        if self.suggested_batches:
            result["suggested_batches"] = [b.to_dict() for b in self.suggested_batches]
        return result


class PlanTokenEstimator:
    """Estimates token usage for entire plans and suggests batching.

    Uses the existing TokenEstimator for per-task estimates and aggregates
    across all tasks in a plan.

    Example usage:
        estimator = PlanTokenEstimator.from_config_file(config_path)
        plan_estimate = estimator.estimate_plan("plan-id", tasks)
        if plan_estimate.exceeds_threshold:
            print("Consider splitting into batches:")
            for batch in plan_estimate.suggested_batches:
                print(f"  Batch {batch.batch_number}: {batch.task_ids}")
    """

    def __init__(self, config: Optional[TokenEstimationConfig] = None):
        """Initialize the plan token estimator.

        Args:
            config: Optional token estimation config
        """
        self.config = config or TokenEstimationConfig()
        self._task_estimator = TokenEstimator(self.config)

    @classmethod
    def from_config_file(cls, config_path: Path) -> "PlanTokenEstimator":
        """Load estimator from config.yaml.

        Args:
            config_path: Path to config.yaml

        Returns:
            Configured PlanTokenEstimator
        """
        if not config_path.exists():
            return cls()

        try:
            with open(config_path, encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            token_data = data.get("token_estimates", {})
            config = TokenEstimationConfig.from_dict(token_data)
            return cls(config)
        except Exception:
            return cls()

    def estimate_task(self, task: Any) -> TaskTokenEstimate:
        """Estimate tokens for a single task.

        Args:
            task: Task object with id, type, complexity, and files_touched attributes

        Returns:
            TaskTokenEstimate with breakdown
        """
        task_id = getattr(task, "id", str(task))
        task_type = getattr(task, "type", "feature")
        complexity = getattr(task, "complexity", 50)
        files_touched = getattr(task, "files_touched", [])
        file_count = len(files_touched) if files_touched else 0

        # Use underlying estimator
        estimate = self._task_estimator.estimate_tokens(
            complexity=complexity,
            task_type=task_type,
            file_count=file_count,
        )

        return TaskTokenEstimate(
            task_id=task_id,
            task_type=task_type,
            complexity=complexity,
            file_count=file_count,
            base_tokens=estimate.base_tokens,
            complexity_tokens=estimate.complexity_tokens,
            type_multiplier=estimate.type_multiplier,
            file_tokens=estimate.file_tokens,
            total_tokens=estimate.total_tokens,
        )

    def estimate_plan(
        self,
        plan_id: str,
        tasks: List[Any],
        threshold: int = DEFAULT_THRESHOLD,
    ) -> PlanTokenEstimate:
        """Estimate total tokens for a plan.

        Args:
            plan_id: Plan identifier
            tasks: List of task objects
            threshold: Token threshold for warnings (default 50k)

        Returns:
            PlanTokenEstimate with breakdown and batching suggestions
        """
        # Estimate each task
        task_estimates = [self.estimate_task(task) for task in tasks]

        # Calculate totals (base context is shared, not per-task)
        base_context = self.config.base_context
        total_task_tokens = sum(
            te.complexity_tokens for te in task_estimates
        )
        total_file_tokens = sum(te.file_tokens for te in task_estimates)
        total_tokens = base_context + total_task_tokens + total_file_tokens

        exceeds_threshold = total_tokens > threshold

        # Generate batching suggestions if needed
        suggested_batches = None
        recommendations = []

        if exceeds_threshold:
            suggested_batches = self._suggest_batches(task_estimates, threshold)
            recommendations = self._generate_recommendations(
                total_tokens, threshold, len(suggested_batches) if suggested_batches else 1
            )

        return PlanTokenEstimate(
            plan_id=plan_id,
            base_context=base_context,
            task_count=len(tasks),
            total_task_tokens=total_task_tokens,
            total_file_tokens=total_file_tokens,
            total_tokens=total_tokens,
            threshold=threshold,
            exceeds_threshold=exceeds_threshold,
            tasks=task_estimates,
            suggested_batches=suggested_batches,
            recommendations=recommendations,
        )

    def _suggest_batches(
        self,
        task_estimates: List[TaskTokenEstimate],
        threshold: int,
    ) -> List[BatchSuggestion]:
        """Suggest how to batch tasks to stay under threshold.

        Uses a simple greedy algorithm: add tasks to current batch
        until threshold would be exceeded, then start a new batch.

        Args:
            task_estimates: List of task estimates
            threshold: Token threshold per batch

        Returns:
            List of batch suggestions
        """
        batches = []
        current_batch: List[str] = []
        current_tokens = self.config.base_context  # Each batch needs base context

        for te in task_estimates:
            task_tokens = te.complexity_tokens + te.file_tokens

            if current_tokens + task_tokens > threshold and current_batch:
                # Start new batch
                batches.append(BatchSuggestion(
                    batch_number=len(batches) + 1,
                    task_ids=current_batch,
                    estimated_tokens=current_tokens,
                ))
                current_batch = []
                current_tokens = self.config.base_context

            current_batch.append(te.task_id)
            current_tokens += task_tokens

        # Add final batch
        if current_batch:
            batches.append(BatchSuggestion(
                batch_number=len(batches) + 1,
                task_ids=current_batch,
                estimated_tokens=current_tokens,
            ))

        return batches

    def _generate_recommendations(
        self,
        total_tokens: int,
        threshold: int,
        batch_count: int,
    ) -> List[str]:
        """Generate recommendations for handling large plans.

        Args:
            total_tokens: Total estimated tokens
            threshold: Threshold that was exceeded
            batch_count: Number of suggested batches

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if batch_count > 1:
            recommendations.append(
                f"Split into {batch_count} batches to stay under {threshold:,} tokens per session"
            )

        recommendations.append("Use intermediate commits for recovery points")
        recommendations.append("Update state.md frequently between tasks")

        if total_tokens > threshold * 2:
            recommendations.append(
                "Consider breaking down high-complexity tasks further"
            )

        return recommendations

    def format_estimate(
        self,
        estimate: PlanTokenEstimate,
        show_tasks: bool = True,
    ) -> str:
        """Format estimate for human-readable output.

        Args:
            estimate: Plan token estimate
            show_tasks: Whether to show per-task breakdown

        Returns:
            Formatted string output
        """
        lines = []

        lines.append(f"\nPlan Token Estimate: {estimate.plan_id}")
        lines.append("=" * 50)

        # Breakdown
        lines.append(f"  Base context:     {estimate.base_context:>10,}")
        lines.append(
            f"  Tasks ({estimate.task_count}):        {estimate.total_task_tokens:>10,}  "
            f"(avg {estimate.total_task_tokens // max(estimate.task_count, 1):,} per task)"
        )
        lines.append(
            f"  Files touched:    {estimate.total_file_tokens:>10,}  "
            f"({estimate.total_file_tokens // 2000} files × 2,000)"
        )
        lines.append("  " + "─" * 40)
        lines.append(f"  Total estimate:   {estimate.total_tokens:>10,} tokens")

        # Warning if threshold exceeded
        if estimate.exceeds_threshold:
            lines.append("")
            lines.append(f"⚠️  This plan may exceed comfortable session limits ({estimate.threshold:,} tokens).")
            lines.append("")

            if estimate.recommendations:
                lines.append("Recommendations:")
                for i, rec in enumerate(estimate.recommendations, 1):
                    lines.append(f"  {i}. {rec}")

            if estimate.suggested_batches:
                lines.append("")
                lines.append("Suggested batches:")
                for batch in estimate.suggested_batches:
                    task_range = f"{batch.task_ids[0]}-{batch.task_ids[-1]}" if len(batch.task_ids) > 1 else batch.task_ids[0]
                    lines.append(
                        f"  Batch {batch.batch_number}: {task_range} (~{batch.estimated_tokens:,} tokens)"
                    )
        else:
            lines.append("")
            lines.append(f"✅ Plan is within comfortable limits ({estimate.threshold:,} tokens)")

        # Optional per-task breakdown
        if show_tasks and estimate.tasks:
            lines.append("")
            lines.append("Per-task breakdown:")
            for te in estimate.tasks:
                lines.append(
                    f"  {te.task_id}: {te.total_tokens:,} tokens "
                    f"({te.task_type}, complexity={te.complexity}, files={te.file_count})"
                )

        return "\n".join(lines)
