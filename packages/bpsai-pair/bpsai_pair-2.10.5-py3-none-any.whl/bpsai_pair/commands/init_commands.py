"""Init commands for bpsai-pair CLI.

Contains the init and feature commands extracted from core.py:
- init: Initialize repo with governance, context, prompts, scripts, and workflows
- feature: Create feature branch and scaffold context

Also contains helper functions:
- repo_root: Get repo root with better error message
- _select_ci_workflow: Select CI workflow based on preset
- ensure_v2_config: Ensure v2 config exists
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Try relative imports first, fall back to absolute
try:
    from ..core import ops
    from ..core.config import Config
    from ..core.presets import get_preset, get_preset_names, list_presets
except ImportError:
    from bpsai_pair.core import ops
    from bpsai_pair.core.config import Config
    from bpsai_pair.core.presets import get_preset, get_preset_names, list_presets


# Initialize Rich console
console = Console()


def get_tier() -> str:
    """Get the current license tier.

    Returns:
        License tier string (e.g., "solo", "pro", "team", "enterprise")
    """
    try:
        from ..licensing import get_tier as _get_tier
        return _get_tier()
    except Exception:
        return "solo"


def get_current_tier_display_name() -> str:
    """Get the display name for the current tier.

    Returns:
        Display name (e.g., "Solo", "Pro", "Team", "Enterprise")
    """
    try:
        from ..licensing import get_current_tier_display_name as _get_display
        return _get_display()
    except Exception:
        return "Solo"


def _check_wizard_dependencies() -> bool:
    """Check if wizard dependencies are installed.

    Returns:
        True if all wizard dependencies are available
    """
    try:
        import fastapi  # noqa: F401
        import jinja2  # noqa: F401
        import uvicorn  # noqa: F401
        return True
    except ImportError:
        return False


def _launch_wizard(root: Path) -> None:
    """Launch the setup wizard.

    Args:
        root: Project root directory
    """
    import os

    # Change to project root so wizard uses correct config path
    original_cwd = os.getcwd()
    try:
        os.chdir(root)

        from bpsai_pair.commands.wizard import run_server

        console.print()
        console.print("[bold]Launching Setup Wizard...[/bold]")
        console.print("[dim]The wizard will open in your browser.[/dim]")
        console.print("[dim]Complete the wizard, then press Ctrl+C to continue.[/dim]")
        console.print()

        run_server(port=8765, no_browser=False, demo=False)
    finally:
        os.chdir(original_cwd)


def repo_root() -> Path:
    """Get repo root with better error message."""
    try:
        p = ops.find_project_root()
    except ops.ProjectRootNotFoundError:
        console.print(
            "[red]x Not in a git repository.[/red]\n"
            "Please run from your project root directory (where .git exists).\n"
            "[dim]Hint: cd to your project directory first[/dim]"
        )
        raise typer.Exit(1)
    if not ops.GitOps.is_repo(p):
        console.print(
            "[red]x Not in a git repository.[/red]\n"
            "Please run from your project root directory (where .git exists).\n"
            "[dim]Hint: cd to your project directory first[/dim]"
        )
        raise typer.Exit(1)
    return p


def _select_ci_workflow(root: Path, ci_type: str) -> None:
    """Select the appropriate CI workflow based on preset ci_type.

    Renames the preset-specific workflow to ci.yml and removes the others.

    Args:
        root: Project root directory
        ci_type: "node", "python", or "fullstack"
    """
    workflows_dir = root / ".github" / "workflows"
    if not workflows_dir.exists():
        return

    ci_yml = workflows_dir / "ci.yml"
    ci_node = workflows_dir / "ci-node.yml"
    ci_python = workflows_dir / "ci-python.yml"

    # Select the appropriate workflow based on ci_type
    if ci_type == "node" and ci_node.exists():
        # Use Node-only workflow
        if ci_yml.exists():
            ci_yml.unlink()
        ci_node.rename(ci_yml)
        if ci_python.exists():
            ci_python.unlink()
    elif ci_type == "python" and ci_python.exists():
        # Use Python-only workflow
        if ci_yml.exists():
            ci_yml.unlink()
        ci_python.rename(ci_yml)
        if ci_node.exists():
            ci_node.unlink()
    else:
        # fullstack or fallback: keep ci.yml (has both), remove variants
        if ci_node.exists():
            ci_node.unlink()
        if ci_python.exists():
            ci_python.unlink()


def _has_unrendered_cookiecutter_template(path: Path) -> bool:
    """Check if a file contains unrendered cookiecutter template variables.

    Args:
        path: Path to the file to check

    Returns:
        True if file contains {{ cookiecutter.xxx }} patterns
    """
    try:
        content = path.read_text(encoding="utf-8")
        return "{{" in content and "cookiecutter" in content
    except Exception:
        return False


def ensure_v2_config(root: Path) -> Path:
    """Ensure v2 config exists at .paircoder/config.yaml.

    - Detects and regenerates configs with unrendered cookiecutter templates.
    - If only legacy .paircoder.yml exists, it will be read and re-saved into v2 format.
    - If nothing exists, a default config will be written in v2 format.
    """
    v2_path = root / ".paircoder" / "config.yaml"

    if v2_path.exists():
        # Check for unrendered cookiecutter templates
        if _has_unrendered_cookiecutter_template(v2_path):
            console.print(
                "[yellow]⚠ Detected unrendered cookiecutter template in config.yaml, regenerating...[/yellow]"
            )
            v2_path.unlink()
        else:
            return v2_path

    # Also check alternate v2 path
    v2_yml_path = root / ".paircoder" / "config.yml"
    if v2_yml_path.exists():
        if _has_unrendered_cookiecutter_template(v2_yml_path):
            console.print(
                "[yellow]⚠ Detected unrendered cookiecutter template in config.yml, regenerating...[/yellow]"
            )
            v2_yml_path.unlink()
        else:
            return v2_yml_path

    # Load from legacy/env/defaults and persist in v2 location
    cfg = Config.load(root)
    cfg.save(root, use_v2=True)
    return v2_path


def init_command(
    template: Optional[str] = typer.Argument(
        None, help="Path to template (optional, uses bundled template if not provided)"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Interactive mode to gather project info"
    ),
    preset: Optional[str] = typer.Option(
        None, "--preset", "-p",
        help="Use a preset configuration (python-cli, python-api, react, fullstack, library, minimal, autonomous)"
    ),
    project_name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Project name (used with --preset)"
    ),
    goal: Optional[str] = typer.Option(
        None, "--goal", "-g", help="Primary goal (used with --preset)"
    ),
):
    """Initialize repo with governance, context, prompts, scripts, and workflows.

    Use --preset for quick setup with project-type-specific defaults:

        bpsai-pair init --preset python-cli --name "My CLI" --goal "Build awesome CLI"

    Available presets: python-cli, python-api, react, fullstack, library, minimal, autonomous

    Use --interactive for guided setup, or no flags for minimal scaffolding.
    """
    import yaml

    # Import here to avoid circular imports
    try:
        from .. import init_bundled_cli
    except ImportError:
        from bpsai_pair import init_bundled_cli

    root = repo_root()

    # Get license status using module-level helpers
    tier = get_tier()
    tier_display = get_current_tier_display_name()

    console.print(f"[dim]License tier: {tier_display}[/dim]")

    if tier == "solo":
        console.print(
            "[yellow]Tip:[/yellow] Activate a license for access to the Setup Wizard"
        )
        console.print(
            "[dim]Run: bpsai-pair license install <path-to-license.json>[/dim]"
        )

    # Offer wizard to licensed users (unless using --preset or --interactive)
    if tier != "solo" and not preset and not interactive:
        if _check_wizard_dependencies():
            use_wizard = typer.confirm(
                "Would you like to use the Setup Wizard?",
                default=True
            )
            if use_wizard:
                _launch_wizard(root)
                return
        else:
            console.print(
                "[dim]Tip: Install wizard dependencies for web-based setup:[/dim]"
            )
            console.print("[dim]  pip install bpsai-pair[wizard][/dim]")

    preexisting_config = Config.find_config_file(root)

    # Handle preset-based initialization
    if preset:
        preset_obj = get_preset(preset)
        if not preset_obj:
            console.print(f"[red]x Unknown preset: {preset}[/red]")
            console.print(f"[dim]Available presets: {', '.join(get_preset_names())}[/dim]")
            raise typer.Exit(1)

        # Get project name and goal
        p_name = project_name or typer.prompt("Project name", default="My Project")
        p_goal = goal or typer.prompt("Primary goal", default="Build awesome software")

        # Generate config from preset
        config_dict = preset_obj.to_config_dict(p_name, p_goal)

        # Ensure .paircoder directory exists
        paircoder_dir = root / ".paircoder"
        paircoder_dir.mkdir(exist_ok=True)

        # Write config file
        config_file = paircoder_dir / "config.yaml"
        with open(config_file, 'w', encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

        console.print(f"[green]![/green] Applied preset: {preset}")
        console.print(f"  Project: {p_name}")
        console.print(f"  Goal: {p_goal}")
        console.print(f"  Coverage target: {preset_obj.coverage_target}%")
        console.print(f"  Flows: {', '.join(preset_obj.enabled_flows)}")

    elif interactive:
        # Interactive mode to gather project information
        pname = typer.prompt("Project name", default="My Project")
        primary_goal = typer.prompt("Primary goal", default="Build awesome software")
        coverage = typer.prompt("Coverage target (%)", default="80")

        # Ask about preset selection
        console.print("\n[bold]Available presets:[/bold]")
        for p in list_presets():
            console.print(f"  {p.name}: {p.description}")

        use_preset = typer.confirm("\nWould you like to use a preset?", default=False)
        if use_preset:
            preset_choice = typer.prompt(
                "Select preset",
                default="python-cli"
            )
            preset_obj = get_preset(preset_choice)
            if preset_obj:
                config_dict = preset_obj.to_config_dict(pname, primary_goal)
                config_dict["project"]["coverage_target"] = int(coverage)

                paircoder_dir = root / ".paircoder"
                paircoder_dir.mkdir(exist_ok=True)
                config_file = paircoder_dir / "config.yaml"
                with open(config_file, 'w', encoding="utf-8") as f:
                    yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
                console.print(f"[green]![/green] Applied preset: {preset_choice}")
            else:
                console.print("[yellow]! Unknown preset, using defaults[/yellow]")
                config = Config(
                    project_name=pname,
                    primary_goal=primary_goal,
                    coverage_target=int(coverage)
                )
                config.save(root, use_v2=True)
        else:
            # Create a config file without preset
            config = Config(
                project_name=pname,
                primary_goal=primary_goal,
                coverage_target=int(coverage)
            )
            config.save(root, use_v2=True)

    # Use bundled template if none provided
    if template is None:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing scaffolding...", total=None)
            result = init_bundled_cli.main()
            progress.update(task, completed=True)

        # Check if bundled template initialization failed
        if result != 0:
            console.print("[red]x Failed to initialize bundled scaffolding[/red]")
            console.print("[dim]The packaged template may be missing or corrupted.[/dim]")
            raise typer.Exit(1)

        # Select preset-specific CI workflow if a preset was used
        if preset:
            _select_ci_workflow(root, preset_obj.ci_type)

        console.print("[green]![/green] Initialized repo with pair-coding scaffolding")
        # Ensure v2 configuration exists (canonical: .paircoder/config.yaml)
        if not preset:  # Don't overwrite preset config
            ensure_v2_config(root)
        console.print("[dim]Review diffs and commit changes[/dim]")

        # Show next steps including Trello setup
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Review and commit the generated files")
        console.print("  2. Read .paircoder/context/state.md to understand the workflow")
        console.print("\n[bold]Optional - Connect to Trello:[/bold]")
        console.print("  1. Get API key from [link=https://trello.com/power-ups/admin]trello.com/power-ups/admin[/link]")
        console.print("  2. Set environment variables:")
        console.print("     [dim]export TRELLO_API_KEY=your_key[/dim]")
        console.print("     [dim]export TRELLO_TOKEN=your_token[/dim]")
        console.print("  3. Run: [bold]bpsai-pair trello connect[/bold]")
        console.print("  4. Run: [bold]bpsai-pair trello use-board <board-id>[/bold]")
        console.print("\n[dim]See .paircoder/docs/USER_GUIDE.md for full documentation[/dim]")
    else:
        # Use provided template (simplified for now)
        console.print(f"[yellow]Using template: {template}[/yellow]")
        # Ensure v2 configuration exists (canonical: .paircoder/config.yaml)
        if not preset:  # Don't overwrite preset config
            ensure_v2_config(root)
        # If this repo had no config before init ran, ensure we have a canonical v2 config file.
        # This keeps v1 repos stable (no surprise migrations) while making new scaffolds v2-native.
        if preexisting_config is None and not preset:
            v2_config = root / ".paircoder" / "config.yaml"
            v2_config_yml = root / ".paircoder" / "config.yml"
            if not v2_config.exists() and not v2_config_yml.exists():
                # Use defaults/env (or the legacy config that the template may have created)
                # and persist them to the canonical v2 location.
                Config.load(root).save(root, use_v2=True)


def feature_command(
    name: str = typer.Argument(..., help="Feature branch name (without prefix)"),
    primary: str = typer.Option("", "--primary", "-p", help="Primary goal to stamp into context"),
    phase: str = typer.Option("", "--phase", help="Phase goal for Next action"),
    force: bool = typer.Option(False, "--force", "-f", help="Bypass dirty-tree check"),
    type: str = typer.Option(
        "feature",
        "--type",
        "-t",
        help="Branch type: feature|fix|refactor",
        case_sensitive=False,
    ),
):
    """Create feature branch and scaffold context (cross-platform)."""
    root = repo_root()

    # Validate branch type
    branch_type = type.lower()
    if branch_type not in {"feature", "fix", "refactor"}:
        console.print(
            f"[red]x Invalid branch type: {type}[/red]\n"
            "Must be one of: feature, fix, refactor"
        )
        raise typer.Exit(1)

    # Use Python ops instead of shell script
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Creating {branch_type}/{name}...", total=None)

        try:
            if force:
                from ..core.bypass_log import log_bypass
                log_bypass(
                    command="feature",
                    target=name,
                    reason="Bypassing dirty-tree check",
                    bypass_type="dirty_tree_bypass",
                )

            ops.FeatureOps.create_feature(
                root=root,
                name=name,
                branch_type=branch_type,
                primary_goal=primary,
                phase=phase,
                force=force
            )
            progress.update(task, completed=True)

            console.print(f"[green]![/green] Created branch [bold]{branch_type}/{name}[/bold]")
            console.print("[green]![/green] Updated context with primary goal and phase")
            console.print("[dim]Next: Connect your agent and share /context files[/dim]")

        except ValueError as e:
            progress.update(task, completed=True)
            console.print(f"[red]x {e}[/red]")
            raise typer.Exit(1)
