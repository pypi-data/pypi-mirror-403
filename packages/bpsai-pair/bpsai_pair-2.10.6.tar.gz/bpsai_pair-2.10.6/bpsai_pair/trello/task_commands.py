"""
Trello-backed task commands - Hub file.

This module registers all ttask commands by importing from focused modules:
- task_lifecycle: start, done, block
- task_display: list, show
- task_operations: move, comment, check, uncheck
"""
import typer

# Create the app
app = typer.Typer(name="ttask", help="Trello task commands")

# Import command functions from focused modules
from .task_lifecycle import task_start, task_done, task_block
from .task_display import task_list, task_show
from .task_operations import task_move, task_comment, check_item, uncheck_item

# Register commands
app.command("list")(task_list)
app.command("show")(task_show)
app.command("start")(task_start)
app.command("done")(task_done)
app.command("block")(task_block)
app.command("move")(task_move)
app.command("comment")(task_comment)
app.command("check")(check_item)
app.command("uncheck")(uncheck_item)

# Re-export for backward compatibility
from .task_helpers import (
    get_board_client,
    format_card_id,
    log_activity,
    get_unchecked_ac_items,
    log_bypass,
    get_task_id_from_card,
    update_local_task_status,
    run_completion_hooks,
    update_plan_status_if_needed,
    check_task_budget,
    auto_check_acceptance_criteria,
    AGENT_TYPE,
    console,
)

# Re-export private functions with original names for backward compatibility
_get_unchecked_ac_items = get_unchecked_ac_items
_log_bypass = log_bypass
_get_task_id_from_card = get_task_id_from_card
_update_local_task_status = update_local_task_status
_run_completion_hooks = run_completion_hooks
_update_plan_status_if_needed = update_plan_status_if_needed
_check_task_budget = check_task_budget
_auto_check_acceptance_criteria = auto_check_acceptance_criteria
