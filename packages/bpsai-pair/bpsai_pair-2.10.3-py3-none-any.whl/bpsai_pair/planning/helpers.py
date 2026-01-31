"""Shared helper functions for planning commands.

Utilities extracted from commands.py for better code organization.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING
import json
import re

from rich.console import Console

if TYPE_CHECKING:
    from .models import Task
    from .parser import TaskParser
    from .state import StateManager

# Shared console instance for all planning commands
console = Console()


def find_paircoder_dir() -> Path:
    """Find .paircoder directory in current or parent directories."""
    from ..core.ops import find_paircoder_dir as _find_paircoder_dir
    return _find_paircoder_dir()


def get_state_manager() -> "StateManager":
    """Get a StateManager instance for the current project."""
    from .state import StateManager
    return StateManager(find_paircoder_dir())


def is_trello_enabled() -> bool:
    """Check if Trello is enabled in config (trello.enabled + board_id)."""
    try:
        paircoder_dir = find_paircoder_dir()
        config_path = paircoder_dir / "config.yaml"
        if not config_path.exists():
            return False

        import yaml
        with open(config_path, encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        trello_config = config.get("trello", {})
        return trello_config.get("enabled", False) and trello_config.get("board_id")
    except Exception:
        return False


def get_linked_trello_card(task_id: str) -> Optional[str]:
    """Get Trello card ID from task's frontmatter (trello_card_id or trello_url)."""
    from .parser import TaskParser, parse_frontmatter

    try:
        paircoder_dir = find_paircoder_dir()
        task_parser = TaskParser(paircoder_dir / "tasks")

        # Find the task file
        task = task_parser.get_task_by_id(task_id)
        if not task or not task.source_path:
            return None

        # Read the task file to get frontmatter
        with open(task.source_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse frontmatter
        frontmatter, _ = parse_frontmatter(content)
        if not frontmatter:
            return None

        # Check for trello_card_id
        if "trello_card_id" in frontmatter:
            card_id = frontmatter["trello_card_id"]
            # Format as TRELLO-XXX if it's just a number
            if isinstance(card_id, (int, str)):
                card_str = str(card_id)
                if card_str.isdigit():
                    return f"TRELLO-{card_str}"
                elif card_str.startswith("TRELLO-"):
                    return card_str
                else:
                    return card_str  # Return as-is (could be shortLink)

        # Check for trello_url
        if "trello_url" in frontmatter:
            url = frontmatter["trello_url"]
            # Extract ID from URL like https://trello.com/c/ABC123/...
            match = re.search(r'/c/([^/]+)', url)
            if match:
                return match.group(1)

        return None
    except Exception:
        return None


def log_bypass(command: str, task_id: str, reason: str = "forced") -> None:
    """Log bypass to .paircoder/history/bypass_log.jsonl for audit."""
    try:
        paircoder_dir = find_paircoder_dir()
        log_path = paircoder_dir / "history" / "bypass_log.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "task_id": task_id,
            "reason": reason,
        }

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Best effort logging


