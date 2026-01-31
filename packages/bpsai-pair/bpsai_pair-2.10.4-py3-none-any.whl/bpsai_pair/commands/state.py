"""Task state CLI commands.

Location: tools/cli/bpsai_pair/commands/state.py
"""
import re
import typer
from pathlib import Path
from typing import Optional, Dict, Any, List, Set

app = typer.Typer(help="Task execution state management")


def find_paircoder_dir() -> Path:
    """Find .paircoder directory."""
    from ..core.ops import find_paircoder_dir as _find
    return _find()


def extract_done_tasks_from_state_md(content: str) -> Set[str]:
    """
    Extract task IDs that are marked as done in state.md content.

    Recognizes patterns like:
    - T29.4.1: ... ✓ done
    - ~~T29.4.2: ...~~ ✓ DONE
    - | T29.4.3 | ... | ✓ done |
    - T29.4.4: ... [done]

    Args:
        content: state.md file content

    Returns:
        Set of task IDs marked as done
    """
    done_tasks = set()

    # Pattern to find task IDs (T followed by digits, dots, and more digits)
    task_id_pattern = r'\b(T\d+(?:\.\d+)+)\b'

    # Split into lines for context-aware parsing
    for line in content.split('\n'):
        # Skip lines that don't contain task IDs
        task_ids = re.findall(task_id_pattern, line)
        if not task_ids:
            continue

        # Check if line indicates task is done
        line_lower = line.lower()

        # Various done indicators
        is_done = any([
            '✓' in line and ('done' in line_lower or 'complete' in line_lower),
            '~~' in line and ('done' in line_lower or '✓' in line),
            re.search(r'\|\s*✓\s*done\s*\|', line_lower),
            re.search(r'\|\s*done\s*\|', line_lower),
            re.search(r'\[done\]', line_lower),
            re.search(r'\[completed\]', line_lower),
            # Table format with done status
            re.search(r'\|\s*✓\s*done', line_lower),
        ])

        if is_done:
            done_tasks.update(task_ids)

    return done_tasks


def is_trello_enabled(paircoder_dir: Path) -> bool:
    """Check if Trello integration is enabled."""
    import yaml
    config_path = paircoder_dir / "config.yaml"
    if not config_path.exists():
        return False
    try:
        with open(config_path, encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        return config.get("trello", {}).get("enabled", False)
    except Exception:
        return False


def get_trello_card_status(task_id: str) -> Dict[str, Any]:
    """
    Get Trello card status for a task.

    Args:
        task_id: Task ID (e.g., T29.4.1)

    Returns:
        Dict with: found, list_name, ac_total, ac_checked, card_id
    """
    try:
        from ..trello.task_commands import get_board_client

        client, config = get_board_client()

        # Search for card by task ID prefix in title (e.g., [T29.4.1])
        card, lst = client.find_card_with_prefix(task_id)

        if not card:
            return {"found": False}

        # Get checklist items (acceptance criteria)
        ac_total = 0
        ac_checked = 0

        try:
            checklists = client.get_card_checklists(card)
            for checklist in checklists:
                if "acceptance" in checklist.get("name", "").lower():
                    items = checklist.get("checkItems", [])
                    ac_total += len(items)
                    ac_checked += sum(1 for item in items if item.get("state") == "complete")
        except Exception:
            pass  # Best effort

        return {
            "found": True,
            "list_name": lst.name if lst else "",
            "ac_total": ac_total,
            "ac_checked": ac_checked,
            "card_id": getattr(card, 'short_id', getattr(card, 'id', '')),
        }
    except Exception as e:
        return {"found": False, "error": str(e)}


def parse_acceptance_criteria_from_body(body: str) -> List[Dict[str, Any]]:
    """
    Parse acceptance criteria checkboxes from task markdown body.

    Looks for checkbox patterns like:
    - [ ] Unchecked item
    - [x] Checked item
    - [X] Checked item (uppercase)

    Args:
        body: Markdown body content

    Returns:
        List of dicts with 'text' and 'checked' keys
    """
    ac_items = []

    for line in body.split('\n'):
        stripped = line.strip()

        if stripped.startswith('- [x]') or stripped.startswith('- [X]'):
            # Checked item
            item_text = re.sub(r'^- \[[xX]\]\s*', '', stripped)
            ac_items.append({'text': item_text, 'checked': True})
        elif stripped.startswith('- [ ]'):
            # Unchecked item
            item_text = re.sub(r'^- \[ \]\s*', '', stripped)
            ac_items.append({'text': item_text, 'checked': False})

    return ac_items


def validate_task_completion_local(task_id: str, paircoder_dir: Path) -> Dict[str, Any]:
    """
    Fast local-only validation for hooks. Must complete in <100ms.

    NO network calls. NO Trello API. Just local file checks.

    Checks:
    1. Local task file (if exists): status must be done, AC must be verified

    Args:
        task_id: Task ID to validate
        paircoder_dir: Path to .paircoder directory

    Returns:
        Dict with: valid (bool), errors (list), local_status
    """
    from ..planning.parser import TaskParser

    errors = []
    local_status = None
    has_source = False

    # Check local task file only - NO network calls
    try:
        task_parser = TaskParser(paircoder_dir / "tasks")
        task = task_parser.get_task_by_id(task_id)

        if task:
            has_source = True
            local_status = task.status.value if hasattr(task.status, 'value') else str(task.status)

            # Check status
            if local_status != "done":
                errors.append(f"Local task file shows status: {local_status} (expected: done)")

            # Check acceptance criteria from task body markdown
            body = getattr(task, 'body', '') or ''
            ac_items = parse_acceptance_criteria_from_body(body)
            if ac_items:
                unchecked = [item for item in ac_items if not item.get('checked', False)]
                if unchecked:
                    errors.append(f"Local task has {len(unchecked)} unchecked AC items")
    except Exception:
        pass  # Task file may not exist

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "local_status": local_status,
        "has_source": has_source,
    }


