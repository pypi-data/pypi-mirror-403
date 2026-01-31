"""Subagent CLI commands for Claude Code.

This module provides commands for managing Claude Code subagents:
- subagent_app: Typer app for subagent commands
- subagent_gaps(): List detected subagent gaps from session history
"""

import typer

from .display_helpers import console, find_project_root
from .subagent_detector import SubagentGapPersistence, detect_subagent_gaps

# Typer app for subagent commands
subagent_app = typer.Typer(
    help="Manage Claude Code subagents",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@subagent_app.command("gaps")
def subagent_gaps(
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
    clear: bool = typer.Option(False, "--clear", help="Clear gap history"),
    analyze: bool = typer.Option(False, "--analyze", help="Run fresh analysis"),
) -> None:
    """List detected subagent gaps from session history.

    Shows patterns that suggest subagents would be beneficial, such as
    context isolation needs, specialized personas, or resumable workflows.

    Examples:

        # List detected gaps
        bpsai-pair subagent gaps

        # Output as JSON
        bpsai-pair subagent gaps --json

        # Clear gap history
        bpsai-pair subagent gaps --clear

        # Run fresh analysis
        bpsai-pair subagent gaps --analyze
    """
    import json

    try:
        project_dir = find_project_root()
    except Exception:
        console.print("[red]Could not find project root[/red]")
        raise typer.Exit(1)

    history_dir = project_dir / ".paircoder" / "history"

    persistence = SubagentGapPersistence(history_dir=history_dir)

    # Handle --clear
    if clear:
        persistence.clear_gaps()
        console.print("[green]Subagent gap history cleared[/green]")
        return

    # Load or detect gaps
    if analyze:
        console.print("[cyan]Analyzing session history for subagent patterns...[/cyan]\n")
        gaps = detect_subagent_gaps(history_dir=history_dir)
        # Save newly detected gaps
        for gap in gaps:
            persistence.save_gap(gap)
    else:
        gaps = persistence.load_gaps()

    # JSON output
    if json_out:
        output = {
            "gaps": [g.to_dict() for g in gaps],
            "total": len(gaps),
        }
        console.print(json.dumps(output, indent=2))
        return

    # Display gaps
    if not gaps:
        console.print("[dim]No subagent gaps detected.[/dim]")
        console.print("\n[dim]Tips:[/dim]")
        console.print("  - Use --analyze to run fresh detection")
        console.print("  - Subagent gaps are detected from patterns like:")
        console.print("    • Requests for specific personas or roles")
        console.print("    • Context isolation needs")
        console.print("    • Multi-session/resumable workflows")
        console.print("    • Read-only analysis patterns")
        return

    console.print(f"[bold]Detected Subagent Gaps ({len(gaps)}):[/bold]\n")

    for i, gap in enumerate(gaps, 1):
        # Confidence indicator
        if gap.confidence >= 0.7:
            conf_style = "green"
        elif gap.confidence >= 0.5:
            conf_style = "yellow"
        else:
            conf_style = "dim"

        console.print(
            f"[bold]{i}. {gap.suggested_name}[/bold] "
            f"[{conf_style}](confidence: {gap.confidence:.0%})[/{conf_style}]"
        )
        console.print(f"   {gap.description}")

        if gap.indicators:
            console.print(f"   Indicators: {', '.join(gap.indicators)}")

        if gap.suggested_model:
            console.print(f"   Suggested model: {gap.suggested_model}")

        if gap.suggested_tools:
            tools_str = ", ".join(gap.suggested_tools[:3])
            if len(gap.suggested_tools) > 3:
                tools_str += "..."
            console.print(f"   Suggested tools: {tools_str}")

        features = []
        if gap.needs_context_isolation:
            features.append("context isolation")
        if gap.needs_resumability:
            features.append("resumable")
        if features:
            console.print(f"   Features: {', '.join(features)}")

        console.print(f"   Occurrences: {gap.occurrence_count}")
        console.print(f"   [dim]Detected: {gap.detected_at[:10]}[/dim]")
        console.print()

    console.print(
        "[dim]Subagent creation from gaps will be available in a future release.[/dim]"
    )
