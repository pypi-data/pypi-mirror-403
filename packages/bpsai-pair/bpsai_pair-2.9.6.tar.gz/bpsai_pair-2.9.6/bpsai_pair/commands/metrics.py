"""Metrics commands for token tracking and cost estimation.

Extracted from cli.py as part of EPIC-003 CLI Architecture Refactor.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

# Initialize Rich console
console = Console()


def print_json(data: dict) -> None:
    """Print JSON to stdout without Rich formatting."""
    sys.stdout.write(json.dumps(data, indent=2))
    sys.stdout.write("\n")
    sys.stdout.flush()


# Try relative imports first, fall back to absolute
try:
    from ..core import ops
    from ..metrics import MetricsCollector, MetricsReporter, BudgetEnforcer, VelocityTracker
except ImportError:
    from bpsai_pair.core import ops
    from bpsai_pair.metrics import MetricsCollector, MetricsReporter, BudgetEnforcer, VelocityTracker


def repo_root() -> Path:
    """Get repo root with better error message."""
    p = ops.find_project_root()
    if not ops.GitOps.is_repo(p):
        console.print(
            "[red]✗ Not in a git repository.[/red]\n"
            "Please run from your project root directory (where .git exists).\n"
            "[dim]Hint: cd to your project directory first[/dim]"
        )
        raise typer.Exit(1)
    return p


def _get_metrics_collector() -> MetricsCollector:
    """Get a metrics collector instance."""
    root = repo_root()
    history_dir = root / ".paircoder" / "history"
    return MetricsCollector(history_dir)


def _get_velocity_tracker() -> VelocityTracker:
    """Get a velocity tracker instance."""
    root = repo_root()
    history_dir = root / ".paircoder" / "history"
    return VelocityTracker(history_dir)


def _get_burndown_generator():
    """Get a burndown generator instance."""
    try:
        from ..metrics import BurndownGenerator
    except ImportError:
        from bpsai_pair.metrics import BurndownGenerator
    root = repo_root()
    history_dir = root / ".paircoder" / "history"
    return BurndownGenerator(history_dir)


def _get_accuracy_analyzer():
    """Get an accuracy analyzer instance."""
    try:
        from ..metrics.accuracy import AccuracyAnalyzer
    except ImportError:
        from bpsai_pair.metrics.accuracy import AccuracyAnalyzer
    root = repo_root()
    history_dir = root / ".paircoder" / "history"
    return AccuracyAnalyzer(history_dir)


def _get_token_tracker():
    """Get a token feedback tracker instance."""
    try:
        from ..metrics.estimation import TokenFeedbackTracker
    except ImportError:
        from bpsai_pair.metrics.estimation import TokenFeedbackTracker
    root = repo_root()
    history_dir = root / ".paircoder" / "history"
    return TokenFeedbackTracker(history_dir)


# Metrics sub-app for token tracking and cost estimation
app = typer.Typer(
    help="Token tracking and cost estimation",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@app.command("summary")
def metrics_summary(
    period: str = typer.Option("daily", "--period", "-p", help="Period: daily, weekly, monthly"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show metrics summary for a time period."""
    collector = _get_metrics_collector()
    reporter = MetricsReporter(collector)

    summary = reporter.get_summary(period)

    if json_out:
        print_json(summary.to_dict())
    else:
        console.print(reporter.format_summary_report(summary))


