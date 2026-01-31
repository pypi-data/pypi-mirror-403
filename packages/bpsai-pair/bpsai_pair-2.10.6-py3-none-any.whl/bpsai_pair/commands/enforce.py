"""
Enforcement commands for Claude Code hooks.

These commands are designed to be called from PreToolUse hooks to validate
and potentially block tool operations that would violate workflow rules.

Exit codes:
- 0: Operation allowed
- 2: Operation blocked (PreToolUse will prevent the tool from running)
"""

import sys
import json
import re
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(
    help="Enforcement gates for Claude Code hooks",
    context_settings={"help_option_names": ["-h", "--help"]}
)


def find_paircoder_dir() -> Optional[Path]:
    """Find .paircoder directory."""
    try:
        from ..core.ops import find_paircoder_dir as _find
        return _find()
    except Exception:
        return None


def is_trello_enabled() -> bool:
    """Check if Trello integration is enabled."""
    import yaml
    paircoder_dir = find_paircoder_dir()
    if not paircoder_dir:
        return False
    config_path = paircoder_dir / "config.yaml"
    if not config_path.exists():
        return False
    try:
        with open(config_path, encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        return config.get("trello", {}).get("enabled", False) and config.get("trello", {}).get("board_id")
    except Exception:
        return False


def is_strict_ac_enabled() -> bool:
    """Check if strict AC verification is enabled."""
    import yaml
    paircoder_dir = find_paircoder_dir()
    if not paircoder_dir:
        return False
    config_path = paircoder_dir / "config.yaml"
    if not config_path.exists():
        return False
    try:
        with open(config_path, encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        return config.get("enforcement", {}).get("strict_ac_verification", False)
    except Exception:
        return False


def get_trello_card_for_task(task_id: str) -> Optional[dict]:
    """Get Trello card info for a task."""
    try:
        from ..commands.state import get_trello_card_status
        result = get_trello_card_status(task_id)
        if result.get("found"):
            return result
        return None
    except Exception:
        return None


def is_card_in_done_list(card_info: dict) -> bool:
    """Check if Trello card is in a Done list."""
    list_name = card_info.get("list_name", "").lower()
    done_lists = ["done", "deployed", "complete", "deployed/done"]
    return any(done in list_name for done in done_lists)


def extract_task_id_from_path(file_path: str) -> Optional[str]:
    """Extract task ID from file path like .../T29.5.7.task.md"""
    path = Path(file_path)
    if not path.name.endswith(".task.md"):
        return None
    # Extract task ID (everything before .task.md)
    task_id = path.name.replace(".task.md", "")
    return task_id


def extract_status_from_content(content: str) -> Optional[str]:
    """Extract status from YAML frontmatter in content."""
    # Look for status field in frontmatter
    match = re.search(r'^status:\s*(\S+)', content, re.MULTILINE)
    if match:
        return match.group(1).strip().strip('"').strip("'")
    return None


def output_block_message(reason: str) -> None:
    """Output a blocking message in the format Claude Code expects."""
    # Exit code 2 blocks in PreToolUse
    # stderr is shown to Claude as feedback
    sys.stderr.write(f"\n{'='*60}\n")
    sys.stderr.write("BLOCKED BY ENFORCEMENT GATE\n")
    sys.stderr.write(f"{'='*60}\n\n")
    sys.stderr.write(f"{reason}\n\n")
    sys.stderr.write("This edit has been prevented to maintain workflow integrity.\n")
    sys.stderr.write(f"{'='*60}\n")


@app.command("task-edit")
def enforce_task_edit(
    file_path: str = typer.Option(..., "--file", "-f", help="Path to file being edited"),
    new_content: str = typer.Option("", "--new-content", "-c", help="New content (from stdin if not provided)"),
    old_content: str = typer.Option("", "--old-content", "-o", help="Old content for comparison"),
):
    """
    Enforce task edit rules for PreToolUse hook.

    Blocks edits that would set a task to 'done' status without proper
    Trello completion when Trello integration is enabled.

    Exit codes:
    - 0: Edit allowed
    - 2: Edit blocked

    Examples:
        bpsai-pair enforce task-edit --file /path/to/T29.5.7.task.md --new-content "..."
    """
    # Read new content from stdin if not provided
    if not new_content and not sys.stdin.isatty():
        new_content = sys.stdin.read()

    # Check if this is a task file
    task_id = extract_task_id_from_path(file_path)
    if not task_id:
        # Not a task file, allow the edit
        sys.exit(0)

    # Check if Trello is enabled
    if not is_trello_enabled():
        # No Trello, allow the edit (other enforcement handles this)
        sys.exit(0)

    # Check if strict AC is enabled
    if not is_strict_ac_enabled():
        # Not in strict mode, allow (but warn)
        sys.exit(0)

    # Extract status from new content
    new_status = extract_status_from_content(new_content)

    # If not setting to done, allow
    if new_status != "done":
        sys.exit(0)

    # Check if old content already had done status
    if old_content:
        old_status = extract_status_from_content(old_content)
        if old_status == "done":
            # Already done, allow edits to done tasks
            sys.exit(0)

    # Setting status to done - verify Trello card is in Done list
    card_info = get_trello_card_for_task(task_id)

    if not card_info:
        # No Trello card found - block
        output_block_message(
            f"Task {task_id} has no linked Trello card.\n\n"
            "To complete this task:\n"
            f"  1. Find/create the Trello card: bpsai-pair ttask list\n"
            f"  2. Complete via Trello: bpsai-pair ttask done TRELLO-XXX --summary \"...\"\n\n"
            "Do NOT edit the task file directly to set status: done"
        )
        sys.exit(2)

    if not is_card_in_done_list(card_info):
        card_id = card_info.get("card_id", "???")
        current_list = card_info.get("list_name", "Unknown")

        output_block_message(
            f"Task {task_id} Trello card is in '{current_list}', not Done.\n\n"
            "To complete this task:\n"
            f"  bpsai-pair ttask done TRELLO-{card_id} --summary \"...\"\n\n"
            "This will:\n"
            "  - Verify acceptance criteria\n"
            "  - Move card to Done list\n"
            "  - Update local task file automatically\n\n"
            "Do NOT edit the task file directly to set status: done"
        )
        sys.exit(2)

    # Card is in Done list, check AC
    ac_total = card_info.get("ac_total", 0)
    ac_checked = card_info.get("ac_checked", 0)

    if ac_total > 0 and ac_checked < ac_total:
        card_id = card_info.get("card_id", "???")
        output_block_message(
            f"Task {task_id} has {ac_checked}/{ac_total} AC items checked.\n\n"
            "All acceptance criteria must be verified before completion.\n\n"
            "To check AC items:\n"
            f"  bpsai-pair ttask check TRELLO-{card_id} \"<item text>\"\n\n"
            "Then complete:\n"
            f"  bpsai-pair ttask done TRELLO-{card_id} --summary \"...\""
        )
        sys.exit(2)

    # All checks passed - allow the edit
    sys.exit(0)


@app.command("state-edit")
def enforce_state_edit(
    file_path: str = typer.Option(..., "--file", "-f", help="Path to file being edited"),
    new_content: str = typer.Option("", "--new-content", "-c", help="New content"),
):
    """
    Enforce state.md edit rules for PreToolUse hook.

    Blocks edits that would mark tasks as done in state.md without
    proper completion via ttask done.

    Exit codes:
    - 0: Edit allowed
    - 2: Edit blocked
    """
    # Read new content from stdin if not provided
    if not new_content and not sys.stdin.isatty():
        new_content = sys.stdin.read()

    # Check if this is state.md
    path = Path(file_path)
    if path.name != "state.md":
        sys.exit(0)

    # Check if Trello is enabled
    if not is_trello_enabled():
        sys.exit(0)

    if not is_strict_ac_enabled():
        sys.exit(0)

    paircoder_dir = find_paircoder_dir()
    if not paircoder_dir:
        sys.exit(0)

    # Get OLD content from the actual file to compare
    state_path = Path(file_path)
    old_content = ""
    if state_path.exists():
        try:
            old_content = state_path.read_text(encoding='utf-8')
        except Exception:
            pass

    # Extract tasks marked as done in BOTH old and new content
    # PERFORMANCE: Use local-only validation (no Trello API calls)
    # Full Trello validation would take 69+ seconds and break hooks
    from ..commands.state import (
        extract_done_tasks_from_state_md,
        validate_task_completion_local,
    )

    old_done_tasks = set(extract_done_tasks_from_state_md(old_content)) if old_content else set()
    new_done_tasks = set(extract_done_tasks_from_state_md(new_content))

    # Find NEWLY marked done tasks (in new but not in old)
    newly_done_tasks = new_done_tasks - old_done_tasks

    if not newly_done_tasks:
        # No new completions, allow the edit
        sys.exit(0)

    # Validate each NEWLY done task using FAST local-only validation
    # NO network calls - hooks must complete in <100ms
    invalid_tasks = []
    for task_id in newly_done_tasks:
        # Fast local-only validation (no Trello API calls)
        result = validate_task_completion_local(task_id, paircoder_dir)

        # If no local source found, allow (might be quick task or Trello-only)
        # Full Trello validation can be done manually with: bpsai-pair state validate --full
        if not result.get("has_source", False):
            continue

        if not result["valid"]:
            invalid_tasks.append({
                "task_id": task_id,
                "errors": result["errors"]
            })

    if invalid_tasks:
        error_details = []
        for task in invalid_tasks:
            error_details.append(f"\n{task['task_id']}:")
            for err in task["errors"]:
                error_details.append(f"  - {err}")

        output_block_message(
            f"Cannot mark {len(invalid_tasks)} task(s) as done in state.md:\n"
            + "\n".join(error_details) + "\n\n"
                                         "Complete tasks properly:\n"
                                         "  bpsai-pair ttask done TRELLO-XXX --summary \"...\"\n"
                                         "  bpsai-pair task update <id> --status done\n\n"
                                         "Full validation with Trello:\n"
                                         "  bpsai-pair state validate --full\n\n"
                                         "Do NOT edit state.md to mark tasks as done manually."
        )
        sys.exit(2)

    sys.exit(0)


def find_task_file(task_id: str, paircoder_dir: Path) -> Optional[Path]:
    """Find task file for a given task ID."""
    tasks_dir = paircoder_dir / "tasks"
    if not tasks_dir.exists():
        return None

    # Search for task file in all subdirectories
    for task_file in tasks_dir.rglob(f"{task_id}.task.md"):
        return task_file
    return None


def extract_status_from_file(task_file: Path) -> Optional[str]:
    """Extract status from a task file's YAML frontmatter."""
    try:
        content = task_file.read_text(encoding='utf-8')
        return extract_status_from_content(content)
    except Exception:
        return None
