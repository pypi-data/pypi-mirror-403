"""Upgrade command for updating existing v2.x projects.

Extracted from T-upgrade-command-spec.md as part of Sprint 23 Critical Fixes.

Commands:
- upgrade: Upgrade existing v2.x project with latest skills, agents, and docs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import shutil

import typer
from rich.console import Console

# Try relative imports first, fall back to absolute
try:
    from ..core import ops
except ImportError:
    from bpsai_pair.core import ops

console = Console()


@dataclass
class UpgradePlan:
    """What will be upgraded."""
    skills_to_update: list = field(default_factory=list)
    skills_to_add: list = field(default_factory=list)
    agents_to_update: list = field(default_factory=list)
    agents_to_add: list = field(default_factory=list)
    commands_to_update: list = field(default_factory=list)
    commands_to_add: list = field(default_factory=list)
    docs_to_update: list = field(default_factory=list)
    config_sections_to_add: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def get_template_dir() -> Optional[Path]:
    """Get path to cookiecutter template in installed package.

    Uses importlib.resources for robust package data access that works
    in both development mode and when pip-installed from a wheel.
    """
    template_subpath = ("cookiecutter-paircoder", "{{cookiecutter.project_slug}}")

    # Primary: Use importlib.resources (works for both dev and installed)
    try:
        import importlib.resources as resources

        # Get the package data directory as a Traversable
        data_dir = resources.files("bpsai_pair.data")

        # Use joinpath to navigate to the template directory
        # This returns a Path-like object that works with both
        # filesystem packages and zip-imported packages
        template_traversable = data_dir.joinpath(*template_subpath)

        # Convert to Path - str() works for all Traversable types
        template_dir = Path(str(template_traversable))
        if template_dir.exists():
            return template_dir
    except (ModuleNotFoundError, TypeError, AttributeError):
        # ModuleNotFoundError: bpsai_pair.data doesn't exist as a package
        # TypeError/AttributeError: importlib.resources API issue
        pass

    # Fallback: Development mode with direct file path
    cli_dir = Path(__file__).parent.parent
    template_dir = cli_dir / "data" / template_subpath[0] / template_subpath[1]
    if template_dir.exists():
        return template_dir

    return None


def get_bundled_skills(template: Path) -> dict:
    """Get all skills bundled with the CLI."""
    skills_dir = template / ".claude" / "skills"
    skills = {}

    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    skills[skill_dir.name] = skill_file

    return skills


def get_bundled_agents(template: Path) -> dict:
    """Get all agents bundled with the CLI."""
    agents_dir = template / ".claude" / "agents"
    agents = {}

    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            agents[agent_file.stem] = agent_file

    return agents


def get_bundled_commands(template: Path) -> dict:
    """Get all commands bundled with the CLI.

    Note: Commands are .md files in .claude/commands/ that define
    slash commands for Claude Code.
    """
    commands_dir = template / ".claude" / "commands"
    commands = {}

    if commands_dir.exists():
        for cmd_file in commands_dir.glob("*.md"):
            commands[cmd_file.stem] = cmd_file

    return commands


def plan_upgrade(project_root: Path, template: Path) -> UpgradePlan:
    """Create upgrade plan by comparing project to template."""
    plan = UpgradePlan()

    # Check skills
    bundled_skills = get_bundled_skills(template)
    project_skills_dir = project_root / ".claude" / "skills"

    for skill_name, skill_path in bundled_skills.items():
        project_skill = project_skills_dir / skill_name / "SKILL.md"
        if not project_skill.exists():
            plan.skills_to_add.append(skill_name)
        else:
            try:
                if project_skill.read_text(encoding="utf-8") != skill_path.read_text(encoding="utf-8"):
                    plan.skills_to_update.append(skill_name)
            except Exception:
                plan.warnings.append(f"Could not compare skill: {skill_name}")

    # Check agents
    bundled_agents = get_bundled_agents(template)
    project_agents_dir = project_root / ".claude" / "agents"

    for agent_name, agent_path in bundled_agents.items():
        project_agent = project_agents_dir / f"{agent_name}.md"
        if not project_agent.exists():
            plan.agents_to_add.append(agent_name)
        else:
            try:
                if project_agent.read_text(encoding="utf-8") != agent_path.read_text(encoding="utf-8"):
                    plan.agents_to_update.append(agent_name)
            except Exception:
                plan.warnings.append(f"Could not compare agent: {agent_name}")

    # Check commands (slash commands in .claude/commands/)
    bundled_commands = get_bundled_commands(template)
    project_commands_dir = project_root / ".claude" / "commands"

    for cmd_name, cmd_path in bundled_commands.items():
        project_cmd = project_commands_dir / f"{cmd_name}.md"
        if not project_cmd.exists():
            plan.commands_to_add.append(cmd_name)
        else:
            try:
                if project_cmd.read_text(encoding="utf-8") != cmd_path.read_text(encoding="utf-8"):
                    plan.commands_to_update.append(cmd_name)
            except Exception:
                plan.warnings.append(f"Could not compare command: {cmd_name}")

    # Check safe docs (never touch state.md, project.md, or config values)
    safe_docs = [
        ("CLAUDE.md", "CLAUDE.md"),
        ("AGENTS.md", "AGENTS.md"),
        (".paircoder/capabilities.yaml", ".paircoder/capabilities.yaml"),
        (".paircoder/context/workflow.md", ".paircoder/context/workflow.md"),
        (".claude/settings.json", ".claude/settings.json"),
    ]

    for template_rel, project_rel in safe_docs:
        template_file = template / template_rel
        project_file = project_root / project_rel

        if template_file.exists():
            if not project_file.exists():
                plan.docs_to_update.append(project_rel)
            else:
                try:
                    if project_file.read_text(encoding="utf-8") != template_file.read_text(encoding="utf-8"):
                        plan.docs_to_update.append(project_rel)
                except Exception:
                    plan.warnings.append(f"Could not compare doc: {project_rel}")

    # Check config sections
    config_path = project_root / ".paircoder" / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

            required_sections = ["trello", "hooks", "estimation", "metrics"]
            for section in required_sections:
                if section not in config:
                    plan.config_sections_to_add.append(section)
        except Exception:
            plan.warnings.append("Could not parse config.yaml")

    return plan


def execute_upgrade(
    project_root: Path,
    template: Path,
    plan: UpgradePlan,
    skills: bool = True,
    agents: bool = True,
    commands: bool = True,
    docs: bool = True,
    config: bool = True,
) -> dict:
    """Execute the upgrade plan.

    Returns:
        Dict with counts of what was updated
    """
    results = {
        "skills_added": 0,
        "skills_updated": 0,
        "agents_added": 0,
        "agents_updated": 0,
        "commands_added": 0,
        "commands_updated": 0,
        "docs_updated": 0,
        "config_sections_added": 0,
    }

    # Update skills
    if skills:
        bundled_skills = get_bundled_skills(template)
        for skill_name in plan.skills_to_add:
            if skill_name in bundled_skills:
                src = bundled_skills[skill_name]
                dst_dir = project_root / ".claude" / "skills" / skill_name
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst_dir / "SKILL.md")
                results["skills_added"] += 1

        for skill_name in plan.skills_to_update:
            if skill_name in bundled_skills:
                src = bundled_skills[skill_name]
                dst_dir = project_root / ".claude" / "skills" / skill_name
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst_dir / "SKILL.md")
                results["skills_updated"] += 1

    # Update agents
    if agents:
        bundled_agents = get_bundled_agents(template)
        for agent_name in plan.agents_to_add:
            if agent_name in bundled_agents:
                src = bundled_agents[agent_name]
                dst_dir = project_root / ".claude" / "agents"
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst_dir / f"{agent_name}.md")
                results["agents_added"] += 1

        for agent_name in plan.agents_to_update:
            if agent_name in bundled_agents:
                src = bundled_agents[agent_name]
                dst_dir = project_root / ".claude" / "agents"
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst_dir / f"{agent_name}.md")
                results["agents_updated"] += 1

    # Update commands (slash commands in .claude/commands/)
    if commands:
        bundled_commands = get_bundled_commands(template)
        for cmd_name in plan.commands_to_add:
            if cmd_name in bundled_commands:
                src = bundled_commands[cmd_name]
                dst_dir = project_root / ".claude" / "commands"
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst_dir / f"{cmd_name}.md")
                results["commands_added"] += 1

        for cmd_name in plan.commands_to_update:
            if cmd_name in bundled_commands:
                src = bundled_commands[cmd_name]
                dst_dir = project_root / ".claude" / "commands"
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst_dir / f"{cmd_name}.md")
                results["commands_updated"] += 1

    # Update docs
    if docs:
        for doc_rel in plan.docs_to_update:
            src = template / doc_rel
            dst = project_root / doc_rel
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                results["docs_updated"] += 1

    # Add config sections (merge, don't overwrite)
    if config and plan.config_sections_to_add:
        config_path = project_root / ".paircoder" / "config.yaml"
        if config_path.exists():
            try:
                import yaml
                config_data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

                defaults = {
                    "trello": {
                        "enabled": False,
                        "board_id": "",
                    },
                    "hooks": {
                        "enabled": True,
                        "on_task_start": ["start_timer", "sync_trello", "update_state"],
                        "on_task_complete": ["stop_timer", "record_metrics", "sync_trello", "update_state", "check_unblocked"],
                        "on_task_block": ["sync_trello", "update_state"],
                    },
                    "estimation": {
                        "complexity_to_hours": {
                            "xs": {"range": [0, 15], "hours": [0.5, 1.0, 2.0]},
                            "s": {"range": [16, 30], "hours": [1.0, 2.0, 4.0]},
                            "m": {"range": [31, 50], "hours": [2.0, 4.0, 8.0]},
                            "l": {"range": [51, 75], "hours": [4.0, 8.0, 16.0]},
                            "xl": {"range": [76, 100], "hours": [8.0, 16.0, 32.0]},
                        }
                    },
                    "metrics": {
                        "enabled": True,
                        "store_path": ".paircoder/history/metrics.jsonl",
                    },
                }

                for section in plan.config_sections_to_add:
                    if section in defaults:
                        config_data[section] = defaults[section]
                        results["config_sections_added"] += 1

                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not update config: {e}[/yellow]")

    return results


# Typer app for upgrade command
upgrade_app = typer.Typer(
    help="Upgrade existing v2.x project with latest content",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@upgrade_app.callback(invoke_without_command=True)
def upgrade_command(
    ctx: typer.Context,
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would change without making changes"),
    only_skills: bool = typer.Option(False, "--skills", help="Only update skills"),
    only_agents: bool = typer.Option(False, "--agents", help="Only update agents"),
    only_commands: bool = typer.Option(False, "--commands", help="Only update slash commands"),
    only_docs: bool = typer.Option(False, "--docs", help="Only update safe doc files"),
    only_config: bool = typer.Option(False, "--config", help="Only add missing config sections"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Upgrade existing v2.x project with latest skills, agents, commands, and docs.

    This command updates generic project files without touching project-specific
    content like state.md, project.md, or existing config values.

    Safe files (always update):
    - CLAUDE.md, AGENTS.md
    - .paircoder/capabilities.yaml
    - .paircoder/context/workflow.md
    - .claude/skills/* (all skills)
    - .claude/agents/* (all agents)
    - .claude/commands/* (all slash commands)

    Never touched:
    - .paircoder/context/state.md
    - .paircoder/context/project.md
    - .paircoder/plans/*, .paircoder/tasks/*
    - Existing config values (board_id, project name, etc.)
    """
    # Skip if a subcommand is being invoked
    if ctx.invoked_subcommand is not None:
        return

    project_root = ops.find_project_root()

    # Check this is a v2.x project
    paircoder_dir = project_root / ".paircoder"
    if not paircoder_dir.exists():
        console.print("[red]No .paircoder/ directory found. Run 'bpsai-pair init' first.[/red]")
        raise typer.Exit(1)

    config_path = paircoder_dir / "config.yaml"
    if not config_path.exists():
        console.print("[red]No config.yaml found. Run 'bpsai-pair init' first.[/red]")
        raise typer.Exit(1)

    # Get template directory
    template = get_template_dir()
    if not template:
        console.print("[red]Could not find bundled template. Is bpsai-pair installed correctly?[/red]")
        raise typer.Exit(1)

    # Plan upgrade
    plan = plan_upgrade(project_root, template)

    # Check if anything needs updating
    has_updates = any([
        plan.skills_to_add,
        plan.skills_to_update,
        plan.agents_to_add,
        plan.agents_to_update,
        plan.commands_to_add,
        plan.commands_to_update,
        plan.docs_to_update,
        plan.config_sections_to_add,
    ])

    if not has_updates:
        console.print("[green]Project is up to date. Nothing to upgrade.[/green]")
        return

    # Show plan
    console.print("\n[bold]Upgrade Plan:[/bold]\n")

    if plan.skills_to_add:
        console.print("  [cyan]Skills to add:[/cyan]")
        for s in plan.skills_to_add:
            console.print(f"    + {s}")

    if plan.skills_to_update:
        console.print("  [cyan]Skills to update:[/cyan]")
        for s in plan.skills_to_update:
            console.print(f"    ~ {s}")

    if plan.agents_to_add:
        console.print("  [cyan]Agents to add:[/cyan]")
        for a in plan.agents_to_add:
            console.print(f"    + {a}")

    if plan.agents_to_update:
        console.print("  [cyan]Agents to update:[/cyan]")
        for a in plan.agents_to_update:
            console.print(f"    ~ {a}")

    if plan.commands_to_add:
        console.print("  [cyan]Commands to add:[/cyan]")
        for c in plan.commands_to_add:
            console.print(f"    + {c}")

    if plan.commands_to_update:
        console.print("  [cyan]Commands to update:[/cyan]")
        for c in plan.commands_to_update:
            console.print(f"    ~ {c}")

    if plan.docs_to_update:
        console.print("  [cyan]Docs to update:[/cyan]")
        for d in plan.docs_to_update:
            console.print(f"    ~ {d}")

    if plan.config_sections_to_add:
        console.print("  [cyan]Config sections to add:[/cyan]")
        for c in plan.config_sections_to_add:
            console.print(f"    + {c}")

    if plan.warnings:
        console.print("\n  [yellow]Warnings:[/yellow]")
        for w in plan.warnings:
            console.print(f"    ! {w}")

    if dry_run:
        console.print("\n[dim]--dry-run specified. No changes made.[/dim]")
        return

    # Determine what to upgrade
    # If no specific flags, upgrade everything
    upgrade_all = not any([only_skills, only_agents, only_commands, only_docs, only_config])

    do_skills = upgrade_all or only_skills
    do_agents = upgrade_all or only_agents
    do_commands = upgrade_all or only_commands
    do_docs = upgrade_all or only_docs
    do_config = upgrade_all or only_config

    # Confirm unless forced
    if not force:
        console.print("")
        confirm = typer.confirm("Proceed with upgrade?")
        if not confirm:
            console.print("[dim]Aborted.[/dim]")
            raise typer.Exit(0)

    # Execute
    console.print("\n[bold]Upgrading...[/bold]")
    results = execute_upgrade(
        project_root,
        template,
        plan,
        skills=do_skills,
        agents=do_agents,
        commands=do_commands,
        docs=do_docs,
        config=do_config,
    )

    console.print("\n[green]Upgrade complete![/green]")

    # Summary
    summary_parts = []
    if do_skills and (results["skills_added"] or results["skills_updated"]):
        summary_parts.append(f"{results['skills_added']} skills added, {results['skills_updated']} updated")
    if do_agents and (results["agents_added"] or results["agents_updated"]):
        summary_parts.append(f"{results['agents_added']} agents added, {results['agents_updated']} updated")
    if do_commands and (results["commands_added"] or results["commands_updated"]):
        summary_parts.append(f"{results['commands_added']} commands added, {results['commands_updated']} updated")
    if do_docs and results["docs_updated"]:
        summary_parts.append(f"{results['docs_updated']} docs updated")
    if do_config and results["config_sections_added"]:
        summary_parts.append(f"{results['config_sections_added']} config sections added")

    if summary_parts:
        console.print(f"  {', '.join(summary_parts)}")


def register_upgrade_command(app: typer.Typer):
    """Register upgrade command with the main app."""
    app.add_typer(upgrade_app, name="upgrade")
