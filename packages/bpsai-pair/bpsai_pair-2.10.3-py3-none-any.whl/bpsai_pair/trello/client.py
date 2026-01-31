"""
Trello client wrapper.
"""
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CustomFieldDefinition:
    """Represents a Trello custom field definition."""
    id: str
    name: str
    field_type: str  # 'text', 'number', 'checkbox', 'list', 'date'
    options: Dict[str, str]  # For list type: option_id -> option_text


@dataclass
class EffortMapping:
    """Maps complexity scores to effort values (S/M/L)."""
    small: tuple = (0, 25)
    medium: tuple = (26, 50)
    large: tuple = (51, 100)

    def get_effort(self, complexity: int) -> str:
        """Convert complexity score to S/M/L effort."""
        if complexity <= self.small[1]:
            return "S"
        elif complexity <= self.medium[1]:
            return "M"
        else:
            return "L"


class TrelloService:
    """Wrapper around the Trello API client."""

    def __init__(self, api_key: str, token: str):
        """Initialize Trello service.

        Args:
            api_key: Trello API key
            token: Trello API token
        """
        try:
            from trello import TrelloClient
            self.client = TrelloClient(api_key=api_key, token=token)
        except ImportError as e:
            raise ImportError(f"Error importing Trello client: {e}")
        self.board = None
        self.lists: Dict[str, Any] = {}

    def healthcheck(self) -> bool:
        """Check if the connection is working.

        Returns:
            True if connection works, False otherwise
        """
        try:
            self.client.list_boards()
            return True
        except Exception as e:
            logger.warning(f"Trello healthcheck failed: {e}")
            return False

    def list_boards(self) -> List[Any]:
        """List all accessible boards.

        Returns:
            List of Trello board objects
        """
        return self.client.list_boards()

    def set_board(self, board_id: str) -> Any:
        """Set the active board.

        Args:
            board_id: Trello board ID

        Returns:
            The board object
        """
        self.board = self.client.get_board(board_id)
        self.lists = {lst.name: lst for lst in self.board.all_lists()}
        return self.board

    def get_board_lists(self) -> Dict[str, Any]:
        """Get all lists on the current board.

        Returns:
            Dict mapping list names to list objects

        Raises:
            ValueError: If no board is set
        """
        if not self.board:
            raise ValueError("Board not set. Call set_board() first.")
        return self.lists

    def get_cards_in_list(self, list_name: str) -> List[Any]:
        """Get all cards in a list.

        Args:
            list_name: Name of the list

        Returns:
            List of card objects
        """
        lst = self.lists.get(list_name)
        if not lst:
            return []
        return lst.list_cards()

    def move_card(self, card: Any, list_name: str) -> None:
        """Move a card to a different list.

        Args:
            card: Card object to move
            list_name: Name of target list (created if doesn't exist)
        """
        target = self.lists.get(list_name)
        if not target:
            target = self.board.add_list(list_name)
            self.lists[list_name] = target
        card.change_list(target.id)

    def add_comment(self, card: Any, comment: str) -> None:
        """Add a comment to a card.

        Args:
            card: Card object
            comment: Comment text
        """
        card.comment(comment)

    def is_card_blocked(self, card: Any) -> bool:
        """Check if a card has unchecked dependencies.

        Args:
            card: Card object

        Returns:
            True if card has unchecked items in 'card dependencies' checklist
        """
        try:
            for checklist in card.checklists:
                if checklist.name.lower() == 'card dependencies':
                    for item in checklist.items:
                        if not item.get('checked', False):
                            return True
        except Exception:
            pass
        return False

    def find_card(self, card_id: str) -> tuple[Optional[Any], Optional[Any]]:
        """Find a card by ID or short ID.

        Args:
            card_id: Card ID, short ID, or TRELLO-<short_id>

        Returns:
            Tuple of (card, list) or (None, None) if not found
        """
        if not self.board:
            return None, None

        # Normalize card_id
        if card_id.startswith("TRELLO-"):
            card_id = card_id[7:]  # Remove prefix

        for lst in self.board.all_lists():
            for card in lst.list_cards():
                if (card.id == card_id or
                    str(card.short_id) == card_id):
                    return card, lst
        return None, None

    def find_card_with_prefix(self, prefix: str) -> tuple[Optional[Any], Optional[Any]]:
        """Find a card by prefix in title (e.g., '[TASK-001]').

        Args:
            prefix: Prefix to search for in card title

        Returns:
            Tuple of (card, list) or (None, None) if not found
        """
        if not self.board:
            return None, None

        # Format prefix with brackets if not already
        search_prefix = prefix if prefix.startswith("[") else f"[{prefix}]"

        for lst in self.board.all_lists():
            for card in lst.list_cards():
                if search_prefix in card.name:
                    return card, lst
        return None, None

    def move_card_by_task_id(self, task_id: str, target_list: str, comment: Optional[str] = None) -> bool:
        """Move a card by task ID to a target list.

        Args:
            task_id: Task ID (e.g., 'TASK-001')
            target_list: Name of target list
            comment: Optional comment to add

        Returns:
            True if card was found and moved
        """
        card, _ = self.find_card_with_prefix(task_id)
        if not card:
            return False

        self.move_card(card, target_list)

        if comment:
            self.add_comment(card, comment)

        return True

    # ========== Board Structure Methods ==========

    def get_board_structure(self) -> Dict[str, Any]:
        """Fetch complete board configuration.

        Discovers and returns all lists, custom field definitions, and labels
        from the current board. This should be called before sync operations
        to ensure we have the correct IDs and names.

        Returns:
            Dict with 'lists', 'custom_fields', and 'labels' mappings

        Raises:
            ValueError: If no board is set
        """
        if not self.board:
            raise ValueError("Board not set. Call set_board() first.")

        # Get lists with exact names
        lists = {lst.name: lst.id for lst in self.board.all_lists()}

        # Get custom field definitions with IDs and options
        custom_fields = {}
        for field in self.get_custom_fields():
            custom_fields[field.name] = {
                "id": field.id,
                "type": field.field_type,
                "options": field.options,
            }

        # Get labels with IDs
        labels = {}
        for lbl in self.get_labels():
            if lbl['name']:  # Skip unnamed labels
                labels[lbl['name']] = lbl['id']

        return {
            "lists": lists,
            "custom_fields": custom_fields,
            "labels": labels,
        }

    # ========== Custom Field Methods ==========

    def get_custom_fields(self) -> List[CustomFieldDefinition]:
        """Get all custom field definitions for the current board.

        Returns:
            List of CustomFieldDefinition objects

        Raises:
            ValueError: If no board is set
        """
        if not self.board:
            raise ValueError("Board not set. Call set_board() first.")

        definitions = self.board.get_custom_field_definitions()
        result = []

        for defn in definitions:
            options = {}
            if defn.field_type == 'list':
                options = defn.list_options

            result.append(CustomFieldDefinition(
                id=defn.id,
                name=defn.name,
                field_type=defn.field_type,
                options=options
            ))

        return result

    def get_custom_field_by_name(self, name: str) -> Optional[CustomFieldDefinition]:
        """Find a custom field by name.

        Args:
            name: Name of the custom field (case-insensitive)

        Returns:
            CustomFieldDefinition or None if not found
        """
        fields = self.get_custom_fields()
        name_lower = name.lower()

        for field in fields:
            if field.name.lower() == name_lower:
                return field

        return None

    def set_custom_field_value(
        self,
        card: Any,
        field: CustomFieldDefinition,
        value: Union[str, int, float, bool]
    ) -> bool:
        """Set a custom field value on a card.

        Args:
            card: Trello card object
            field: Custom field definition
            value: Value to set (type depends on field type)

        Returns:
            True if successful
        """
        try:
            if field.field_type == 'text':
                post_args = {'value': {'text': str(value)}}
            elif field.field_type == 'number':
                post_args = {'value': {'number': str(value)}}
            elif field.field_type == 'checkbox':
                post_args = {'value': {'checked': 'true' if value else 'false'}}
            elif field.field_type == 'list':
                # Find option ID by value text
                option_id = None
                value_str = str(value)
                for opt_id, opt_text in field.options.items():
                    if opt_text.lower() == value_str.lower():
                        option_id = opt_id
                        break

                if not option_id:
                    logger.warning(f"Option '{value}' not found for field '{field.name}'")
                    return False

                post_args = {'idValue': option_id}
            elif field.field_type == 'date':
                # Expect ISO format: YYYY-MM-DDTHH:MM:SS.000Z
                post_args = {'value': {'date': str(value)}}
            else:
                logger.warning(f"Unknown field type: {field.field_type}")
                return False

            self.client.fetch_json(
                f'/card/{card.id}/customField/{field.id}/item',
                http_method='PUT',
                post_args=post_args
            )
            return True

        except Exception as e:
            logger.error(f"Failed to set custom field '{field.name}': {e}")
            return False

    def set_card_status(
        self,
        card: Any,
        status: str,
        status_field_name: str = "Status"
    ) -> bool:
        """Set the Status custom field on a card.

        This triggers Butler automation to move the card to the correct list.
        Instead of moving cards directly, set the Status field and let Butler
        handle the movement based on its automation rules.

        Args:
            card: Trello card object
            status: Status value (e.g., 'Enqueued', 'In Progress', 'Done')
            status_field_name: Name of the status custom field (default: "Status")

        Returns:
            True if successful, False otherwise
        """
        field = self.get_custom_field_by_name(status_field_name)
        if not field:
            logger.warning(f"Status field '{status_field_name}' not found on board")
            return False

        if field.field_type != 'list':
            logger.warning(f"Status field must be a list type, got {field.field_type}")
            return False

        return self.set_custom_field_value(card, field, status)

    def set_card_custom_fields(
        self,
        card: Any,
        field_values: Dict[str, Union[str, int, float, bool]]
    ) -> Dict[str, bool]:
        """Set multiple custom fields on a card.

        Args:
            card: Trello card object
            field_values: Dict mapping field names to values

        Returns:
            Dict mapping field names to success status
        """
        results = {}

        for field_name, value in field_values.items():
            field = self.get_custom_field_by_name(field_name)
            if not field:
                # Only debug log - missing fields are expected on some boards
                logger.debug(f"Custom field '{field_name}' not found on board, skipping")
                results[field_name] = False
                continue

            results[field_name] = self.set_custom_field_value(card, field, value)

        return results

    def set_effort_field(self, card: Any, complexity: int, field_name: str = "Effort") -> bool:
        """Set the Effort custom field based on complexity score.

        Args:
            card: Trello card object
            complexity: Complexity score (0-100)
            field_name: Name of the effort field (default: "Effort")

        Returns:
            True if successful
        """
        field = self.get_custom_field_by_name(field_name)
        if not field:
            logger.warning(f"Effort field '{field_name}' not found on board")
            return False

        # Handle both number and list type effort fields
        if field.field_type == 'number':
            # Pass complexity directly as numeric value
            return self.set_custom_field_value(card, field, complexity)
        elif field.field_type == 'list':
            # Map complexity to S/M/L dropdown option
            effort_mapping = EffortMapping()
            effort = effort_mapping.get_effort(complexity)
            return self.set_custom_field_value(card, field, effort)
        else:
            logger.warning(f"Effort field must be number or list type, got {field.field_type}")
            return False

    def create_card_with_custom_fields(
        self,
        list_name: str,
        name: str,
        desc: str = "",
        custom_fields: Optional[Dict[str, Union[str, int, float, bool]]] = None
    ) -> Optional[Any]:
        """Create a card with custom fields.

        Args:
            list_name: Name of the list to create the card in
            name: Card name/title
            desc: Card description
            custom_fields: Dict mapping field names to values

        Returns:
            Created card object or None if failed
        """
        target_list = self.lists.get(list_name)
        if not target_list:
            logger.error(f"List '{list_name}' not found")
            return None

        try:
            card = target_list.add_card(name=name, desc=desc)

            if custom_fields:
                self.set_card_custom_fields(card, custom_fields)

            return card

        except Exception as e:
            logger.error(f"Failed to create card: {e}")
            return None

    # ========== Label Methods ==========

    def get_labels(self) -> List[Dict[str, str]]:
        """Get all labels on the current board.

        Returns:
            List of label dicts with 'id', 'name', 'color'
        """
        if not self.board:
            raise ValueError("Board not set. Call set_board() first.")

        labels = self.board.get_labels()
        return [
            {'id': lbl.id, 'name': lbl.name, 'color': lbl.color}
            for lbl in labels
        ]

    def get_label_by_name(self, name: str) -> Optional[Dict[str, str]]:
        """Find a label by name.

        Args:
            name: Label name (case-insensitive)

        Returns:
            Label dict or None if not found
        """
        labels = self.get_labels()
        name_lower = name.lower()

        for label in labels:
            if label['name'] and label['name'].lower() == name_lower:
                return label

        return None

    def create_label(self, name: str, color: str) -> Optional[Dict[str, str]]:
        """Create a label on the board.

        Args:
            name: Label name
            color: Color name (green, yellow, orange, red, purple, blue, sky, lime, pink, black)

        Returns:
            Created label dict or None if failed
        """
        if not self.board:
            raise ValueError("Board not set. Call set_board() first.")

        try:
            label = self.board.add_label(name=name, color=color)
            return {'id': label.id, 'name': label.name, 'color': label.color}
        except Exception as e:
            logger.error(f"Failed to create label: {e}")
            return None

    def ensure_label_exists(self, name: str, color: str) -> Optional[Dict[str, str]]:
        """Ensure a label exists, creating it if necessary.

        Args:
            name: Label name
            color: Color to use if creating

        Returns:
            Label dict or None if failed
        """
        existing = self.get_label_by_name(name)
        if existing:
            return existing

        return self.create_label(name, color)

    def add_label_to_card(self, card: Any, label_name: str) -> bool:
        """Add a label to a card by name.

        Args:
            card: Trello card object
            label_name: Name of the label to add

        Returns:
            True if successful
        """
        label = self.get_label_by_name(label_name)
        if not label:
            logger.warning(f"Label '{label_name}' not found")
            return False

        try:
            # Use the direct API call to add label by ID
            # (Card.add_label expects a Label object, but we have a dict)
            card.client.fetch_json(
                f'/cards/{card.id}/idLabels',
                http_method='POST',
                post_args={'value': label['id']}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add label: {e}")
            return False

    # ========== Checklist Methods ==========

    def get_card_checklists(self, card: Any) -> List[Dict[str, Any]]:
        """Get all checklists on a card.

        Args:
            card: Trello card object

        Returns:
            List of checklist dicts with 'id', 'name', 'items'
        """
        try:
            checklists = []
            for cl in card.checklists:
                items = []
                for item in cl.items:
                    items.append({
                        'id': item.get('id'),
                        'name': item.get('name'),
                        'checked': item.get('checked', False),
                        'pos': item.get('pos', 0),
                    })
                checklists.append({
                    'id': cl.id,
                    'name': cl.name,
                    'items': items,
                })
            return checklists
        except Exception as e:
            logger.error(f"Failed to get checklists: {e}")
            return []

    def get_checklist_by_name(self, card: Any, name: str) -> Optional[Dict[str, Any]]:
        """Find a checklist by name on a card.

        Args:
            card: Trello card object
            name: Checklist name to find

        Returns:
            Checklist dict or None if not found
        """
        checklists = self.get_card_checklists(card)
        for cl in checklists:
            if cl['name'].lower() == name.lower():
                return cl
        return None

    def create_checklist(self, card: Any, name: str) -> Optional[Dict[str, Any]]:
        """Create a new checklist on a card.

        Args:
            card: Trello card object
            name: Name for the new checklist

        Returns:
            Checklist dict with 'id', 'name' or None if failed
        """
        try:
            checklist = card.add_checklist(name, [])
            return {
                'id': checklist.id,
                'name': checklist.name,
                'items': [],
            }
        except Exception as e:
            logger.error(f"Failed to create checklist: {e}")
            return None

    def add_checklist_item(
        self,
        card: Any,
        checklist_id: str,
        name: str,
        checked: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Add an item to a checklist.

        Args:
            card: Trello card object
            checklist_id: ID of the checklist
            name: Name/text of the item
            checked: Whether the item is checked

        Returns:
            Item dict with 'id', 'name', 'checked' or None if failed
        """
        try:
            # Use direct API call
            result = self.client.fetch_json(
                f'/checklists/{checklist_id}/checkItems',
                http_method='POST',
                post_args={
                    'name': name,
                    'checked': 'true' if checked else 'false',
                }
            )
            return {
                'id': result.get('id'),
                'name': result.get('name'),
                'checked': result.get('state') == 'complete',
            }
        except Exception as e:
            logger.error(f"Failed to add checklist item: {e}")
            return None

    def update_checklist_item(
        self,
        card: Any,
        checklist_id: str,
        item_id: str,
        checked: Optional[bool] = None,
        name: Optional[str] = None
    ) -> bool:
        """Update a checklist item.

        Args:
            card: Trello card object
            checklist_id: ID of the checklist
            item_id: ID of the item to update
            checked: New checked state (optional)
            name: New name (optional)

        Returns:
            True if successful
        """
        try:
            post_args = {}
            if checked is not None:
                post_args['state'] = 'complete' if checked else 'incomplete'
            if name is not None:
                post_args['name'] = name

            if not post_args:
                return True  # Nothing to update

            self.client.fetch_json(
                f'/cards/{card.id}/checkItem/{item_id}',
                http_method='PUT',
                post_args=post_args
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update checklist item: {e}")
            return False

    def delete_checklist(self, checklist_id: str) -> bool:
        """Delete a checklist.

        Args:
            checklist_id: ID of the checklist to delete

        Returns:
            True if successful
        """
        try:
            self.client.fetch_json(
                f'/checklists/{checklist_id}',
                http_method='DELETE'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete checklist: {e}")
            return False

    def delete_checklist_item(
        self,
        checklist_id: str,
        item_id: str
    ) -> bool:
        """Delete a checklist item.

        Args:
            checklist_id: ID of the checklist
            item_id: ID of the item to delete

        Returns:
            True if successful
        """
        try:
            self.client.fetch_json(
                f'/checklists/{checklist_id}/checkItems/{item_id}',
                http_method='DELETE'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete checklist item: {e}")
            return False

    def ensure_checklist(
        self,
        card: Any,
        name: str,
        items: List[str],
        checked_items: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Ensure a checklist exists with the specified items.

        Creates the checklist if it doesn't exist, or updates it if it does.
        Items are matched by name. Stale items (on card but not in items list)
        are removed to keep the checklist in sync.

        Args:
            card: Trello card object
            name: Checklist name
            items: List of item names
            checked_items: List of item names that should be checked

        Returns:
            Checklist dict or None if failed
        """
        checked_items = checked_items or []

        # Check if checklist already exists
        existing = self.get_checklist_by_name(card, name)

        if existing:
            # Update existing checklist
            existing_names = {item['name']: item for item in existing['items']}
            items_set = set(items)

            # Remove stale items (on card but not in local task)
            for item_name, item in existing_names.items():
                if item_name not in items_set:
                    self.delete_checklist_item(existing['id'], item['id'])
                    logger.info(f"Removed stale checklist item: {item_name}")

            # Add missing items or update existing ones
            for item_name in items:
                if item_name not in existing_names:
                    checked = item_name in checked_items
                    self.add_checklist_item(card, existing['id'], item_name, checked)
                else:
                    # Update checked state if needed
                    item = existing_names[item_name]
                    should_be_checked = item_name in checked_items
                    if item['checked'] != should_be_checked:
                        self.update_checklist_item(
                            card, existing['id'], item['id'],
                            checked=should_be_checked
                        )

            return existing
        else:
            # Create new checklist
            checklist = self.create_checklist(card, name)
            if not checklist:
                return None

            # Add items
            for item_name in items:
                checked = item_name in checked_items
                self.add_checklist_item(card, checklist['id'], item_name, checked)

            return checklist

    # ========== Due Date Methods ==========

    def get_due_date(self, card: Any) -> Optional[Any]:
        """Get the due date from a card.

        Args:
            card: Trello card object

        Returns:
            Due date as datetime or None if not set
        """
        return getattr(card, 'due_date', None)

    def set_due_date(self, card: Any, due_date: Optional[Any]) -> bool:
        """Set the due date on a card.

        Args:
            card: Trello card object
            due_date: Due date as datetime, or None to clear

        Returns:
            True if successful
        """
        try:
            card.set_due(due_date)
            return True
        except Exception as e:
            logger.error(f"Failed to set due date: {e}")
            return False

    # ========== Board Template Methods ==========

    def find_board_by_name(self, name: str) -> Optional[Any]:
        """Find a board by name.

        Args:
            name: Board name to search for (case-insensitive)

        Returns:
            Board object or None if not found
        """
        boards = self.list_boards()
        name_lower = name.lower()

        for board in boards:
            if board.name.lower() == name_lower and not board.closed:
                return board

        return None

    def copy_board_from_template(
        self,
        template_name: str,
        new_board_name: str,
        keep_cards: bool = False
    ) -> Optional[Any]:
        """Create a new board by copying from a template board.

        This preserves:
        - All lists
        - Custom field definitions
        - Labels (with colors)
        - Butler automation rules
        - Board settings

        Optionally preserves:
        - Cards (if keep_cards=True)
        - Checklists on cards

        Args:
            template_name: Name of the template board to copy
            new_board_name: Name for the new board
            keep_cards: Whether to copy cards from the template

        Returns:
            New board object or None if failed

        Raises:
            ValueError: If template board not found
        """
        # Find the template board
        template = self.find_board_by_name(template_name)
        if not template:
            raise ValueError(f"Template board '{template_name}' not found")

        try:
            # Determine what to keep from the source
            # Trello API supports: cards, checklists, customFields, labels
            keep_from_source = "customFields,labels"
            if keep_cards:
                keep_from_source = "cards,checklists,customFields,labels"

            # Create new board by copying from template
            # Using the Trello REST API directly since py-trello doesn't have this method
            result = self.client.fetch_json(
                '/boards',
                http_method='POST',
                post_args={
                    'name': new_board_name,
                    'idBoardSource': template.id,
                    'keepFromSource': keep_from_source,
                    'prefs_permissionLevel': 'private',
                }
            )

            # Get the new board object
            new_board = self.client.get_board(result['id'])
            logger.info(f"Created board '{new_board_name}' from template '{template_name}'")
            return new_board

        except Exception as e:
            logger.error(f"Failed to copy board from template: {e}")
            return None

    def get_board_info(self, board: Any) -> Dict[str, Any]:
        """Get detailed information about a board.

        Args:
            board: Board object

        Returns:
            Dict with board info including lists, custom_fields, labels count
        """
        try:
            self.set_board(board.id)
            structure = self.get_board_structure()

            return {
                'id': board.id,
                'name': board.name,
                'url': board.url,
                'lists': list(structure['lists'].keys()),
                'custom_fields': list(structure['custom_fields'].keys()),
                'labels': list(structure['labels'].keys()),
                'list_count': len(structure['lists']),
                'custom_field_count': len(structure['custom_fields']),
                'label_count': len(structure['labels']),
            }
        except Exception as e:
            logger.error(f"Failed to get board info: {e}")
            return {
                'id': board.id,
                'name': board.name,
                'url': board.url,
                'error': str(e),
            }