@app.command("task")
def metrics_task(
    task_id: str = typer.Argument(..., help="Task ID"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show metrics for a specific task."""
    collector = _get_metrics_collector()
    reporter = MetricsReporter(collector)

    metrics = reporter.get_task_metrics(task_id)

    if json_out:
        print_json(metrics)
    else:
        console.print(f"[bold]Task Metrics: {task_id}[/bold]")
        console.print(f"Events: {metrics['events']} ({metrics['successful']} success, {metrics['failed']} failed)")
        console.print(f"Tokens: {metrics['tokens']['total']:,} ({metrics['tokens']['input']:,} in / {metrics['tokens']['output']:,} out)")
        console.print(f"Cost: ${metrics['cost_usd']:.4f}")
        console.print(f"Duration: {metrics['duration_ms'] / 1000:.1f}s")


@app.command("breakdown")
def metrics_breakdown(
    by: str = typer.Option("agent", "--by", "-b", help="Breakdown by: agent, task, model"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show cost breakdown by dimension."""
    collector = _get_metrics_collector()
    reporter = MetricsReporter(collector)

    breakdown = reporter.get_breakdown(by)

    if json_out:
        print_json(breakdown)
    else:
        total_cost = sum(v["cost_usd"] for v in breakdown.values())
        table = Table(title=f"Cost Breakdown by {by.title()}")
        table.add_column(by.title(), style="cyan")
        table.add_column("Events", justify="right")
        table.add_column("Tokens", justify="right")
        table.add_column("Cost", justify="right")
        table.add_column("%", justify="right")

        for key, stats in sorted(breakdown.items(), key=lambda x: x[1]["cost_usd"], reverse=True):
            pct = (stats["cost_usd"] / total_cost * 100) if total_cost > 0 else 0
            table.add_row(
                key,
                str(stats["events"]),
                f"{stats['tokens']['total']:,}",
                f"${stats['cost_usd']:.4f}",
                f"{pct:.1f}%",
            )

        console.print(table)


@app.command("budget")
def metrics_budget(
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show budget status."""
    collector = _get_metrics_collector()
    enforcer = BudgetEnforcer(collector)

    status = enforcer.check_budget()

    if json_out:
        print_json({
            "daily": {
                "spent": status.daily_spent,
                "limit": status.daily_limit,
                "remaining": status.daily_remaining,
                "percent": status.daily_percent,
            },
            "monthly": {
                "spent": status.monthly_spent,
                "limit": status.monthly_limit,
                "remaining": status.monthly_remaining,
                "percent": status.monthly_percent,
            },
            "alert": {
                "triggered": status.alert_triggered,
                "message": status.alert_message,
            },
        })
    else:
        console.print("[bold]Budget Status[/bold]")
        console.print("")
        console.print(f"Daily:   ${status.daily_spent:.2f} / ${status.daily_limit:.2f} ({status.daily_percent:.1f}%)")
        console.print(f"         Remaining: ${status.daily_remaining:.2f}")
        console.print("")
        console.print(f"Monthly: ${status.monthly_spent:.2f} / ${status.monthly_limit:.2f} ({status.monthly_percent:.1f}%)")
        console.print(f"         Remaining: ${status.monthly_remaining:.2f}")

        if status.alert_triggered:
            console.print("")
            console.print(f"[yellow]⚠ {status.alert_message}[/yellow]")


@app.command("export")
def metrics_export(
    output: str = typer.Option("metrics.csv", "--output", "-o", help="Output file path"),
    format_type: str = typer.Option("csv", "--format", "-f", help="Export format: csv"),
):
    """Export metrics to file."""
    collector = _get_metrics_collector()
    reporter = MetricsReporter(collector)

    if format_type.lower() == "csv":
        csv_content = reporter.export_csv()
        Path(output).write_text(csv_content, encoding="utf-8")
        console.print(f"[green]✓[/green] Exported metrics to {output}")
    else:
        console.print(f"[red]Unsupported format: {format_type}[/red]")
        raise typer.Exit(1)


@app.command("velocity")
def metrics_velocity(
    weeks: int = typer.Option(4, "--weeks", "-w", help="Number of weeks for rolling average"),
    sprints: int = typer.Option(3, "--sprints", "-s", help="Number of sprints for average"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show velocity metrics for project planning."""
    root = repo_root()
    tracker = _get_velocity_tracker()

    # Get current sprint from state.md if available
    try:
        from ..planning.state import StateManager
    except ImportError:
        from bpsai_pair.planning.state import StateManager

    state_manager = StateManager(root / ".paircoder")
    current_sprint = state_manager.state.active_sprint_id or ""

    stats = tracker.get_velocity_stats(
        current_sprint=current_sprint,
        weeks_for_average=weeks,
        sprints_for_average=sprints,
    )

    if json_out:
        print_json(stats.to_dict())
    else:
        console.print("[bold]Velocity Metrics[/bold]")
        console.print("")

        console.print(f"Points completed this week:     {stats.points_this_week}")
        if current_sprint:
            console.print(f"Points completed this sprint:   {stats.points_this_sprint} ({current_sprint})")
        else:
            console.print(f"Points completed this sprint:   {stats.points_this_sprint}")
        console.print("")

        console.print(f"Average weekly velocity ({weeks} weeks): {stats.avg_weekly_velocity:.1f}")
        console.print(f"Average sprint velocity ({sprints} sprints): {stats.avg_sprint_velocity:.1f}")
        console.print("")

        # Show weekly breakdown
        breakdown = tracker.get_weekly_breakdown(weeks=weeks)
        if breakdown and any(b["points"] > 0 for b in breakdown):
            console.print("[bold]Weekly Breakdown:[/bold]")
            table = Table()
            table.add_column("Week Start", style="cyan")
            table.add_column("Points", justify="right")

            for entry in breakdown:
                table.add_row(entry["week_start"], str(entry["points"]))

            console.print(table)
            console.print("")

        # Show sprint breakdown
        sprint_breakdown = tracker.get_sprint_breakdown()
        if sprint_breakdown:
            console.print("[bold]Sprint Breakdown:[/bold]")
            table = Table()
            table.add_column("Sprint", style="cyan")
            table.add_column("Points", justify="right")

            for sprint_id in sorted(sprint_breakdown.keys(), reverse=True):
                table.add_row(sprint_id, str(sprint_breakdown[sprint_id]))

            console.print(table)

        if stats.weeks_tracked == 0 and stats.sprints_tracked == 0:
            console.print("[dim]No velocity data recorded yet.[/dim]")
            console.print("[dim]Velocity is tracked when tasks are completed.[/dim]")


@app.command("burndown")
def metrics_burndown(
    sprint: str = typer.Option(None, "--sprint", "-s", help="Sprint ID (default: current sprint)"),
    start_date: str = typer.Option(None, "--start", help="Sprint start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(None, "--end", help="Sprint end date (YYYY-MM-DD)"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Generate burndown chart data for a sprint."""
    from datetime import datetime, timedelta

    try:
        from ..metrics import BurndownGenerator, SprintConfig
        from ..planning.state import StateManager
        from ..planning.parser import TaskParser
    except ImportError:
        from bpsai_pair.metrics import SprintConfig
        from bpsai_pair.planning.state import StateManager
        from bpsai_pair.planning.parser import TaskParser

    root = repo_root()
    generator = _get_burndown_generator()

    # Get sprint ID
    if not sprint:
        state_manager = StateManager(root / ".paircoder")
        sprint = state_manager.state.active_sprint_id or ""
        if not sprint:
            console.print("[yellow]No sprint specified and no active sprint found.[/yellow]")
            console.print("Use --sprint to specify a sprint ID.")
            raise typer.Exit(1)

    # Parse dates or use defaults
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            console.print(f"[red]Invalid date format: {start_date}. Use YYYY-MM-DD.[/red]")
            raise typer.Exit(1)
    else:
        # Default to 2 weeks ago
        start_dt = datetime.now() - timedelta(days=14)

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            console.print(f"[red]Invalid date format: {end_date}. Use YYYY-MM-DD.[/red]")
            raise typer.Exit(1)
    else:
        # Default to today
        end_dt = datetime.now()

    # Get total points from tasks
    task_parser = TaskParser(root / ".paircoder" / "tasks")
    tasks = task_parser.parse_all()
    sprint_tasks = [t for t in tasks if t.sprint == sprint]
    total_points = sum(t.complexity for t in sprint_tasks)

    if total_points == 0:
        console.print(f"[yellow]No tasks found for sprint '{sprint}'.[/yellow]")
        raise typer.Exit(1)

    # Create config and generate burndown
    config = SprintConfig(
        sprint_id=sprint,
        start_date=start_dt,
        end_date=end_dt,
        total_points=total_points,
    )

    data = generator.generate(config)

    if json_out:
        print_json(data.to_dict())
    else:
        console.print(f"[bold]Burndown Chart: {sprint}[/bold]")
        console.print("")
        console.print(f"Period: {config.start_date.strftime('%Y-%m-%d')} to {config.end_date.strftime('%Y-%m-%d')}")
        console.print(f"Total Points: {config.total_points}")
        console.print("")

        if data.data_points:
            table = Table()
            table.add_column("Date", style="cyan")
            table.add_column("Remaining", justify="right")
            table.add_column("Ideal", justify="right")
            table.add_column("Completed", justify="right")
            table.add_column("Status")

            for point in data.data_points:
                # Determine status indicator
                diff = point.remaining - point.ideal
                if diff < -5:
                    status = "[green]▲ Ahead[/green]"
                elif diff > 5:
                    status = "[red]▼ Behind[/red]"
                else:
                    status = "[yellow]● On Track[/yellow]"

                table.add_row(
                    point.date.strftime("%Y-%m-%d"),
                    str(point.remaining),
                    f"{point.ideal:.0f}",
                    str(point.completed),
                    status,
                )

            console.print(table)

            # Show summary
            last_point = data.data_points[-1]
            console.print("")
            console.print(f"Current Progress: {last_point.completed}/{config.total_points} points")
            pct = (last_point.completed / config.total_points * 100) if config.total_points > 0 else 0
            console.print(f"Completion: {pct:.0f}%")
        else:
            console.print("[dim]No data points generated. Check sprint dates.[/dim]")


@app.command("accuracy")
def metrics_accuracy(
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show estimation accuracy report.

    Analyzes how accurate task estimates have been compared to actual time spent.
    Shows overall accuracy, bias direction, and breakdowns by task type and complexity.
    """
    analyzer = _get_accuracy_analyzer()
    report = analyzer.generate_report()
    stats = report["stats"]

    if json_out:
        print_json(report)
    else:
        console.print("[bold]Estimation Accuracy Report[/bold]")
        console.print("=" * 26)
        console.print("")

        if stats["total_tasks"] == 0:
            console.print("[dim]No historical data available.[/dim]")
            console.print("[dim]Accuracy is tracked when tasks are completed with time tracking.[/dim]")
            return

        # Overall stats
        console.print(f"Overall Accuracy: {stats['overall_accuracy']:.0f}%")
        bias_str = f"Bias: {stats['bias_direction'].title()}"
        if stats["bias_direction"] != "neutral":
            bias_str += f" by {stats['bias_percent']:.0f}%"
        console.print(bias_str)
        console.print("")

        # By Task Type
        by_type = report["by_task_type"]
        if by_type:
            console.print("[bold]By Task Type:[/bold]")
            for t in by_type:
                bias_info = ""
                if t["bias_direction"] != "neutral":
                    direction = "under" if t["bias_direction"] == "optimistic" else "over"
                    bias_info = f" ({t['bias_percent']:.0f}% {direction}estimate)"
                console.print(f"- {t['task_type'].title()}: {t['accuracy_percent']:.0f}% accurate{bias_info}")
            console.print("")

        # By Complexity
        by_band = report["by_complexity_band"]
        if by_band:
            console.print("[bold]By Complexity:[/bold]")
            for b in by_band:
                console.print(f"- {b['band']} ({b['complexity_range']}): {b['accuracy_percent']:.0f}% accurate")
            console.print("")

        # Recommendation
        console.print(f"[bold]Recommendation:[/bold] {report['recommendation']}")


@app.command("tokens")
def metrics_tokens(
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show token estimation accuracy report.

    Analyzes how accurate token estimates have been compared to actual usage.
    Shows overall accuracy ratio, breakdowns by task type, and recommendations
    for adjusting estimation coefficients.
    """
    tracker = _get_token_tracker()
    report = tracker.generate_report()
    stats = report["stats"]

    if json_out:
        print_json(report)
    else:
        console.print("[bold]Token Estimation Accuracy Report[/bold]")
        console.print("=" * 34)
        console.print("")

        if stats["total_tasks"] == 0:
            console.print("[dim]No token usage data available.[/dim]")
            console.print("[dim]Token accuracy is tracked when tasks are completed with metrics recording.[/dim]")
            return

        # Overall stats
        accuracy_pct = int((1 / stats["avg_ratio"]) * 100) if stats["avg_ratio"] > 0 else 100
        console.print(f"Tasks Analyzed: {stats['total_tasks']}")
        console.print(f"Avg Ratio (actual/estimated): {stats['avg_ratio']:.2f}x")

        if stats["avg_ratio"] > 1.1:
            console.print(f"[yellow]Bias: Underestimating by ~{int((stats['avg_ratio'] - 1) * 100)}%[/yellow]")
        elif stats["avg_ratio"] < 0.9:
            console.print(f"[yellow]Bias: Overestimating by ~{int((1 - stats['avg_ratio']) * 100)}%[/yellow]")
        else:
            console.print("[green]Bias: Estimates are well-calibrated[/green]")
        console.print("")

        # By Task Type
        by_type = report["by_task_type"]
        if by_type:
            console.print("[bold]By Task Type:[/bold]")
            for task_type, type_stats in by_type.items():
                ratio = type_stats["avg_ratio"]
                ratio_str = f"{ratio:.2f}x"
                if ratio > 1.1:
                    ratio_str = f"[yellow]{ratio:.2f}x (underestimate)[/yellow]"
                elif ratio < 0.9:
                    ratio_str = f"[cyan]{ratio:.2f}x (overestimate)[/cyan]"
                console.print(f"- {task_type.title()}: {ratio_str} ({type_stats['count']} tasks)")
            console.print("")

        # Recommendations
        recommendations = report.get("recommendations", [])
        if recommendations:
            console.print("[bold]Recommendations:[/bold]")
            for rec in recommendations:
                console.print(f"- {rec}")
        else:
            console.print("[dim]No coefficient adjustments recommended yet.[/dim]")
