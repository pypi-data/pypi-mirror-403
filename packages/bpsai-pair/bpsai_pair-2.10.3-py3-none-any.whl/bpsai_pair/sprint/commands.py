"""Sprint CLI commands for PairCoder.

Provides commands for sprint lifecycle management including
listing sprints and completing sprints with checklists.

Extracted from planning/cli_commands.py as part of EPIC-003 Phase 2.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

# Import from planning module
from ..planning.models import TaskStatus
from ..planning.parser import PlanParser, TaskParser
from ..planning.state import StateManager

console = Console()

app = typer.Typer(
    help="Sprint lifecycle management commands",
    context_settings={"help_option_names": ["-h", "--help"]}
)


def find_paircoder_dir() -> Path:
    """Find .paircoder directory in current or parent directories."""
    from ..core.ops import find_paircoder_dir as _find_paircoder_dir
    return _find_paircoder_dir()


def get_state_manager() -> StateManager:
    """Get a StateManager instance for the current project."""
    return StateManager(find_paircoder_dir())


# Sprint completion checklist items
SPRINT_COMPLETION_CHECKLIST = [
    ("Cookie cutter template synced", "Have you synced changes to the cookie cutter template?"),
    ("CHANGELOG.md updated", "Have you updated CHANGELOG.md with new features/fixes?"),
    ("Documentation updated", "Have you updated relevant documentation?"),
    ("Tests passing", "Are all tests passing?"),
    ("Version bumped (if release)", "Have you bumped the version number if this is a release?"),
]


@app.command("complete")
def sprint_complete(
    sprint_id: str = typer.Argument(..., help="Sprint ID to complete (e.g., sprint-17)"),
    skip_checklist: bool = typer.Option(False, "--skip-checklist", help="Skip checklist confirmation (logged)"),
    reason: str = typer.Option("", "--reason", "-r", help="Reason for skipping checklist (required with --skip-checklist)"),
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Plan ID (uses active plan if not specified)"),
):
    """Complete a sprint with checklist verification.

    Ensures important tasks are not forgotten at sprint end:
    - Cookie cutter template sync
    - CHANGELOG.md updates
    - Documentation updates
    - Version bump (for releases)

    Examples:
        # Complete sprint with checklist
        bpsai-pair sprint complete sprint-17

        # Skip checklist (requires reason)
        bpsai-pair sprint complete sprint-17 --skip-checklist --reason "Hotfix deployment"
    """
    paircoder_dir = find_paircoder_dir()

    # Validate skip_checklist requires reason
    if skip_checklist:
        if not reason:
            console.print("[red]❌ --skip-checklist requires --reason[/red]")
            console.print("[dim]Example: --skip-checklist --reason 'Hotfix deployment'[/dim]")
            raise typer.Exit(1)

        from ..core.bypass_log import log_bypass
        log_bypass(
            command="sprint complete",
            target=sprint_id,
            reason=reason,
            bypass_type="skip_checklist",
        )

    # Get active plan if not specified
    if not plan_id:
        state_manager = get_state_manager()
        state = state_manager.load_state()
        if state and state.active_plan_id:
            plan_id = state.active_plan_id
        else:
            console.print("[red]No active plan. Specify --plan or set an active plan.[/red]")
            raise typer.Exit(1)

    # Load plan to verify sprint exists
    plan_parser = PlanParser(paircoder_dir / "plans")
    plan = plan_parser.get_plan_by_id(plan_id)

    if not plan:
        console.print(f"[red]Plan not found: {plan_id}[/red]")
        raise typer.Exit(1)

    # Check if sprint exists in plan
    sprint_found = False
    for sprint in plan.sprints:
        if sprint.id == sprint_id or sprint.id == f"{plan_id}-{sprint_id}":
            sprint_found = True
            break

    if not sprint_found:
        console.print(f"[yellow]Warning: Sprint '{sprint_id}' not found in plan. Continuing anyway.[/yellow]")

    # Get task stats for this sprint
    task_parser = TaskParser(paircoder_dir / "tasks")
    all_tasks = task_parser.list_tasks()
    sprint_tasks = [t for t in all_tasks if t.sprint == sprint_id]

    completed = len([t for t in sprint_tasks if t.status == TaskStatus.DONE])
    total = len(sprint_tasks)

    console.print(f"\n[bold]Completing Sprint: {sprint_id}[/bold]")
    console.print(f"Plan: {plan_id}")
    console.print(f"Tasks: {completed}/{total} completed\n")

    if total > 0 and completed < total:
        incomplete_tasks = [t for t in sprint_tasks if t.status != TaskStatus.DONE]
        console.print("[yellow]Warning: Some tasks are incomplete:[/yellow]")
        for task in incomplete_tasks[:5]:
            console.print(f"  - {task.id}: {task.title} ({task.status.value})")
        if len(incomplete_tasks) > 5:
            console.print(f"  ... and {len(incomplete_tasks) - 5} more")
        console.print()

    # Show and verify checklist
    if not skip_checklist:
        console.print("[bold]Pre-completion Checklist:[/bold]\n")

        all_confirmed = True
        responses = {}

        for item_id, question in SPRINT_COMPLETION_CHECKLIST:
            response = typer.confirm(f"  {question}", default=False)
            responses[item_id] = response
            if not response:
                all_confirmed = False

        console.print()

        # Show summary
        console.print("[bold]Checklist Summary:[/bold]")
        for item_id, question in SPRINT_COMPLETION_CHECKLIST:
            status = "[green]✓[/green]" if responses[item_id] else "[red]✗[/red]"
            console.print(f"  {status} {item_id}")

        console.print()

        if not all_confirmed:
            console.print("[yellow]Some items are not complete.[/yellow]")
            proceed = typer.confirm("Proceed anyway?", default=False)
            if not proceed:
                console.print("[dim]Sprint completion cancelled.[/dim]")
                console.print("\n[bold]To generate release tasks:[/bold]")
                console.print(f"  bpsai-pair release plan --sprint {sprint_id}")
                raise typer.Exit(0)

    # Mark sprint as complete
    console.print(f"\n[green]✓ Sprint {sprint_id} marked as complete[/green]")

    # Suggest next steps
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("  1. Archive completed tasks: [dim]bpsai-pair task archive[/dim]")
    console.print("  2. Generate changelog: [dim]bpsai-pair task changelog-preview[/dim]")
    console.print("  3. Create release: [dim]bpsai-pair release plan --sprint {sprint_id}[/dim]")


@app.command("list")
def sprint_list(
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Plan ID (uses active plan if not specified)"),
):
    """List sprints in a plan."""
    paircoder_dir = find_paircoder_dir()

    # Get active plan if not specified
    if not plan_id:
        state_manager = get_state_manager()
        state = state_manager.load_state()
        if state and state.active_plan_id:
            plan_id = state.active_plan_id
        else:
            console.print("[red]No active plan. Specify --plan or set an active plan.[/red]")
            raise typer.Exit(1)

    plan_parser = PlanParser(paircoder_dir / "plans")
    plan = plan_parser.get_plan_by_id(plan_id)

    if not plan:
        console.print(f"[red]Plan not found: {plan_id}[/red]")
        raise typer.Exit(1)

    if not plan.sprints:
        console.print("[dim]No sprints defined in this plan.[/dim]")
        return

    # Get task stats
    task_parser = TaskParser(paircoder_dir / "tasks")
    all_tasks = task_parser.list_tasks()

    table = Table(title=f"Sprints in {plan_id}")
    table.add_column("Sprint", style="cyan")
    table.add_column("Goal")
    table.add_column("Tasks", justify="right")
    table.add_column("Done", justify="right")
    table.add_column("Points", justify="right")

    for sprint in plan.sprints:
        sprint_tasks = [t for t in all_tasks if t.sprint == sprint.id]
        completed = len([t for t in sprint_tasks if t.status == TaskStatus.DONE])
        total = len(sprint_tasks)
        points = sum(t.complexity for t in sprint_tasks)

        status = f"{completed}/{total}"
        if total > 0 and completed == total:
            status = f"[green]{status}[/green]"

        table.add_row(
            sprint.id,
            sprint.goal[:40] + "..." if len(sprint.goal) > 40 else sprint.goal,
            str(total),
            status,
            str(points),
        )

    console.print(table)
