"""
Custom field operations for Trello sync.

This module contains:
- TaskSyncConfig for configuring field mappings
- Label and stack inference functions
- Custom field validation and mapping
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging

from .client import EffortMapping
from .sync_helpers import (
    TASK_STATUS_TO_TRELLO_STATUS,
    STACK_KEYWORDS,
    LABEL_TO_STACK_MAPPING,
)

logger = logging.getLogger(__name__)


@dataclass
class TaskSyncConfig:
    """Configuration for syncing tasks to Trello."""
    # Custom field mappings
    project_field: str = "Project"
    stack_field: str = "Stack"
    status_field: str = "Status"
    effort_field: str = "Effort"
    repo_url_field: str = "Repo URL"
    deployment_tag_field: str = "Deployment Tag"

    # Default values for custom fields
    default_project: Optional[str] = None  # e.g., "PairCoder"
    default_stack: Optional[str] = None  # e.g., "Worker/Function"
    default_repo_url: Optional[str] = None  # e.g., "https://github.com/org/repo"

    # Effort mapping ranges
    effort_mapping: EffortMapping = field(default_factory=EffortMapping)

    # Status mapping (task status -> Trello Status dropdown value)
    status_mapping: Dict[str, str] = field(default_factory=lambda: TASK_STATUS_TO_TRELLO_STATUS.copy())

    # Whether to create missing labels
    create_missing_labels: bool = True

    # Default list for new cards (Intake/Backlog for Butler workflow)
    default_list: str = "Intake/Backlog"

    # Card description template (None uses default BPS template)
    card_template: Optional[str] = None

    # Whether to preserve manually edited card descriptions
    preserve_manual_edits: bool = True

    # Whether to use Butler workflow (set Status field instead of moving cards)
    use_butler_workflow: bool = True

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "TaskSyncConfig":
        """Create TaskSyncConfig from a config dictionary.

        Expected config structure (from config.yaml):
        ```yaml
        trello:
          sync:
            custom_fields:
              project: "Project"
              stack: "Stack"
              status: "Status"
              effort: "Effort"
            effort_mapping:
              S: [0, 25]
              M: [26, 50]
              L: [51, 100]
            default_list: "Backlog"
            create_missing_labels: true
            preserve_manual_edits: true
        ```

        Args:
            config: Configuration dictionary (usually from config.yaml's trello.sync section)

        Returns:
            Configured TaskSyncConfig instance
        """
        sync_config = config.get("sync", {})
        custom_fields = sync_config.get("custom_fields", {})

        # Parse effort mapping if provided
        effort_config = sync_config.get("effort_mapping", {})
        if effort_config:
            effort_mapping = EffortMapping(
                small=(effort_config.get("S", [0, 25])[0], effort_config.get("S", [0, 25])[1]),
                medium=(effort_config.get("M", [26, 50])[0], effort_config.get("M", [26, 50])[1]),
                large=(effort_config.get("L", [51, 100])[0], effort_config.get("L", [51, 100])[1]),
            )
        else:
            effort_mapping = EffortMapping()

        # Parse status mapping if provided
        status_config = sync_config.get("status_mapping", {})
        if status_config:
            status_mapping = status_config.copy()
        else:
            status_mapping = TASK_STATUS_TO_TRELLO_STATUS.copy()

        # Get default values from config (trello.defaults section)
        defaults = config.get("defaults", {})

        return cls(
            project_field=custom_fields.get("project", "Project"),
            stack_field=custom_fields.get("stack", "Stack"),
            status_field=custom_fields.get("status", "Status"),
            effort_field=custom_fields.get("effort", "Effort"),
            repo_url_field=custom_fields.get("repo_url", "Repo URL"),
            deployment_tag_field=custom_fields.get("deployment_tag", "Deployment Tag"),
            default_project=defaults.get("project"),  # e.g., "PairCoder"
            default_stack=defaults.get("stack"),  # e.g., "Worker/Function"
            default_repo_url=defaults.get("repo_url"),  # e.g., "https://github.com/org/repo"
            effort_mapping=effort_mapping,
            status_mapping=status_mapping,
            create_missing_labels=sync_config.get("create_missing_labels", True),
            default_list=sync_config.get("default_list", "Intake/Backlog"),
            card_template=sync_config.get("card_template"),
            preserve_manual_edits=sync_config.get("preserve_manual_edits", True),
            use_butler_workflow=sync_config.get("use_butler_workflow", True),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to config dictionary format.

        Returns:
            Dictionary suitable for saving to config.yaml
        """
        result = {
            "sync": {
                "custom_fields": {
                    "project": self.project_field,
                    "stack": self.stack_field,
                    "status": self.status_field,
                    "effort": self.effort_field,
                    "repo_url": self.repo_url_field,
                    "deployment_tag": self.deployment_tag_field,
                },
                "effort_mapping": {
                    "S": list(self.effort_mapping.small),
                    "M": list(self.effort_mapping.medium),
                    "L": list(self.effort_mapping.large),
                },
                "status_mapping": self.status_mapping.copy(),
                "default_list": self.default_list,
                "create_missing_labels": self.create_missing_labels,
                "preserve_manual_edits": self.preserve_manual_edits,
                "use_butler_workflow": self.use_butler_workflow,
            }
        }
        # Add defaults section if any defaults are set
        if self.default_project or self.default_stack or self.default_repo_url:
            result["defaults"] = {}
            if self.default_project:
                result["defaults"]["project"] = self.default_project
            if self.default_stack:
                result["defaults"]["stack"] = self.default_stack
            if self.default_repo_url:
                result["defaults"]["repo_url"] = self.default_repo_url
        return result

    def get_trello_status(self, task_status: str) -> str:
        """Map task status to Trello Status custom field value.

        Args:
            task_status: Local task status (e.g., 'pending', 'in_progress')

        Returns:
            Trello Status dropdown value (e.g., 'Enqueued', 'In Progress')
        """
        return self.status_mapping.get(task_status, task_status.replace('_', ' ').title())


def infer_label(task: Any) -> Optional[str]:
    """Infer label category from task title and tags.

    Args:
        task: Task data object with tags and title attributes

    Returns:
        Label name (e.g., "Frontend", "Documentation") or None
    """
    # Check tags first
    for tag in task.tags:
        tag_lower = tag.lower()
        for label, keywords in STACK_KEYWORDS.items():
            if tag_lower in keywords or any(kw in tag_lower for kw in keywords):
                return label

    # Check title
    title_lower = task.title.lower()
    for label, keywords in STACK_KEYWORDS.items():
        if any(kw in title_lower for kw in keywords):
            return label

    return None


def label_to_stack(label: Optional[str]) -> Optional[str]:
    """Convert an inferred label to a valid Stack dropdown value.

    Args:
        label: Inferred label name (e.g., "Documentation")

    Returns:
        Valid Stack dropdown value (e.g., "Collection") or None
    """
    if not label:
        return None
    return LABEL_TO_STACK_MAPPING.get(label)


def infer_stack(task: Any) -> Optional[str]:
    """Infer valid Stack dropdown value from task.

    Args:
        task: Task data object with tags and title attributes

    Returns:
        Valid Stack dropdown value or None
    """
    label = infer_label(task)
    return label_to_stack(label)


def validate_and_map_custom_fields(
    custom_fields: Dict[str, str],
    field_validator: Optional[Any]
) -> Dict[str, str]:
    """Validate and map custom field values before setting them.

    This function:
    1. Validates each field value against the board's actual options
    2. Maps aliases (e.g., 'cli' -> 'Worker/Function') to valid values
    3. Logs warnings for invalid values that will be skipped

    Args:
        custom_fields: Dict of field_name -> value to validate
        field_validator: FieldValidator instance or None

    Returns:
        Dict of validated field_name -> value (invalid fields removed)
    """
    if not field_validator:
        logger.warning("No field validator available, skipping validation")
        return custom_fields

    validated = {}
    for field_name, value in custom_fields.items():
        is_valid, mapped_value, option_id, error = field_validator.map_and_validate(
            field_name, value
        )
        if error:
            logger.warning(f"Skipping invalid field: {error}")
        elif mapped_value is not None:
            validated[field_name] = mapped_value
            if mapped_value != value:
                logger.debug(f"Mapped {field_name}: '{value}' -> '{mapped_value}'")
        else:
            # For non-dropdown fields, keep original value
            validated[field_name] = value

    return validated
