"""Trello custom field discovery and validation.

This module provides utilities for fetching custom field definitions from
Trello boards and validating field values before setting them. This prevents
"Option not found" errors and provides better error messages.
"""

from typing import Any, Optional
import json
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def fetch_board_custom_fields(board_id: str, client: Any) -> dict[str, dict]:
    """
    Fetch all custom field definitions from a Trello board.

    Args:
        board_id: Trello board ID
        client: TrelloService instance with board already set

    Returns:
        Dict mapping field name -> {id, type, options (if dropdown)}

    Example:
        {
            "Project": {
                "id": "abc123",
                "type": "list",  # dropdown
                "options": {
                    "PairCoder": "option_id_1",
                    "Aurora": "option_id_2",
                    ...
                }
            },
            "Effort": {
                "id": "def456",
                "type": "list",
                "options": {"S": "...", "M": "...", "L": "..."}
            },
            "Deployment Tag": {
                "id": "ghi789",
                "type": "text",
                "options": None
            }
        }
    """
    fields = {}

    try:
        custom_field_defs = client.get_custom_fields()

        for field in custom_field_defs:
            field_data = {
                "id": field.id,
                "type": field.field_type,
                "options": None
            }

            # For dropdown (list) fields, map option text -> option ID
            if field.field_type == "list" and field.options:
                # field.options is already {id: text}, we want {text: id}
                field_data["options"] = {
                    text: opt_id
                    for opt_id, text in field.options.items()
                }

            fields[field.name] = field_data

    except Exception as e:
        logger.warning(f"Failed to fetch custom fields for board {board_id}: {e}")

    return fields


def validate_field_value(
    field_name: str,
    value: str,
    board_fields: dict[str, dict]
) -> tuple[bool, str | None, str | None]:
    """
    Validate a custom field value against board's actual options.

    Args:
        field_name: Name of the custom field
        value: Value to set
        board_fields: Board's custom field definitions from fetch_board_custom_fields()

    Returns:
        (is_valid, option_id, error_message)

    Example:
        validate_field_value("Stack", "CLI", board_fields)
        # Returns: (False, None, "Invalid value 'CLI' for Stack. Valid options: React, Flask, Worker/Function, Infra, Collection")

        validate_field_value("Stack", "Worker/Function", board_fields)
        # Returns: (True, "option_abc123", None)
    """
    if field_name not in board_fields:
        return (False, None, f"Custom field '{field_name}' not found on board")

    field = board_fields[field_name]

    # Text fields accept any value
    if field["type"] == "text":
        return (True, None, None)

    # Number fields accept numeric values
    if field["type"] == "number":
        try:
            float(value)
            return (True, None, None)
        except (ValueError, TypeError):
            return (False, None, f"Field '{field_name}' requires a numeric value, got '{value}'")

    # Checkbox fields
    if field["type"] == "checkbox":
        if str(value).lower() in ("true", "false", "yes", "no", "1", "0"):
            return (True, None, None)
        return (False, None, f"Checkbox field '{field_name}' requires true/false value, got '{value}'")

    # Date fields - basic validation
    if field["type"] == "date":
        # Accept ISO format dates
        return (True, None, None)

    # Dropdown (list) fields must match an option
    if field["type"] == "list":
        if not field["options"]:
            return (False, None, f"Field '{field_name}' has no options configured")

        # Exact match
        if value in field["options"]:
            return (True, field["options"][value], None)

        # Case-insensitive match
        for opt_name, opt_id in field["options"].items():
            if opt_name.lower() == value.lower():
                return (True, opt_id, None)

        # No match - return error with valid options
        valid_options = ", ".join(sorted(field["options"].keys()))
        return (False, None, f"Invalid value '{value}' for {field_name}. Valid options: {valid_options}")

    # Unknown field type - allow it
    return (True, None, None)


