"""
Card creation and update operations for Trello sync.

This module contains:
- build_card_description: Build BPS-formatted card description
- should_update_description: Check if description should be updated
- create_card: Create a new Trello card for a task
- update_card: Update an existing card with task data
"""
from typing import Any, Optional
import logging

from .templates import CardDescriptionTemplate, should_preserve_description
from .sync_fields import (
    TaskSyncConfig,
    infer_label,
    infer_stack,
    validate_and_map_custom_fields,
)
from .sync_checklists import sync_checklist
from .sync_helpers import (
    BPS_LABELS,
    calculate_due_date_from_effort,
)

logger = logging.getLogger(__name__)


def build_card_description(task: Any, template: Optional[str] = None) -> str:
    """Build BPS-formatted card description.

    Args:
        task: Task data object
        template: Optional custom template string

    Returns:
        Formatted description string
    """
    return CardDescriptionTemplate.from_task_data(task, template=template)


def should_update_description(existing_desc: str, preserve_manual_edits: bool = True) -> bool:
    """Check if we should update an existing card description.

    Args:
        existing_desc: Current card description
        preserve_manual_edits: Whether to preserve manual edits

    Returns:
        True if we should update, False to preserve manual edits
    """
    if not preserve_manual_edits:
        return True

    return not should_preserve_description(existing_desc)


def create_card(
    service: Any,
    task: Any,
    list_name: str,
    config: TaskSyncConfig,
    field_validator: Optional[Any] = None
) -> Optional[Any]:
    """Create a new Trello card for a task.

    Args:
        service: TrelloService instance
        task: Task data object
        list_name: Target list name
        config: TaskSyncConfig instance
        field_validator: Optional FieldValidator for validation

    Returns:
        Created card or None
    """
    # Build card name with task ID prefix
    card_name = f"[{task.id}] {task.title}"
    description = build_card_description(task, config.card_template)

    # Build custom fields
    custom_fields = {}

    # Project field - use config default if set, otherwise plan_title
    project = config.default_project or task.plan_title
    if project:
        custom_fields[config.project_field] = project

    # Stack field - use config default if set, otherwise infer from task
    stack = config.default_stack or infer_stack(task)
    if stack:
        custom_fields[config.stack_field] = stack

    # Status field - use proper mapping for Butler workflow
    custom_fields[config.status_field] = config.get_trello_status(task.status)

    # Repo URL field - use config default if set
    if config.default_repo_url:
        custom_fields[config.repo_url_field] = config.default_repo_url

    # Validate and map custom field values before setting
    validated_fields = validate_and_map_custom_fields(custom_fields, field_validator)

    # Create card
    card = service.create_card_with_custom_fields(
        list_name=list_name,
        name=card_name,
        desc=description,
        custom_fields=validated_fields
    )

    if not card:
        return None

    # Set effort field (separate because it uses complexity mapping)
    service.set_effort_field(card, task.complexity, config.effort_field)

    # Add labels (use infer_label for label names, not Stack dropdown values)
    label = infer_label(task)
    if label:
        service.add_label_to_card(card, label)

    # Add labels from tags
    for tag in task.tags:
        tag_title = tag.title()
        if tag_title in BPS_LABELS:
            service.add_label_to_card(card, tag_title)

    # Create acceptance criteria checklist if task has acceptance criteria
    if task.acceptance_criteria:
        sync_checklist(service, card, task.acceptance_criteria, task.checked_criteria)

    # Set due date - use explicit date if provided, otherwise calculate from effort
    due_date = task.due_date
    if due_date is None:
        # Calculate due date from effort/complexity
        effort = config.effort_mapping.get_effort(task.complexity)
        due_date = calculate_due_date_from_effort(effort)
    service.set_due_date(card, due_date)

    logger.info(f"Created card for {task.id}: {card_name}")
    return card


def update_card(
    service: Any,
    card: Any,
    task: Any,
    config: TaskSyncConfig,
    field_validator: Optional[Any] = None
) -> Any:
    """Update an existing card with task data.

    Args:
        service: TrelloService instance
        card: Existing Trello card
        task: Task data object
        config: TaskSyncConfig instance
        field_validator: Optional FieldValidator for validation

    Returns:
        Updated card
    """
    # Update card title to match task
    expected_name = f"[{task.id}] {task.title}"
    if card.name != expected_name:
        card.set_name(expected_name)
        logger.info(f"Updated card title for {task.id}")

    # Check if we should update the description or preserve manual edits
    existing_desc = getattr(card, 'description', '') or ''
    if should_update_description(existing_desc, config.preserve_manual_edits):
        description = build_card_description(task, config.card_template)
        card.set_description(description)
    else:
        logger.info(f"Preserving manual edits for {task.id}")

    # Update custom fields
    custom_fields = {}

    # Project field - use config default if set, otherwise plan_title
    project = config.default_project or task.plan_title
    if project:
        custom_fields[config.project_field] = project

    # Stack field - use config default if set, otherwise infer from task
    stack = config.default_stack or infer_stack(task)
    if stack:
        custom_fields[config.stack_field] = stack

    # Status field - use proper mapping for Butler workflow
    custom_fields[config.status_field] = config.get_trello_status(task.status)

    # Repo URL field - use config default if set
    if config.default_repo_url:
        custom_fields[config.repo_url_field] = config.default_repo_url

    # Validate and map custom field values before setting
    validated_fields = validate_and_map_custom_fields(custom_fields, field_validator)
    service.set_card_custom_fields(card, validated_fields)
    service.set_effort_field(card, task.complexity, config.effort_field)

    # Add labels (use infer_label for label names, not Stack dropdown values)
    label = infer_label(task)
    if label:
        service.add_label_to_card(card, label)

    for tag in task.tags:
        tag_title = tag.title()
        if tag_title in BPS_LABELS:
            service.add_label_to_card(card, tag_title)

    # Sync acceptance criteria checklist
    if task.acceptance_criteria:
        sync_checklist(service, card, task.acceptance_criteria, task.checked_criteria)

    # Sync due date
    if task.due_date is not None:
        service.set_due_date(card, task.due_date)

    logger.info(f"Updated card for {task.id}")
    return card
