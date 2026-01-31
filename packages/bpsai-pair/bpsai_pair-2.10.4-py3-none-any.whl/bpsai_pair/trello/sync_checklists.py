"""
Checklist synchronization for Trello sync operations.

This module contains:
- sync_checklist: Sync acceptance criteria to Trello card checklist
- sync_checklist_to_task: Sync checklist state from Trello back to task body
"""
from typing import Dict, List, Optional, Any
import re
import logging

logger = logging.getLogger(__name__)


def sync_checklist(
    service: Any,
    card: Any,
    acceptance_criteria: List[str],
    checked_criteria: Optional[List[str]] = None,
    checklist_name: str = "Acceptance Criteria"
) -> Optional[Dict[str, Any]]:
    """Sync acceptance criteria to a card checklist.

    Args:
        service: TrelloService instance
        card: Trello card object
        acceptance_criteria: List of acceptance criteria strings
        checked_criteria: List of criteria that should be checked
        checklist_name: Name for the checklist

    Returns:
        Checklist dict or None if failed
    """
    if not acceptance_criteria:
        return None

    checked_criteria = checked_criteria or []

    # Use service.ensure_checklist to create or update
    return service.ensure_checklist(
        card=card,
        name=checklist_name,
        items=acceptance_criteria,
        checked_items=checked_criteria
    )


def sync_checklist_to_task(
    service: Any,
    card: Any,
    task: Any,
    checklist_name: str = "Acceptance Criteria"
) -> Optional[Dict[str, Any]]:
    """Sync checklist state from Trello card back to task body.

    Updates checkbox items in the task body based on Trello checklist state.

    Args:
        service: TrelloService instance
        card: Trello card object
        task: Task object
        checklist_name: Name of the checklist to sync

    Returns:
        Dict with changes made, or None if no changes
    """
    # Get the checklist from the card
    checklist = service.get_checklist_by_name(card, checklist_name)
    if not checklist:
        return None

    # Build a map of item name -> checked state
    checklist_state = {}
    for item in checklist.get('items', []):
        item_name = item.get('name', '').strip()
        item_checked = item.get('checked', False)
        checklist_state[item_name] = item_checked

    if not checklist_state:
        return None

    # Get the task body
    body = getattr(task, 'body', '') or ''
    if not body:
        return None

    # Track changes
    changes = {"items_updated": []}
    new_lines = []
    body_changed = False

    for line in body.split('\n'):
        stripped = line.strip()

        # Check if this is a checkbox line
        if stripped.startswith('- [ ]') or stripped.startswith('- [x]') or stripped.startswith('- [X]'):
            # Extract the item text
            item_text = re.sub(r'^- \[[ xX]\]\s*', '', stripped)

            # Check if this item is in our checklist
            if item_text in checklist_state:
                is_checked_in_trello = checklist_state[item_text]
                is_checked_locally = stripped.startswith('- [x]') or stripped.startswith('- [X]')

                if is_checked_in_trello != is_checked_locally:
                    # Update the checkbox state
                    # Preserve original indentation
                    indent = line[:len(line) - len(line.lstrip())]
                    if is_checked_in_trello:
                        new_line = f"{indent}- [x] {item_text}"
                    else:
                        new_line = f"{indent}- [ ] {item_text}"
                    new_lines.append(new_line)
                    changes["items_updated"].append({
                        "item": item_text,
                        "from": "checked" if is_checked_locally else "unchecked",
                        "to": "checked" if is_checked_in_trello else "unchecked"
                    })
                    body_changed = True
                    continue

        new_lines.append(line)

    # Update task body if changed
    if body_changed:
        task.body = '\n'.join(new_lines)
        return changes

    return None
