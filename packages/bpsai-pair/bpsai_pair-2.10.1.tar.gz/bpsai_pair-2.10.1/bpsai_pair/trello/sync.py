"""
Trello sync module for syncing tasks to Trello cards with custom fields.

This module serves as a coordinator, delegating to specialized modules:
- sync_helpers: Constants and utility functions
- sync_fields: Custom field configuration and operations
- sync_cards: Card creation and update operations
- sync_checklists: Checklist synchronization
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import logging
import re

from .client import TrelloService
from .fields import FieldValidator
from .templates import should_preserve_description
from ..core.constants import extract_task_id_from_card_name

# Re-export from sync_helpers for backward compatibility
from .sync_helpers import (
    BPS_LABELS,
    TASK_STATUS_TO_TRELLO_STATUS,
    TRELLO_STATUS_TO_TASK_STATUS,
    STACK_KEYWORDS,
    LABEL_TO_STACK_MAPPING,
    LIST_TO_STATUS,
    DueDateConfig,
    calculate_due_date_from_effort,
    normalize_list_name as _normalize_list_name,
    get_status_for_list_flexible as _get_status_for_list_flexible,
)

# Re-export from sync_fields for backward compatibility
from .sync_fields import (
    TaskSyncConfig,
    infer_label as _infer_label,
    infer_stack as _infer_stack,
    label_to_stack as _label_to_stack,
    validate_and_map_custom_fields as _validate_and_map_custom_fields,
)

# Re-export from sync_cards for backward compatibility
from .sync_cards import (
    build_card_description as _build_card_description,
    should_update_description as _should_update_description,
    create_card as _create_card,
    update_card as _update_card,
)

# Re-export from sync_checklists for backward compatibility
from .sync_checklists import (
    sync_checklist as _sync_checklist,
    sync_checklist_to_task as _sync_checklist_to_task,
)

logger = logging.getLogger(__name__)


@dataclass
class TaskData:
    """Task data for syncing to Trello."""
    id: str
    title: str
    description: str = ""
    status: str = "pending"
    priority: str = "P1"
    complexity: int = 50
    tags: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    checked_criteria: List[str] = field(default_factory=list)
    plan_title: Optional[str] = None
    due_date: Optional[Any] = None

    @classmethod
    def from_task(cls, task: Any) -> "TaskData":
        """Create TaskData from a Task object."""
        acceptance_criteria = []
        checked_criteria = []
        if hasattr(task, 'body') and task.body:
            for line in task.body.split('\n'):
                line = line.strip()
                if line.startswith('- [x]') or line.startswith('- [X]'):
                    item = re.sub(r'^- \[[xX]\]\s*', '', line)
                    acceptance_criteria.append(item)
                    checked_criteria.append(item)
                elif line.startswith('- [ ]'):
                    item = re.sub(r'^- \[ \]\s*', '', line)
                    acceptance_criteria.append(item)

        return cls(
            id=task.id,
            title=task.title,
            description=getattr(task, 'body', '') or '',
            status=task.status,
            priority=getattr(task, 'priority', 'P1'),
            complexity=getattr(task, 'complexity', 50),
            tags=getattr(task, 'tags', []) or [],
            acceptance_criteria=acceptance_criteria,
            checked_criteria=checked_criteria,
            plan_title=getattr(task, 'plan', None),
            due_date=getattr(task, 'due_date', None),
        )


class TrelloSyncManager:
    """Manages syncing tasks to Trello with custom fields."""

    def __init__(self, service: TrelloService, config: Optional[TaskSyncConfig] = None):
        """Initialize sync manager.

        Args:
            service: Configured TrelloService
            config: Sync configuration (uses defaults if not provided)
        """
        self.service = service
        self.config = config or TaskSyncConfig()
        self._field_validator: Optional[FieldValidator] = None

    @property
    def field_validator(self) -> Optional[FieldValidator]:
        """Lazy-load field validator for the board."""
        if self._field_validator is None:
            try:
                if self.service.board:
                    self._field_validator = FieldValidator(
                        self.service.board.id,
                        self.service,
                        use_cache=True
                    )
            except (AttributeError, TypeError):
                pass
        return self._field_validator

    def validate_and_map_custom_fields(
        self,
        custom_fields: Dict[str, str]
    ) -> Dict[str, str]:
        """Validate and map custom field values before setting them."""
        return _validate_and_map_custom_fields(custom_fields, self.field_validator)

    def infer_label(self, task: TaskData) -> Optional[str]:
        """Infer label category from task title and tags."""
        return _infer_label(task)

    def label_to_stack(self, label: Optional[str]) -> Optional[str]:
        """Convert an inferred label to a valid Stack dropdown value."""
        return _label_to_stack(label)

    def infer_stack(self, task: TaskData) -> Optional[str]:
        """Infer valid Stack dropdown value from task."""
        return _infer_stack(task)

    def build_card_description(self, task: TaskData) -> str:
        """Build BPS-formatted card description."""
        return _build_card_description(task, self.config.card_template)

    def should_update_description(self, existing_desc: str) -> bool:
        """Check if we should update an existing card description."""
        return _should_update_description(existing_desc, self.config.preserve_manual_edits)

    def ensure_bps_labels(self) -> Dict[str, bool]:
        """Ensure all BPS labels exist on the board."""
        results = {}
        if not self.config.create_missing_labels:
            return results
        for label_name, color in BPS_LABELS.items():
            label = self.service.ensure_label_exists(label_name, color)
            results[label_name] = label is not None
        return results

    def sync_task_to_card(
        self,
        task: TaskData,
        list_name: Optional[str] = None,
        update_existing: bool = True
    ) -> Optional[Any]:
        """Sync a task to a Trello card."""
        target_list = list_name or self.config.default_list
        existing_card, existing_list = self.service.find_card_with_prefix(task.id)

        if existing_card:
            if not update_existing:
                logger.info(f"Card for {task.id} already exists, skipping")
                return existing_card
            return self._update_card(existing_card, task)
        else:
            return self._create_card(task, target_list)

    def _create_card(self, task: TaskData, list_name: str) -> Optional[Any]:
        """Create a new Trello card for a task."""
        return _create_card(self.service, task, list_name, self.config, self.field_validator)

    def _update_card(self, card: Any, task: TaskData) -> Any:
        """Update an existing card with task data."""
        return _update_card(self.service, card, task, self.config, self.field_validator)

    def _sync_checklist(
        self,
        card: Any,
        acceptance_criteria: List[str],
        checked_criteria: Optional[List[str]] = None,
        checklist_name: str = "Acceptance Criteria"
    ) -> Optional[Dict[str, Any]]:
        """Sync acceptance criteria to a card checklist."""
        return _sync_checklist(
            self.service, card, acceptance_criteria, checked_criteria, checklist_name
        )

    def sync_tasks(
        self,
        tasks: List[TaskData],
        list_name: Optional[str] = None,
        update_existing: bool = True
    ) -> Dict[str, Optional[Any]]:
        """Sync multiple tasks to Trello cards."""
        self.ensure_bps_labels()
        results = {}
        for task in tasks:
            card = self.sync_task_to_card(task, list_name, update_existing)
            results[task.id] = card
        return results


def create_sync_manager(
    api_key: str,
    token: str,
    board_id: str,
    config: Optional[TaskSyncConfig] = None
) -> TrelloSyncManager:
    """Create a configured TrelloSyncManager."""
    service = TrelloService(api_key, token)
    service.set_board(board_id)
    return TrelloSyncManager(service, config)


@dataclass
class SyncConflict:
    """Represents a sync conflict between Trello and local."""
    task_id: str
    field: str
    local_value: Any
    trello_value: Any
    resolution: str = "trello_wins"


@dataclass
class SyncResult:
    """Result of a sync operation."""
    task_id: str
    action: str
    changes: Dict[str, Any] = field(default_factory=dict)
    conflicts: List[SyncConflict] = field(default_factory=list)
    error: Optional[str] = None


class TrelloToLocalSync:
    """Syncs changes from Trello back to local task files."""

    def __init__(self, service: TrelloService, tasks_dir: Path):
        """Initialize the reverse sync manager."""
        self.service = service
        self.tasks_dir = tasks_dir
        self._task_parser = None

    @property
    def task_parser(self):
        """Lazy load TaskParser."""
        if self._task_parser is None:
            from ..planning.parser import TaskParser
            self._task_parser = TaskParser(self.tasks_dir)
        return self._task_parser

    def extract_task_id(self, card_name: str) -> Optional[str]:
        """Extract task ID from card name."""
        return extract_task_id_from_card_name(card_name)

    def get_list_status(self, list_name: str) -> Optional[str]:
        """Map Trello list name to task status."""
        return _get_status_for_list_flexible(list_name)

    def _sync_checklist_to_task(
        self,
        card: Any,
        task: Any,
        checklist_name: str = "Acceptance Criteria"
    ) -> Optional[Dict[str, Any]]:
        """Sync checklist state from Trello card back to task body."""
        return _sync_checklist_to_task(self.service, card, task, checklist_name)

    def sync_card_to_task(self, card: Any, detect_conflicts: bool = True) -> SyncResult:
        """Sync a single Trello card back to local task."""
        card_name = card.name
        task_id = self.extract_task_id(card_name)

        if not task_id:
            return SyncResult(
                task_id="unknown",
                action="skipped",
                error=f"Could not extract task ID from: {card_name}"
            )

        task = self.task_parser.get_task_by_id(task_id)
        if not task:
            return SyncResult(
                task_id=task_id,
                action="skipped",
                error=f"Task not found locally: {task_id}"
            )

        changes = {}
        conflicts = []

        list_name = card.get_list().name if hasattr(card, 'get_list') else None
        if list_name:
            new_status = self.get_list_status(list_name)
            if new_status:
                old_status = task.status.value if hasattr(task.status, 'value') else str(task.status)
                if old_status != new_status:
                    if detect_conflicts:
                        conflicts.append(SyncConflict(
                            task_id=task_id,
                            field="status",
                            local_value=old_status,
                            trello_value=new_status,
                            resolution="trello_wins"
                        ))
                    changes["status"] = {"from": old_status, "to": new_status}
                    from ..planning.models import TaskStatus
                    task.status = TaskStatus(new_status)

        if hasattr(card, 'due_date') and card.due_date:
            card_due = card.due_date
            task_due = getattr(task, 'due_date', None)
            if card_due != task_due:
                changes["due_date"] = {"from": task_due, "to": card_due}
                if hasattr(task, 'due_date'):
                    task.due_date = card_due

        checklist_changes = self._sync_checklist_to_task(card, task)
        if checklist_changes:
            changes["checklist"] = checklist_changes

        if changes:
            try:
                self.task_parser.save(task)
                return SyncResult(
                    task_id=task_id,
                    action="updated",
                    changes=changes,
                    conflicts=conflicts
                )
            except Exception as e:
                return SyncResult(
                    task_id=task_id,
                    action="error",
                    error=str(e)
                )

        return SyncResult(
            task_id=task_id,
            action="skipped",
            changes={}
        )

    def sync_all_cards(self, list_filter: Optional[List[str]] = None) -> List[SyncResult]:
        """Sync all cards from Trello board to local tasks."""
        results = []
        try:
            cards = self.service.board.get_cards()
        except Exception as e:
            logger.error(f"Failed to get cards from board: {e}")
            return [SyncResult(task_id="board", action="error", error=str(e))]

        for card in cards:
            if list_filter:
                try:
                    card_list = card.get_list()
                    if card_list.name not in list_filter:
                        continue
                except Exception:
                    continue

            task_id = self.extract_task_id(card.name)
            if not task_id:
                continue

            result = self.sync_card_to_task(card)
            results.append(result)

        return results

    def get_sync_preview(self) -> List[Dict[str, Any]]:
        """Preview what would be synced without making changes."""
        preview = []
        try:
            cards = self.service.board.get_cards()
        except Exception as e:
            logger.error(f"Failed to get cards: {e}")
            return []

        for card in cards:
            task_id = self.extract_task_id(card.name)
            if not task_id:
                continue

            task = self.task_parser.get_task_by_id(task_id)
            if not task:
                preview.append({
                    "task_id": task_id,
                    "card_name": card.name,
                    "action": "skip",
                    "reason": "Task not found locally"
                })
                continue

            try:
                list_name = card.get_list().name
                trello_status = self.get_list_status(list_name)
                local_status = task.status.value if hasattr(task.status, 'value') else str(task.status)

                if trello_status and trello_status != local_status:
                    preview.append({
                        "task_id": task_id,
                        "card_name": card.name,
                        "action": "update",
                        "field": "status",
                        "from": local_status,
                        "to": trello_status
                    })
                else:
                    preview.append({
                        "task_id": task_id,
                        "card_name": card.name,
                        "action": "skip",
                        "reason": "No changes"
                    })
            except Exception as e:
                preview.append({
                    "task_id": task_id,
                    "card_name": card.name,
                    "action": "error",
                    "reason": str(e)
                })

        return preview


def create_reverse_sync(
    api_key: str,
    token: str,
    board_id: str,
    tasks_dir: Path
) -> TrelloToLocalSync:
    """Create a TrelloToLocalSync instance."""
    service = TrelloService(api_key, token)
    service.set_board(board_id)
    return TrelloToLocalSync(service, tasks_dir)
