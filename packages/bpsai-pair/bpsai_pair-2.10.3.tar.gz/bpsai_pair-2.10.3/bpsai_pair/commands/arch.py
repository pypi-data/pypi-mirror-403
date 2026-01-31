"""Architecture checking CLI commands.

Provides commands for checking code against architecture constraints:
- File size limits
- Function length limits
- Function count per file
- Import count limits

Usage:
    bpsai-pair arch check                    # Check entire project
    bpsai-pair arch check --staged           # Check staged files only
    bpsai-pair arch check src/               # Check specific directory
    bpsai-pair arch check --fix              # Show suggested fixes
    bpsai-pair arch check --strict           # Fail on warnings too
"""
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..core.enforcement import (
    ArchitectureEnforcer,
    ArchitectureViolation,
    ViolationType,
    SplitAnalyzer,
    SplitAnalysisResult,
)

app = typer.Typer(
    help="Architecture enforcement commands",
    context_settings={"help_option_names": ["-h", "--help"]},
)

console = Console()


def format_violation_type(vtype: ViolationType) -> str:
    """Format violation type for display."""
    type_map = {
        ViolationType.FILE_TOO_LARGE: "file too large",
        ViolationType.FUNCTION_TOO_LONG: "function too long",
        ViolationType.TOO_MANY_FUNCTIONS: "too many functions",
        ViolationType.TOO_MANY_IMPORTS: "too many imports",
    }
    return type_map.get(vtype, str(vtype.value))


def display_violations(
    violations: list[ArchitectureViolation],
    show_fix: bool = False,
    enforcer: Optional[ArchitectureEnforcer] = None,
) -> tuple[int, int]:
    """Display violations in a formatted table.

    Returns:
        Tuple of (error_count, warning_count)
    """
    if not violations:
        console.print("[green]✓ No architecture violations found[/green]")
        return 0, 0

    # Separate errors and warnings
    errors = [v for v in violations if v.severity == "error"]
    warnings = [v for v in violations if v.severity == "warning"]

    # Display errors
    if errors:
        console.print(f"\n[red]✗ {len(errors)} error(s):[/red]")
        table = Table(show_header=True, header_style="bold red")
        table.add_column("File", style="cyan")
        table.add_column("Violation", style="red")
        table.add_column("Value", justify="right")
        table.add_column("Threshold", justify="right")

        for v in errors:
            details = ""
            if v.details and "function_name" in v.details:
                details = f" ({v.details['function_name']})"
            table.add_row(
                str(v.file),
                format_violation_type(v.violation_type) + details,
                str(v.current_value),
                str(v.threshold),
            )
        console.print(table)

        # Show fix suggestions if requested
        if show_fix and enforcer:
            console.print("\n[bold]Suggested fixes:[/bold]")
            seen_files = set()
            for v in errors:
                if v.file not in seen_files and v.violation_type == ViolationType.FILE_TOO_LARGE:
                    seen_files.add(v.file)
                    suggestion = enforcer.suggest_split(v)
                    console.print(f"\n  [cyan]{v.file}[/cyan]:")
                    for module in suggestion.suggested_modules:
                        console.print(f"    → Extract to: [green]{module}[/green]")

    # Display warnings
    if warnings:
        console.print(f"\n[yellow]⚠ {len(warnings)} warning(s):[/yellow]")
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("File", style="cyan")
        table.add_column("Violation", style="yellow")
        table.add_column("Value", justify="right")
        table.add_column("Threshold", justify="right")

        for v in warnings:
            table.add_row(
                str(v.file),
                format_violation_type(v.violation_type),
                str(v.current_value),
                str(v.threshold),
            )
        console.print(table)

    return len(errors), len(warnings)


