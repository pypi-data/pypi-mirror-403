"""
MCP Trello Tools

Implements Trello integration tools:
- paircoder_trello_sync_plan: Sync plan tasks to Trello board
- paircoder_trello_update_card: Update Trello card on task state change
"""

from pathlib import Path
from typing import Any, Optional


def find_paircoder_dir() -> Path:
    """Find the .paircoder directory."""
    from ...core.ops import find_paircoder_dir as _find_paircoder_dir, ProjectRootNotFoundError
    try:
        paircoder_dir = _find_paircoder_dir()
    except ProjectRootNotFoundError:
        raise FileNotFoundError("No .paircoder directory found")
    if not paircoder_dir.exists():
        raise FileNotFoundError("No .paircoder directory found")
    return paircoder_dir


def get_trello_service():
    """Get a connected Trello service."""
    from ...trello.auth import load_token
    from ...trello.client import TrelloService

    token_data = load_token()
    if not token_data:
        raise ValueError("Not connected to Trello. Run 'bpsai-pair trello connect' first.")

    return TrelloService(
        api_key=token_data["api_key"],
        token=token_data["token"]
    )


def _check_all_acceptance_criteria_mcp(card, service, checklist_name: str = "Acceptance Criteria") -> int:
    """Check off all items in the Acceptance Criteria checklist.

    Args:
        card: Trello card object
        service: TrelloService instance
        checklist_name: Name of the checklist to check off

    Returns:
        Number of items that were checked off
    """
    try:
        card.fetch()  # Refresh to get checklists
    except Exception:
        pass

    if not hasattr(card, 'checklists') or not card.checklists:
        return 0

    checked_count = 0

    for checklist in card.checklists:
        if checklist.name.lower() != checklist_name.lower():
            continue

        for item in checklist.items:
            # Skip already checked items
            if item.get("checked"):
                continue

            item_name = item.get("name", "")

            # Use TrelloService's update_checklist_item method
            try:
                checklist_id = checklist.id
                item_id = item.get("id")
                if service.update_checklist_item(card, checklist_id, item_id, checked=True):
                    checked_count += 1
            except Exception:
                # Try py-trello's method as fallback
                try:
                    checklist.set_checklist_item(item_name, checked=True)
                    checked_count += 1
                except Exception:
                    pass  # Best effort - continue with other items

    return checked_count


