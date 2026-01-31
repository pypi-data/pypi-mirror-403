"""
GitHub CLI commands for PairCoder.

Provides commands for GitHub integration including PR management,
status checking, and task-linked workflows.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..licensing import require_feature
from .client import GitHubService
from .pr import PRManager, PRWorkflow

console = Console()
app = typer.Typer(
    help="GitHub integration commands",
    context_settings={"help_option_names": ["-h", "--help"]}
)


def _find_paircoder_dir() -> Path:
    """Find .paircoder directory."""
    from ..core.ops import find_paircoder_dir
    return find_paircoder_dir()


def _get_github_service() -> GitHubService:
    """Get GitHub service instance."""
    return GitHubService()


def _get_pr_manager() -> PRManager:
    """Get PR manager instance."""
    paircoder_dir = _find_paircoder_dir()
    return PRManager(paircoder_dir=paircoder_dir)


@app.command("status")
@require_feature("github")
def status(
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Check GitHub connection status."""
    service = _get_github_service()
    health = service.healthcheck()

    if json_out:
        sys.stdout.write(json.dumps(health, indent=2))
        sys.stdout.write("\n")
        return

    if health["ok"]:
        console.print("[green]GitHub integration is working[/green]")
    else:
        console.print("[yellow]GitHub integration has issues[/yellow]")

    console.print(f"  gh CLI available: {'[green]Yes[/green]' if health['gh_cli'] else '[red]No[/red]'}")
    console.print(f"  Repository: {health['repo'] or '[dim]Not a GitHub repo[/dim]'}")
    console.print(f"  Authenticated: {'[green]Yes[/green]' if health['authenticated'] else '[red]No[/red]'}")

    if not health["gh_cli"]:
        console.print("\n[dim]Install gh CLI: https://cli.github.com/[/dim]")
        console.print("[dim]Then run: gh auth login[/dim]")