def validate_task_completion_full(task_id: str, paircoder_dir: Path) -> Dict[str, Any]:
    """
    Full validation including Trello. Can be slow (network calls).

    Checks:
    1. Local task file (if exists): status must be done, AC must be verified
    2. Trello card (if linked): must be in Done list, AC must be checked

    Args:
        task_id: Task ID to validate
        paircoder_dir: Path to .paircoder directory

    Returns:
        Dict with: valid (bool), errors (list), local_status, trello_status
    """
    # Start with local validation
    local_result = validate_task_completion_local(task_id, paircoder_dir)
    errors = list(local_result["errors"])
    local_status = local_result["local_status"]
    has_source = local_result["has_source"]
    trello_status = None

    # Check Trello if enabled - THIS IS THE SLOW PART
    if is_trello_enabled(paircoder_dir):
        trello_result = get_trello_card_status(task_id)
        trello_status = trello_result

        if trello_result.get("found"):
            has_source = True
            list_name = trello_result.get("list_name", "")

            # Check if in Done list
            done_lists = ["done", "deployed", "complete", "deployed/done"]
            is_in_done = any(done in list_name.lower() for done in done_lists)

            if not is_in_done:
                errors.append(f"Trello card is in '{list_name}' (expected: Done list)")

            # Check AC
            ac_total = trello_result.get("ac_total", 0)
            ac_checked = trello_result.get("ac_checked", 0)

            if ac_total > 0 and ac_checked < ac_total:
                errors.append(f"Trello card has {ac_checked}/{ac_total} AC items checked")

    # Must have at least one source of truth
    if not has_source:
        errors.append(f"No source of truth found for {task_id} (no local task file, no Trello card)")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "local_status": local_status,
        "trello_status": trello_status,
    }


def validate_task_completion(
    task_id: str, paircoder_dir: Path, include_trello: bool = False
) -> Dict[str, Any]:
    """
    Validate that a task marked as done in state.md is actually complete.

    By default, only performs fast local validation (no network calls).
    Use include_trello=True for full validation including Trello API calls.

    Args:
        task_id: Task ID to validate
        paircoder_dir: Path to .paircoder directory
        include_trello: If True, include Trello validation (slow, network calls)

    Returns:
        Dict with: valid (bool), errors (list), local_status, trello_status
    """
    if include_trello:
        return validate_task_completion_full(task_id, paircoder_dir)
    else:
        result = validate_task_completion_local(task_id, paircoder_dir)
        # Add trello_status key for API compatibility
        result["trello_status"] = None
        return result