@app.command("check")
def check(
    path: Optional[str] = typer.Argument(
        None,
        help="File or directory to check (defaults to current directory)",
    ),
    staged: bool = typer.Option(
        False,
        "--staged",
        "-s",
        help="Check only git staged files",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Show suggested fixes for violations",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Fail on warnings as well as errors",
    ),
):
    """Check architecture constraints.

    Analyzes Python files for architecture violations:
    - Files over 400 lines (error) or 200 lines (warning)
    - Functions over 50 lines
    - More than 15 functions per file
    - More than 20 imports

    Examples:
        bpsai-pair arch check                    # Check current directory
        bpsai-pair arch check src/               # Check specific directory
        bpsai-pair arch check --staged           # Check staged files only
        bpsai-pair arch check --fix              # Show fix suggestions
        bpsai-pair arch check --strict           # Fail on warnings too
    """
    # Create enforcer (loads config if available)
    enforcer = ArchitectureEnforcer.from_config(Path.cwd())

    violations: list[ArchitectureViolation] = []

    if staged:
        # Check only staged files
        console.print("[bold]Checking staged files...[/bold]")
        violations = enforcer.check_staged_files()
    else:
        # Determine path to check
        check_path = Path(path) if path else Path.cwd()

        if not check_path.exists():
            console.print(f"[red]Error: Path not found: {check_path}[/red]")
            raise typer.Exit(code=2)

        if check_path.is_file():
            console.print(f"[bold]Checking file: {check_path}[/bold]")
            violations = enforcer.check_file(check_path)
        else:
            console.print(f"[bold]Checking directory: {check_path}[/bold]")
            violations = enforcer.check_directory(check_path)

    # Display results
    error_count, warning_count = display_violations(
        violations,
        show_fix=fix,
        enforcer=enforcer if fix else None,
    )

    # Determine exit code
    if error_count > 0:
        raise typer.Exit(code=1)
    elif strict and warning_count > 0:
        raise typer.Exit(code=1)
    else:
        raise typer.Exit(code=0)


@app.command("suggest-split")
def suggest_split(
    file_path: str = typer.Argument(
        ...,
        help="Python file to analyze for splitting",
    ),
):
    """Suggest how to split a large file into smaller modules.

    Analyzes a Python file and identifies logical components (classes,
    function groups) that could be extracted into separate modules.

    Examples:
        bpsai-pair arch suggest-split security/sandbox.py
        bpsai-pair arch suggest-split core/config.py
    """
    path = Path(file_path)

    # Validate file exists
    if not path.exists():
        console.print(f"[red]Error: File not found: {path}[/red]")
        raise typer.Exit(code=2)

    # Validate it's a Python file
    if path.suffix != ".py":
        console.print(f"[red]Error: Not a Python file (.py): {path}[/red]")
        raise typer.Exit(code=2)

    # Analyze the file
    analyzer = SplitAnalyzer()
    result = analyzer.analyze(path)

    # Display results
    _display_split_analysis(result)

    raise typer.Exit(code=0)


def _display_split_analysis(result: SplitAnalysisResult) -> None:
    """Display split analysis results.

    Args:
        result: SplitAnalysisResult from analyzer
    """
    # Header
    console.print()
    console.print(
        f"[bold]Split Suggestions for {result.source_file.name}[/bold] "
        f"({result.total_lines} lines)"
    )
    console.print("=" * 60)
    console.print()

    # Check if file needs splitting
    if not result.needs_split:
        console.print(
            f"[green]✓ File is within recommended size limits "
            f"({result.total_lines} lines < 200)[/green]"
        )
        console.print("[dim]No splitting recommended.[/dim]")
        return

    if not result.components:
        console.print(
            "[yellow]⚠ File exceeds size limits but no clear components detected.[/yellow]"
        )
        console.print("[dim]Consider manual refactoring.[/dim]")
        return

    # Display detected components
    console.print("[bold]Detected components:[/bold]")
    console.print()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Component", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Lines", justify="right")
    table.add_column("Extract to", style="green")

    for i, comp in enumerate(result.components, 1):
        # Format component name with details
        name = comp.name
        if comp.component_type == "class" and comp.functions:
            name += f" ({len(comp.functions)} methods)"
        elif comp.component_type == "function_group" and comp.functions:
            name += f" ({len(comp.functions)} functions)"

        table.add_row(
            str(i),
            name,
            comp.component_type.replace("_", " "),
            f"{comp.start_line}-{comp.end_line} ({comp.line_count})",
            comp.suggested_filename,
        )

    console.print(table)
    console.print()

    # Display hub file recommendation
    if result.hub_recommendation:
        console.print("[bold]Recommended hub file structure:[/bold]")
        console.print()
        console.print(
            f"[dim]The original {result.source_file.name} becomes a hub that "
            "re-exports the public API:[/dim]"
        )
        console.print()

        # Show a simplified version
        console.print("[cyan]```python[/cyan]")
        for line in result.hub_recommendation.split("\n")[:15]:
            console.print(f"[dim]{line}[/dim]")
        if len(result.hub_recommendation.split("\n")) > 15:
            console.print("[dim]...[/dim]")
        console.print("[cyan]```[/cyan]")
        console.print()

    # Summary
    total_extractable = sum(c.line_count for c in result.components)
    console.print("[bold]Summary:[/bold]")
    console.print(f"  • Total lines: {result.total_lines}")
    console.print(f"  • Components detected: {len(result.components)}")
    console.print(f"  • Lines in components: ~{total_extractable}")
    console.print(
        f"  • Estimated hub size: ~{max(20, result.total_lines - total_extractable + 20)} lines"
    )