def register_trello_tools(server: Any) -> None:
    """Register Trello tools with the MCP server."""

    @server.tool()
    async def paircoder_trello_sync_plan(
        plan_id: str,
        board_id: Optional[str] = None,
        create_lists: bool = False,
        link_cards: bool = True,
        dry_run: bool = False,
    ) -> dict:
        """
        Sync plan tasks to Trello board as cards.

        Args:
            plan_id: Plan ID to sync
            board_id: Target Trello board ID (uses default if not specified)
            create_lists: Create sprint lists if missing
            link_cards: Store card IDs in task files
            dry_run: Preview without making changes

        Returns:
            Sync results with created/updated cards
        """
        try:
            from ...planning.parser import PlanParser, TaskParser

            paircoder_dir = find_paircoder_dir()
            plan_parser = PlanParser(paircoder_dir / "plans")
            task_parser = TaskParser(paircoder_dir / "tasks")

            # Load plan
            plan = plan_parser.get_plan_by_id(plan_id)
            if not plan:
                return {"error": {"code": "PLAN_NOT_FOUND", "message": f"Plan not found: {plan_id}"}}

            # Load tasks
            tasks = task_parser.get_tasks_for_plan(plan_id)
            if not tasks:
                return {"error": {"code": "NO_TASKS", "message": f"No tasks found for plan: {plan_id}"}}

            results = {
                "plan_id": plan_id,
                "board_id": board_id,
                "lists_created": [],
                "cards_created": [],
                "cards_updated": [],
                "errors": [],
                "dry_run": dry_run,
            }

            if dry_run:
                # Preview mode
                for task in tasks:
                    results["cards_created"].append({
                        "task_id": task.id,
                        "title": task.title,
                        "sprint": task.sprint or "Backlog",
                        "would_create": True,
                    })
                return results

            # Connect to Trello
            try:
                service = get_trello_service()
            except (ImportError, ValueError) as e:
                return {"error": {"code": "TRELLO_NOT_CONNECTED", "message": str(e)}}

            # Set board
            if board_id:
                service.set_board(board_id)
                results["board_id"] = board_id
            else:
                # Try to get default board from config
                return {"error": {"code": "NO_BOARD", "message": "No board_id specified"}}

            # Group tasks by sprint
            sprints_tasks = {}
            for task in tasks:
                sprint_name = task.sprint or "Backlog"
                if sprint_name not in sprints_tasks:
                    sprints_tasks[sprint_name] = []
                sprints_tasks[sprint_name].append(task)

            # Process each sprint
            for sprint_name, sprint_tasks in sprints_tasks.items():
                # Get or create list
                board_lists = service.get_board_lists()
                if sprint_name not in board_lists:
                    if create_lists:
                        service.board.add_list(sprint_name)
                        service.lists = {lst.name: lst for lst in service.board.all_lists()}
                        results["lists_created"].append(sprint_name)
                    else:
                        results["errors"].append(f"List not found: {sprint_name}")
                        continue

                target_list = service.lists.get(sprint_name)
                if not target_list:
                    continue

                # Create cards for tasks
                for task in sprint_tasks:
                    try:
                        # Check if card already exists
                        existing_cards = target_list.list_cards()
                        existing = None
                        for card in existing_cards:
                            if f"[{task.id}]" in card.name:
                                existing = card
                                break

                        # Card description
                        desc = f"""## Objective
{task.objective or task.title}

## Details
- **Priority:** {task.priority}
- **Complexity:** {task.complexity}
- **Sprint:** {task.sprint or 'N/A'}

---
*Synced from PairCoder*
"""

                        if existing:
                            # Update existing card
                            existing.set_description(desc)
                            results["cards_updated"].append({
                                "task_id": task.id,
                                "card_id": existing.id,
                            })
                        else:
                            # Create new card
                            card_name = f"[{task.id}] {task.title}"
                            card = target_list.add_card(card_name, desc)
                            results["cards_created"].append({
                                "task_id": task.id,
                                "card_id": card.id,
                            })

                            # Update task file with card ID if requested
                            if link_cards:
                                _update_task_with_card_id(task.id, card.id, task_parser)

                    except Exception as e:
                        results["errors"].append(f"Failed to create card for {task.id}: {str(e)}")

            return results

        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}

    @server.tool()
    async def paircoder_trello_update_card(
        task_id: str,
        action: str,
        comment: Optional[str] = None,
    ) -> dict:
        """
        Update Trello card on task state change.

        Args:
            task_id: Task ID to update
            action: Action type (start, complete, block, comment)
            comment: Comment or additional info

        Returns:
            Update result
        """
        try:
            from ...planning.parser import TaskParser

            paircoder_dir = find_paircoder_dir()
            task_parser = TaskParser(paircoder_dir / "tasks")

            # Find task
            task = task_parser.get_task_by_id(task_id)
            if not task:
                return {"error": {"code": "TASK_NOT_FOUND", "message": f"Task not found: {task_id}"}}

            # Check if task has trello_card_id
            if not hasattr(task, "trello_card_id") or not task.trello_card_id:
                return {"error": {"code": "NOT_LINKED", "message": f"Task {task_id} not linked to Trello"}}

            # Connect to Trello
            try:
                service = get_trello_service()
            except (ImportError, ValueError) as e:
                return {"error": {"code": "TRELLO_NOT_CONNECTED", "message": str(e)}}

            # Find the card
            card, current_list = service.find_card(task.trello_card_id)
            if not card:
                return {"error": {"code": "CARD_NOT_FOUND", "message": f"Card not found: {task.trello_card_id}"}}

            # Perform action
            if action == "start":
                service.move_card(card, "In Progress")
                service.add_comment(card, "🤖 Started by agent")

            elif action == "complete":
                # Check off all acceptance criteria items first
                checked_count = _check_all_acceptance_criteria_mcp(card, service)

                service.move_card(card, "Done")
                completion_msg = "✅ Completed"
                if comment:
                    completion_msg += f": {comment}"
                if checked_count > 0:
                    completion_msg += f" ({checked_count} acceptance criteria checked)"
                service.add_comment(card, completion_msg)

            elif action == "block":
                # Add blocked label if available
                try:
                    for label in service.board.get_labels():
                        if "block" in label.name.lower():
                            card.add_label(label)
                            break
                except Exception:
                    pass
                block_msg = "⊘ Blocked"
                if comment:
                    block_msg += f": {comment}"
                service.add_comment(card, block_msg)

            elif action == "comment":
                if comment:
                    service.add_comment(card, comment)
                else:
                    return {"error": {"code": "MISSING_COMMENT", "message": "Comment required for comment action"}}

            else:
                return {"error": {"code": "INVALID_ACTION", "message": f"Unknown action: {action}"}}

            return {
                "updated": True,
                "task_id": task_id,
                "card_id": task.trello_card_id,
                "action": action,
            }

        except FileNotFoundError:
            return {"error": {"code": "NOT_FOUND", "message": "No .paircoder directory found"}}
        except Exception as e:
            return {"error": {"code": "ERROR", "message": str(e)}}


def _update_task_with_card_id(task_id: str, card_id: str, task_parser) -> bool:
    """Update task file with Trello card ID."""
    try:
        # Find task file
        task_file = task_parser._find_task_file(task_id)
        if not task_file:
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