@app.command("show")
def show_state(
    task_id: str = typer.Argument(..., help="Task ID (e.g., T28.1)"),
):
    """Show current execution state for a task.
    
    Examples:
        bpsai-pair state show T28.1
    """
    from rich.console import Console
    from rich.panel import Panel
    
    from ..core.task_state import (
        get_state_manager,
        VALID_TRANSITIONS,
        TRANSITION_TRIGGERS,
        is_state_machine_enabled,
    )
    
    console = Console()
    
    # Check if enabled
    if not is_state_machine_enabled():
        console.print("[yellow]⚠️ State machine is disabled in config[/yellow]")
        console.print("[dim]Enable with: enforcement.state_machine: true in config.yaml[/dim]\n")
    
    mgr = get_state_manager()
    current = mgr.get_state(task_id)
    
    # Build state info
    valid_next = VALID_TRANSITIONS.get(current, [])
    
    lines = [f"[bold]State:[/bold] {current.value}"]
    
    if valid_next:
        lines.append("")
        lines.append("[bold]Next valid states:[/bold]")
        for next_state in valid_next:
            trigger = TRANSITION_TRIGGERS.get((current, next_state), "")
            lines.append(f"  • {next_state.value}")
            if trigger:
                lines.append(f"    [dim]→ {trigger}[/dim]")
    else:
        lines.append("")
        lines.append("[green]✓ Complete (terminal state)[/green]")
    
    console.print(Panel("\n".join(lines), title=f"Task {task_id}"))


