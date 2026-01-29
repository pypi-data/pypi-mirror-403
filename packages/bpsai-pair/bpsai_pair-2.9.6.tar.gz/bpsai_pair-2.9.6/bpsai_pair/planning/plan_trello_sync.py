"""Plan Trello sync commands.

Extracted from plan_commands.py for better modularity.
"""

from typing import Optional
import json

import typer

from .parser import PlanParser, TaskParser
from .helpers import (
    console,
    find_paircoder_dir,
    get_linked_trello_card,
    update_task_with_card_id,
)

plan_sync_trello_app = typer.Typer(
    help="Sync plan to Trello",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@plan_sync_trello_app.command("sync")
def plan_sync_trello(
    plan_id: str = typer.Argument(..., help="Plan ID to sync"),
    board_id: Optional[str] = typer.Option(None, "--board", "-b", help="Target Trello board ID (uses config default if not specified)"),
    target_list: Optional[str] = typer.Option(None, "--target-list", "-t", help="Target list for cards (default: Intake/Backlog, use 'Planned/Ready' for sprint planning)"),
    create_lists: bool = typer.Option(False, "--create-lists/--no-create-lists", help="Create sprint lists if missing"),
    link_cards: bool = typer.Option(True, "--link/--no-link", help="Store card IDs in task files"),
    apply_defaults: bool = typer.Option(False, "--apply-defaults", "-d", help="Apply project defaults from config to new cards"),
    only_new: bool = typer.Option(False, "--only-new", help="Only sync tasks without existing Trello cards (skip linked tasks)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without making changes"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Sync plan tasks to Trello board as cards.

    Uses board_id from .paircoder/config.yaml if --board is not specified.

    By default, cards are created in 'Intake/Backlog'. For sprint planning,
    use --target-list "Planned/Ready" to place cards directly in the ready queue.

    Use --apply-defaults to set custom fields from config.yaml trello.defaults section.
    """
    paircoder_dir = find_paircoder_dir()
    plan_parser = PlanParser(paircoder_dir / "plans")
    task_parser = TaskParser(paircoder_dir / "tasks")

    # Load plan
    plan = plan_parser.get_plan_by_id(plan_id)
    if not plan:
        console.print(f"[red]Plan not found: {plan_id}[/red]")
        raise typer.Exit(1)

    # Load tasks
    tasks = task_parser.get_tasks_for_plan(plan_id)
    if not tasks:
        console.print(f"[yellow]No tasks found for plan: {plan_id}[/yellow]")
        raise typer.Exit(1)

    # Load config to get board_id if not provided
    import yaml
    config_file = paircoder_dir / "config.yaml"
    full_config = {}
    if config_file.exists():
        with open(config_file, encoding='utf-8') as f:
            full_config = yaml.safe_load(f) or {}

    # Use config board_id as default if --board not specified
    effective_board_id = board_id or full_config.get("trello", {}).get("board_id")

    results = {
        "plan_id": plan_id,
        "board_id": effective_board_id,
        "lists_created": [],
        "cards_created": [],
        "cards_updated": [],
        "cards_skipped": [],
        "errors": [],
        "dry_run": dry_run,
        "only_new": only_new,
    }

    # Group tasks by sprint
    sprints_tasks = {}
    for task in tasks:
        sprint_name = task.sprint or "Backlog"
        if sprint_name not in sprints_tasks:
            sprints_tasks[sprint_name] = []
        sprints_tasks[sprint_name].append(task)

    if dry_run:
        # Preview mode
        console.print(f"\n[bold]Would sync plan:[/bold] {plan_id}")
        if effective_board_id:
            console.print(f"[bold]Target board:[/bold] {effective_board_id}")
        else:
            console.print("[bold]Target board:[/bold] [yellow](not specified)[/yellow]")
        console.print("\n[bold]Tasks to sync:[/bold]")

        for sprint_name, sprint_tasks in sorted(sprints_tasks.items()):
            console.print(f"\n  [cyan]{sprint_name}[/cyan]:")
            for task in sprint_tasks:
                console.print(f"    [{task.id}] {task.title}")
                results["cards_created"].append({
                    "task_id": task.id,
                    "title": task.title,
                    "sprint": sprint_name,
                })

        console.print(f"\n[dim]Total: {len(tasks)} tasks in {len(sprints_tasks)} lists[/dim]")

        if json_out:
            console.print(json.dumps(results, indent=2))
        return

    # Check for Trello connection
    if not effective_board_id:
        console.print("[red]Board ID required. Either:[/red]")
        console.print("  1. Use --board <board-id>")
        console.print("  2. Set trello.board_id in .paircoder/config.yaml")
        console.print("\n[dim]Run 'bpsai-pair trello boards --json' to see available boards.[/dim]")
        raise typer.Exit(1)

    board_id = effective_board_id  # Use effective board_id for the rest

    try:
        from ..trello.auth import load_token
        from ..trello.client import TrelloService
        from ..trello.sync import TrelloSyncManager, TaskData, TaskSyncConfig

        token_data = load_token()
        if not token_data:
            console.print("[red]Not connected to Trello. Run 'bpsai-pair trello connect' first.[/red]")
            raise typer.Exit(1)

        service = TrelloService(
            api_key=token_data["api_key"],
            token=token_data["token"]
        )

        # Set board
        service.set_board(board_id)
        results["board_id"] = board_id

        # Use config already loaded earlier
        trello_config = full_config.get("trello", {})

        # Create sync config from file or use defaults
        sync_config = TaskSyncConfig.from_config(trello_config)
        sync_manager = TrelloSyncManager(service, sync_config)

        console.print(f"\n[bold]Syncing plan:[/bold] {plan_id}")
        console.print(f"[bold]Target board:[/bold] {service.board.name}")
        if target_list:
            console.print(f"[bold]Target list:[/bold] {target_list}")
        else:
            console.print(f"[dim]Target list:[/dim] {sync_config.default_list} (default - use --target-list 'Planned/Ready' for sprint planning)")

        # Ensure BPS labels exist on the board
        console.print("\n[dim]Ensuring BPS labels exist...[/dim]")
        label_results = sync_manager.ensure_bps_labels()
        labels_created = sum(1 for v in label_results.values() if v)
        if labels_created:
            console.print(f"  [green]+ Created {labels_created} BPS labels[/green]")

        # Process each sprint
        for sprint_name, sprint_tasks in sorted(sprints_tasks.items()):
            console.print(f"\n  [cyan]{sprint_name}[/cyan]:")

            # Determine which list to use for new cards
            effective_list = target_list or sync_config.default_list
            board_lists = service.get_board_lists()
            if effective_list not in board_lists:
                if create_lists:
                    service.board.add_list(effective_list)
                    service.lists = {lst.name: lst for lst in service.board.all_lists()}
                    results["lists_created"].append(effective_list)
                    console.print(f"    [green]+ Created list: {effective_list}[/green]")
                else:
                    results["errors"].append(f"List not found: {effective_list}")
                    console.print(f"    [red]✗ List not found: {effective_list}[/red]")
                    continue

            # Sync cards for tasks
            for task in sprint_tasks:
                try:
                    # Skip tasks that already have a linked card when --only-new
                    if only_new:
                        linked_card = get_linked_trello_card(task.id)
                        if linked_card:
                            results["cards_skipped"].append({
                                "task_id": task.id,
                                "reason": "already_linked",
                            })
                            console.print(f"    [dim]⊘[/dim] {task.id}: Already linked (skipped)")
                            continue

                    # Convert to TaskData with plan title for Project field
                    task_data = TaskData.from_task(task)
                    task_data.plan_title = plan.title if plan else plan_id

                    # Check if card already exists
                    existing_card, _ = service.find_card_with_prefix(task.id)

                    # Skip tasks with existing cards when --only-new
                    if only_new and existing_card:
                        results["cards_skipped"].append({
                            "task_id": task.id,
                            "reason": "card_exists",
                        })
                        console.print(f"    [dim]⊘[/dim] {task.id}: Card exists on board (skipped)")
                        continue

                    # For new cards: use the effective list
                    # For existing cards: pass None to update in place
                    card_target_list = None if existing_card else effective_list

                    # Sync using TrelloSyncManager
                    card = sync_manager.sync_task_to_card(
                        task=task_data,
                        list_name=card_target_list,
                        update_existing=True
                    )

                    if card:
                        if existing_card:
                            results["cards_updated"].append({
                                "task_id": task.id,
                                "card_id": card.id,
                            })
                            console.print(f"    [yellow]↻[/yellow] {task.id}: {task.title}")
                        else:
                            results["cards_created"].append({
                                "task_id": task.id,
                                "card_id": card.id,
                            })
                            stack = sync_manager.infer_stack(task_data)
                            stack_info = f" [{stack}]" if stack else ""
                            console.print(f"    [green]+[/green] {task.id}: {task.title}{stack_info}")

                            # Update task file with card ID if requested
                            # Use short_id for TRELLO-### format compatibility
                            if link_cards:
                                update_task_with_card_id(task, str(card.short_id), task_parser)

                            # Apply project defaults if requested
                            if apply_defaults:
                                defaults = trello_config.get("defaults", {})
                                if defaults:
                                    field_mapping = {
                                        "project": "Project",
                                        "stack": "Stack",
                                        "repo_url": "Repo URL",
                                        "deployment_tag": "Deployment Tag",
                                    }
                                    field_values = {}
                                    for key, val in defaults.items():
                                        field_name = field_mapping.get(key, key.replace("_", " ").title())
                                        field_values[field_name] = val
                                    if field_values:
                                        service.set_card_custom_fields(card, field_values)
                    else:
                        results["errors"].append(f"Failed to sync card for {task.id}")
                        console.print(f"    [red]✗[/red] {task.id}: Failed to sync")

                except Exception as e:
                    error_msg = f"Failed to create card for {task.id}: {str(e)}"
                    results["errors"].append(error_msg)
                    console.print(f"    [red]✗[/red] {task.id}: {str(e)}")

        # Summary
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Lists created: {len(results['lists_created'])}")
        console.print(f"  Cards created: {len(results['cards_created'])}")
        console.print(f"  Cards updated: {len(results['cards_updated'])}")
        if results["cards_skipped"]:
            console.print(f"  Cards skipped: {len(results['cards_skipped'])}")
        if results["errors"]:
            console.print(f"  [red]Errors: {len(results['errors'])}[/red]")

        if json_out:
            console.print(json.dumps(results, indent=2))

    except ImportError:
        console.print("[red]py-trello not installed. Install with: pip install 'bpsai-pair[trello]'[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
