"""Template CLI commands for PairCoder.

Provides commands for cookiecutter template management including
drift detection, listing, and auto-sync.

Extracted from planning/cli_commands.py as part of EPIC-003 Phase 2.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

# Import shared helper from release commands
from .commands import get_template_path, find_paircoder_dir
from ..core.ops import ProjectRootNotFoundError

console = Console()

app = typer.Typer(
    help="Cookiecutter template management commands",
    context_settings={"help_option_names": ["-h", "--help"]}
)

# Minimal required template files with their check modes
# Mode: "content" = full content comparison (with cookiecutter var normalization)
#       "exists" = just check file exists in both locations
#       "version" = check only version field matches (for yaml files)
REQUIRED_TEMPLATE_FILES: list[tuple[str, Literal["content", "exists", "version"]]] = [
    # Core project files - existence check (project will customize)
    (".gitignore", "exists"),
    (".agentpackignore", "exists"),
    ("README.md", "exists"),
    # CLAUDE.md - existence check (projects customize with specific rules)
    ("CLAUDE.md", "exists"),
    # Config files - version field match only
    (".paircoder/config.yaml", "version"),
    (".paircoder/capabilities.yaml", "version"),
    # PairCoder context files - existence check (project-specific content)
    (".paircoder/context/state.md", "exists"),
    (".paircoder/context/project.md", "exists"),
    (".paircoder/context/workflow.md", "content"),
    # Claude settings
    (".claude/settings.json", "content"),
    # Skills - existence check only (project may customize)
    (".claude/skills/designing-and-implementing/SKILL.md", "exists"),
    (".claude/skills/implementing-with-tdd/SKILL.md", "exists"),
    (".claude/skills/reviewing-code/SKILL.md", "exists"),
    (".claude/skills/finishing-branches/SKILL.md", "exists"),
    (".claude/skills/creating-skills/SKILL.md", "exists"),
    (".claude/skills/architecting-modules/SKILL.md", "exists"),
    (".claude/skills/managing-task-lifecycle/SKILL.md", "exists"),
    (".claude/skills/planning-with-trello/SKILL.md", "exists"),
    # Commands - content check (should be consistent)
    (".claude/commands/pc-plan.md", "content"),
    (".claude/commands/start-task.md", "content"),
    (".claude/commands/prep-release.md", "content"),
]


def extract_version_field(content: str, file_path: str) -> str | None:
    """Extract version field from YAML content.

    Uses regex instead of YAML parsing because template files may have
    unquoted cookiecutter variables that break YAML parsing.
    """
    # Look for version: "X.Y.Z" or version: 'X.Y.Z' at start of line
    match = re.search(r'^version:\s*["\']?([^"\'\n]+)["\']?\s*$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def compute_line_diff(source_content: str, template_content: str) -> int:
    """Compute the number of different lines between source and template."""
    import difflib

    source_lines = source_content.splitlines()
    template_lines = template_content.splitlines()

    diff = list(difflib.unified_diff(template_lines, source_lines, lineterm=""))
    # Count lines that are actually different (starting with + or -)
    # but not the header lines
    changed_lines = 0
    for line in diff:
        if line.startswith("+") or line.startswith("-"):
            if not line.startswith("+++") and not line.startswith("---"):
                changed_lines += 1

    return changed_lines


@app.command("check")
def template_check(
    fail_on_drift: bool = typer.Option(False, "--fail-on-drift", help="Exit with code 1 if drift detected"),
    fix: bool = typer.Option(False, "--fix", help="Auto-sync template from source files"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed diff information"),
):
    """Check for drift between source files and cookie cutter template.

    Compares key project files with their equivalents in the cookie cutter
    template to detect when the template needs updating.

    Examples:
        # Check for drift
        bpsai-pair template check

        # Fail in CI if drift detected
        bpsai-pair template check --fail-on-drift

        # Auto-fix by syncing template from source
        bpsai-pair template check --fix
    """
    try:
        paircoder_dir = find_paircoder_dir()
    except ProjectRootNotFoundError:
        console.print("[red]❌ Not in a PairCoder project[/red]")
        console.print("   Run 'bpsai-pair init' to initialize a project, or run from a git repository.")
        raise typer.Exit(1)

    project_root = paircoder_dir.parent

    template_path = get_template_path(paircoder_dir)

    console.print("\n[bold]Cookie Cutter Template Status[/bold]\n")

    if not template_path:
        console.print("[yellow]⚠️  Template not found[/yellow]")
        console.print("Expected at: tools/cli/bpsai_pair/data/cookiecutter-paircoder")
        if fail_on_drift:
            raise typer.Exit(1)
        return

    # Template files are under {{cookiecutter.project_slug}}
    template_project_dir = template_path / "{{cookiecutter.project_slug}}"
    if not template_project_dir.exists():
        console.print("[yellow]⚠️  Template project directory not found[/yellow]")
        if fail_on_drift:
            raise typer.Exit(1)
        return

    results: list[tuple[str, str, str]] = []
    has_drift = False
    files_to_sync: list[tuple[Path, Path, str]] = []

    def normalize_for_compare(content: str) -> str:
        """Normalize content for comparison, ignoring cookiecutter variables."""
        # Replace cookiecutter variables with placeholder
        return re.sub(r'\{\{[\s]*cookiecutter\.[^}]+\}\}', '{{COOKIECUTTER_VAR}}', content)

    for file_rel, check_mode in REQUIRED_TEMPLATE_FILES:
        source_path = project_root / file_rel
        template_file = template_project_dir / file_rel

        # Check source exists
        if not source_path.exists():
            results.append((file_rel, "⚠️", "Source file not found"))
            continue

        # Check template exists
        if not template_file.exists():
            results.append((file_rel, "⚠️", "Not in template"))
            has_drift = True
            continue

        # Existence check only - just verify both files exist
        if check_mode == "exists":
            results.append((file_rel, "✅", "Exists"))
            continue

        # Version check - compare only version field in YAML
        if check_mode == "version":
            source_content = source_path.read_text(encoding="utf-8")
            template_content = template_file.read_text(encoding="utf-8")

            source_version = extract_version_field(source_content, file_rel)
            template_version = extract_version_field(template_content, file_rel)

            if source_version == template_version:
                results.append((file_rel, "✅", f"Version match ({source_version})"))
            else:
                has_drift = True
                results.append((file_rel, "⚠️", f"Version mismatch ({source_version} vs {template_version})"))
                files_to_sync.append((source_path, template_file, file_rel))
            continue

        # Content check - full file comparison
        source_content = source_path.read_text(encoding="utf-8")
        template_content = template_file.read_text(encoding="utf-8")

        source_normalized = normalize_for_compare(source_content)
        template_normalized = normalize_for_compare(template_content)

        if source_normalized == template_normalized:
            results.append((file_rel, "✅", "In sync"))
        else:
            line_diff = compute_line_diff(source_normalized, template_normalized)
            has_drift = True
            results.append((file_rel, "⚠️", f"Drift detected ({line_diff} lines changed)"))
            files_to_sync.append((source_path, template_file, file_rel))

    # Display results
    from rich.table import Table as RichTable
    table = RichTable(title=None, show_header=True, header_style="bold")
    table.add_column("File", style="cyan")
    table.add_column("Status")
    table.add_column("Details")

    for file_path, status, details in results:
        table.add_row(file_path, status, details)

    console.print(table)

    # Summary
    in_sync = sum(1 for _, s, _ in results if s == "✅")
    drifted = sum(1 for f, s, d in results if s == "⚠️" and "Drift" in d)
    warnings = sum(1 for _, s, _ in results if s == "⚠️")

    console.print()
    if has_drift:
        console.print(f"[yellow]⚠️  {len(files_to_sync)} file(s) have drifted from template[/yellow]")

        if fix:
            console.print("\n[bold]Syncing template from source...[/bold]")
            for source_path, template_file, rel_path in files_to_sync:
                # Read source and write to template
                content = source_path.read_text(encoding="utf-8")
                template_file.write_text(content, encoding="utf-8")
                console.print(f"  [green]✓[/green] Updated {rel_path}")
            console.print(f"\n[green]Synced {len(files_to_sync)} file(s) to template[/green]")
        else:
            console.print("\n[dim]Run with --fix to sync template from source files[/dim]")

        if fail_on_drift and not fix:
            raise typer.Exit(1)
    else:
        console.print(f"[green]✓ All {in_sync} checked files are in sync[/green]")


@app.command("list")
def template_list():
    """List files tracked for template sync."""
    from rich.table import Table as RichTable

    try:
        paircoder_dir = find_paircoder_dir()
    except ProjectRootNotFoundError:
        console.print("[red]❌ Not in a PairCoder project[/red]")
        console.print("   Run 'bpsai-pair init' to initialize a project, or run from a git repository.")
        raise typer.Exit(1)

    template_path = get_template_path(paircoder_dir)

    console.print("\n[bold]Required Template Files[/bold]\n")

    if not template_path:
        console.print("[yellow]⚠️  Template not found[/yellow]")
        return

    template_project_dir = template_path / "{{cookiecutter.project_slug}}"
    if not template_project_dir.exists():
        console.print("[yellow]⚠️  Template project directory not found[/yellow]")
        return

    console.print(f"Template: {template_path.name}")
    console.print()

    # Show required files with their check modes
    table = RichTable(title=None, show_header=True, header_style="bold")
    table.add_column("File", style="cyan")
    table.add_column("Check Mode")
    table.add_column("Description")

    mode_descriptions = {
        "content": "Full content comparison",
        "exists": "Existence check only",
        "version": "Version field match",
    }

    for file_path, check_mode in REQUIRED_TEMPLATE_FILES:
        description = mode_descriptions.get(check_mode, check_mode)
        table.add_row(file_path, check_mode, description)

    console.print(table)
    console.print()
    console.print(f"[dim]Total: {len(REQUIRED_TEMPLATE_FILES)} required files[/dim]")
