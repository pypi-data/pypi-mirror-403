"""Budget tracking and enforcement for AI agent usage."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
import logging

from .collector import MetricsCollector

logger = logging.getLogger(__name__)


@dataclass
class BudgetConfig:
    """Budget configuration."""
    daily_limit_usd: float = 10.00
    monthly_limit_usd: float = 200.00
    alert_threshold: float = 0.8  # Alert at 80% of limit


@dataclass
class BudgetStatus:
    """Current budget status."""
    daily_spent: float
    daily_limit: float
    daily_remaining: float
    daily_percent: float
    monthly_spent: float
    monthly_limit: float
    monthly_remaining: float
    monthly_percent: float
    alert_triggered: bool
    alert_message: Optional[str] = None

    @property
    def within_budget(self) -> bool:
        return self.daily_remaining > 0 and self.monthly_remaining > 0


class BudgetEnforcer:
    """Enforces budget limits on agent invocations."""

    def __init__(self, collector: MetricsCollector, config: Optional[BudgetConfig] = None):
        self.collector = collector
        self.config = config or BudgetConfig()

    def check_budget(self) -> BudgetStatus:
        """Check current spend against limits."""
        now = datetime.now()

        # Calculate daily spend
        daily_totals = self.collector.get_daily_totals(now)
        daily_spent = daily_totals["cost_usd"]
        daily_remaining = max(0, self.config.daily_limit_usd - daily_spent)
        daily_percent = (daily_spent / self.config.daily_limit_usd) * 100 if self.config.daily_limit_usd > 0 else 0

        # Calculate monthly spend
        start_of_month = datetime(now.year, now.month, 1)
        monthly_events = self.collector.load_events(start_of_month, now)
        monthly_spent = sum(e.cost_usd for e in monthly_events)
        monthly_remaining = max(0, self.config.monthly_limit_usd - monthly_spent)
        monthly_percent = (monthly_spent / self.config.monthly_limit_usd) * 100 if self.config.monthly_limit_usd > 0 else 0

        # Check alert threshold
        alert_triggered = False
        alert_message = None

        if daily_percent >= self.config.alert_threshold * 100:
            alert_triggered = True
            alert_message = f"Daily spend at {daily_percent:.1f}% of limit"
        elif monthly_percent >= self.config.alert_threshold * 100:
            alert_triggered = True
            alert_message = f"Monthly spend at {monthly_percent:.1f}% of limit"

        return BudgetStatus(
            daily_spent=round(daily_spent, 4),
            daily_limit=self.config.daily_limit_usd,
            daily_remaining=round(daily_remaining, 4),
            daily_percent=round(daily_percent, 1),
            monthly_spent=round(monthly_spent, 4),
            monthly_limit=self.config.monthly_limit_usd,
            monthly_remaining=round(monthly_remaining, 4),
            monthly_percent=round(monthly_percent, 1),
            alert_triggered=alert_triggered,
            alert_message=alert_message,
        )

    def can_proceed(self, estimated_cost: float) -> Tuple[bool, str]:
        """Check if an operation within budget can proceed."""
        status = self.check_budget()

        if status.daily_remaining < estimated_cost:
            return False, f"Would exceed daily limit (${status.daily_remaining:.2f} remaining)"

        if status.monthly_remaining < estimated_cost:
            return False, f"Would exceed monthly limit (${status.monthly_remaining:.2f} remaining)"

        if status.alert_triggered:
            logger.warning(status.alert_message)

        return True, "OK"

    def estimate_cost(self, agent: str, model: str,
                      estimated_input_tokens: int,
                      estimated_output_tokens: int) -> float:
        """Estimate cost for a planned operation."""
        return self.collector.calculate_cost(
            agent, model,
            estimated_input_tokens,
            estimated_output_tokens
        )

    def get_remaining_budget(self) -> Tuple[float, float]:
        """Get remaining daily and monthly budget."""
        status = self.check_budget()
        return status.daily_remaining, status.monthly_remaining
