"""Skill CLI commands for skill management and validation.

This module provides commands for managing Claude Code skills:
- skill_app: Typer app for skill commands
- skill_validate(): Validate skills against Anthropic specs
- skill_list(): List all skills
- skill_install(): Install a skill from URL or local path
- skill_export(): Export skills to other AI tool formats
- skill_score_cmd(): Score skills on quality dimensions

Gap-related commands (suggest, gaps, generate) are in skill_gap_commands.py.
"""

from typing import Optional

import typer

from .display_helpers import (
    console,
    find_project_root,
    display_result,
    display_skill_score,
    display_score_table,
)
from .validator import SkillValidator, find_skills_dir
from .installer import (
    install_skill,
    SkillInstallerError,
    SkillSource,
    parse_source,
    get_target_dir,
    extract_skill_name,
)
from .exporter import (
    export_skill,
    export_all_skills,
    check_portability,
    ExportFormat,
    SkillExporterError,
)
from .scorer import (
    SkillScorer,
    SkillScore,
)
from .skill_gap_commands import register_gap_commands

# Typer app for skill commands
skill_app = typer.Typer(
    help="Manage and validate Claude Code skills",
    context_settings={"help_option_names": ["-h", "--help"]},
)

# Register gap-related commands (suggest, gaps, generate)
register_gap_commands(skill_app)


