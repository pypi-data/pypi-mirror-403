"""Plan CLI commands.

Commands for creating and managing plans (goals, tasks, sprints).
"""

from datetime import datetime
from typing import Optional, List
import json

import typer
from rich.table import Table

from .models import Plan, Task, TaskStatus, PlanStatus, PlanType
from .parser import PlanParser, TaskParser
from .helpers import (
    console,
    find_paircoder_dir,
    get_state_manager,
)
from .plan_trello_sync import plan_sync_trello
from .plan_estimation import plan_estimate, planning_status

plan_app = typer.Typer(
    help="Manage plans (goals, tasks, sprints)",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@plan_app.command("new")
def plan_new(
    slug: str = typer.Argument(..., help="Short identifier (e.g., 'workspace-filter')"),
    plan_type: str = typer.Option(
        "feature", "--type", "-t",
        help="Type: feature|bugfix|refactor|chore"
    ),
    title: Optional[str] = typer.Option(None, "--title", "-T", help="Plan title"),
    skill: str = typer.Option(
        "planning-with-trello",
        "--skill", "-s",
        help="Associated skill for this plan"
    ),
    flow: Optional[str] = typer.Option(
        None,
        "--flow", "-f",
        help="[DEPRECATED] Use --skill instead",
        hidden=True
    ),
    goal: Optional[List[str]] = typer.Option(None, "--goal", "-g", help="Plan goals (repeatable)"),
):
    """Create a new plan."""
    paircoder_dir = find_paircoder_dir()
    plan_parser = PlanParser(paircoder_dir / "plans")

    # Generate plan ID
    date_str = datetime.now().strftime("%Y-%m")
    plan_id = f"plan-{date_str}-{slug}"

    # Check if plan already exists
    existing = plan_parser.get_plan_by_id(plan_id)
    if existing:
        console.print(f"[red]Plan already exists: {plan_id}[/red]")
        raise typer.Exit(1)

    # Validate plan type
    try:
        ptype = PlanType(plan_type)
    except ValueError:
        console.print(f"[red]Invalid plan type: {plan_type}[/red]")
        console.print("Valid types: feature, bugfix, refactor, chore")
        raise typer.Exit(1)

    # Handle deprecated --flow option
    actual_skill = skill
    if flow:
        console.print("[yellow]⚠ Warning: --flow is deprecated, use --skill instead[/yellow]")
        actual_skill = flow

    # Create plan with skills
    plan = Plan(
        id=plan_id,
        title=title or slug.replace("-", " ").title(),
        type=ptype,
        status=PlanStatus.PLANNED,
        created_at=datetime.now(),
        skills=[actual_skill],
        goals=list(goal) if goal else [],
    )

    # Save plan
    plan_path = plan_parser.save(plan)

    console.print(f"[green]Created plan:[/green] {plan_id}")
    console.print(f"  Path: {plan_path}")
    console.print(f"  Type: {plan_type}")
    console.print(f"  Skill: {actual_skill}")

    if goal:
        console.print("  Goals:")
        for g in goal:
            console.print(f"    - {g}")

    console.print("")
    console.print("[dim]Next steps:[/dim]")
    console.print(f"  1. Add tasks: bpsai-pair plan add-task {plan_id}")
    console.print(f"  2. Read skill: .claude/skills/{actual_skill}/SKILL.md")


@plan_app.command("list")
def plan_list(
    status: Optional[str] = typer.Option(
        None, "--status", "-s",
        help="Filter: planned|in_progress|complete|archived"
    ),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all plans."""
    paircoder_dir = find_paircoder_dir()
    plan_parser = PlanParser(paircoder_dir / "plans")
    task_parser = TaskParser(paircoder_dir / "tasks")

    plans = plan_parser.parse_all()

    # Filter by status if specified
    if status:
        plans = [p for p in plans if p.status.value == status]

    if json_out:
        data = [p.to_dict() for p in plans]
        console.print(json.dumps(data, indent=2, default=str))
        return

    if not plans:
        console.print("[dim]No plans found.[/dim]")
        return

    table = Table(title=f"Plans ({len(plans)})")
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Tasks", justify="right")

    for plan in plans:
        # Count actual task files with matching plan_id
        task_count = len(task_parser.get_tasks_for_plan(plan.id))
        table.add_row(
            plan.id,
            plan.title,
            plan.type.value,
            f"{plan.status_emoji} {plan.status.value}",
            str(task_count),
        )

    console.print(table)


@plan_app.command("show")
def plan_show(
    plan_id: str = typer.Argument(..., help="Plan ID"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show details of a specific plan."""
    paircoder_dir = find_paircoder_dir()
    plan_parser = PlanParser(paircoder_dir / "plans")
    task_parser = TaskParser(paircoder_dir / "tasks")

    plan = plan_parser.get_plan_by_id(plan_id)

    if not plan:
        console.print(f"[red]Plan not found: {plan_id}[/red]")
        raise typer.Exit(1)

    if json_out:
        console.print(json.dumps(plan.to_dict(), indent=2, default=str))
        return

    console.print(f"[bold]{plan.status_emoji} {plan.id}[/bold]")
    console.print(f"{'=' * 60}")
    console.print(f"[cyan]Title:[/cyan] {plan.title}")
    console.print(f"[cyan]Type:[/cyan] {plan.type.value}")
    console.print(f"[cyan]Status:[/cyan] {plan.status.value}")

    if plan.owner:
        console.print(f"[cyan]Owner:[/cyan] {plan.owner}")
    if plan.created_at:
        console.print(f"[cyan]Created:[/cyan] {plan.created_at.strftime('%Y-%m-%d')}")

    if plan.skills:
        console.print(f"\n[cyan]Skills:[/cyan] {', '.join(plan.skills)}")
    elif plan.flows:
        console.print(f"\n[cyan]Flows:[/cyan] {', '.join(plan.flows)} [dim](deprecated)[/dim]")

    if plan.goals:
        console.print("\n[cyan]Goals:[/cyan]")
        for goal in plan.goals:
            console.print(f"  - {goal}")

    if plan.sprints:
        console.print("\n[cyan]Sprints:[/cyan]")
        for sprint in plan.sprints:
            console.print(f"  [{sprint.id}] {sprint.title}")
            if sprint.goal:
                console.print(f"       Goal: {sprint.goal}")
            console.print(f"       Tasks: {len(sprint.task_ids)}")

    # Load actual task files for status
    tasks = task_parser.parse_all(plan.slug)
    if tasks:
        console.print("\n[cyan]Tasks:[/cyan]")
        for task in tasks:
            console.print(f"  {task.status_emoji} {task.id}: {task.title}")
            console.print(f"       Priority: {task.priority} | Complexity: {task.complexity}")


@plan_app.command("tasks")
def plan_tasks(
    plan_id: str = typer.Argument(..., help="Plan ID"),
    status: Optional[str] = typer.Option(
        None, "--status", "-s",
        help="Filter: pending|in_progress|review|done|blocked"
    ),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List tasks for a specific plan."""
    paircoder_dir = find_paircoder_dir()
    plan_parser = PlanParser(paircoder_dir / "plans")
    task_parser = TaskParser(paircoder_dir / "tasks")

    plan = plan_parser.get_plan_by_id(plan_id)
    if not plan:
        console.print(f"[red]Plan not found: {plan_id}[/red]")
        raise typer.Exit(1)

    tasks = task_parser.parse_all(plan.slug)

    if status:
        tasks = [t for t in tasks if t.status.value == status]

    if json_out:
        data = [t.to_dict() for t in tasks]
        console.print(json.dumps(data, indent=2, default=str))
        return

    if not tasks:
        console.print(f"[dim]No tasks found for plan: {plan_id}[/dim]")
        return

    table = Table(title=f"Tasks for {plan_id}")
    table.add_column("Status", width=3)
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Priority")
    table.add_column("Complexity", justify="right")
    table.add_column("Sprint")

    for task in tasks:
        table.add_row(
            task.status_emoji,
            task.id,
            task.title,
            task.priority,
            str(task.complexity),
            task.sprint or "-",
        )

    console.print(table)


@plan_app.command("status")
def plan_status_cmd(
    plan_id: str = typer.Argument("current", help="Plan ID or 'current' for active plan"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show individual task list"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show plan status with sprint/task breakdown."""
    paircoder_dir = find_paircoder_dir()
    state_manager = get_state_manager()
    plan_parser = PlanParser(paircoder_dir / "plans")
    task_parser = TaskParser(paircoder_dir / "tasks")

    # If "current", get from state
    if plan_id == "current":
        plan_id = state_manager.get_active_plan_id()
        if not plan_id:
            console.print("[yellow]No active plan. Specify a plan ID.[/yellow]")
            console.print("[dim]List plans: bpsai-pair plan list[/dim]")
            raise typer.Exit(1)

    # Load plan
    plan = plan_parser.get_plan_by_id(plan_id)
    if not plan:
        console.print(f"[red]Plan not found: {plan_id}[/red]")
        raise typer.Exit(1)

    # Load tasks for this plan (filter by plan_id in frontmatter)
    tasks = task_parser.get_tasks_for_plan(plan.id)

    # Calculate task counts
    task_counts = {"pending": 0, "in_progress": 0, "done": 0, "blocked": 0, "cancelled": 0}
    for task in tasks:
        status_key = task.status.value
        if status_key in task_counts:
            task_counts[status_key] += 1

    total_tasks = len(tasks)
    done_count = task_counts["done"]
    progress_pct = int((done_count / total_tasks) * 100) if total_tasks > 0 else 0

    # Group tasks by sprint
    sprints_tasks = {}
    no_sprint = []
    for task in tasks:
        if task.sprint:
            if task.sprint not in sprints_tasks:
                sprints_tasks[task.sprint] = []
            sprints_tasks[task.sprint].append(task)
        else:
            no_sprint.append(task)

    # Find blockers with reasons
    blockers = []
    for task in tasks:
        if task.status == TaskStatus.BLOCKED:
            if task.depends_on:
                reason = f"depends on {', '.join(task.depends_on)}"
            else:
                reason = "blocked"
            blockers.append((task.id, task.title, reason))

    # JSON output
    if json_out:
        data = {
            "plan_id": plan.id,
            "title": plan.title,
            "status": plan.status.value,
            "type": plan.type.value,
            "goals": plan.goals,
            "progress_percent": progress_pct,
            "task_counts": task_counts,
            "total_tasks": total_tasks,
            "sprints": {
                sprint_id: {
                    "tasks": len(tasks_list),
                    "done": sum(1 for t in tasks_list if t.status == TaskStatus.DONE),
                }
                for sprint_id, tasks_list in sprints_tasks.items()
            },
            "blockers": [{"id": b[0], "title": b[1], "reason": b[2]} for b in blockers],
        }
        console.print(json.dumps(data, indent=2))
        return

    # Rich output
    console.print(f"\n[bold]Plan:[/bold] {plan.id}")
    console.print(f"[bold]Title:[/bold] {plan.title}")
    console.print(f"[bold]Status:[/bold] {plan.status_emoji} {plan.status.value}")
    console.print(f"[bold]Type:[/bold] {plan.type.value}")

    # Goals
    if plan.goals:
        console.print("\n[bold]Goals:[/bold]")
        for goal in plan.goals:
            check = "✓" if "complete" in goal.lower() or "done" in goal.lower() else "○"
            console.print(f"  {check} {goal}")

    # Sprint progress
    if sprints_tasks:
        console.print("\n[bold]Sprint Progress:[/bold]")
        for sprint_id in sorted(sprints_tasks.keys()):
            sprint_tasks = sprints_tasks[sprint_id]
            sprint_total = len(sprint_tasks)
            sprint_done = sum(1 for t in sprint_tasks if t.status == TaskStatus.DONE)
            sprint_pct = int((sprint_done / sprint_total) * 100) if sprint_total > 0 else 0

            # Progress bar (16 chars)
            filled = int(sprint_pct / 6.25)  # 16 blocks = 100%
            bar = "█" * filled + "░" * (16 - filled)
            console.print(f"  {sprint_id} [{bar}] {sprint_pct:3d}%  ({sprint_done}/{sprint_total} tasks)")

    # Overall task status
    console.print("\n[bold]Task Status:[/bold]")
    console.print(f"  ✓ Done:        {task_counts['done']}")
    console.print(f"  ● In Progress: {task_counts['in_progress']}")
    console.print(f"  ○ Pending:     {task_counts['pending']}")
    console.print(f"  ⊘ Blocked:     {task_counts['blocked']}")
    if task_counts['cancelled'] > 0:
        console.print(f"  ✗ Cancelled:   {task_counts['cancelled']}")

    # Overall progress
    filled = int(progress_pct / 6.25)
    bar = "█" * filled + "░" * (16 - filled)
    console.print(f"\n[bold]Overall:[/bold] [{bar}] {progress_pct}% ({done_count}/{total_tasks} tasks)")

    # Blockers
    if blockers:
        console.print("\n[bold]Blockers:[/bold]")
        for task_id, title, reason in blockers:
            console.print(f"  [red]⊘[/red] {task_id}: {title}")
            console.print(f"    [dim]→ {reason}[/dim]")

    # Verbose: show all tasks
    if verbose:
        console.print("\n[bold]All Tasks:[/bold]")
        table = Table(show_header=True)
        table.add_column("Status", width=3)
        table.add_column("ID", style="cyan")
        table.add_column("Title")
        table.add_column("Sprint")
        table.add_column("Priority")

        for task in sorted(tasks, key=lambda t: (t.sprint or "", t.priority, t.id)):
            table.add_row(
                task.status_emoji,
                task.id,
                task.title[:40] + "..." if len(task.title) > 40 else task.title,
                task.sprint or "-",
                task.priority,
            )

        console.print(table)

    console.print("")


# Register the sync-trello command from extracted module
plan_app.command("sync-trello")(plan_sync_trello)


# Register the estimate command from extracted module
plan_app.command("estimate")(plan_estimate)


@plan_app.command("add-task")
def plan_add_task(
    plan_id: str = typer.Argument(..., help="Plan ID"),
    task_id: str = typer.Option(..., "--id", help="Task ID (e.g., TASK-007)"),
    title: str = typer.Option(..., "--title", "-t", help="Task title"),
    task_type: str = typer.Option("feature", "--type", help="Task type"),
    priority: str = typer.Option("P1", "--priority", "-p", help="Priority (P0, P1, P2)"),
    complexity: int = typer.Option(50, "--complexity", "-c", help="Complexity (0-100)"),
    sprint: Optional[str] = typer.Option(None, "--sprint", "-s", help="Sprint ID"),
):
    """Add a task to a plan."""
    paircoder_dir = find_paircoder_dir()
    plan_parser = PlanParser(paircoder_dir / "plans")
    task_parser = TaskParser(paircoder_dir / "tasks")

    plan = plan_parser.get_plan_by_id(plan_id)
    if not plan:
        console.print(f"[red]Plan not found: {plan_id}[/red]")
        raise typer.Exit(1)

    # Create task
    task = Task(
        id=task_id,
        title=title,
        plan_id=plan.id,
        type=task_type,
        priority=priority,
        complexity=complexity,
        status=TaskStatus.PENDING,
        sprint=sprint,
    )

    # Save task
    task_path = task_parser.save(task)

    console.print(f"[green]Created task:[/green] {task_id}")
    console.print(f"  Path: {task_path}")
    console.print(f"  Plan: {plan_id}")
