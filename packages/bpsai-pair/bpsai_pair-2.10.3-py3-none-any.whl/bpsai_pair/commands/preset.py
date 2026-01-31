"""Preset commands for managing configuration presets.

Extracted from cli.py as part of EPIC-003 CLI Architecture Refactor.
"""

from __future__ import annotations

import json
import sys

import typer
from rich.console import Console
from rich.table import Table

# Try relative imports first, fall back to absolute
try:
    from ..core.presets import get_preset, list_presets, get_preset_names
except ImportError:
    from bpsai_pair.core.presets import get_preset, list_presets, get_preset_names


def print_json(data: dict) -> None:
    """Print JSON to stdout without Rich formatting."""
    sys.stdout.write(json.dumps(data, indent=2))
    sys.stdout.write("\n")
    sys.stdout.flush()


# Initialize Rich console
console = Console()

# Preset sub-app for managing configuration presets
app = typer.Typer(
    help="Manage configuration presets",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@app.command("list")
def preset_list(
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List available configuration presets."""
    presets = list_presets()

    if json_out:
        print_json([{
            "name": p.name,
            "description": p.description,
            "project_type": p.project_type,
            "coverage_target": p.coverage_target,
            "flows": p.enabled_flows,
        } for p in presets])
    else:
        table = Table(title="Available Presets")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Description")
        table.add_column("Coverage", justify="right")

        for p in presets:
            table.add_row(
                p.name,
                p.project_type,
                p.description,
                f"{p.coverage_target}%"
            )

        console.print(table)
        console.print("\n[dim]Use: bpsai-pair init --preset <name> --name <project> --goal <goal>[/dim]")


@app.command("show")
def preset_show(
    name: str = typer.Argument(..., help="Preset name"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show details for a specific preset."""
    preset = get_preset(name)

    if not preset:
        console.print(f"[red]✗ Unknown preset: {name}[/red]")
        console.print(f"[dim]Available: {', '.join(get_preset_names())}[/dim]")
        raise typer.Exit(1)

    if json_out:
        print_json({
            "name": preset.name,
            "description": preset.description,
            "project_type": preset.project_type,
            "coverage_target": preset.coverage_target,
            "default_branch_type": preset.default_branch_type,
            "main_branch": preset.main_branch,
            "python_formatter": preset.python_formatter,
            "node_formatter": preset.node_formatter,
            "ci_type": preset.ci_type,
            "flows": preset.enabled_flows,
            "pack_excludes": preset.pack_excludes,
            "model_routing": preset.model_routing,
        })
    else:
        console.print(f"[bold cyan]{preset.name}[/bold cyan]")
        console.print(f"[dim]{preset.description}[/dim]\n")

        console.print("[bold]Project Settings[/bold]")
        console.print(f"  Type: {preset.project_type}")
        console.print(f"  Coverage target: {preset.coverage_target}%")

        console.print("\n[bold]Workflow Settings[/bold]")
        console.print(f"  Branch type: {preset.default_branch_type}")
        console.print(f"  Main branch: {preset.main_branch}")

        console.print("\n[bold]CI & Formatters[/bold]")
        console.print(f"  CI workflow: {preset.ci_type}")
        console.print(f"  Python: {preset.python_formatter}")
        console.print(f"  Node: {preset.node_formatter}")

        console.print("\n[bold]Enabled Flows[/bold]")
        for flow in preset.enabled_flows:
            console.print(f"  - {flow}")

        console.print(f"\n[bold]Pack Excludes[/bold] ({len(preset.pack_excludes)} patterns)")
        for exclude in preset.pack_excludes[:5]:
            console.print(f"  - {exclude}")
        if len(preset.pack_excludes) > 5:
            console.print(f"  ... and {len(preset.pack_excludes) - 5} more")

        if preset.model_routing:
            console.print("\n[bold]Model Routing[/bold]")
            console.print("  [green]✓[/green] Complexity-based routing enabled")


@app.command("preview")
def preset_preview(
    name: str = typer.Argument(..., help="Preset name"),
    project_name: str = typer.Option("My Project", "--name", "-n", help="Project name"),
    goal: str = typer.Option("Build awesome software", "--goal", "-g", help="Primary goal"),
):
    """Preview the config.yaml that would be generated."""
    preset = get_preset(name)

    if not preset:
        console.print(f"[red]✗ Unknown preset: {name}[/red]")
        console.print(f"[dim]Available: {', '.join(get_preset_names())}[/dim]")
        raise typer.Exit(1)

    yaml_output = preset.to_yaml(project_name, goal)
    console.print("[bold]Generated config.yaml:[/bold]\n")
    console.print(yaml_output)