def get_cached_board_fields(
    board_id: str,
    client: Any,
    force_refresh: bool = False,
    cache_dir: Optional[Path] = None
) -> dict[str, dict]:
    """
    Get board custom fields, using cache if available.

    Args:
        board_id: Trello board ID
        client: TrelloService instance
        force_refresh: Force refresh from API even if cache is valid
        cache_dir: Directory for cache files (default: .paircoder/cache)

    Returns:
        Dict mapping field names to field definitions

    Cache location: .paircoder/cache/trello_fields_{board_id}.json
    Cache TTL: 1 hour
    """
    if cache_dir is None:
        cache_dir = Path(".paircoder/cache")

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"trello_fields_{board_id}.json"

    # Check cache
    if not force_refresh and cache_file.exists():
        try:
            cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
            cache_age = time.time() - cache_data.get("timestamp", 0)
            if cache_age < 3600:  # 1 hour TTL
                logger.debug(f"Using cached custom fields for board {board_id} (age: {cache_age:.0f}s)")
                return cache_data["fields"]
        except (json.JSONDecodeError, KeyError) as e:
            logger.debug(f"Cache read error, will refresh: {e}")

    # Fetch fresh
    logger.debug(f"Fetching fresh custom fields for board {board_id}")
    fields = fetch_board_custom_fields(board_id, client)

    # Save to cache
    try:
        cache_file.write_text(json.dumps({
            "timestamp": time.time(),
            "board_id": board_id,
            "fields": fields
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Failed to write cache: {e}")

    return fields


# ==================== Field Mapping with Fallbacks ====================


# Default mappings for common aliases
DEFAULT_STACK_MAPPINGS: dict[str, str] = {
    "cli": "Worker/Function",
    "python": "Flask",
    "backend": "Flask",
    "api": "Flask",
    "frontend": "React",
    "ui": "React",
    "worker": "Worker/Function",
    "function": "Worker/Function",
    "docs": "Collection",
    "documentation": "Collection",
    "devops": "Infra",
    "ci": "Infra",
    "cd": "Infra",
    "infrastructure": "Infra",
}

DEFAULT_STATUS_MAPPINGS: dict[str, str] = {
    "pending": "Planning",
    "ready": "Enqueued",
    "in_progress": "In progress",
    "review": "Testing",
    "done": "Done",
    "blocked": "Blocked",
    "todo": "Planning",
    "to do": "Planning",
    "in-progress": "In progress",
    "in progress": "In progress",
}


def map_value_to_option(
    field_name: str,
    value: str,
    board_fields: dict[str, dict],
    mappings: dict[str, str] | None = None
) -> tuple[str | None, str | None]:
    """
    Map a value to a valid board option, using mappings if provided.

    Args:
        field_name: Name of the custom field
        value: Value to map (might not be exact match)
        board_fields: Board's custom field definitions
        mappings: Optional dict of aliases -> valid values

    Returns:
        (mapped_value, option_id) or (None, None) if no match

    Example:
        # With mapping: {"cli": "Worker/Function", "python": "Flask"}
        map_value_to_option("Stack", "cli", board_fields, mappings)
        # Returns: ("Worker/Function", "option_id_xyz")
    """
    if field_name not in board_fields:
        return (None, None)

    field = board_fields[field_name]

    # Non-list fields don't need mapping
    if field["type"] != "list" or not field["options"]:
        return (value, None)

    # Direct match
    if value in field["options"]:
        return (value, field["options"][value])

    # Try mapping
    if mappings:
        value_lower = value.lower()
        if value_lower in mappings:
            mapped = mappings[value_lower]
            if mapped in field["options"]:
                return (mapped, field["options"][mapped])

    # Case-insensitive match
    for opt_name, opt_id in field["options"].items():
        if opt_name.lower() == value.lower():
            return (opt_name, opt_id)

    return (None, None)


def get_default_mappings_for_field(field_name: str) -> dict[str, str] | None:
    """Get default value mappings for common field names.

    Args:
        field_name: Name of the custom field (case-insensitive)

    Returns:
        Dict of value aliases -> valid option names, or None
    """
    field_lower = field_name.lower()

    if field_lower == "stack":
        return DEFAULT_STACK_MAPPINGS
    elif field_lower == "status":
        return DEFAULT_STATUS_MAPPINGS

    return None


class FieldValidator:
    """Validates and transforms field values for a Trello board.

    This class provides a high-level interface for validating field values
    and applying mappings before setting them on cards.
    """

    def __init__(
        self,
        board_id: str,
        client: Any,
        use_cache: bool = True,
        custom_mappings: dict[str, dict[str, str]] | None = None
    ):
        """Initialize the field validator.

        Args:
            board_id: Trello board ID
            client: TrelloService instance
            use_cache: Whether to use cached field definitions
            custom_mappings: Custom value mappings per field
        """
        self.board_id = board_id
        self.client = client
        self.custom_mappings = custom_mappings or {}

        # Load field definitions
        if use_cache:
            self.board_fields = get_cached_board_fields(board_id, client)
        else:
            self.board_fields = fetch_board_custom_fields(board_id, client)

    def refresh_fields(self) -> None:
        """Force refresh field definitions from the API."""
        self.board_fields = get_cached_board_fields(
            self.board_id, self.client, force_refresh=True
        )

    def validate(self, field_name: str, value: str) -> tuple[bool, str | None, str | None]:
        """Validate a field value.

        Args:
            field_name: Name of the custom field
            value: Value to validate

        Returns:
            (is_valid, option_id, error_message)
        """
        return validate_field_value(field_name, value, self.board_fields)

    def map_and_validate(
        self,
        field_name: str,
        value: str,
        mappings: dict[str, str] | None = None
    ) -> tuple[bool, str | None, str | None, str | None]:
        """Map and validate a field value."""

        if field_name not in self.board_fields:
            return (False, None, None, f"Field '{field_name}' not found on board")

        field = self.board_fields[field_name]

        # For list/dropdown fields, try mapping first
        if field["type"] == "list":
            mapped, option_id = map_value_to_option(
                field_name, value, self.board_fields, mappings
            )
            if mapped:
                return (True, mapped, option_id, None)
            # Fall through to validate_field_value for error message

        # Validate all field types (including non-list)
        is_valid, option_id, error = validate_field_value(
            field_name, value, self.board_fields
        )

        return (is_valid, value if is_valid else None, option_id, error)

    def get_valid_options(self, field_name: str) -> list[str] | None:
        """Get valid options for a dropdown field.

        Args:
            field_name: Name of the custom field

        Returns:
            List of valid option names, or None if not a dropdown
        """
        if field_name not in self.board_fields:
            return None

        field = self.board_fields[field_name]
        if field["type"] != "list" or not field["options"]:
            return None

        return sorted(field["options"].keys())

    def list_fields(self) -> dict[str, dict]:
        """Get all field definitions.

        Returns:
            Dict mapping field names to field definitions
        """
        return self.board_fields
