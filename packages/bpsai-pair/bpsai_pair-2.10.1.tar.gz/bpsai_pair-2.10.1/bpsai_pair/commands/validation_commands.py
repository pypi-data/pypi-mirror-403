"""Validation commands for bpsai-pair CLI.

Contains the status, validate, ci, and history-log commands extracted from core.py:
- status: Show current context loop status
- validate: Validate repo structure and context consistency
- ci: Run local CI checks
- history-log: Log file changes (hidden command)

Also contains helper functions:
- _get_containment_status: Get containment status information
- print_json: Print JSON to stdout without Rich formatting
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Try relative imports first, fall back to absolute
try:
    from ..core import ops
    from ..core.config import Config
except ImportError:
    from bpsai_pair.core import ops
    from bpsai_pair.core.config import Config


# Initialize Rich console
console = Console()

# Environment variable support
CONTEXT_DIR = os.getenv("PAIRCODER_CONTEXT_DIR", ".paircoder/context")


def print_json(data: dict) -> None:
    """Print JSON to stdout without Rich formatting."""
    sys.stdout.write(json.dumps(data, indent=2))
    sys.stdout.write("\n")
    sys.stdout.flush()


def repo_root() -> Path:
    """Get repo root with better error message."""
    try:
        p = ops.find_project_root()
    except ops.ProjectRootNotFoundError:
        console.print(
            "[red]x Not in a git repository.[/red]\n"
            "Please run from your project root directory (where .git exists).\n"
            "[dim]Hint: cd to your project directory first[/dim]"
        )
        raise typer.Exit(1)
    if not ops.GitOps.is_repo(p):
        console.print(
            "[red]x Not in a git repository.[/red]\n"
            "Please run from your project root directory (where .git exists).\n"
            "[dim]Hint: cd to your project directory first[/dim]"
        )
        raise typer.Exit(1)
    return p


def _get_containment_status(root: Path) -> Optional[dict]:
    """Get containment status information.

    Returns:
        Dict with containment status or None if not configured.
    """
    try:
        config = Config.load(root)
    except Exception:
        return None

    containment = config.containment
    is_active = os.environ.get("PAIRCODER_CONTAINMENT") == "1"

    # Don't return anything if containment is not enabled and not active
    if not containment.enabled and not is_active:
        return None

    checkpoint = os.environ.get("PAIRCODER_CONTAINMENT_CHECKPOINT", "")

    # Count protected paths (readonly + blocked)
    readonly_dir_count = len(containment.readonly_directories)
    readonly_file_count = len(containment.readonly_files)
    blocked_dir_count = len(containment.blocked_directories)
    blocked_file_count = len(containment.blocked_files)

    total_dir_count = readonly_dir_count + blocked_dir_count
    total_file_count = readonly_file_count + blocked_file_count

    network_count = len(containment.allow_network)

    # Collect paths for preview (show first few)
    protected_paths = (
        containment.readonly_directories[:5] +
        containment.blocked_directories[:2]
    )

    return {
        "enabled": containment.enabled,
        "active": is_active,
        "mode": containment.mode,
        "checkpoint": checkpoint if checkpoint else None,
        "readonly_dirs": readonly_dir_count,
        "readonly_files": readonly_file_count,
        "blocked_dirs": blocked_dir_count,
        "blocked_files": blocked_file_count,
        "total_dirs": total_dir_count,
        "total_files": total_file_count,
        "network_domains": network_count,
        "protected_paths": protected_paths,
        "allow_network": containment.allow_network,
    }


def status_command(
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show current context loop status and recent changes."""
    root = repo_root()
    context_dir = root / CONTEXT_DIR

    state_file = context_dir / "state.md"

    # Get current branch
    current_branch = ops.GitOps.current_branch(root)
    is_clean = ops.GitOps.is_clean(root)

    # Parse context sync - check v2 format first
    context_data = {}

    if state_file.exists():
        content = state_file.read_text(encoding="utf-8")

        # v2 state.md format
        plan_match = re.search(r'\*\*Plan:\*\*\s*(.*)', content)
        status_match = re.search(r'\*\*Status:\*\*\s*(.*)', content)
        # Get first bullet from "What Was Just Done"
        last_section = re.search(r'## What Was Just Done\n\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
        # Get first item from "What's Next"
        next_section = re.search(r"## What's Next\n\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
        blockers_section = re.search(r'## Blockers\n\n(.*?)(?=\n## |\Z)', content, re.DOTALL)

        last_text = "Not set"
        if last_section:
            lines = [l.strip() for l in last_section.group(1).strip().split('\n') if l.strip()]
            if lines:
                last_text = lines[0].lstrip('- ')

        next_text = "Not set"
        if next_section:
            lines = [l.strip() for l in next_section.group(1).strip().split('\n') if l.strip()]
            if lines:
                next_text = lines[0].lstrip('0123456789. ')

        blockers_text = "None"
        if blockers_section:
            blockers_text = blockers_section.group(1).strip() or "None"

        context_data = {
            "phase": status_match.group(1) if status_match else "Not set",
            "overall": plan_match.group(1) if plan_match else "Not set",
            "last": last_text,
            "next": next_text,
            "blockers": blockers_text
        }

    # Check for recent pack
    pack_files = list(root.glob("*.tgz"))
    latest_pack = None
    if pack_files:
        latest_pack = max(pack_files, key=lambda p: p.stat().st_mtime)

    age_hours = None
    if latest_pack:
        age_hours = (datetime.now() - datetime.fromtimestamp(latest_pack.stat().st_mtime)).total_seconds() / 3600

    # Get containment status
    containment_status = _get_containment_status(root)

    if json_out:
        result = {
            "branch": current_branch,
            "clean": is_clean,
            "context": context_data,
            "latest_pack": str(latest_pack.name) if latest_pack else None,
            "pack_age": age_hours
        }
        # Add containment status if configured
        if containment_status:
            result["containment"] = containment_status
        print_json(result)
    else:
        # Create a nice table
        table = Table(title="PairCoder Status", show_header=False)
        table.add_column("Field", style="cyan", width=20)
        table.add_column("Value", style="white")

        # Git status
        table.add_row("Branch", f"[bold]{current_branch}[/bold]")
        table.add_row("Working Tree", "[green]Clean[/green]" if is_clean else "[yellow]Modified[/yellow]")

        # Context status
        if context_data:
            table.add_row("Phase", context_data["phase"])
            table.add_row("Overall Goal", context_data["overall"][:60] + "..." if len(context_data["overall"]) > 60 else context_data["overall"])
            table.add_row("Last Action", context_data["last"][:60] + "..." if len(context_data["last"]) > 60 else context_data["last"])
            table.add_row("Next Action", context_data["next"][:60] + "..." if len(context_data["next"]) > 60 else context_data["next"])
            if context_data["blockers"] and context_data["blockers"] != "None":
                table.add_row("Blockers", f"[red]{context_data['blockers']}[/red]")

        # Pack status
        if latest_pack:
            age_str = f"{age_hours:.1f} hours ago" if age_hours < 24 else f"{age_hours/24:.1f} days ago"
            table.add_row("Latest Pack", f"{latest_pack.name} ({age_str})")

        console.print(table)

        # Containment status section
        if containment_status:
            console.print()
            console.print("[bold]Containment Status[/bold]")

            if containment_status["active"]:
                mode_str = f"[green]ACTIVE[/green] (contained autonomy, mode: {containment_status['mode']})"
            else:
                mode_str = f"[yellow]CONFIGURED[/yellow] (not active, mode: {containment_status['mode']})"

            console.print(f"   Mode: {mode_str}")

            if containment_status["checkpoint"]:
                console.print(f"   Checkpoint: {containment_status['checkpoint']}")

            # Show path counts
            total_dirs = containment_status["total_dirs"]
            total_files = containment_status["total_files"]
            console.print(f"   Protected Paths: {total_dirs} directories, {total_files} files")

            # Show network restriction
            net_count = containment_status["network_domains"]
            console.print(f"   Network: Restricted ({net_count} domains allowed)")

            # Show protected paths preview
            if containment_status["protected_paths"]:
                console.print()
                console.print("   [dim]Protected:[/dim]")
                for path in containment_status["protected_paths"][:5]:
                    console.print(f"   [dim]- {path}[/dim]")
                remaining = len(containment_status["protected_paths"]) - 5
                if remaining > 0:
                    console.print(f"   [dim]... and {remaining} more[/dim]")

        # Suggestions
        if not is_clean:
            console.print("\n[yellow]! Working tree has uncommitted changes[/yellow]")
            console.print("[dim]Consider committing or stashing before creating a pack[/dim]")

        if not latest_pack or (latest_pack and age_hours is not None and age_hours > 24):
            console.print("\n[dim]Tip: Run 'bpsai-pair pack' to create a fresh context pack[/dim]")


def validate_command(
    fix: bool = typer.Option(False, "--fix", help="Attempt to fix issues"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Validate repo structure and context consistency."""
    root = repo_root()
    issues = []
    fixes = []

    # Check required files
    required_files = [
        Path(".paircoder/context/state.md"),
        Path(".paircoder/config.yaml"),
        Path("AGENTS.md"),
        Path("CLAUDE.md"),
        Path(".agentpackignore"),
    ]

    for file_path in required_files:
        full_path = root / file_path

        if not full_path.exists():
            issues.append(f"Missing required file: {file_path}")
            if fix:
                # Create with minimal content
                full_path.parent.mkdir(parents=True, exist_ok=True)
                if file_path.name == "state.md":
                    full_path.write_text("# Current State\n\n## Active Plan\n\nNo active plan.\n\n## Current Focus\n\nNone.\n", encoding="utf-8")
                elif file_path.name == "config.yaml":
                    full_path.write_text("version: 2.1\nproject_name: unnamed\n", encoding="utf-8")
                elif file_path.name == "AGENTS.md":
                    full_path.write_text("# AGENTS.md\n\nSee `.paircoder/` for project context.\n", encoding="utf-8")
                elif file_path.name == "CLAUDE.md":
                    full_path.write_text("# CLAUDE.md\n\nSee `.paircoder/context/state.md` for current state.\n", encoding="utf-8")
                elif file_path.name == ".agentpackignore":
                    full_path.write_text(".git/\n.venv/\n__pycache__/\nnode_modules/\n", encoding="utf-8")
                else:
                    full_path.touch()
                fixes.append(f"Created {file_path}")

    # Check context sync format (state.md)
    state_file = root / ".paircoder" / "context" / "state.md"

    if state_file.exists():
        content = state_file.read_text(encoding="utf-8")
        required_sections = ["## Active Plan", "## Current Focus"]
        for section in required_sections:
            if section not in content:
                issues.append(f"Missing state section: {section}")

    # Check for uncommitted context changes
    if not ops.GitOps.is_clean(root):
        context_files = [
            ".paircoder/context/state.md",
            "AGENTS.md",
        ]
        for cf in context_files:
            if (root / cf).exists():
                result = subprocess.run(
                    ["git", "diff", "--name-only", cf],
                    cwd=root,
                    capture_output=True,
                    text=True
                )
                if result.stdout.strip():
                    issues.append(f"Uncommitted changes in {cf}")

    if json_out:
        result = {
            "valid": len(issues) == 0,
            "issues": issues,
            "fixes_applied": fixes if fix else []
        }
        print_json(result)
    else:
        if issues:
            console.print("[red]x Validation failed[/red]")
            console.print("\nIssues found:")
            for issue in issues:
                console.print(f"  - {issue}")

            if fixes:
                console.print("\n[green]Fixed:[/green]")
                for fix_msg in fixes:
                    console.print(f"  ! {fix_msg}")
            elif not fix:
                console.print("\n[dim]Run with --fix to attempt automatic fixes[/dim]")
        else:
            console.print("[green]! All validation checks passed[/green]")


def ci_command(
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Run local CI checks (cross-platform)."""
    root = repo_root()

    if json_out:
        # Skip progress spinner for JSON output to avoid polluting stdout
        results = ops.LocalCI.run_all(root)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running CI checks...", total=None)

            results = ops.LocalCI.run_all(root)

            progress.update(task, completed=True)

    if json_out:
        print_json(results)
    else:
        console.print("[bold]Local CI Results[/bold]\n")

        # Python results
        if results["python"]:
            console.print("[cyan]Python:[/cyan]")
            for check, status in results["python"].items():
                icon = "!" if "passed" in status else "x"
                color = "green" if "passed" in status else "yellow"
                console.print(f"  [{color}]{icon}[/{color}] {check}: {status}")

        # Node results
        if results["node"]:
            console.print("\n[cyan]Node.js:[/cyan]")
            for check, status in results["node"].items():
                icon = "!" if "passed" in status else "x"
                color = "green" if "passed" in status else "yellow"
                console.print(f"  [{color}]{icon}[/{color}] {check}: {status}")

        if not results["python"] and not results["node"]:
            console.print("[dim]No Python or Node.js project detected[/dim]")


def history_log_command(
    file_path: Optional[str] = typer.Argument(None, help="File path to log (or use CLAUDE_TOOL_INPUT_FILE_PATH env var)"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress output, exit 0 on errors"),
):
    """Log a file change to the history log (cross-platform).

    This command is designed for use in Claude Code hooks as a cross-platform
    alternative to shell commands. It creates the history directory if needed
    and appends the timestamp and file path to changes.log.

    The file path can be provided as an argument or read from the
    CLAUDE_TOOL_INPUT_FILE_PATH environment variable (set by Claude Code).

    Use --quiet for hooks (suppresses errors, always exits 0).
    """
    try:
        # Get file path from argument or environment variable
        path_to_log = file_path or os.environ.get("CLAUDE_TOOL_INPUT_FILE_PATH")
        if not path_to_log:
            if quiet:
                return
            console.print("[red]No file path provided and CLAUDE_TOOL_INPUT_FILE_PATH not set[/red]")
            raise typer.Exit(1)

        root = repo_root()
        history_dir = root / ".paircoder" / "history"
        history_dir.mkdir(parents=True, exist_ok=True)

        log_file = history_dir / "changes.log"
        timestamp = datetime.now().isoformat(timespec="seconds")
        entry = f"{timestamp} {path_to_log}\n"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)

        if not quiet:
            console.print(f"[green]![/green] Logged: {path_to_log}")
    except Exception as e:
        if quiet:
            return  # Silent exit for hooks
        console.print(f"[red]Error logging file change: {e}[/red]")
        raise typer.Exit(1)
