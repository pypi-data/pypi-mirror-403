"""Standup CLI commands.

Commands for generating and posting daily standup summaries.
"""

from datetime import datetime
from typing import Optional

import typer

from .helpers import console, find_paircoder_dir

standup_app = typer.Typer(
    help="Daily standup summary commands",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@standup_app.command("generate")
def standup_generate(
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Filter by plan ID"),
    since: int = typer.Option(24, "--since", "-s", help="Hours to look back for completed tasks"),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown, slack, trello"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write to file instead of stdout"),
):
    """Generate a daily standup summary.

    Shows completed tasks, in-progress work, and blockers.

    Examples:
        # Generate markdown summary
        bpsai-pair standup generate

        # Generate Slack-formatted summary
        bpsai-pair standup generate --format slack

        # Look back 48 hours
        bpsai-pair standup generate --since 48

        # Save to file
        bpsai-pair standup generate -o standup.md
    """
    from .standup import generate_standup

    paircoder_dir = find_paircoder_dir()

    summary = generate_standup(
        paircoder_dir=paircoder_dir,
        plan_id=plan_id,
        since_hours=since,
        format=format,
    )

    if output:
        from pathlib import Path
        Path(output).write_text(summary, encoding="utf-8")
        console.print(f"[green]Wrote standup summary to {output}[/green]")
    else:
        console.print(summary)


@standup_app.command("post")
def standup_post(
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Filter by plan ID"),
    since: int = typer.Option(24, "--since", "-s", help="Hours to look back"),
):
    """Post standup summary to Trello board's Notes list.

    Adds a comment to the weekly summary card with today's standup.
    """
    from .standup import StandupGenerator

    paircoder_dir = find_paircoder_dir()

    # Load config to get board ID
    config_file = paircoder_dir / "config.yaml"
    if not config_file.exists():
        console.print("[red]No config.yaml found[/red]")
        raise typer.Exit(1)

    import yaml
    config = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
    board_id = config.get("trello", {}).get("board_id")

    if not board_id:
        import yaml
        config_file = paircoder_dir / "config.yaml"
        if config_file.exists():
            with open(config_file, encoding='utf-8') as f:
                full_config = yaml.safe_load(f) or {}
                board_id = full_config.get("trello", {}).get("board_id")

        if not board_id:
            console.print("[red]Board ID required. Use --board <board-id> or configure default board.[/red]")
            console.print("[dim]List boards: bpsai-pair trello boards[/dim]")
            console.print("[dim]Set default: bpsai-pair trello use-board <board-id>[/dim]")
            raise typer.Exit(1)
        else:
            console.print(f"[dim]Using board from config: {board_id}[/dim]")

    generator = StandupGenerator(paircoder_dir)
    summary = generator.generate(since_hours=since, plan_id=plan_id)
    comment = summary.to_trello_comment()

    # Post to Trello
    try:
        from ..trello.auth import load_token
        from ..trello.client import TrelloService

        token_data = load_token()
        if not token_data:
            console.print("[red]Not connected to Trello[/red]")
            raise typer.Exit(1)

        service = TrelloService(
            api_key=token_data["api_key"],
            token=token_data["token"]
        )
        service.set_board(board_id)

        # Find or create weekly summary card in Notes list
        notes_cards = service.get_cards_in_list("Notes / Ops Log")
        summary_card = None

        week_str = datetime.now().strftime("Week %W")
        for card in notes_cards:
            if week_str in card.name or "Weekly Summary" in card.name:
                summary_card = card
                break

        if summary_card:
            service.add_comment(summary_card, comment)
            console.print(f"[green]Posted standup to '{summary_card.name}'[/green]")
        else:
            console.print("[yellow]No weekly summary card found in Notes / Ops Log[/yellow]")
            console.print("[dim]Create a card with 'Week' or 'Weekly Summary' in the title[/dim]")
            console.print("\n[bold]Generated Summary:[/bold]")
            console.print(comment)

    except ImportError:
        console.print("[red]Trello module not available[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error posting to Trello: {e}[/red]")
        raise typer.Exit(1)
