"""Skill gap CLI commands for gap detection and generation.

This module provides commands for managing skill gaps:
- skill_suggest(): Analyze session history and suggest new skills
- skill_gaps(): List detected skill gaps from session history
- skill_generate(): Generate a skill from a detected gap
"""

from typing import Optional

import typer

from .display_helpers import (
    console,
    find_project_root,
)
from .validator import find_skills_dir
from .suggestion import (
    suggest_skills,
    SkillDraftCreator,
    SkillSuggestionError,
)
from .gap_detector import (
    GapPersistence,
    detect_gaps_from_history,
)
from .generator import (
    SkillGenerator,
    SkillGeneratorError,
    save_generated_skill,
)


def register_gap_commands(app: typer.Typer) -> None:
    """Register gap-related commands on a Typer app."""

    @app.command("suggest")
    def skill_suggest(
        json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
        create: Optional[int] = typer.Option(
            None, "--create", "-c", help="Create draft for suggestion N"
        ),
        min_occurrences: int = typer.Option(
            3, "--min", "-m", help="Minimum pattern occurrences"
        ),
    ) -> None:
        """Analyze session history and suggest new skills.

        Scans recent workflow patterns and suggests skills that could automate
        frequently repeated command sequences.

        Examples:

            # Show suggestions
            bpsai-pair skill suggest

            # Output as JSON
            bpsai-pair skill suggest --json

            # Create draft for first suggestion
            bpsai-pair skill suggest --create 1

            # Require at least 5 occurrences
            bpsai-pair skill suggest --min 5
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
            skills_dir.mkdir(parents=True, exist_ok=True)

        console.print("[cyan]Analyzing session patterns...[/cyan]\n")

        # Get suggestions
        suggestions = suggest_skills(
            history_dir=history_dir,
            skills_dir=skills_dir,
            min_occurrences=min_occurrences,
        )

        if json_out:
            output = {
                "suggestions": suggestions,
                "total": len(suggestions),
            }
            console.print(json.dumps(output, indent=2))
            return

        if not suggestions:
            console.print("[dim]No patterns found that would benefit from a skill.[/dim]")
            console.print("\n[dim]Tips:[/dim]")
            console.print("  - Patterns need at least 3 occurrences by default")
            console.print("  - Try using --min to lower the threshold")
            console.print("  - More session history helps detect patterns")
            return

        console.print(f"[bold]Suggested Skills ({len(suggestions)}):[/bold]\n")

        for i, suggestion in enumerate(suggestions, 1):
            name = suggestion.get("name", "unknown")
            confidence = suggestion.get("confidence", 0)
            description = suggestion.get("description", "")
            occurrences = suggestion.get("occurrences", 0)
            estimated_savings = suggestion.get("estimated_savings", "")
            overlaps = suggestion.get("overlaps_with", [])

            # Confidence indicator
            if confidence >= 80:
                conf_style = "green"
            elif confidence >= 60:
                conf_style = "yellow"
            else:
                conf_style = "dim"

            console.print(
                f"[bold]{i}. {name}[/bold] "
                f"[{conf_style}](confidence: {confidence}%)[/{conf_style}]"
            )
            console.print(f"   [dim]{description}[/dim]")
            console.print(f"   Pattern occurrences: {occurrences}")
            if estimated_savings:
                console.print(f"   Estimated savings: {estimated_savings}")
            if overlaps:
                console.print(
                    f"   [yellow]⚠ May overlap with: {', '.join(overlaps)}[/yellow]"
                )
            console.print()

        # Handle --create option
        if create is not None:
            if create < 1 or create > len(suggestions):
                console.print(
                    f"[red]Invalid suggestion number. Choose 1-{len(suggestions)}[/red]"
                )
                raise typer.Exit(1)

            suggestion = suggestions[create - 1]
            console.print(f"[cyan]Creating draft for: {suggestion['name']}[/cyan]")

            try:
                creator = SkillDraftCreator(skills_dir=skills_dir)
                result = creator.create_draft(suggestion)

                if result["success"]:
                    console.print(
                        f"[green]\u2705 Created draft: {result['path']}[/green]"
                    )

                    validation = result.get("validation", {})
                    if validation.get("valid"):
                        console.print("   [green]\u2713[/green] Passes validation")
                    else:
                        console.print(
                            "   [yellow]\u26a0[/yellow] Review validation warnings"
                        )
                        for error in validation.get("errors", []):
                            console.print(f"      [red]{error}[/red]")

            except SkillSuggestionError as e:
                console.print(f"[red]\u274c Failed to create draft: {e}[/red]")
                raise typer.Exit(1)
        else:
            console.print("[dim]Use --create N to create a draft for suggestion N[/dim]")

    @app.command("gaps")
    def skill_gaps(
        json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
        clear: bool = typer.Option(False, "--clear", help="Clear gap history"),
        analyze: bool = typer.Option(False, "--analyze", help="Run fresh analysis"),
    ) -> None:
        """List detected skill gaps from session history.

        Shows patterns that were repeated frequently but don't have matching skills.
        Use this to identify opportunities for new skill creation.

        Examples:

            # List detected gaps
            bpsai-pair skill gaps

            # Output as JSON
            bpsai-pair skill gaps --json

            # Clear gap history
            bpsai-pair skill gaps --clear

            # Run fresh analysis
            bpsai-pair skill gaps --analyze
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

        persistence = GapPersistence(history_dir=history_dir)

        # Handle --clear
        if clear:
            persistence.clear_gaps()
            console.print("[green]Gap history cleared[/green]")
            return

        # Load or detect gaps
        if analyze:
            console.print("[cyan]Analyzing session history for gaps...[/cyan]\n")
            gaps = detect_gaps_from_history(
                history_dir=history_dir,
                skills_dir=skills_dir,
            )
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
            console.print("[dim]No skill gaps detected.[/dim]")
            console.print("\n[dim]Tips:[/dim]")
            console.print("  - Use --analyze to run fresh detection")
            console.print("  - Gaps are detected from repeated workflows")
            console.print("  - Use `skill suggest` for pattern-based suggestions")
            return

        console.print(f"[bold]Detected Skill Gaps ({len(gaps)}):[/bold]\n")

        for i, gap in enumerate(gaps, 1):
            # Confidence indicator
            if gap.confidence >= 0.8:
                conf_style = "green"
            elif gap.confidence >= 0.5:
                conf_style = "yellow"
            else:
                conf_style = "dim"

            console.print(
                f"[bold]{i}. {gap.suggested_name}[/bold] "
                f"[{conf_style}](confidence: {gap.confidence:.0%})[/{conf_style}]"
            )
            console.print(
                f"   Pattern: {' → '.join(gap.pattern[:4])}"
                f"{'...' if len(gap.pattern) > 4 else ''}"
            )
            console.print(f"   Frequency: {gap.frequency} occurrences")
            console.print(f"   Estimated savings: {gap.time_saved_estimate}")
            console.print(f"   [dim]Detected: {gap.detected_at[:10]}[/dim]")
            console.print()

        console.print(
            "[dim]Use `bpsai-pair skill generate N` to create a skill from gap N[/dim]"
        )

    @app.command("generate")
    def skill_generate(
        gap_id: Optional[int] = typer.Argument(
            None, help="Gap ID to generate from (1-based)"
        ),
        auto_approve: bool = typer.Option(
            False, "--auto-approve", "-y", help="Save without confirmation"
        ),
        overwrite: bool = typer.Option(
            False, "--overwrite", "-o", help="Overwrite existing skill"
        ),
        preview: bool = typer.Option(
            False, "--preview", "-p", help="Preview without saving"
        ),
    ) -> None:
        """Generate a skill from a detected gap.

        Creates a skill draft from patterns detected by `skill gaps`. The generated
        skill follows Anthropic specs and includes observed commands as workflow steps.

        Examples:

            # List available gaps
            bpsai-pair skill generate

            # Preview generated skill
            bpsai-pair skill generate 1 --preview

            # Generate and save with confirmation
            bpsai-pair skill generate 1

            # Auto-approve and save
            bpsai-pair skill generate 1 --auto-approve

            # Overwrite existing skill
            bpsai-pair skill generate 1 --overwrite --auto-approve
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
            skills_dir.mkdir(parents=True, exist_ok=True)

        # Load gaps
        persistence = GapPersistence(history_dir=history_dir)
        gaps = persistence.load_gaps()

        if not gaps:
            console.print("[dim]No skill gaps found.[/dim]")
            console.print(
                "\n[dim]Run `bpsai-pair skill gaps --analyze` to detect patterns.[/dim]"
            )
            return

        # If no gap_id provided, list available gaps
        if gap_id is None:
            console.print("[bold]Available Gaps:[/bold]\n")
            for i, gap in enumerate(gaps, 1):
                console.print(
                    f"  {i}. [cyan]{gap.suggested_name}[/cyan] "
                    f"(confidence: {gap.confidence:.0%})"
                )
                console.print(
                    f"     Pattern: {' → '.join(gap.pattern[:3])}"
                    f"{'...' if len(gap.pattern) > 3 else ''}"
                )
            console.print(
                "\n[dim]Use `bpsai-pair skill generate <N>` to generate from gap N[/dim]"
            )
            return

        # Validate gap_id
        if gap_id < 1 or gap_id > len(gaps):
            console.print(
                f"[red]Invalid gap ID: {gap_id}. Valid range: 1-{len(gaps)}[/red]"
            )
            raise typer.Exit(1)

        gap = gaps[gap_id - 1]
        console.print(f"[cyan]Generating skill from gap: {gap.suggested_name}[/cyan]\n")

        # Generate skill
        generator = SkillGenerator()
        generated = generator.generate_from_gap(gap)

        # Preview mode
        if preview:
            console.print("[bold]Generated Skill Preview:[/bold]\n")
            console.print("─" * 60)
            console.print(generated.content)
            console.print("─" * 60)
            console.print("\n[dim]Use `--auto-approve` to save this skill[/dim]")
            return

        # Show preview before saving (unless auto_approve)
        if not auto_approve:
            console.print("[bold]Generated Skill:[/bold]\n")
            console.print("─" * 60)
            # Show truncated preview
            lines = generated.content.split("\n")
            preview_lines = lines[:30]
            console.print("\n".join(preview_lines))
            if len(lines) > 30:
                console.print(f"\n... ({len(lines) - 30} more lines)")
            console.print("─" * 60)
            console.print()

            # Ask for confirmation
            confirm = typer.confirm("Save this skill?")
            if not confirm:
                console.print("[dim]Cancelled.[/dim]")
                return

        # Save the skill
        try:
            result = save_generated_skill(
                generated,
                skills_dir,
                force=overwrite,
                auto_approve=True,
            )

            if result["success"]:
                console.print(f"[green]✅ Created skill: {result['path']}[/green]")

                validation = result.get("validation", {})
                if validation.get("valid"):
                    console.print("   [green]✓[/green] Passes validation")
                else:
                    console.print("   [yellow]⚠[/yellow] Review validation warnings:")
                    for error in validation.get("errors", []):
                        console.print(f"      [red]{error}[/red]")
                    for warning in validation.get("warnings", []):
                        console.print(f"      [yellow]{warning}[/yellow]")

                if result.get("requires_review"):
                    console.print(
                        "\n[dim]Note: Review and customize the generated skill "
                        "before use.[/dim]"
                    )

        except SkillGeneratorError as e:
            console.print(f"[red]✖ Failed to save: {e}[/red]")
            raise typer.Exit(1)
