"""Orchestrate commands for multi-agent coordination.

Extracted from cli.py as part of EPIC-003 CLI Architecture Refactor.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

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
    from ..orchestration import Orchestrator, HandoffManager
    from ..orchestration import AgentSelector, SelectionCriteria, select_agent_for_task
except ImportError:
    from bpsai_pair.core import ops
    from bpsai_pair.orchestration import Orchestrator, HandoffManager
    from bpsai_pair.orchestration import AgentSelector, SelectionCriteria, select_agent_for_task


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


def _load_task_metadata(root: Path, task_id: str) -> tuple[str, list[str]]:
    """Load task title and tags from task file."""
    import yaml as yaml_mod

    task_file = root / ".paircoder" / "tasks" / f"{task_id}.task.md"
    if not task_file.exists():
        return "", []

    try:
        content = task_file.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml_mod.safe_load(parts[1])
                title = frontmatter.get("title", "")
                tags = frontmatter.get("tags", [])
                return title, tags if isinstance(tags, list) else []
    except Exception:
        pass

    return "", []


# Orchestration sub-app for multi-agent coordination
app = typer.Typer(
    help="Multi-agent orchestration commands",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@app.command("task")
def orchestrate_task(
    task_id: str = typer.Argument(..., help="Task ID to orchestrate"),
    prefer: Optional[str] = typer.Option(None, "--prefer", help="Preferred agent"),
    max_cost: Optional[float] = typer.Option(None, "--max-cost", help="Maximum cost in USD"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show decision without executing"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Orchestrate a task to the best agent."""
    root = repo_root()
    orchestrator = Orchestrator(project_root=root)

    constraints = {}
    if prefer:
        constraints["prefer"] = prefer
    if max_cost:
        constraints["max_cost"] = max_cost

    assignment = orchestrator.assign_task(task_id, constraints)

    if not dry_run:
        assignment = orchestrator.execute(assignment, dry_run=False)

    if json_out:
        print_json({
            "task_id": assignment.task_id,
            "agent": assignment.agent,
            "status": assignment.status,
            "score": assignment.score,
            "reasoning": assignment.reasoning,
        })
    else:
        console.print(f"[bold]Task:[/bold] {assignment.task_id}")
        console.print(f"[bold]Agent:[/bold] {assignment.agent}")
        console.print(f"[bold]Score:[/bold] {assignment.score:.2f}")
        console.print(f"[bold]Status:[/bold] {assignment.status}")
        if assignment.reasoning:
            console.print(f"[bold]Reasoning:[/bold] {assignment.reasoning}")


