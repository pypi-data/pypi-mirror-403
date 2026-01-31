"""Display helpers for skills CLI commands.

This module provides shared display utilities for skills commands:
- console: Shared Rich Console instance
- find_project_root(): Find project root directory
- display_result(): Display validation result for a skill
- display_classified_gap(): Display a classified gap with optional gate status
- display_score_bar(): Display a score as a visual bar
- display_skill_score(): Display a single skill score
- display_score_table(): Display skills as a score table
"""

from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.table import Table

from .classifier import ClassifiedGap, GapType
from .gates import GateStatus, QualityGateResult
from .scorer import SkillScore

# Shared console instance
console = Console()


def find_project_root() -> Path:
    """Find project root by looking for .paircoder directory."""
    from ..core.ops import find_project_root as _find_project_root

    return _find_project_root()


def display_result(
    name: str,
    result: dict,
    console: Optional[Console] = None,
) -> None:
    """Display validation result for a skill.

    Args:
        name: Skill name
        result: Validation result dict with 'valid', 'warnings', 'errors' keys
        console: Optional Console instance (uses shared instance if not provided)
    """
    if console is None:
        console = globals()["console"]

    if result["valid"] and not result["warnings"]:
        console.print(f"[green]\u2705 {name}[/green]")
    elif result["valid"]:
        console.print(f"[yellow]\u26a0\ufe0f  {name}[/yellow]")
        for warning in result["warnings"]:
            console.print(f"   [dim]- {warning}[/dim]")
    else:
        console.print(f"[red]\u274c {name}[/red]")
        for error in result["errors"]:
            console.print(f"   [red]- {error}[/red]")
        for warning in result["warnings"]:
            console.print(f"   [dim]- {warning}[/dim]")


def display_classified_gap(
    gap: ClassifiedGap,
    gate_result: Optional[QualityGateResult] = None,
    console: Optional[Console] = None,
) -> None:
    """Display a single classified gap with optional gate status.

    Args:
        gap: ClassifiedGap to display
        gate_result: Optional quality gate evaluation result
        console: Optional Console instance (uses shared instance if not provided)
    """
    if console is None:
        console = globals()["console"]

    # Type color
    if gap.gap_type == GapType.SKILL:
        type_style = "green"
    elif gap.gap_type == GapType.SUBAGENT:
        type_style = "blue"
    else:
        type_style = "yellow"

    # Confidence color
    if gap.confidence >= 0.7:
        conf_style = "green"
    elif gap.confidence >= 0.5:
        conf_style = "yellow"
    else:
        conf_style = "dim"

    # Gate status
    gate_str = ""
    if gate_result is not None:
        if gate_result.can_generate and gate_result.overall_status == GateStatus.PASS:
            gate_str = " [green]✓ PASS[/green]"
        elif gate_result.overall_status == GateStatus.BLOCK:
            gate_str = " [red]✗ BLOCKED[/red]"
        else:
            gate_str = " [yellow]⚠ WARNING[/yellow]"

    console.print(
        f"  [{type_style}]{gap.gap_type.value.upper():10}[/{type_style}] "
        f"[bold]{gap.suggested_name}[/bold] "
        f"[{conf_style}]({gap.confidence:.0%})[/{conf_style}]"
        f"{gate_str}"
    )
    console.print(
        f"             [dim]{gap.description[:60]}{'...' if len(gap.description) > 60 else ''}[/dim]"
    )

    # Show blocking reasons if gate failed
    if gate_result is not None and not gate_result.can_generate:
        blocking = [r for r in gate_result.gate_results if r.status == GateStatus.BLOCK]
        warnings = [r for r in gate_result.gate_results if r.status == GateStatus.WARN]
        if blocking:
            reasons = ", ".join(r.reason for r in blocking)
            console.print(f"             [red]Blocked: {reasons}[/red]")
        elif warnings:
            reasons = ", ".join(r.reason for r in warnings)
            console.print(f"             [yellow]Warning: {reasons}[/yellow]")


