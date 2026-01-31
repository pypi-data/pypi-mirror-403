"""Gaps CLI commands for unified gap detection and classification.

This module provides commands for managing skill and subagent gaps:
- gaps_app: Typer app for gap commands
- gaps_detect(): Detect and classify all gaps from session history
- gaps_list(): List all classified gaps
- gaps_show(): Show detailed classification for a specific gap
- gaps_check(): Check quality gates for a specific gap
"""

from typing import Optional

import typer

from .display_helpers import (
    console,
    find_project_root,
    display_classified_gap,
    display_score_bar,
)
from .validator import find_skills_dir
from .classifier import GapType, detect_and_classify_all
from .gates import GateStatus, GapQualityGate, QualityGateResult, evaluate_gap_quality

# Typer app for gap commands
gaps_app = typer.Typer(
    help="Unified gap detection and classification",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@gaps_app.command("detect")
def gaps_detect(
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
    analyze: bool = typer.Option(False, "--analyze", help="Force fresh analysis"),
    with_gates: bool = typer.Option(
        True, "--with-gates/--no-gates", help="Evaluate quality gates"
    ),
) -> None:
    """Detect and classify all gaps from session history.

    Runs both skill and subagent gap detection, then classifies each gap
    to determine whether it should become a skill, subagent, or either.

    Quality gates are evaluated by default to filter out low-value patterns.
    Use --no-gates to skip gate evaluation.

    Examples:

        # Detect and classify gaps with quality gates
        bpsai-pair gaps detect

        # Skip quality gate evaluation
        bpsai-pair gaps detect --no-gates

        # Output as JSON
        bpsai-pair gaps detect --json

        # Force fresh analysis
        bpsai-pair gaps detect --analyze
    """
    import json

    try:
        project_dir = find_project_root()
    except Exception:
        console.print("[red]Could not find project root[/red]")
        raise typer.Exit(1)

    history_dir = project_dir / ".paircoder" / "history"
    try:
        skills_dir = find_skills_dir()
    except FileNotFoundError:
        skills_dir = project_dir / ".claude" / "skills"

    subagents_dir = project_dir / ".claude" / "agents"

    console.print("[cyan]Detecting and classifying gaps...[/cyan]\n")

    # Detect and classify
    classified = detect_and_classify_all(
        history_dir=history_dir,
        skills_dir=skills_dir,
        subagents_dir=subagents_dir,
    )

    # Evaluate quality gates if enabled
    gate_results: dict[str, QualityGateResult] = {}
    if with_gates:
        gate = GapQualityGate()
        for gap in classified:
            gate_results[gap.id] = gate.evaluate(gap)

    # JSON output
    if json_out:
        output = {
            "gaps": [g.to_dict() for g in classified],
            "total": len(classified),
            "by_type": {
                "skill": len([g for g in classified if g.gap_type == GapType.SKILL]),
                "subagent": len(
                    [g for g in classified if g.gap_type == GapType.SUBAGENT]
                ),
                "ambiguous": len(
                    [g for g in classified if g.gap_type == GapType.AMBIGUOUS]
                ),
            },
        }
        if with_gates:
            output["gates"] = {
                gap_id: {
                    "passed": result.can_generate,
                    "status": result.overall_status.value,
                    "blocking_gates": [
                        r.gate_name
                        for r in result.gate_results
                        if r.status == GateStatus.BLOCK
                    ],
                    "warnings": [
                        r.gate_name
                        for r in result.gate_results
                        if r.status == GateStatus.WARN
                    ],
                }
                for gap_id, result in gate_results.items()
            }
            output["summary"] = {
                "passed": len([r for r in gate_results.values() if r.can_generate]),
                "blocked": len(
                    [
                        r
                        for r in gate_results.values()
                        if r.overall_status == GateStatus.BLOCK
                    ]
                ),
                "warned": len(
                    [
                        r
                        for r in gate_results.values()
                        if r.overall_status == GateStatus.WARN
                    ]
                ),
            }
        console.print(json.dumps(output, indent=2))
        return

    # Display results
    if not classified:
        console.print("[dim]No gaps detected.[/dim]")
        console.print("\n[dim]Tips:[/dim]")
        console.print("  - Gaps are detected from repeated workflows in history")
        console.print("  - Use `skill suggest` for pattern-based skill suggestions")
        console.print("  - Use `subagent gaps` for subagent-specific detection")
        return

    # Group by type
    skills = [g for g in classified if g.gap_type == GapType.SKILL]
    subagents = [g for g in classified if g.gap_type == GapType.SUBAGENT]
    ambiguous = [g for g in classified if g.gap_type == GapType.AMBIGUOUS]

    console.print(f"[bold]Classified Gaps ({len(classified)} total):[/bold]\n")

    if skills:
        console.print("[bold green]SKILLS:[/bold green]")
        for gap in skills:
            gate_result = gate_results.get(gap.id) if with_gates else None
            display_classified_gap(gap, gate_result)
        console.print()

    if subagents:
        console.print("[bold blue]SUBAGENTS:[/bold blue]")
        for gap in subagents:
            gate_result = gate_results.get(gap.id) if with_gates else None
            display_classified_gap(gap, gate_result)
        console.print()

    if ambiguous:
        console.print("[bold yellow]AMBIGUOUS (user decision needed):[/bold yellow]")
        for gap in ambiguous:
            gate_result = gate_results.get(gap.id) if with_gates else None
            display_classified_gap(gap, gate_result)
        console.print()

    # Summary
    console.print("[dim]Summary:[/dim]")
    console.print(
        f"  Skills: {len(skills)} | Subagents: {len(subagents)} | Ambiguous: {len(ambiguous)}"
    )

    # Gate summary if enabled
    if with_gates and gate_results:
        passed = len([r for r in gate_results.values() if r.can_generate])
        blocked = len(
            [r for r in gate_results.values() if r.overall_status == GateStatus.BLOCK]
        )
        warned = len(
            [r for r in gate_results.values() if r.overall_status == GateStatus.WARN]
        )
        console.print(
            f"  Gates: [green]{passed} passed[/green] | "
            f"[red]{blocked} blocked[/red] | [yellow]{warned} warned[/yellow]"
        )


@gaps_app.command("list")
def gaps_list(
    gap_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="Filter by type: skill, subagent, ambiguous"
    ),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all classified gaps.

    Shows gaps that have been detected and classified. Use --type to filter
    by classification.

    Examples:

        # List all gaps
        bpsai-pair gaps list

        # List only skill gaps
        bpsai-pair gaps list --type skill

        # List ambiguous gaps
        bpsai-pair gaps list --type ambiguous
    """
    import json

    try:
        project_dir = find_project_root()
    except Exception:
        console.print("[red]Could not find project root[/red]")
        raise typer.Exit(1)

    history_dir = project_dir / ".paircoder" / "history"
    try:
        skills_dir = find_skills_dir()
    except FileNotFoundError:
        skills_dir = project_dir / ".claude" / "skills"

    subagents_dir = project_dir / ".claude" / "agents"

    # Detect and classify
    classified = detect_and_classify_all(
        history_dir=history_dir,
        skills_dir=skills_dir,
        subagents_dir=subagents_dir,
    )

    # Filter by type if specified
    if gap_type:
        try:
            filter_type = GapType(gap_type.lower())
            classified = [g for g in classified if g.gap_type == filter_type]
        except ValueError:
            console.print(
                f"[red]Invalid type: {gap_type}. Use: skill, subagent, ambiguous[/red]"
            )
            raise typer.Exit(1)

    # JSON output
    if json_out:
        output = {
            "gaps": [g.to_dict() for g in classified],
            "total": len(classified),
        }
        console.print(json.dumps(output, indent=2))
        return

    if not classified:
        console.print("[dim]No gaps found.[/dim]")
        return

    console.print(f"[bold]Gaps ({len(classified)}):[/bold]\n")

    for gap in classified:
        display_classified_gap(gap)


@gaps_app.command("show")
def gaps_show(
    gap_id: str = typer.Argument(..., help="Gap ID to show details for"),
) -> None:
    """Show detailed classification for a specific gap.

    Displays full classification details including scores, reasoning,
    and recommendations.

    Examples:

        # Show gap details
        bpsai-pair gaps show skill-testing-workflows
    """
    try:
        project_dir = find_project_root()
    except Exception:
        console.print("[red]Could not find project root[/red]")
        raise typer.Exit(1)

    history_dir = project_dir / ".paircoder" / "history"
    try:
        skills_dir = find_skills_dir()
    except FileNotFoundError:
        skills_dir = project_dir / ".claude" / "skills"

    subagents_dir = project_dir / ".claude" / "agents"

    # Detect and classify
    classified = detect_and_classify_all(
        history_dir=history_dir,
        skills_dir=skills_dir,
        subagents_dir=subagents_dir,
    )

    # Find the gap
    gap = None
    for g in classified:
        if g.id == gap_id or g.suggested_name == gap_id:
            gap = g
            break

    if not gap:
        console.print(f"[red]Gap not found: {gap_id}[/red]")
        console.print("\n[dim]Available gaps:[/dim]")
        for g in classified[:5]:
            console.print(f"  - {g.id}")
        raise typer.Exit(1)

    # Display detailed view
    console.print(f"\n[bold]Gap: {gap.suggested_name}[/bold]")
    console.print(f"ID: {gap.id}")
    type_color = (
        "green"
        if gap.gap_type == GapType.SKILL
        else "blue" if gap.gap_type == GapType.SUBAGENT else "yellow"
    )
    console.print(f"Type: [{type_color}]{gap.gap_type.value.upper()}[/]")
    console.print(f"Confidence: {gap.confidence:.0%}")
    console.print(f"\n{gap.description}")

    console.print("\n[bold]Classification Scores:[/bold]")
    display_score_bar("Portability", gap.portability_score)
    display_score_bar("Isolation", gap.isolation_score)
    display_score_bar("Persona", gap.persona_score)
    display_score_bar("Resumability", gap.resumability_score)
    display_score_bar("Simplicity", gap.simplicity_score)

    console.print("\n[bold]Reasoning:[/bold]")
    console.print(f"  {gap.reasoning}")

    if gap.skill_recommendation:
        console.print("\n[bold green]Skill Recommendation:[/bold green]")
        console.print(f"  Name: {gap.skill_recommendation.suggested_name}")
        if gap.skill_recommendation.allowed_tools:
            console.print(
                f"  Tools: {', '.join(gap.skill_recommendation.allowed_tools)}"
            )
        console.print(
            f"  Portability: {', '.join(gap.skill_recommendation.estimated_portability)}"
        )

    if gap.subagent_recommendation:
        console.print("\n[bold blue]Subagent Recommendation:[/bold blue]")
        console.print(f"  Name: {gap.subagent_recommendation.suggested_name}")
        if gap.subagent_recommendation.suggested_model:
            console.print(f"  Model: {gap.subagent_recommendation.suggested_model}")
        if gap.subagent_recommendation.suggested_tools:
            console.print(
                f"  Tools: {', '.join(gap.subagent_recommendation.suggested_tools)}"
            )
        if gap.subagent_recommendation.persona_hint:
            console.print(
                f"  Persona: {gap.subagent_recommendation.persona_hint[:60]}..."
            )


@gaps_app.command("check")
def gaps_check(
    gap_id: str = typer.Argument(..., help="Gap ID or name to check"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Check quality gates for a specific gap.

    Evaluates a gap against pre-generation quality gates to determine
    if it should become a skill or be blocked.

    Examples:

        # Check a specific gap
        bpsai-pair gaps check skill-testing-workflows

        # Output as JSON
        bpsai-pair gaps check GAP-001 --json
    """
    import json

    try:
        project_dir = find_project_root()
    except Exception:
        console.print("[red]Could not find project root[/red]")
        raise typer.Exit(1)

    history_dir = project_dir / ".paircoder" / "history"
    try:
        skills_dir = find_skills_dir()
    except FileNotFoundError:
        skills_dir = project_dir / ".claude" / "skills"

    # Detect and classify to find the gap
    classified = detect_and_classify_all(
        history_dir=history_dir,
        skills_dir=skills_dir,
    )

    # Find the gap
    gap = None
    for g in classified:
        if g.id == gap_id or g.suggested_name == gap_id:
            gap = g
            break

    if not gap:
        console.print(f"[red]Gap not found: {gap_id}[/red]")
        if classified:
            console.print("\n[dim]Available gaps:[/dim]")
            for g in classified[:5]:
                console.print(f"  - {g.suggested_name} ({g.id})")
        raise typer.Exit(1)

    # Evaluate quality gates
    result = evaluate_gap_quality(gap, skills_dir=skills_dir)

    # JSON output
    if json_out:
        console.print(json.dumps(result.to_dict(), indent=2))
        return

    # Display results
    console.print(f"\n[bold]Quality Gate Results: {result.gap_name}[/bold]")
    console.print("=" * 50)

    # Overall status
    if result.overall_status == GateStatus.PASS:
        console.print("[green]Overall: ✅ PASS[/green]")
    elif result.overall_status == GateStatus.WARN:
        console.print("[yellow]Overall: ⚠️ WARN[/yellow]")
    else:
        console.print("[red]Overall: ❌ BLOCKED[/red]")

    console.print(f"\nCan Generate: {'Yes' if result.can_generate else 'No'}")
    console.print("\n[bold]Gate Results:[/bold]")

    for gate in result.gate_results:
        if gate.status == GateStatus.PASS:
            icon = "[green]✅[/green]"
        elif gate.status == GateStatus.WARN:
            icon = "[yellow]⚠️[/yellow]"
        else:
            icon = "[red]❌[/red]"

        score_bar = "█" * int(gate.score * 10) + "░" * (10 - int(gate.score * 10))
        console.print(f"  {icon} {gate.gate_name:12} [{score_bar}] {gate.score:.2f}")
        console.print(f"     {gate.reason}")
        if gate.details:
            console.print(f"     [dim]{gate.details}[/dim]")

    console.print(f"\n[bold]Recommendation:[/bold]\n  {result.recommendation}")