def check_state_md_updated(paircoder_dir: Path, task_id: str) -> dict:
    """Check if state.md was updated since task started (uses timer or file mtime)."""
    import os

    state_path = paircoder_dir / "context" / "state.md"

    # If state.md doesn't exist, we can't check
    if not state_path.exists():
        return {"updated": True, "reason": "state.md not found - skipping check"}

    state_mtime = os.path.getmtime(state_path)

    # Try to get task start time from timer cache
    timer_cache_path = paircoder_dir / "time-tracking-cache.json"
    task_start_time = None

    if timer_cache_path.exists():
        try:
            with open(timer_cache_path, encoding='utf-8') as f:
                cache_data = json.load(f)

            # Check for active timer for this task
            active = cache_data.get("_active", {})
            if active.get("task_id") == task_id and active.get("start"):
                start_str = active["start"]
                task_start_time = datetime.fromisoformat(start_str).timestamp()

            # Also check for completed entries for this task (last entry)
            if task_start_time is None and task_id in cache_data:
                entries = cache_data[task_id].get("entries", [])
                if entries:
                    # Use the last entry's start time
                    last_entry = entries[-1]
                    if last_entry.get("start"):
                        task_start_time = datetime.fromisoformat(last_entry["start"]).timestamp()

        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    # If we couldn't get timer start time, use task file modification time
    if task_start_time is None:
        task_files = list(paircoder_dir.glob(f"tasks/**/{task_id}.task.md"))
        task_files.extend(list(paircoder_dir.glob(f"tasks/{task_id}.task.md")))
        if task_files:
            # Use the file creation or modification time as fallback
            task_file = task_files[0]
            task_start_time = os.path.getmtime(task_file)

    # If we still can't determine start time, allow the update
    if task_start_time is None:
        return {"updated": True, "reason": "Could not determine task start time - skipping check"}

    # Check if state.md was modified after task started
    if state_mtime > task_start_time:
        return {"updated": True, "reason": "state.md updated after task started"}
    else:
        return {
            "updated": False,
            "reason": "state.md was last modified before task started",
        }


def check_for_manual_edits(paircoder_dir: Path, tasks: list) -> list:
    """Detect manual edits by comparing file status with CLI cache."""
    import os
    from .cli_update_cache import get_cli_update_cache, detect_manual_edit

    cli_cache = get_cli_update_cache(paircoder_dir)
    manual_edits = []

    for task in tasks:
        # Get task file path
        task_file = paircoder_dir / "tasks" / f"{task.id}.task.md"
        if not task_file.exists():
            continue

        # Get file modification time
        file_mtime = datetime.fromtimestamp(os.path.getmtime(task_file))

        # Check for manual edit
        result = detect_manual_edit(
            cache=cli_cache,
            task_id=task.id,
            file_mtime=file_mtime,
            current_status=task.status.value,
        )

        if result["detected"]:
            manual_edits.append({
                "task_id": task.id,
                "current_status": result["current_status"],
                "last_cli_status": result["last_cli_status"],
                "last_cli_update": result["last_cli_update"],
                "file_mtime": result["file_mtime"],
            })

    return manual_edits


def show_time_tracking(task: "Task", paircoder_dir: Path) -> None:
    """Display estimated vs actual hours with variance for a task."""
    # Always show estimated hours
    estimate = task.estimated_hours
    console.print(f"\n[cyan]Estimated:[/cyan] {estimate.expected_hours:.1f}h ({estimate.size_band.upper()}) [{estimate.min_hours:.1f}h - {estimate.max_hours:.1f}h]")

    # Try to get actual hours from time tracking
    actual_hours = task.get_actual_hours(paircoder_dir)

    if actual_hours is not None:
        # Calculate variance
        variance_hours = actual_hours - estimate.expected_hours
        if estimate.expected_hours > 0:
            variance_percent = (variance_hours / estimate.expected_hours) * 100
        else:
            variance_percent = 0.0

        console.print(f"[cyan]Actual:[/cyan] {actual_hours:.1f}h")

        # Show variance with color coding
        sign = "+" if variance_hours > 0 else ""
        if abs(variance_percent) <= 10:
            color = "green"  # Accurate estimate
        elif variance_hours > 0:
            color = "red"  # Took longer than estimated
        else:
            color = "yellow"  # Finished early

        console.print(f"[cyan]Variance:[/cyan] [{color}]{sign}{variance_hours:.1f}h ({sign}{variance_percent:.1f}%)[/{color}]")