@skill_app.command("validate")
def skill_validate(
    skill_name: Optional[str] = typer.Argument(None, help="Specific skill to validate"),
    fix: bool = typer.Option(False, "--fix", help="Auto-correct simple issues"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Validate skills against Anthropic specs.

    Checks:
    - Frontmatter has only 'name' and 'description' fields
    - Description under 1024 characters
    - 3rd-person voice (warns on 2nd person)
    - File under 500 lines
    - Name matches directory name

    Use --fix to auto-correct simple issues.
    """
    import json

    try:
        skills_dir = find_skills_dir()
    except FileNotFoundError:
        console.print("[red]Could not find .claude/skills directory[/red]")
        raise typer.Exit(1)

    validator = SkillValidator(skills_dir)

    if skill_name:
        # Validate single skill
        skill_dir = skills_dir / skill_name
        if not skill_dir.exists():
            console.print(f"[red]Skill not found: {skill_name}[/red]")
            raise typer.Exit(1)

        if fix:
            fixed = validator.fix_skill(skill_dir)
            if fixed:
                console.print(f"[green]Fixed issues in {skill_name}[/green]")

        result = validator.validate_skill(skill_dir)
        if json_out:
            console.print(json.dumps(result, indent=2))
        else:
            display_result(skill_name, result)
        raise typer.Exit(0 if result["valid"] else 1)

    # Validate all skills
    results = validator.validate_all()

    if not results:
        console.print("[dim]No skills found in .claude/skills/[/dim]")
        return

    if fix:
        console.print("[cyan]Attempting to fix issues...[/cyan]\n")
        for skill_name_key in results:
            skill_dir = skills_dir / skill_name_key
            fixed = validator.fix_skill(skill_dir)
            if fixed:
                console.print(f"  [green]Fixed: {skill_name_key}[/green]")
        console.print()
        # Re-validate after fixes
        results = validator.validate_all()

    if json_out:
        console.print(json.dumps(results, indent=2))
        return

    console.print(f"\n[bold]Validating {len(results)} skills...[/bold]\n")

    for skill_name_key, result in sorted(results.items()):
        display_result(skill_name_key, result)

    # Summary
    summary = validator.get_summary(results)
    console.print(
        f"\n[bold]Summary:[/bold] {summary['passed']} pass, "
        f"{summary['with_warnings']} warnings, {summary['failed']} errors"
    )

    if summary["failed"] > 0:
        raise typer.Exit(1)


@skill_app.command("list")
def skill_list() -> None:
    """List all skills in .claude/skills/."""
    from rich.table import Table

    try:
        skills_dir = find_skills_dir()
    except FileNotFoundError:
        console.print("[red]Could not find .claude/skills directory[/red]")
        raise typer.Exit(1)

    skills = []
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            skills.append(skill_dir.name)

    if not skills:
        console.print("[dim]No skills found.[/dim]")
        return

    table = Table(title=f"Skills ({len(skills)})")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="dim")

    for skill_name in sorted(skills):
        table.add_row(skill_name, f".claude/skills/{skill_name}/")

    console.print(table)


@skill_app.command("install")
def skill_install(
    source: str = typer.Argument(..., help="Source URL or local path to skill"),
    project: bool = typer.Option(
        False, "--project", help="Install to project .claude/skills/"
    ),
    personal: bool = typer.Option(
        False, "--personal", help="Install to ~/.claude/skills/"
    ),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Install with different name"
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", "-o", help="Overwrite existing skill"
    ),
) -> None:
    """Install a skill from URL or local path.

    Examples:

        # Install from local path
        bpsai-pair skill install ~/my-skills/custom-review

        # Install from GitHub
        bpsai-pair skill install https://github.com/user/repo/tree/main/.claude/skills/skill

        # Install with different name
        bpsai-pair skill install ./my-skill --name renamed-skill

        # Install to personal directory
        bpsai-pair skill install ./my-skill --personal

        # Overwrite existing skill
        bpsai-pair skill install ./my-skill --overwrite
    """
    try:
        # Parse source to show what we're doing
        source_type, parsed = parse_source(source)
        skill_name = name or extract_skill_name(source)

        console.print(f"\n[bold]Installing skill: {skill_name}[/bold]")

        if source_type == SkillSource.PATH:
            console.print(f"  Source: [dim]{parsed}[/dim]")
        else:
            console.print(f"  Source: [dim]{source}[/dim]")

        # If neither --project nor --personal specified, default to project
        if not project and not personal:
            project = True

        # Get target directory for display
        target_dir = get_target_dir(project=project, personal=personal)
        console.print(f"  Target: [dim]{target_dir}[/dim]\n")

        console.print(
            "[cyan]Downloading...[/cyan]"
            if source_type == SkillSource.URL
            else "[cyan]Copying...[/cyan]"
        )

        # Install
        result = install_skill(
            source,
            project=project,
            personal=personal,
            name=name,
            force=overwrite,
        )

        console.print("[cyan]Validating...[/cyan]")
        console.print("  [green]\u2713[/green] Frontmatter valid")
        console.print("  [green]\u2713[/green] Description under 1024 chars")
        console.print(
            "  [green]\u2713[/green] No conflicts with existing skills"
            if not overwrite
            else "  [yellow]\u2713[/yellow] Overwrote existing skill"
        )

        console.print(
            f"\n[green]\u2705 Installed {result['skill_name']} to "
            f"{result['installed_to']}/[/green]"
        )

    except SkillInstallerError as e:
        console.print(f"\n[red]\u274c Installation failed: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]\u274c Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@skill_app.command("export")
def skill_export(
    skill_name: Optional[str] = typer.Argument(
        None, help="Skill to export (or use --all)"
    ),
    format: str = typer.Option(
        "cursor",
        "--format",
        "-f",
        help="Export format: cursor, continue, windsurf, codex, chatgpt, all",
    ),
    all_skills: bool = typer.Option(False, "--all", "-a", help="Export all skills"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be created without creating"
    ),
) -> None:
    """Export skills to other AI coding tool formats.

    Supported formats:
    - cursor: Export to .cursor/rules/
    - continue: Export to .continue/context/
    - windsurf: Export to .windsurfrules
    - codex: Export to ~/.codex/skills/ (OpenAI Codex CLI)
    - chatgpt: Export to ./chatgpt-skills/ (for custom GPTs)
    - all: Export to all formats at once

    Examples:

        # Export single skill to Cursor
        bpsai-pair skill export my-skill --format cursor

        # Export to Codex CLI
        bpsai-pair skill export my-skill --format codex

        # Export to ChatGPT format
        bpsai-pair skill export my-skill --format chatgpt

        # Export to all platforms at once
        bpsai-pair skill export my-skill --format all

        # Export all skills to Continue.dev
        bpsai-pair skill export --all --format continue

        # Dry run to see what would be created
        bpsai-pair skill export my-skill --format windsurf --dry-run
    """
    if not skill_name and not all_skills:
        console.print("[red]Error: Specify a skill name or use --all[/red]")
        raise typer.Exit(1)

    # Parse format
    try:
        export_format = ExportFormat(format.lower())
    except ValueError:
        console.print(
            f"[red]Error: Invalid format '{format}'. "
            "Use: cursor, continue, windsurf, codex, chatgpt, all[/red]"
        )
        raise typer.Exit(1)

    # Get directories
    try:
        skills_dir = find_skills_dir()
        project_dir = find_project_root()
    except FileNotFoundError:
        console.print("[red]Could not find .claude/skills directory[/red]")
        raise typer.Exit(1)

    if dry_run:
        console.print("[yellow]Dry run mode - no files will be created[/yellow]\n")

    try:
        if all_skills:
            console.print(f"[bold]Exporting all skills to {format}...[/bold]\n")
            results = export_all_skills(
                format=export_format,
                skills_dir=skills_dir,
                project_dir=project_dir,
                dry_run=dry_run,
            )

            if not results:
                console.print("[dim]No skills found to export.[/dim]")
                return

            success_count = sum(1 for r in results if r.get("success"))
            for result in results:
                if result.get("success"):
                    path_key = "would_create" if dry_run else "path"
                    console.print(
                        f"  [green]\u2713[/green] {result['skill_name']} → "
                        f"{result.get(path_key, 'N/A')}"
                    )
                    for warning in result.get("warnings", []):
                        console.print(f"    [yellow]⚠ {warning}[/yellow]")
                else:
                    console.print(
                        f"  [red]\u274c {result['skill_name']}: "
                        f"{result.get('error', 'Unknown error')}[/red]"
                    )

            console.print(f"\n[bold]Exported {success_count}/{len(results)} skills[/bold]")

        else:
            console.print(f"[bold]Exporting {skill_name} to {format}...[/bold]\n")

            # Check portability first (skip for 'all' format)
            skill_dir = skills_dir / skill_name
            if skill_dir.exists() and export_format != ExportFormat.ALL:
                warnings = check_portability(skill_dir)
                for warning in warnings:
                    console.print(f"[yellow]⚠ {warning}[/yellow]")
                if warnings:
                    console.print()

            result = export_skill(
                skill_name=skill_name,
                format=export_format,
                skills_dir=skills_dir,
                project_dir=project_dir,
                dry_run=dry_run,
            )

            # Handle 'all' format special result structure
            if result.get("format") == "all":
                exported_to = result.get("exported_to", {})
                for fmt_name, path in exported_to.items():
                    console.print(f"  [green]\u2713[/green] {fmt_name}: {path}")

                for warning in result.get("warnings", []):
                    console.print(f"\n[yellow]⚠ {warning}[/yellow]")

                console.print(f"\n{result.get('summary', 'Export complete')}")
            elif dry_run:
                console.print(f"[dim]Would create: {result.get('would_create')}[/dim]")
            else:
                console.print(f"[green]\u2705 Exported to {result.get('path')}[/green]")

    except SkillExporterError as e:
        console.print(f"\n[red]\u274c Export failed: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]\u274c Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@skill_app.command("score")
def skill_score_cmd(
    skill_name: Optional[str] = typer.Argument(None, help="Specific skill to score"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Score skills on quality dimensions.

    Evaluates skills on token efficiency, trigger clarity, completeness,
    usage frequency, and portability.

    Examples:

        # Score all skills
        bpsai-pair skill score

        # Score specific skill
        bpsai-pair skill score implementing-with-tdd

        # Output as JSON
        bpsai-pair skill score --json
    """
    import json

    try:
        skills_dir = find_skills_dir()
    except FileNotFoundError:
        console.print("[red]Could not find .claude/skills directory[/red]")
        raise typer.Exit(1)

    scorer = SkillScorer(skills_dir)

    if skill_name:
        # Score single skill
        score = scorer.score_skill(skill_name)
        if not score:
            console.print(f"[red]Skill not found: {skill_name}[/red]")
            raise typer.Exit(1)

        if json_out:
            console.print(json.dumps(score.to_dict(), indent=2))
            return

        display_skill_score(score)
    else:
        # Score all skills
        scores = scorer.score_all()

        if not scores:
            console.print("[dim]No skills found to score.[/dim]")
            return

        if json_out:
            output = {
                "skills": [s.to_dict() for s in scores],
                "total": len(scores),
                "average_score": sum(s.overall_score for s in scores) // len(scores),
            }
            console.print(json.dumps(output, indent=2))
            return

        display_score_table(scores)
