"""Plan estimation commands.

Extracted from plan_commands.py for better modularity.
"""

import json

import typer

from .parser import PlanParser, TaskParser
from .token_estimator import PlanTokenEstimator, DEFAULT_THRESHOLD
from .helpers import (
    console,
    find_paircoder_dir,
    get_state_manager,
    populate_files_touched,
)

plan_estimation_app = typer.Typer(
    help="Plan estimation utilities",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@plan_estimation_app.command("estimate")
def plan_estimate(
    plan_id: str = typer.Argument(..., help="Plan ID to estimate"),
    threshold: int = typer.Option(
        DEFAULT_THRESHOLD, "--threshold", "-t",
        help="Token threshold for warnings (default 50000)"
    ),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
    show_tasks: bool = typer.Option(True, "--show-tasks/--no-tasks", help="Show per-task breakdown"),
):
    """Estimate token usage for a plan and suggest batching if needed.

    Analyzes all tasks in a plan to estimate total token usage.
    Warns when the plan exceeds comfortable session limits and
    suggests how to split the work into manageable batches.

    Example:
        bpsai-pair plan estimate plan-2025-12-sprint-19-methodology
    """
    paircoder_dir = find_paircoder_dir()
    plan_parser = PlanParser(paircoder_dir / "plans")
    task_parser = TaskParser(paircoder_dir / "tasks")

    # Find the plan
    plan = plan_parser.get_plan_by_id(plan_id)
    if not plan:
        console.print(f"[red]Plan not found: {plan_id}[/red]")
        raise typer.Exit(1)

    # Get tasks for this plan
    tasks = task_parser.get_tasks_for_plan(plan_id)
    if not tasks:
        console.print(f"[yellow]No tasks found for plan: {plan_id}[/yellow]")
        raise typer.Exit(0)

    # Parse files_touched from task files
    for task in tasks:
        populate_files_touched(task, paircoder_dir / "tasks")

    # Create estimator and estimate
    config_path = paircoder_dir / "config.yaml"
    estimator = PlanTokenEstimator.from_config_file(config_path)
    estimate = estimator.estimate_plan(plan_id, tasks, threshold=threshold)

    if json_out:
        console.print(json.dumps(estimate.to_dict(), indent=2))
    else:
        output = estimator.format_estimate(estimate, show_tasks=show_tasks)
        console.print(output)


def planning_status() -> str:
    """Get planning status for the enhanced status command.

    Call this from the main status command to include planning info.
    """
    state_manager = get_state_manager()
    return state_manager.format_status_report()
