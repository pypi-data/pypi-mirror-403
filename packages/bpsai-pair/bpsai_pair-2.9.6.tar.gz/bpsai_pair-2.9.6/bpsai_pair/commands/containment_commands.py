"""Containment commands: contained-auto, claude666, rollback, list, cleanup.

This module handles contained autonomy mode and checkpoint management.
"""
from __future__ import annotations

import atexit
import os
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

# Try relative imports first, fall back to absolute
try:
    from ..core import ops
except ImportError:
    from bpsai_pair.core import ops

# Initialize Rich console
console = Console()

# Global reference for cleanup
_active_containment_manager = None


def repo_root() -> Path:
    """Get repo root with better error message."""
    p = ops.find_project_root()
    if not ops.GitOps.is_repo(p):
        console.print(
            "[red]x Not in a git repository.[/red]\n"
            "Please run from your project root directory (where .git exists).\n"
            "[dim]Hint: cd to your project directory first[/dim]"
        )
        raise typer.Exit(1)
    return p


def _cleanup_containment():
    """Cleanup handler for containment on exit."""
    global _active_containment_manager
    if _active_containment_manager is not None:
        _active_containment_manager.deactivate()
        _active_containment_manager = None

        # Restore stashed changes if any
        stash_ref = os.environ.get("PAIRCODER_CONTAINMENT_STASH")
        if stash_ref:
            try:
                # Check if working directory is dirty (has changes from container session)
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                is_dirty = len(result.stdout.strip()) > 0

                if is_dirty:
                    # Don't pop stash - would conflict with container's changes
                    console.print()
                    console.print("[yellow]⚠ Your stashed changes were NOT restored[/yellow]")
                    console.print("[dim]  The container session left uncommitted changes.[/dim]")
                    console.print("[dim]  To restore your original changes after resolving:[/dim]")
                    console.print("[dim]    git stash pop[/dim]")
                else:
                    # Safe to restore stashed changes
                    # Find the stash index for our specific stash message
                    project_root = os.getcwd()
                    list_result = subprocess.run(
                        ["git", "stash", "list"],
                        capture_output=True,
                        text=True,
                        check=False,
                        cwd=project_root,
                    )
                    stash_idx = None
                    for line in list_result.stdout.strip().split("\n"):
                        if stash_ref in line:
                            # Extract stash index (e.g., "stash@{0}")
                            stash_idx = line.split(":")[0]
                            break

                    if stash_idx:
                        # Pop the specific stash we created
                        pop_result = subprocess.run(
                            ["git", "stash", "pop", stash_idx],
                            capture_output=True,
                            text=True,
                            check=False,
                            cwd=project_root,
                        )
                        if pop_result.returncode == 0:
                            console.print()
                            console.print("[green]✓ Restored your stashed changes[/green]")
                        else:
                            console.print()
                            console.print("[yellow]⚠ Could not restore stashed changes[/yellow]")
                            console.print(f"[dim]  {pop_result.stderr.strip()}[/dim]")
                    else:
                        console.print()
                        console.print("[yellow]⚠ Could not find stashed changes[/yellow]")
                        console.print(f"[dim]  Stash message: {stash_ref}[/dim]")
            except Exception:
                pass  # Don't fail cleanup on stash errors

        # Clear environment variables
        os.environ.pop("PAIRCODER_CONTAINMENT", None)
        os.environ.pop("PAIRCODER_CONTAINMENT_CHECKPOINT", None)
        os.environ.pop("PAIRCODER_CONTAINMENT_STASH", None)


ROBOT_DEVIL_ART = """
[red]
    ╔══════════════════════════════════════════╗
    ║         .---.                            ║
    ║        /  6 6\\    CLAUDE 666             ║
    ║        \\  ^  /    Beast Mode Activated   ║
    ║         '-.-'                            ║
    ║        /|   |\\    Powerful but Contained ║
    ║       (_|   |_)                          ║
    ╚══════════════════════════════════════════╝
[/red]
"""