def populate_files_touched(task: "Task", tasks_dir: Path) -> None:
    """Parse files_touched from task file's Files section."""
    # Find task file
    task_file = None
    for ext in [".task.md", ".md"]:
        candidate = tasks_dir / f"{task.id}{ext}"
        if candidate.exists():
            task_file = candidate
            break

    if not task_file:
        task.files_touched = []
        return

    try:
        content = task_file.read_text(encoding="utf-8")

        # Find "Files to Modify" section
        files = []
        in_files_section = False

        for line in content.split("\n"):
            line_stripped = line.strip()

            # Check for section header
            if line_stripped.startswith("# Files") or line_stripped.startswith("## Files"):
                in_files_section = True
                continue

            # Check for next section
            if in_files_section and line_stripped.startswith("#"):
                break

            # Parse file entries
            if in_files_section and line_stripped.startswith("- "):
                file_path = line_stripped[2:].strip()
                # Handle backticks around file paths
                file_path = file_path.strip("`")
                if file_path:
                    files.append(file_path)

        task.files_touched = files
    except Exception:
        task.files_touched = []


def update_task_with_card_id(task: "Task", card_id: str, task_parser: "TaskParser") -> bool:
    """Insert trello_card_id into task file's frontmatter."""
    try:
        # Find task file - use source_path if available, otherwise search
        task_file = None
        if hasattr(task, 'source_path') and task.source_path:
            task_file = task.source_path
        else:
            # Search for task file in tasks directory
            for ext in [".task.md", ".md"]:
                candidate = task_parser.tasks_dir / f"{task.id}{ext}"
                if candidate.exists():
                    task_file = candidate
                    break

        if not task_file or not task_file.exists():
            return False

        content = task_file.read_text(encoding="utf-8")

        # Insert trello_card_id into frontmatter
        if "trello_card_id:" not in content:
            # Find end of frontmatter
            lines = content.split("\n")
            new_lines = []
            in_frontmatter = False
            inserted = False

            for line in lines:
                if line.strip() == "---":
                    if in_frontmatter and not inserted:
                        # Insert before closing ---
                        new_lines.append(f'trello_card_id: "{card_id}"')
                        inserted = True
                    in_frontmatter = not in_frontmatter
                new_lines.append(line)

            task_file.write_text("\n".join(new_lines), encoding="utf-8")
            return True

        return False
    except Exception:
        return False


def run_status_hooks(paircoder_dir: Path, task_id: str, new_status: str, task: "Task") -> None:
    """Trigger hooks (timer, Trello) based on task status change."""
    try:
        from ..core.hooks import HookRunner, HookContext, load_config

        config = load_config(paircoder_dir)
        runner = HookRunner(config, paircoder_dir)

        if not runner.enabled:
            return

        # Map status to event name
        status_to_event = {
            "in_progress": "on_task_start",
            "review": "on_task_review",
            "done": "on_task_complete",
            "blocked": "on_task_block",
        }

        event = status_to_event.get(new_status)
        if not event:
            return

        # Create hook context
        ctx = HookContext(
            task_id=task_id,
            task=task,
            event=event,
            agent="cli",
            extra={"summary": f"Task updated to {new_status}"},
        )

        # Run the hooks
        results = runner.run_hooks(event, ctx)

        # Report hook results
        for result in results:
            if result.success:
                if result.result and result.result.get("trello_synced"):
                    target_list = result.result.get("target_list", "")
                    console.print(f"  [dim]→ Trello: moved to '{target_list}'[/dim]")
                elif result.result and result.result.get("timer_started"):
                    console.print("  [dim]→ Timer started[/dim]")
                elif result.result and result.result.get("timer_stopped"):
                    formatted_duration = result.result.get("formatted_duration", "")
                    formatted_total = result.result.get("formatted_total", "")
                    if formatted_duration and formatted_total:
                        console.print(f"  [dim]→ Timer stopped: {formatted_duration} (total: {formatted_total})[/dim]")
                    else:
                        duration = result.result.get("duration_seconds", 0)
                        console.print(f"  [dim]→ Timer stopped ({duration:.0f}s)[/dim]")
            else:
                if result.error and "Not connected" not in result.error:
                    console.print(f"  [yellow]→ {result.hook}: {result.error}[/yellow]")

    except ImportError:
        pass  # Hooks module not available
    except Exception as e:
        console.print(f"  [yellow]→ Hooks error: {e}[/yellow]")


