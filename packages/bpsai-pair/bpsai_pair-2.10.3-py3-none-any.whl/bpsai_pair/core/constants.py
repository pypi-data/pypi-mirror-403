"""
Central constants for PairCoder CLI.

This module contains shared constants used across the CLI,
particularly task ID patterns for consistent validation.
"""
import re

# Task ID pattern supporting multiple formats:
# - TASK-XXX: Legacy format (e.g., TASK-142)
# - T{sprint}.{seq}: Sprint tasks (e.g., T18.1, T18.12)
# - REL-{sprint}-{seq}: Release tasks (e.g., REL-18-01)
# - BUG-XXX: Bug fixes (e.g., BUG-005)
TASK_ID_PATTERN = r"(TASK-\d+|T\d+\.\d+|REL-\d+-\d+|BUG-\d+)"

# Compiled regex for performance
TASK_ID_REGEX = re.compile(TASK_ID_PATTERN, re.IGNORECASE)

# Pattern for matching task IDs in titles like "[TASK-001] Title" or "[T18.1] Title"
TASK_ID_IN_TITLE_PATTERN = r"\[?" + TASK_ID_PATTERN[1:-1] + r"\]?"  # Remove outer parens

# Glob patterns for finding task files
TASK_FILE_GLOBS = [
    "TASK-*.task.md",
    "T*.task.md",
    "REL-*.task.md",
    "BUG-*.task.md",
]


def is_valid_task_id(task_id: str) -> bool:
    """Check if a string is a valid task ID.

    Args:
        task_id: String to check

    Returns:
        True if valid task ID format
    """
    return bool(TASK_ID_REGEX.fullmatch(task_id))


def extract_task_id(text: str) -> str | None:
    """Extract task ID from text.

    Args:
        text: Text potentially containing a task ID

    Returns:
        Task ID or None if not found
    """
    match = TASK_ID_REGEX.search(text)
    return match.group(1).upper() if match else None


def extract_task_id_from_card_name(card_name: str) -> str | None:
    """Extract task ID from Trello card name like '[TASK-066] Title' or '[T18.1] Title'.

    Args:
        card_name: Card name with potential task ID prefix

    Returns:
        Task ID or None if not found
    """
    if card_name.startswith("[") and "]" in card_name:
        potential_id = card_name[1:card_name.index("]")]
        if is_valid_task_id(potential_id):
            return potential_id
    return None