def contained_auto(
    task: Optional[str] = typer.Argument(None, help="Task to work on"),
    skip_checkpoint: bool = typer.Option(
        False, "--skip-checkpoint", help="Skip git checkpoint creation"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt and proceed immediately"
    ),
):
    """Start a contained autonomous session.

    In contained autonomy mode, certain paths are protected from modification:
    - .claude/ directory (agents, commands, skills)
    - Enforcement code (security/, core/, orchestration/)
    - Config files (config.yaml, CLAUDE.md, AGENTS.md)

    A git checkpoint is created automatically for easy rollback.

    After displaying the access control tiers, the command pauses for confirmation
    so you can review the blocked/read-only paths before Claude is invoked.
    Use --yes to skip this confirmation for scripted usage.

    Examples:

        bpsai-pair contained-auto              # Start contained session

        bpsai-pair contained-auto T29.4        # Start with specific task

        bpsai-pair contained-auto --skip-checkpoint  # Skip checkpoint

        bpsai-pair contained-auto -y           # Skip confirmation prompt
    """
    global _active_containment_manager

    try:
        from ..core.config import Config
        from ..security.containment import ContainmentManager
        from ..security.checkpoint import GitCheckpoint
    except ImportError:
        from bpsai_pair.core.config import Config
        from bpsai_pair.security.containment import ContainmentManager
        from bpsai_pair.security.checkpoint import GitCheckpoint

    # Get project root
    project_root = repo_root()
    paircoder_dir = project_root / ".paircoder"

    if not paircoder_dir.exists():
        console.print("[red]No .paircoder directory found[/red]")
        console.print("[dim]Initialize with: bpsai-pair init[/dim]")
        raise typer.Exit(1)

    # Load config
    try:
        config = Config.load(project_root)
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        raise typer.Exit(1)

    # Check if containment is enabled
    if not config.containment.enabled:
        console.print("[yellow]Warning: Containment not enabled in config[/yellow]")
        if not typer.confirm("Enable containment for this session?"):
            console.print("[dim]Aborted. Enable in config.yaml: containment.enabled: true[/dim]")
            raise typer.Abort()

    checkpoint_id = None
    stash_ref = None

    # Create checkpoint if enabled
    if config.containment.auto_checkpoint and not skip_checkpoint:
        try:
            checkpoint = GitCheckpoint(project_root)

            # Warn if dirty working directory
            if checkpoint.is_dirty():
                console.print("[yellow]Warning: Uncommitted changes detected[/yellow]")
                console.print("[dim]Changes will be stashed before checkpoint[/dim]")

            # Create containment checkpoint with auto-stash
            checkpoint_id, stash_ref = checkpoint.create_containment_checkpoint(auto_stash=True)
            console.print(f"[green]✓ Checkpoint created:[/green] {checkpoint_id}")
            if stash_ref:
                console.print(f"[dim]  Stashed changes: {stash_ref}[/dim]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not create checkpoint: {e}[/yellow]")
            if not typer.confirm("Continue without checkpoint?"):
                raise typer.Abort()
    elif skip_checkpoint:
        console.print("[dim]Checkpoint skipped (--skip-checkpoint)[/dim]")

    # Initialize and activate containment
    containment = ContainmentManager(config.containment, project_root)
    containment.activate()
    _active_containment_manager = containment

    # Register cleanup handler
    atexit.register(_cleanup_containment)

    # Set environment variables
    os.environ["PAIRCODER_CONTAINMENT"] = "1"
    if checkpoint_id:
        os.environ["PAIRCODER_CONTAINMENT_CHECKPOINT"] = checkpoint_id
    if stash_ref:
        os.environ["PAIRCODER_CONTAINMENT_STASH"] = stash_ref

    # Display status
    console.print()
    console.print("[bold green]✓ Contained autonomy mode active[/bold green]")
    console.print()

    # Show blocked paths (no read, no write)
    if config.containment.blocked_directories or config.containment.blocked_files:
        console.print("[red]Blocked paths (no read/write):[/red]")
        for blocked_dir in config.containment.blocked_directories:
            console.print(f"  [dim]🚫[/dim] {blocked_dir}")
        for blocked_file in config.containment.blocked_files:
            console.print(f"  [dim]🚫[/dim] {blocked_file}")
        console.print()

    # Show read-only paths (can read, cannot write)
    if config.containment.readonly_directories or config.containment.readonly_files:
        console.print("[yellow]Read-only paths (can read, no write):[/yellow]")
        for readonly_dir in config.containment.readonly_directories:
            console.print(f"  [dim]📁[/dim] {readonly_dir}")
        for readonly_file in config.containment.readonly_files:
            console.print(f"  [dim]📄[/dim] {readonly_file}")
        console.print()

    if task:
        console.print(f"[cyan]Task:[/cyan] {task}")
        console.print()

    console.print("[dim]Blocked paths cannot be accessed. Read-only paths can be read but not modified.[/dim]")

    if checkpoint_id:
        console.print(f"[dim]Rollback available: git reset --hard {checkpoint_id}[/dim]")

    console.print()

    # Confirmation prompt (unless --yes flag)
    if not yes:
        if not typer.confirm("Proceed with these access controls?", default=True):
            console.print("[yellow]Aborted. Adjust containment settings in config.yaml if needed.[/yellow]")
            _cleanup_containment()
            raise typer.Abort()

    # Determine containment mode
    mode = config.containment.mode  # "advisory" or "strict"

    # Check if we can use strict mode
    if mode == "strict":
        try:
            from ..security.sandbox import SandboxRunner
        except ImportError:
            from bpsai_pair.security.sandbox import SandboxRunner

        if not SandboxRunner.is_docker_available():
            console.print("[yellow]Warning: Docker not available for strict containment[/yellow]")
            console.print("[dim]Falling back to advisory mode[/dim]")
            mode = "advisory"
        else:
            console.print("[bold cyan]Mode: STRICT[/bold cyan] (Docker-enforced containment)")
    else:
        console.print("[bold yellow]Mode: ADVISORY[/bold yellow] (path checks only)")

    console.print()
    console.print("[bold]Launching Claude Code with autonomous permissions...[/bold]")
    console.print()

    # Build the claude command
    claude_cmd = ["claude", "--dangerously-skip-permissions"]

    # Add task prompt if provided
    if task:
        claude_cmd.extend(["--prompt", f"Work on task {task}. Remember: containment mode is active - protected paths are read-only."])

    # Execute based on mode
    if mode == "strict":
        # Docker-based containment with OS-enforced read-only mounts
        try:
            from ..security.sandbox import SandboxRunner, SandboxConfig, containment_config_to_mounts
        except ImportError:
            from bpsai_pair.security.sandbox import SandboxRunner, SandboxConfig, containment_config_to_mounts

        # Create sandbox config
        sandbox_config = SandboxConfig(
            enabled=True,
            image=os.environ.get("PAIRCODER_SANDBOX_IMAGE", "paircoder/sandbox:latest"),
            network="none",  # Will be overridden if network_allowlist is set
        )

        # Convert containment config to Docker mounts
        mounts, excluded = containment_config_to_mounts(config.containment, project_root)
        sandbox_config.mounts = mounts[1:]  # Skip the first (base workspace) mount - runner adds it

        # Get network allowlist if configured
        network_allowlist = None
        if hasattr(config.containment, 'allow_network') and config.containment.allow_network:
            network_allowlist = config.containment.allow_network

        # Create runner and execute
        runner = SandboxRunner(project_root, sandbox_config)

        try:
            exit_code = runner.run_interactive(
                claude_cmd,
                env={
                    "PAIRCODER_CONTAINMENT": "1",
                    "PAIRCODER_CONTAINMENT_MODE": "strict",
                    **({"PAIRCODER_CONTAINMENT_CHECKPOINT": checkpoint_id} if checkpoint_id else {}),
                },
                network_allowlist=network_allowlist,
            )
            sys.exit(exit_code)
        except RuntimeError as e:
            console.print(f"[red]Docker error: {e}[/red]")
            console.print("[dim]Falling back to advisory mode[/dim]")
            mode = "advisory"
        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted.[/yellow]")
            raise typer.Exit(130)

    # Advisory mode (default) - run locally with path checks (not enforced)
    claude_exe = shutil.which("claude")
    if claude_exe is None:
        console.print("[red]Error: 'claude' command not found.[/red]")
        console.print("[dim]Install Claude Code: https://docs.anthropic.com/claude-code[/dim]")
        raise typer.Exit(1)

    # Build command with resolved path for cross-platform compatibility
    host_cmd = [claude_exe] + claude_cmd[1:]

    try:
        result = subprocess.run(host_cmd, cwd=project_root)
        sys.exit(result.returncode)
    except FileNotFoundError:
        console.print("[red]Error: 'claude' command not found.[/red]")
        console.print("[dim]Install Claude Code: https://docs.anthropic.com/claude-code[/dim]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Session interrupted.[/yellow]")
        raise typer.Exit(130)


