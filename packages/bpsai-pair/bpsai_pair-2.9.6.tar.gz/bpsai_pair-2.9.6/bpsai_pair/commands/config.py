"""Config commands for configuration validation and management.

Extracted from cli.py as part of EPIC-003 CLI Architecture Refactor.
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

# Try relative imports first, fall back to absolute
try:
    from ..core import ops
except ImportError:
    from bpsai_pair.core import ops

# Initialize Rich console
console = Console()

# Config sub-app for configuration management
app = typer.Typer(
    help="Configuration validation and management",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@app.command("validate")
def config_validate(
    preset: str = typer.Option("minimal", "--preset", "-p", help="Preset to validate against"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Validate config against preset template.

    Checks for missing sections, outdated version, and missing keys
    compared to what the preset would generate.

    Examples:
        # Validate against minimal preset
        bpsai-pair config validate

        # Validate against react preset
        bpsai-pair config validate --preset react

        # Get JSON output
        bpsai-pair config validate --json
    """
    # Import here to avoid circular imports
    try:
        from ..core.config import validate_config, CURRENT_CONFIG_VERSION
    except ImportError:
        from bpsai_pair.core.config import validate_config, CURRENT_CONFIG_VERSION

    try:
        root = ops.find_project_root()
    except ops.ProjectRootNotFoundError:
        console.print("[red]No config file found. Run 'bpsai-pair init' first.[/red]")
        raise typer.Exit(1)
    result = validate_config(root, preset)

    if json_output:
        import json as json_lib
        console.print(json_lib.dumps(result.to_dict(), indent=2))
        raise typer.Exit(0 if result.is_valid else 1)

    # Display validation report
    console.print("\n[bold]Config Validation Report[/bold]")
    console.print("=" * 40)

    # Version info
    if result.current_version:
        version_status = "✓" if result.current_version == CURRENT_CONFIG_VERSION else "⚠"
        console.print(f"\nVersion: {result.current_version} (current: {CURRENT_CONFIG_VERSION}) {version_status}")
    else:
        console.print(f"\nVersion: [red]Not found[/red] (current: {CURRENT_CONFIG_VERSION})")

    # Warnings
    if result.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  ⚠ {warning}")

    # Missing sections
    if result.missing_sections:
        console.print("\n[red]Missing sections:[/red]")
        for section in result.missing_sections:
            console.print(f"  - {section}")

    # Missing keys
    if result.missing_keys:
        console.print("\n[yellow]Missing keys:[/yellow]")
        for section, keys in result.missing_keys.items():
            console.print(f"  {section}:")
            for key in keys:
                console.print(f"    - {key}")

    # Summary
    console.print()
    if result.is_valid:
        console.print("[green]✓ Config is valid and up to date[/green]")
    else:
        console.print(f"[yellow]Run 'bpsai-pair config update --preset {preset}' to add missing sections.[/yellow]")

    raise typer.Exit(0 if result.is_valid else 1)


@app.command("update")
def config_update(
    preset: str = typer.Option("minimal", "--preset", "-p", help="Preset to use for defaults"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be changed without making changes"),
):
    """Update config with missing sections from preset.

    Adds missing sections and keys from the specified preset while
    preserving all existing values. Updates version number if outdated.

    Examples:
        # Update using minimal preset defaults
        bpsai-pair config update

        # Update using react preset
        bpsai-pair config update --preset react

        # Preview changes without applying
        bpsai-pair config update --dry-run
    """
    # Import here to avoid circular imports
    try:
        from ..core.config import update_config, save_raw_config
    except ImportError:
        from bpsai_pair.core.config import update_config, save_raw_config

    try:
        root = ops.find_project_root()
    except ops.ProjectRootNotFoundError:
        console.print("[red]No config file found. Run 'bpsai-pair init' first.[/red]")
        raise typer.Exit(1)

    try:
        updated_config, changes = update_config(root, preset)
    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")
        raise typer.Exit(1)

    if not changes:
        console.print("[green]✓ Config is already up to date[/green]")
        raise typer.Exit(0)

    console.print("\n[bold]Config Update[/bold]")
    console.print("=" * 40)

    console.print(f"\nUsing preset: [cyan]{preset}[/cyan]")
    console.print("\n[bold]Changes:[/bold]")
    for change in changes:
        console.print(f"  • {change}")

    if dry_run:
        console.print("\n[yellow]Dry run - no changes made[/yellow]")
        raise typer.Exit(0)

    # Save the updated config
    config_file = save_raw_config(root, updated_config)

    console.print(f"\n[green]✓ Updated {config_file}[/green]")
    console.print(f"  {len(changes)} change(s) applied")


@app.command("show")
def config_show(
    section: Optional[str] = typer.Argument(None, help="Section to show (e.g., 'hooks', 'trello')"),
):
    """Show current config or a specific section.

    Examples:
        # Show full config
        bpsai-pair config show

        # Show specific section
        bpsai-pair config show hooks
    """
    import yaml

    # Import here to avoid circular imports
    try:
        from ..core.config import load_raw_config
    except ImportError:
        from bpsai_pair.core.config import load_raw_config

    try:
        root = ops.find_project_root()
    except ops.ProjectRootNotFoundError:
        console.print("[red]No config file found. Run 'bpsai-pair init' first.[/red]")
        raise typer.Exit(1)
    raw_config, config_file = load_raw_config(root)

    if raw_config is None:
        console.print("[red]✗ No config file found[/red]")
        raise typer.Exit(1)

    console.print(f"[dim]Config: {config_file}[/dim]\n")

    if section:
        if section not in raw_config:
            console.print(f"[red]✗ Section '{section}' not found[/red]")
            console.print(f"[dim]Available: {', '.join(raw_config.keys())}[/dim]")
            raise typer.Exit(1)
        output = {section: raw_config[section]}
    else:
        output = raw_config

    console.print(yaml.dump(output, default_flow_style=False, sort_keys=False))