def sync_local_ac_for_completion(task_id: str, is_trello: bool = False) -> tuple[bool, str]:
    """Sync local AC items and verify state machine transition for completion.

    This function:
    1. If is_trello: Auto-checks all local AC items (sync from Trello)
    2. Verifies local AC items are all checked
    3. Transitions state machine to LOCAL_AC_VERIFIED (if enabled)

    Args:
        task_id: The task ID to sync AC for
        is_trello: True if coming from ttask done (Trello path), False for local path

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        from ..core.task_state import (
            TaskState,
            get_state_manager,
            is_state_machine_enabled,
            verify_local_ac,
            sync_trello_ac_to_local,
        )

        # For Trello path: auto-check all local AC items (sync from Trello completion)
        if is_trello:
            sync_result = sync_trello_ac_to_local(task_id)
            if sync_result.get("error"):
                return False, f"Failed to sync local AC: {sync_result['error']}"
            if sync_result.get("checked_count", 0) > 0:
                console.print(f"[green]✓ Synced {sync_result['checked_count']} local AC item(s)[/green]")

        # Verify all local AC items are checked
        ac_result = verify_local_ac(task_id)
        if ac_result.get("error"):
            return False, f"AC verification error: {ac_result['error']}"

        if not ac_result["verified"]:
            unchecked = ac_result["unchecked_items"]
            unchecked_list = "\n".join(f"  ○ {item}" for item in unchecked[:5])
            if len(unchecked) > 5:
                unchecked_list += f"\n  ... and {len(unchecked) - 5} more"
            return False, (
                f"{len(unchecked)} local AC item(s) unchecked:\n{unchecked_list}\n"
                f"Check items: bpsai-pair task check {task_id}"
            )

        # Transition state machine if enabled
        if is_state_machine_enabled():
            manager = get_state_manager()
            current = manager.get_state(task_id)

            # Determine the appropriate source state
            if is_trello and current == TaskState.AC_VERIFIED:
                # Trello path: AC_VERIFIED → LOCAL_AC_VERIFIED
                manager.transition(task_id, TaskState.LOCAL_AC_VERIFIED, trigger="sync_local_ac")
            elif current == TaskState.IN_PROGRESS:
                # Non-Trello path: IN_PROGRESS → LOCAL_AC_VERIFIED
                manager.transition(task_id, TaskState.LOCAL_AC_VERIFIED, trigger="verify_local_ac")
            elif current == TaskState.LOCAL_AC_VERIFIED:
                # Already in correct state
                pass
            # else: state machine not tracking this task yet - that's OK

        return True, "Local AC verified"

    except Exception as e:
        return False, f"Error syncing local AC: {e}"


def complete_task_with_state_machine(task_id: str, trigger: str = "completion") -> tuple[bool, str]:
    """Transition task to COMPLETED state via state machine (if enabled).

    Args:
        task_id: The task ID to complete
        trigger: Description of what triggered completion

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        from ..core.task_state import (
            TaskState,
            get_state_manager,
            is_state_machine_enabled,
        )

        if not is_state_machine_enabled():
            return True, "State machine not enabled"

        manager = get_state_manager()
        current = manager.get_state(task_id)

        # Can only complete from LOCAL_AC_VERIFIED
        if current != TaskState.LOCAL_AC_VERIFIED:
            allowed, reason = manager.can_transition(task_id, TaskState.COMPLETED)
            if not allowed:
                return False, reason

        manager.transition(task_id, TaskState.COMPLETED, trigger=trigger)
        return True, "Task completed"

    except Exception as e:
        return False, f"Error completing task: {e}"