@app.command("pr")
@require_feature("github")
def pr_status(
    pr_number: Optional[int] = typer.Argument(None, help="PR number (uses current branch if not provided)"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show PR status for current branch or specific PR."""
    manager = _get_pr_manager()

    if pr_number:
        pr_info = manager.service.client.get_pr_status(pr_number)
    else:
        pr_info = manager.get_pr_for_branch()
        pr_info = manager.service.client.get_pr_status() if not pr_info else None

    if not pr_info:
        console.print("[yellow]No PR found for current branch[/yellow]")
        console.print("[dim]Create one with: bpsai-pair github create --task TASK-XXX[/dim]")
        return

    if json_out:
        sys.stdout.write(json.dumps(pr_info, indent=2))
        sys.stdout.write("\n")
        return

    from .pr import PRInfo
    if isinstance(pr_info, dict):
        pr = PRInfo.from_gh_json(pr_info)
    else:
        pr = pr_info

    console.print(f"[bold]PR #{pr.number}[/bold]: {pr.title}")
    console.print(f"  URL: {pr.url}")
    console.print(f"  State: {pr.state}")
    if pr.task_id:
        console.print(f"  Task: {pr.task_id}")
    if pr.mergeable is not None:
        mergeable_str = "[green]Yes[/green]" if pr.mergeable else "[red]No[/red]"
        console.print(f"  Mergeable: {mergeable_str}")
    if pr.review_decision:
        review_color = "green" if pr.review_decision == "APPROVED" else "yellow"
        console.print(f"  Review: [{review_color}]{pr.review_decision}[/{review_color}]")


@app.command("create")
@require_feature("github")
def create_pr(
    task_id: str = typer.Option(..., "--task", "-t", help="Task ID to link to PR"),
    summary: str = typer.Option("", "--summary", "-s", help="Brief summary of changes"),
    draft: bool = typer.Option(False, "--draft", "-d", help="Create as draft PR"),
    base: Optional[str] = typer.Option(None, "--base", "-b", help="Base branch"),
):
    """Create a PR for a task."""
    manager = _get_pr_manager()

    if not manager.service.is_github_repo():
        console.print("[red]Not a GitHub repository[/red]")
        raise typer.Exit(1)

    # Check if already on default branch
    current = manager.service.get_current_branch()
    default = manager.service.client.get_default_branch()
    if current == default:
        console.print(f"[red]Cannot create PR from {default} branch[/red]")
        console.print("[dim]Create a feature branch first[/dim]")
        raise typer.Exit(1)

    # Check for existing PR
    existing = manager.get_pr_for_branch(current)
    if existing:
        console.print(f"[yellow]PR already exists: #{existing.number}[/yellow]")
        console.print(f"  URL: {existing.url}")
        return

    # Get summary if not provided
    if not summary:
        summary = typer.prompt("Brief summary of changes")

    # Create PR
    console.print(f"Creating PR for {task_id}...")
    pr = manager.create_pr_for_task(
        task_id=task_id,
        summary=summary,
        draft=draft,
        base=base,
    )

    if pr:
        console.print(f"[green]Created PR #{pr.number}[/green]")
        console.print(f"  URL: {pr.url}")
        console.print(f"  Task: {task_id}")
    else:
        console.print("[red]Failed to create PR[/red]")
        console.print("[dim]Check gh auth status[/dim]")
        raise typer.Exit(1)


@app.command("list")
@require_feature("github")
def list_prs(
    state: str = typer.Option("open", "--state", "-s", help="PR state: open, closed, merged, all"),
    task_only: bool = typer.Option(False, "--task-only", help="Only show task-linked PRs"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List pull requests."""
    manager = _get_pr_manager()

    if task_only:
        prs = manager.list_task_prs(state=state)
        pr_data = [{"number": p.number, "title": p.title, "state": p.state, "task_id": p.task_id, "url": p.url} for p in prs]
    else:
        pr_data = manager.service.client.list_prs(state=state)

    if json_out:
        sys.stdout.write(json.dumps(pr_data, indent=2))
        sys.stdout.write("\n")
        return

    if not pr_data:
        console.print(f"[dim]No {state} PRs found[/dim]")
        return

    table = Table(title=f"Pull Requests ({state})")
    table.add_column("#", style="cyan", width=6)
    table.add_column("Title")
    table.add_column("State", width=10)
    if task_only:
        table.add_column("Task", style="green", width=12)

    for pr in pr_data:
        row = [
            str(pr.get("number", pr.number if hasattr(pr, 'number') else "")),
            pr.get("title", pr.title if hasattr(pr, 'title') else ""),
            pr.get("state", pr.state if hasattr(pr, 'state') else ""),
        ]
        if task_only:
            row.append(pr.get("task_id", pr.task_id if hasattr(pr, 'task_id') else ""))
        table.add_row(*row)

    console.print(table)


@app.command("merge")
@require_feature("github")
def merge_pr(
    pr_number: int = typer.Argument(..., help="PR number to merge"),
    method: str = typer.Option("squash", "--method", "-m", help="Merge method: merge, squash, rebase"),
    no_delete: bool = typer.Option(False, "--no-delete", help="Don't delete branch after merge"),
    auto_next: bool = typer.Option(True, "--auto-next/--no-auto-next", help="Auto-assign next task after merge"),
):
    """Merge a PR and optionally assign next task."""
    manager = _get_pr_manager()
    workflow = PRWorkflow(manager, auto_assign_next=auto_next)

    # Check PR status first
    status = manager.service.client.get_pr_status(pr_number)
    if not status:
        console.print(f"[red]PR #{pr_number} not found[/red]")
        raise typer.Exit(1)

    from .pr import PRInfo
    pr = PRInfo.from_gh_json(status)

    if pr.state != "open":
        console.print(f"[yellow]PR #{pr_number} is not open (state: {pr.state})[/yellow]")
        raise typer.Exit(1)

    # Merge
    console.print(f"Merging PR #{pr_number}...")
    success = manager.service.client.merge_pr(
        pr_number=pr_number,
        method=method,
        delete_branch=not no_delete,
    )

    if success:
        console.print(f"[green]Merged PR #{pr_number}[/green]")

        # Handle task update and next assignment
        if pr.task_id:
            next_task = workflow.on_pr_merge(pr_number)
            if next_task:
                console.print(f"[green]Next task assigned: {next_task}[/green]")
    else:
        console.print("[red]Failed to merge PR[/red]")
        console.print("[dim]Check PR status and review requirements[/dim]")
        raise typer.Exit(1)


@app.command("link")
@require_feature("github")
def link_task(
    task_id: str = typer.Argument(..., help="Task ID to link"),
    pr_number: Optional[int] = typer.Option(None, "--pr", "-p", help="PR number (uses current branch PR if not provided)"),
):
    """Link a task to a PR (update PR title)."""
    manager = _get_pr_manager()

    # Get PR
    if pr_number:
        status = manager.service.client.get_pr_status(pr_number)
    else:
        status = manager.service.client.get_pr_status()

    if not status:
        console.print("[red]No PR found[/red]")
        raise typer.Exit(1)

    from .pr import PRInfo
    pr = PRInfo.from_gh_json(status)

    # Check if already linked
    if pr.task_id == task_id:
        console.print(f"[green]PR #{pr.number} is already linked to {task_id}[/green]")
        return

    console.print(f"[green]PR #{pr.number} can be linked to {task_id}[/green]")
    console.print("[dim]Update PR title to include [TASK-XXX] prefix[/dim]")
    console.print(f"[dim]Example: [{task_id}] {pr.title}[/dim]")


@app.command("auto-pr")
@require_feature("github")
def auto_pr(
    draft: bool = typer.Option(True, "--draft/--no-draft", help="Create as draft PR"),
):
    """Auto-create PR for current branch if it has a task ID.

    This command detects the task ID from the branch name and creates a draft PR.
    Branch naming patterns supported:
    - feature/TASK-001-description
    - TASK-001/description
    - TASK-001-description

    Example:
        git checkout -b feature/TASK-001-add-authentication
        git push -u origin HEAD
        bpsai-pair github auto-pr
    """
    from .pr import auto_create_pr_for_branch

    paircoder_dir = _find_paircoder_dir()
    project_root = paircoder_dir.parent

    pr = auto_create_pr_for_branch(
        project_root=project_root,
        paircoder_dir=paircoder_dir,
        draft=draft,
    )

    if pr:
        if hasattr(pr, 'number'):
            console.print(f"[green]Created draft PR #{pr.number}[/green]")
            console.print(f"  URL: {pr.url}")
            if pr.task_id:
                console.print(f"  Task: {pr.task_id}")
        else:
            console.print("[green]PR already exists[/green]")
    else:
        console.print("[yellow]Could not create PR[/yellow]")
        console.print("[dim]Ensure branch name contains TASK-XXX[/dim]")
        console.print("[dim]Example: feature/TASK-001-description[/dim]")


@app.command("archive-merged")
@require_feature("github")
def archive_merged(
    pr_number: Optional[int] = typer.Argument(None, help="Specific PR number to check"),
    check_all: bool = typer.Option(False, "--all", "-a", help="Check all recent merged PRs"),
    limit: int = typer.Option(10, "--limit", "-l", help="Max PRs to check when using --all"),
):
    """Archive tasks whose PRs have been merged.

    Can archive a specific task by PR number, or scan recent merged PRs.

    Examples:
        # Archive task for a specific merged PR
        bpsai-pair github archive-merged 123

        # Check all recently merged PRs and archive their tasks
        bpsai-pair github archive-merged --all
    """
    from .pr import archive_task_on_merge, check_and_archive_merged_prs

    paircoder_dir = _find_paircoder_dir()
    project_root = paircoder_dir.parent

    if pr_number:
        # Archive specific PR's task
        success = archive_task_on_merge(
            pr_number=pr_number,
            project_root=project_root,
            paircoder_dir=paircoder_dir,
        )

        if success:
            console.print(f"[green]Archived task for PR #{pr_number}[/green]")
        else:
            console.print(f"[yellow]Could not archive task for PR #{pr_number}[/yellow]")
            console.print("[dim]PR may not be merged or not linked to a task[/dim]")

    elif check_all:
        # Check all recent merged PRs
        archived = check_and_archive_merged_prs(
            project_root=project_root,
            paircoder_dir=paircoder_dir,
            limit=limit,
        )

        if archived:
            console.print(f"[green]Archived {len(archived)} tasks:[/green]")
            for task_id in archived:
                console.print(f"  - {task_id}")
        else:
            console.print("[dim]No tasks to archive[/dim]")

    else:
        console.print("[yellow]Specify a PR number or use --all[/yellow]")
        console.print("[dim]Examples:[/dim]")
        console.print("[dim]  bpsai-pair github archive-merged 123[/dim]")
        console.print("[dim]  bpsai-pair github archive-merged --all[/dim]")