@app.command("history")
def show_history(
    task_id: Optional[str] = typer.Argument(None, help="Task ID (optional, shows all if omitted)"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of entries to show"),
):
    """Show state transition history.
    
    Examples:
        bpsai-pair state history
        bpsai-pair state history T28.1
        bpsai-pair state history --limit 50
    """
    from rich.console import Console
    from rich.table import Table
    
    from ..core.task_state import get_state_manager
    
    console = Console()
    mgr = get_state_manager()
    
    history = mgr.get_history(task_id=task_id, limit=limit)
    
    if not history:
        console.print("[dim]No state transitions recorded.[/dim]")
        return
    
    table = Table(title="State Transition History")
    table.add_column("Time", style="dim", width=16)
    table.add_column("Task", width=10)
    table.add_column("From", width=14)
    table.add_column("To", width=14)
    table.add_column("Trigger", width=30)
    
    for entry in history:
        ts = entry["timestamp"][:16].replace("T", " ")
        trigger = entry.get("trigger", "")[:30]
        
        # Color code transitions
        to_state = entry["to_state"]
        if to_state == "completed":
            style = "green"
        elif to_state == "blocked":
            style = "red"
        elif to_state == "in_progress":
            style = "cyan"
        else:
            style = ""
        
        table.add_row(
            ts,
            entry["task_id"],
            entry["from_state"],
            f"[{style}]{to_state}[/{style}]" if style else to_state,
            trigger,
        )
    
    console.print(table)


@app.command("list")
def list_states(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by state"),
):
    """List all tracked task states.
    
    Examples:
        bpsai-pair state list
        bpsai-pair state list --status in_progress
    """
    from rich.console import Console
    from rich.table import Table
    
    from ..core.task_state import get_state_manager
    
    console = Console()
    mgr = get_state_manager()
    
    all_states = mgr.get_all_states()
    
    if not all_states:
        console.print("[dim]No tasks being tracked.[/dim]")
        return
    
    # Filter if requested
    if status:
        all_states = {k: v for k, v in all_states.items() if v == status}
        if not all_states:
            console.print(f"[dim]No tasks in state '{status}'[/dim]")
            return
    
    table = Table(title="Tracked Task States")
    table.add_column("Task ID", width=12)
    table.add_column("State", width=14)
    
    for task_id, state in sorted(all_states.items()):
        # Color code
        if state == "completed":
            style = "green"
        elif state == "blocked":
            style = "red"
        elif state == "in_progress":
            style = "cyan"
        else:
            style = "dim"
        
        table.add_row(task_id, f"[{style}]{state}[/{style}]")
    
    console.print(table)


@app.command("reset")
def reset_state(
    task_id: str = typer.Argument(..., help="Task ID to reset"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Reset a task to NOT_STARTED state.
    
    Use this to re-do a task or fix state issues.
    
    Examples:
        bpsai-pair state reset T28.1
        bpsai-pair state reset T28.1 --yes
    """
    from ..core.task_state import get_state_manager
    
    mgr = get_state_manager()
    current = mgr.get_state(task_id)
    
    if current.value == "not_started":
        typer.echo(f"Task {task_id} is already in not_started state.")
        return
    
    if not confirm:
        typer.confirm(
            f"Reset task {task_id} from '{current.value}' to 'not_started'?",
            abort=True
        )
    
    mgr.reset_task(task_id)


@app.command("advance")
def advance_state(
    task_id: str = typer.Argument(..., help="Task ID"),
    to_state: str = typer.Argument(..., help="Target state"),
    reason: str = typer.Option("manual", "--reason", "-r", help="Reason for transition"),
):
    """Manually advance task to a new state.
    
    Only valid transitions are allowed.
    
    Examples:
        bpsai-pair state advance T28.1 budget_checked
        bpsai-pair state advance T28.1 in_progress --reason "Starting work"
    """
    from ..core.task_state import get_state_manager, TaskState
    
    # Parse target state
    try:
        target = TaskState(to_state)
    except ValueError:
        valid = [s.value for s in TaskState]
        typer.echo(f"Invalid state '{to_state}'. Valid states: {', '.join(valid)}", err=True)
        raise typer.Exit(1)
    
    mgr = get_state_manager()
    mgr.transition(task_id, target, trigger=reason)


@app.command("validate")
def validate_state(
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Only output on errors"),
    task_id: Optional[str] = typer.Option(None, "--task", "-t", help="Validate specific task only"),
    full: bool = typer.Option(False, "--full", "-f", help="Full validation including Trello (slow)"),
):
    """
    Validate that tasks marked done in state.md are actually complete.

    By default, performs fast local-only validation (no network calls).
    Use --full for complete validation including Trello API checks.

    Local checks:
    - Local task file: status must be 'done', AC must be verified

    Full checks (--full):
    - All local checks above
    - Trello card: must be in Done list, AC must be checked

    Examples:
        bpsai-pair state validate          # Fast, local only (default)
        bpsai-pair state validate --full   # Full validation with Trello
        bpsai-pair state validate --quiet
        bpsai-pair state validate --task T29.4.1
    """
    from rich.console import Console

    console = Console()

    try:
        paircoder_dir = find_paircoder_dir()
    except Exception as e:
        if not quiet:
            console.print(f"[red]Could not find .paircoder directory: {e}[/red]")
        raise typer.Exit(1)

    state_path = paircoder_dir / "context" / "state.md"
    if not state_path.exists():
        if not quiet:
            console.print("[yellow]No state.md found[/yellow]")
        return  # Not an error - project may not have state.md

    # Read state.md
    content = state_path.read_text(encoding='utf-8')

    # Extract done tasks
    done_tasks = extract_done_tasks_from_state_md(content)

    if not done_tasks:
        if not quiet:
            console.print("[green]✓ No tasks marked as done in state.md[/green]")
        return

    # Filter to specific task if requested
    if task_id:
        if task_id not in done_tasks:
            if not quiet:
                console.print(f"[yellow]Task {task_id} is not marked as done in state.md[/yellow]")
            return
        done_tasks = {task_id}

    # Validate each done task
    all_valid = True
    validation_errors = []

    for tid in sorted(done_tasks):
        result = validate_task_completion(tid, paircoder_dir, include_trello=full)

        if not result["valid"]:
            all_valid = False
            validation_errors.append({
                "task_id": tid,
                "errors": result["errors"],
            })

    # Report results
    if all_valid:
        if not quiet:
            mode = "full (with Trello)" if full else "local"
            console.print(f"[green]✓ All {len(done_tasks)} done tasks validated successfully ({mode})[/green]")
        return

    # Print errors
    console.print(f"\n[red]❌ VALIDATION FAILED: {len(validation_errors)} task(s) have issues[/red]\n")

    for error in validation_errors:
        console.print(f"[yellow]{error['task_id']}:[/yellow]")
        for err in error["errors"]:
            console.print(f"  [red]• {err}[/red]")
        console.print()

    console.print("[dim]Tasks marked as done in state.md must be properly completed:[/dim]")
    console.print("[dim]  • Trello projects: Use 'bpsai-pair ttask done TRELLO-XX --summary \"...\"'[/dim]")
    console.print("[dim]  • Local only: Use 'bpsai-pair task update TASK-XX --status done'[/dim]")
    console.print()

    raise typer.Exit(1)