@app.command("analyze")
def orchestrate_analyze(
    task_id: str = typer.Argument(..., help="Task ID to analyze"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Analyze a task and show routing decision."""
    root = repo_root()
    orchestrator = Orchestrator(project_root=root)

    task = orchestrator.analyze_task(task_id)
    decision = orchestrator.select_agent(task)

    # Also get specialized agent recommendation
    task_title, task_tags = _load_task_metadata(root, task_id)
    specialized_match = select_agent_for_task(
        task_type=task.task_type.value,
        task_title=task_title or task.description[:100],
        task_tags=task_tags,
        complexity={"low": 25, "medium": 50, "high": 75}.get(task.complexity.value, 50),
        agents_dir=root / ".claude" / "agents",
        working_dir=root,
    )

    if json_out:
        print_json({
            "task_id": task.task_id,
            "type": task.task_type.value,
            "complexity": task.complexity.value,
            "recommended_agent": decision.agent,
            "score": decision.score,
            "reasoning": decision.reasoning,
            "specialized_agent": {
                "agent": specialized_match.agent_name,
                "score": specialized_match.score,
                "reasons": specialized_match.reasons,
                "permission_mode": specialized_match.permission_mode,
            },
        })
    else:
        console.print(f"[bold]Task:[/bold] {task.task_id}")
        console.print(f"[bold]Type:[/bold] {task.task_type.value}")
        console.print(f"[bold]Complexity:[/bold] {task.complexity.value}")
        console.print(f"[bold]Recommended Agent:[/bold] {decision.agent}")
        console.print(f"[bold]Score:[/bold] {decision.score:.2f}")
        if decision.reasoning:
            console.print("[bold]Reasoning:[/bold]")
            for reason in decision.reasoning:
                console.print(f"  • {reason}")

        # Show specialized agent recommendation
        if specialized_match.agent_name != "claude-code":
            console.print()
            console.print(f"[bold cyan]Specialized Agent:[/bold cyan] {specialized_match.agent_name}")
            console.print(f"[bold cyan]Score:[/bold cyan] {specialized_match.score:.2f}")
            console.print(f"[bold cyan]Mode:[/bold cyan] {specialized_match.permission_mode}")
            if specialized_match.reasons:
                console.print("[bold cyan]Reasons:[/bold cyan]")
                for reason in specialized_match.reasons:
                    console.print(f"  • {reason}")


@app.command("select-agent")
def orchestrate_select_agent(
    task_id: str = typer.Argument(..., help="Task ID to analyze"),
    prefer: Optional[str] = typer.Option(None, "--prefer", help="Preferred agent"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Select the best specialized agent for a task.

    Uses the AgentSelector to route tasks to specialized agents:
    - planner: For design/planning tasks
    - reviewer: For code review/PR tasks
    - security: For security/auth-related tasks
    - claude-code: Default for general tasks
    """
    root = repo_root()

    # Load task metadata
    task_title, task_tags = _load_task_metadata(root, task_id)

    # Get task characteristics for complexity
    orchestrator = Orchestrator(project_root=root)
    task = orchestrator.analyze_task(task_id)

    # Create selector and select agent
    selector = AgentSelector(
        agents_dir=root / ".claude" / "agents",
        working_dir=root,
    )

    criteria = SelectionCriteria(
        task_type=task.task_type.value,
        task_title=task_title or task.description[:100],
        task_tags=task_tags,
        complexity={"low": 25, "medium": 50, "high": 75}.get(task.complexity.value, 50),
        preferred_agent=prefer,
    )

    match = selector.select(criteria)
    all_matches = selector.get_all_matches(criteria)

    if json_out:
        print_json({
            "task_id": task_id,
            "selected_agent": match.agent_name,
            "score": match.score,
            "reasons": match.reasons,
            "permission_mode": match.permission_mode,
            "all_matches": [m.to_dict() for m in all_matches],
        })
    else:
        console.print(f"[bold]Task:[/bold] {task_id}")
        if task_title:
            console.print(f"[bold]Title:[/bold] {task_title}")
        if task_tags:
            console.print(f"[bold]Tags:[/bold] {', '.join(task_tags)}")
        console.print()
        console.print(f"[bold green]Selected Agent:[/bold green] {match.agent_name}")
        console.print(f"[bold]Score:[/bold] {match.score:.2f}")
        console.print(f"[bold]Permission Mode:[/bold] {match.permission_mode}")
        if match.reasons:
            console.print("[bold]Reasons:[/bold]")
            for reason in match.reasons:
                console.print(f"  • {reason}")

        # Show other candidates if available
        if len(all_matches) > 1:
            console.print()
            console.print("[bold]Other Candidates:[/bold]")
            for m in all_matches[1:4]:  # Show top 3 alternatives
                console.print(f"  • {m.agent_name}: {m.score:.2f}")


@app.command("handoff")
def orchestrate_handoff(
    task_id: str = typer.Argument(..., help="Task ID for handoff"),
    target: str = typer.Option("codex", "--to", help="Target agent"),
    summary: str = typer.Option("", "--summary", help="Conversation summary"),
    output: Optional[str] = typer.Option(None, "--out", help="Output file path"),
):
    """Create a handoff package for another agent."""
    root = repo_root()
    manager = HandoffManager(project_root=root)

    output_path = Path(output) if output else None
    package_path = manager.pack(
        task_id=task_id,
        target_agent=target,
        conversation_summary=summary,
        output_path=output_path,
    )

    console.print(f"[green]✓[/green] Created handoff package: {package_path}")


@app.command("auto-run")
def orchestrate_auto_run(
    task_id: Optional[str] = typer.Argument(None, help="Task ID (auto-selects if not provided)"),
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Plan ID for task selection"),
    create_pr: bool = typer.Option(True, "--pr/--no-pr", help="Create PR on completion"),
    run_tests: bool = typer.Option(True, "--test/--no-test", help="Run tests before PR"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Run autonomous workflow for a single task."""
    # Import here to avoid circular imports
    try:
        from ..orchestration.autonomous import AutonomousWorkflow, WorkflowConfig
    except ImportError:
        from bpsai_pair.orchestration.autonomous import AutonomousWorkflow, WorkflowConfig

    root = repo_root()
    paircoder_dir = root / ".paircoder"

    config = WorkflowConfig(
        auto_select_tasks=task_id is None,
        auto_create_pr=create_pr,
        run_tests_before_pr=run_tests,
    )

    workflow = AutonomousWorkflow(paircoder_dir, config)

    success = workflow.run_task_workflow(task_id=task_id, plan_id=plan_id)

    if json_out:
        print_json(workflow.get_status())
    else:
        status = workflow.get_status()
        if success:
            console.print("[green]Workflow completed successfully[/green]")
        else:
            console.print("[red]Workflow failed or no tasks available[/red]")

        console.print(f"  Phase: {status['workflow_state']['phase']}")
        console.print(f"  Events: {status['workflow_state']['events_count']}")
        if status['workflow_state']['error']:
            console.print(f"  Error: {status['workflow_state']['error']}")


@app.command("auto-session")
def orchestrate_auto_session(
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Plan ID for task selection"),
    max_tasks: int = typer.Option(5, "--max", "-m", help="Maximum tasks to process"),
    create_pr: bool = typer.Option(True, "--pr/--no-pr", help="Create PRs"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Run autonomous session processing multiple tasks."""
    # Import here to avoid circular imports
    try:
        from ..orchestration.autonomous import AutonomousWorkflow, WorkflowConfig
    except ImportError:
        from bpsai_pair.orchestration.autonomous import AutonomousWorkflow, WorkflowConfig

    root = repo_root()
    paircoder_dir = root / ".paircoder"

    config = WorkflowConfig(
        auto_select_tasks=True,
        auto_create_pr=create_pr,
        max_tasks_per_session=max_tasks,
    )

    workflow = AutonomousWorkflow(paircoder_dir, config)
    completed = workflow.run_session(plan_id=plan_id, max_tasks=max_tasks)

    if json_out:
        print_json({"completed_tasks": completed, "count": len(completed)})
    else:
        console.print(f"[green]Session completed: {len(completed)} tasks done[/green]")
        for task_id in completed:
            console.print(f"  - {task_id}")


@app.command("workflow-status")
def orchestrate_workflow_status(
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show current autonomous workflow status."""
    # Import here to avoid circular imports
    try:
        from ..orchestration.autonomous import AutonomousWorkflow
    except ImportError:
        from bpsai_pair.orchestration.autonomous import AutonomousWorkflow

    root = repo_root()
    paircoder_dir = root / ".paircoder"

    workflow = AutonomousWorkflow(paircoder_dir)
    status = workflow.get_status()

    if json_out:
        print_json(status)
    else:
        console.print("[bold]Workflow Status[/bold]")
        console.print(f"  Phase: {status['workflow_state']['phase']}")
        console.print(f"  Current Task: {status['workflow_state']['current_task_id'] or 'None'}")
        console.print(f"  Current Flow: {status['workflow_state']['current_flow'] or 'None'}")
        console.print(f"  PR Number: {status['workflow_state']['pr_number'] or 'None'}")

        console.print("\n[bold]Configuration[/bold]")
        for key, value in status['config'].items():
            console.print(f"  {key}: {value}")
