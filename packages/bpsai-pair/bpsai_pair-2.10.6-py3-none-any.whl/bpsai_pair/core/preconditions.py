"""Pre-command validation hooks.

Validates that prerequisites are met before commands execute.
Block invalid operations early with clear error messages.

Location: tools/cli/bpsai_pair/core/preconditions.py
"""
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

import typer
from rich.console import Console

console = Console()


class PreconditionResult(Enum):
    """Result of precondition check."""
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"


@dataclass
class CheckResult:
    """Result of a precondition check."""
    status: PreconditionResult
    message: str
    suggestion: Optional[str] = None
    
    @property
    def passed(self) -> bool:
        return self.status == PreconditionResult.PASS
    
    @property
    def blocked(self) -> bool:
        return self.status == PreconditionResult.BLOCK


# ============================================================================
# PRECONDITION CHECKS
# ============================================================================

def check_paircoder_project() -> CheckResult:
    """Check if we're in a PairCoder project."""
    from .ops import find_paircoder_dir
    
    paircoder_dir = find_paircoder_dir()
    if paircoder_dir and paircoder_dir.exists():
        return CheckResult(PreconditionResult.PASS, "PairCoder project found")
    
    return CheckResult(
        PreconditionResult.BLOCK,
        "Not in a PairCoder project",
        suggestion="Run: bpsai-pair init"
    )


def check_trello_connected() -> CheckResult:
    """Check if Trello is configured and connected."""
    try:
        from ..trello.task_helpers import get_board_client
        client, config = get_board_client()
        if client:
            return CheckResult(PreconditionResult.PASS, "Trello connected")
    except Exception:
        pass
    
    return CheckResult(
        PreconditionResult.BLOCK,
        "Trello not connected",
        suggestion="Run: bpsai-pair trello connect"
    )


def check_trello_enabled() -> CheckResult:
    """Check if Trello integration is enabled in config."""
    from .config import load_raw_config
    from .ops import find_paircoder_dir

    try:
        paircoder_dir = find_paircoder_dir()
        if paircoder_dir:
            config, _ = load_raw_config(paircoder_dir.parent)
            if config:
                trello_config = config.get("trello", {})
                if trello_config.get("enabled", False):
                    return CheckResult(PreconditionResult.PASS, "Trello enabled in config")
    except Exception:
        pass

    return CheckResult(
        PreconditionResult.WARN,
        "Trello not enabled in config",
        suggestion="Add 'trello: enabled: true' to config.yaml"
    )


def check_task_exists(task_id: str) -> CheckResult:
    """Check if task file exists."""
    from .ops import find_paircoder_dir
    
    paircoder_dir = find_paircoder_dir()
    if not paircoder_dir:
        return CheckResult(PreconditionResult.BLOCK, "Not in PairCoder project")
    
    # Check in tasks directory
    tasks_dir = paircoder_dir / "tasks"
    if tasks_dir.exists():
        # Search recursively for task file
        for task_file in tasks_dir.rglob(f"{task_id}.task.md"):
            return CheckResult(PreconditionResult.PASS, f"Task {task_id} found")
        for task_file in tasks_dir.rglob(f"*{task_id}*.task.md"):
            return CheckResult(PreconditionResult.PASS, f"Task {task_id} found")
    
    return CheckResult(
        PreconditionResult.BLOCK,
        f"Task {task_id} not found",
        suggestion="Check task ID or create task first"
    )


def check_task_status(task_id: str, required_status: str) -> CheckResult:
    """Check if task is in required status."""
    from .ops import find_paircoder_dir
    import yaml
    
    paircoder_dir = find_paircoder_dir()
    if not paircoder_dir:
        return CheckResult(PreconditionResult.WARN, "Could not verify task status")
    
    tasks_dir = paircoder_dir / "tasks"
    if not tasks_dir.exists():
        return CheckResult(PreconditionResult.WARN, "No tasks directory")
    
    # Find task file
    task_file = None
    for tf in tasks_dir.rglob(f"*{task_id}*.task.md"):
        task_file = tf
        break
    
    if not task_file:
        return CheckResult(PreconditionResult.WARN, f"Task {task_id} file not found")
    
    # Parse frontmatter
    try:
        content = task_file.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                status = frontmatter.get("status", "unknown")
                
                if status == required_status:
                    return CheckResult(PreconditionResult.PASS, f"Task is {required_status}")
                
                return CheckResult(
                    PreconditionResult.BLOCK,
                    f"Task is '{status}', must be '{required_status}'",
                    suggestion=f"Task must be in '{required_status}' state first"
                )
    except Exception as e:
        return CheckResult(PreconditionResult.WARN, f"Could not parse task file: {e}")
    
    return CheckResult(PreconditionResult.WARN, "Could not verify task status")


