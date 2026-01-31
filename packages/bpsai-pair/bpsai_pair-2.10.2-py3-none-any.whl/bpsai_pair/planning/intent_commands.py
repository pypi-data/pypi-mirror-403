"""Intent detection CLI commands.

Commands for detecting work intent and suggesting planning modes/flows.
"""

import typer

from .helpers import console

intent_app = typer.Typer(
    help="Intent detection and planning mode commands",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@intent_app.command("detect")
def intent_detect(
    text: str = typer.Argument(..., help="Text to analyze for intent"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Detect work intent from text."""
    from .intent_detection import IntentDetector

    detector = IntentDetector()
    matches = detector.detect_all(text)

    if json_out:
        import json as json_module
        output = [{
            "intent": m.intent.value,
            "confidence": m.confidence,
            "suggested_flow": m.suggested_flow,
            "triggers": m.triggers,
        } for m in matches]
        console.print(json_module.dumps(output, indent=2))
        return

    if not matches:
        console.print("[dim]No clear intent detected[/dim]")
        return

    console.print("[bold]Detected Intents:[/bold]\n")
    for match in matches:
        confidence_color = "green" if match.confidence >= 0.8 else "yellow" if match.confidence >= 0.6 else "dim"
        console.print(f"[{confidence_color}]{match.intent.value}[/{confidence_color}] ({match.confidence:.0%})")
        if match.suggested_flow:
            console.print(f"  Suggested flow: {match.suggested_flow}")
        if match.triggers:
            console.print(f"  Triggers: {', '.join(match.triggers[:3])}")
        console.print()


@intent_app.command("should-plan")
def intent_should_plan(
    text: str = typer.Argument(..., help="Text to analyze"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Check if text should trigger planning mode."""
    from .intent_detection import IntentDetector

    detector = IntentDetector()
    should_plan, match = detector.should_enter_planning_mode(text)

    if json_out:
        import json as json_module
        output = {
            "should_plan": should_plan,
            "intent": match.intent.value if match else None,
            "confidence": match.confidence if match else 0,
            "suggested_flow": match.suggested_flow if match else None,
        }
        console.print(json_module.dumps(output, indent=2))
        return

    if should_plan and match:
        console.print("[green]YES - Planning mode recommended[/green]")
        console.print(f"  Intent: {match.intent.value} ({match.confidence:.0%})")
        console.print(f"  Suggested flow: {match.suggested_flow}")
    else:
        console.print("[dim]No - Direct action is fine[/dim]")


@intent_app.command("suggest-flow")
def intent_suggest_flow(
    text: str = typer.Argument(..., help="Text to analyze"),
):
    """Suggest appropriate flow for text."""
    from .intent_detection import IntentDetector

    detector = IntentDetector()
    flow = detector.get_flow_suggestion(text)

    if flow:
        console.print(f"[green]Suggested flow: {flow}[/green]")
        console.print(f"\n[dim]Run: bpsai-pair flow run {flow}[/dim]")
    else:
        console.print("[dim]No specific flow suggested for this request.[/dim]")