def claude666(
    task: Optional[str] = typer.Argument(None, help="Task to work on"),
    skip_checkpoint: bool = typer.Option(
        False, "--skip-checkpoint", help="Skip git checkpoint creation"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt and proceed immediately"
    ),
):
    """Claude's beast mode - If you know, you know.
    """
    # Show the robot devil art
    console.print(ROBOT_DEVIL_ART)

    # Delegate to contained_auto
    return contained_auto(task=task, skip_checkpoint=skip_checkpoint, yes=yes)


# Containment checkpoint management sub-app
containment_app = typer.Typer(
    help="Containment checkpoint management",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@containment_app.command("rollback")
def containment_rollback(
    checkpoint: Optional[str] = typer.Argument(
        None, help="Checkpoint to rollback to (default: latest containment checkpoint)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Preview rollback without executing"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Skip confirmation prompt"
    ),
    pop_stash: bool = typer.Option(
        True, "--pop-stash/--no-pop-stash", help="Pop stashed changes after rollback"
    ),
):
    """Rollback to a containment checkpoint.

    Restores the repository to the state at the specified checkpoint.
    If no checkpoint is specified, uses the most recent containment checkpoint.

    By default, any changes stashed during checkpoint creation will be
    restored after rollback. Use --no-pop-stash to skip this.

    Examples:
        # Preview rollback to latest checkpoint
        bpsai-pair containment rollback --dry-run

        # Rollback to latest checkpoint
        bpsai-pair containment rollback

        # Rollback to specific checkpoint
        bpsai-pair containment rollback containment-20260113-153045
    """
    try:
        from ..security.checkpoint import (
            GitCheckpoint,
            CheckpointNotFoundError,
            format_rollback_preview,
        )
    except ImportError:
        from bpsai_pair.security.checkpoint import (
            GitCheckpoint,
            CheckpointNotFoundError,
            format_rollback_preview,
        )

    root = repo_root()
    git_checkpoint = GitCheckpoint(root)

    # Find checkpoint to use
    target_checkpoint = checkpoint
    if not target_checkpoint:
        # Get latest containment checkpoint
        latest = git_checkpoint.get_latest_containment_checkpoint()
        if not latest:
            console.print("[yellow]No containment checkpoints found[/yellow]")
            console.print("[dim]Create one with: bpsai-pair contained-auto[/dim]")
            raise typer.Exit(1)
        target_checkpoint = latest["tag"]

    # Preview rollback
    try:
        preview = git_checkpoint.preview_rollback(target_checkpoint)
    except CheckpointNotFoundError:
        console.print(f"[red]Checkpoint not found:[/red] {target_checkpoint}")
        console.print("[dim]List checkpoints with: bpsai-pair containment list[/dim]")
        raise typer.Exit(1)

    console.print(format_rollback_preview(preview))
    console.print()

    if dry_run:
        console.print("[dim]Dry run - no changes made[/dim]")
        return

    # Confirm rollback
    if not force:
        if preview["commits_to_revert"] > 0 or preview["files_changed"]:
            if not typer.confirm("Proceed with rollback?"):
                console.print("[dim]Rollback cancelled[/dim]")
                raise typer.Abort()

    # Check for stash associated with this checkpoint
    stash_ref = None
    if pop_stash:
        # Check environment variable or search stash list
        stash_ref = os.environ.get("PAIRCODER_CONTAINMENT_STASH")
        if not stash_ref:
            # Search for auto-stash in stash list
            result = subprocess.run(
                ["git", "stash", "list"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False
            )
            for line in result.stdout.strip().split("\n"):
                if "Auto-stash before containment checkpoint" in line:
                    stash_ref = "Auto-stash before containment checkpoint"
                    break

    # Execute rollback
    try:
        git_checkpoint.rollback_to(target_checkpoint, stash_uncommitted=True)
        console.print(f"[green]✓ Rolled back to:[/green] {target_checkpoint}")

        # Pop stash if requested and exists
        if pop_stash and stash_ref:
            if git_checkpoint.pop_stash(stash_ref):
                console.print("[green]✓ Restored stashed changes[/green]")
            else:
                console.print("[yellow]Warning: Could not restore stashed changes[/yellow]")

    except Exception as e:
        console.print(f"[red]Rollback failed:[/red] {e}")
        raise typer.Exit(1)


@containment_app.command("list")
def containment_list():
    """List containment checkpoints.

    Shows all checkpoints created by contained-auto sessions.

    Example:
        bpsai-pair containment list
    """
    try:
        from ..security.checkpoint import GitCheckpoint
    except ImportError:
        from bpsai_pair.security.checkpoint import GitCheckpoint

    root = repo_root()
    git_checkpoint = GitCheckpoint(root)

    checkpoints = git_checkpoint.list_containment_checkpoints()

    if not checkpoints:
        console.print("[dim]No containment checkpoints found[/dim]")
        console.print("[dim]Create one with: bpsai-pair contained-auto[/dim]")
        return

    console.print(f"[cyan]Containment Checkpoints ({len(checkpoints)}):[/cyan]")
    console.print()

    for cp in sorted(checkpoints, key=lambda c: c["timestamp"], reverse=True):
        console.print(f"  [bold]{cp['tag']}[/bold]")
        console.print(f"    Commit:  {cp['commit']}")
        console.print(f"    Time:    {cp['timestamp']}")
        if cp.get("message"):
            console.print(f"    Message: {cp['message'][:50]}...")
        console.print()


@containment_app.command("cleanup")
def containment_cleanup(
    keep: int = typer.Option(5, "--keep", "-k", help="Number of checkpoints to keep"),
):
    """Remove old containment checkpoints.

    Keeps the most recent N checkpoints and removes older ones.

    Example:
        bpsai-pair containment cleanup --keep 3
    """
    try:
        from ..security.checkpoint import GitCheckpoint
    except ImportError:
        from bpsai_pair.security.checkpoint import GitCheckpoint

    root = repo_root()
    git_checkpoint = GitCheckpoint(root)

    checkpoints = git_checkpoint.list_containment_checkpoints()

    if len(checkpoints) <= keep:
        console.print(f"[dim]Only {len(checkpoints)} checkpoint(s) - nothing to remove[/dim]")
        return

    # Sort by timestamp (oldest first)
    sorted_checkpoints = sorted(checkpoints, key=lambda c: c["timestamp"])
    to_remove = sorted_checkpoints[:-keep]

    removed = 0
    for cp in to_remove:
        try:
            git_checkpoint.delete_checkpoint(cp["tag"])
            removed += 1
        except Exception:
            pass

    if removed > 0:
        console.print(f"[green]Removed {removed} old checkpoint(s)[/green]")
    else:
        console.print("[dim]No checkpoints removed[/dim]")