def check_git_clean() -> CheckResult:
    """Check if git working tree is clean."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and not result.stdout.strip():
            return CheckResult(PreconditionResult.PASS, "Git tree clean")
        
        if result.returncode == 0:
            changed_files = len(result.stdout.strip().split("\n"))
            return CheckResult(
                PreconditionResult.WARN,
                f"Uncommitted changes ({changed_files} files)",
                suggestion="Commit or stash changes first"
            )
    except subprocess.TimeoutExpired:
        return CheckResult(PreconditionResult.WARN, "Git status timed out")
    except FileNotFoundError:
        return CheckResult(PreconditionResult.WARN, "Git not available")
    except Exception as e:
        return CheckResult(PreconditionResult.WARN, f"Could not check git: {e}")
    
    return CheckResult(PreconditionResult.WARN, "Could not check git status")


def check_has_active_plan() -> CheckResult:
    """Check if there's an active plan."""
    from .ops import find_paircoder_dir
    
    paircoder_dir = find_paircoder_dir()
    if not paircoder_dir:
        return CheckResult(PreconditionResult.BLOCK, "Not in a PairCoder project")
    
    state_file = paircoder_dir / "context" / "state.md"
    if state_file.exists():
        content = state_file.read_text(encoding="utf-8")
        # Look for active plan indicators
        if "Active Plan" in content or "Current Sprint" in content:
            if "(none" not in content.lower() and "no active" not in content.lower():
                return CheckResult(PreconditionResult.PASS, "Active plan found")
    
    return CheckResult(
        PreconditionResult.WARN,
        "No active plan found",
        suggestion="Create a plan: bpsai-pair plan new <slug>"
    )


def check_on_feature_branch() -> CheckResult:
    """Check if we're on a feature branch (not main/master)."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            if branch in ("main", "master"):
                return CheckResult(
                    PreconditionResult.WARN,
                    f"On protected branch '{branch}'",
                    suggestion="Create a feature branch first"
                )
            return CheckResult(PreconditionResult.PASS, f"On branch '{branch}'")
    except Exception:
        pass
    
    return CheckResult(PreconditionResult.WARN, "Could not determine branch")


# ============================================================================
# PRECONDITION RUNNER
# ============================================================================

def run_preconditions(
    checks: list[Callable[[], CheckResult]],
    fail_on_warn: bool = False,
    silent: bool = False,
) -> bool:
    """Run a list of precondition checks.
    
    Args:
        checks: List of check functions to run
        fail_on_warn: If True, warnings also block execution
        silent: If True, don't print pass messages
        
    Returns:
        True if all checks pass, False if blocked
    """
    all_passed = True
    
    for check_fn in checks:
        result = check_fn()
        
        if result.blocked:
            console.print(f"[red]❌ BLOCKED:[/red] {result.message}")
            if result.suggestion:
                console.print(f"[dim]   → {result.suggestion}[/dim]")
            all_passed = False
        elif result.status == PreconditionResult.WARN:
            console.print(f"[yellow]⚠️ WARNING:[/yellow] {result.message}")
            if result.suggestion:
                console.print(f"[dim]   → {result.suggestion}[/dim]")
            if fail_on_warn:
                all_passed = False
        elif not silent:
            console.print(f"[green]✓[/green] {result.message}")
    
    return all_passed


def require_preconditions(*check_fns: Callable[[], CheckResult], fail_on_warn: bool = False):
    """Decorator to add precondition checks to a command.
    
    Example:
        @require_preconditions(check_trello_connected, check_has_active_plan)
        def my_command():
            ...
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not run_preconditions(list(check_fns), fail_on_warn=fail_on_warn):
                raise typer.Exit(1)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# TASK-SPECIFIC CHECKS (Curried functions)
# ============================================================================

def make_task_exists_check(task_id: str) -> Callable[[], CheckResult]:
    """Create a task exists check for a specific task ID."""
    def check() -> CheckResult:
        return check_task_exists(task_id)
    return check


def make_task_status_check(task_id: str, required_status: str) -> Callable[[], CheckResult]:
    """Create a task status check for a specific task ID and status."""
    def check() -> CheckResult:
        return check_task_status(task_id, required_status)
    return check