def display_score_bar(
    label: str,
    score: float,
    console: Optional[Console] = None,
) -> None:
    """Display a score as a visual bar.

    Args:
        label: Score label
        score: Score value (0-1)
        console: Optional Console instance (uses shared instance if not provided)
    """
    if console is None:
        console = globals()["console"]

    filled = int(score * 10)
    bar = "█" * filled + "░" * (10 - filled)
    console.print(f"  {label:12} [{bar}] {score:.2f}")


# Grade color mapping
GRADE_COLORS = {
    "A": "green",
    "B": "cyan",
    "C": "yellow",
    "D": "red",
    "F": "red",
}


def display_skill_score(
    score: SkillScore,
    console: Optional[Console] = None,
) -> None:
    """Display a single skill score.

    Args:
        score: SkillScore to display
        console: Optional Console instance (uses shared instance if not provided)
    """
    if console is None:
        console = globals()["console"]

    grade_color = GRADE_COLORS.get(score.grade, "white")

    console.print(f"\n[bold]Skill: {score.skill_name}[/bold]")
    console.print("=" * 50)
    console.print(
        f"Overall Score: {score.overall_score}/100 "
        f"(Grade: [{grade_color}]{score.grade}[/{grade_color}])"
    )
    console.print("\n[bold]Dimension Scores:[/bold]")

    for dim in score.dimensions:
        score_bar = "█" * int(dim.score * 10) + "░" * (10 - int(dim.score * 10))
        weight_pct = int(dim.weight * 100)
        console.print(
            f"  {dim.name:18} [{score_bar}] {dim.score:.2f} (weight: {weight_pct}%)"
        )
        console.print(f"    [dim]{dim.reason}[/dim]")

    if score.recommendations:
        console.print("\n[bold]Recommendations:[/bold]")
        for i, rec in enumerate(score.recommendations, 1):
            console.print(f"  {i}. {rec}")


def display_score_table(
    scores: List[SkillScore],
    console: Optional[Console] = None,
) -> None:
    """Display skills as a score table.

    Args:
        scores: List of SkillScore
        console: Optional Console instance (uses shared instance if not provided)
    """
    if console is None:
        console = globals()["console"]

    table = Table(title="Skill Quality Report")
    table.add_column("Skill", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Grade", justify="center")
    table.add_column("Token", justify="right")
    table.add_column("Trigger", justify="right")
    table.add_column("Complete", justify="right")
    table.add_column("Portable", justify="right")

    for score in scores:
        token = next((d for d in score.dimensions if d.name == "token_efficiency"), None)
        trigger = next((d for d in score.dimensions if d.name == "trigger_clarity"), None)
        complete = next((d for d in score.dimensions if d.name == "completeness"), None)
        portable = next((d for d in score.dimensions if d.name == "portability"), None)

        grade_style = GRADE_COLORS.get(score.grade, "white")

        table.add_row(
            score.skill_name,
            str(score.overall_score),
            f"[{grade_style}]{score.grade}[/{grade_style}]",
            f"{int(token.score * 100)}" if token else "-",
            f"{int(trigger.score * 100)}" if trigger else "-",
            f"{int(complete.score * 100)}" if complete else "-",
            f"{int(portable.score * 100)}" if portable else "-",
        )

    console.print(table)

    # Summary stats
    avg_score = sum(s.overall_score for s in scores) // len(scores)
    grade_counts: dict[str, int] = {}
    for s in scores:
        grade_counts[s.grade] = grade_counts.get(s.grade, 0) + 1

    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Total: {len(scores)} skills")
    console.print(f"  Average Score: {avg_score}")
    grade_str = ", ".join(f"{g}: {c}" for g, c in sorted(grade_counts.items()))
    console.print(f"  Grades: {grade_str}")

    # Identify skills needing attention
    low_scores = [s for s in scores if s.overall_score < 60]
    if low_scores:
        console.print(f"\n[yellow]Skills needing attention ({len(low_scores)}):[/yellow]")
        for s in low_scores[:3]:
            console.print(f"  - {s.skill_name}: {s.overall_score} ({s.grade})")
            if s.recommendations:
                console.print(f"    → {s.recommendations[0]}")
