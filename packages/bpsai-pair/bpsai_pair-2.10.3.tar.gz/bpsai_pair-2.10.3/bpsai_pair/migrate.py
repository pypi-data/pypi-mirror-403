"""Migration command for upgrading legacy PairCoder structures."""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console

console = Console()


class LegacyVersion(Enum):
    """PairCoder version detection."""
    V1_LEGACY = "v1.x"           # .paircoder.yml + context/
    V2_EARLY = "v2.0-2.1"        # .paircoder/ but missing pieces
    V2_PARTIAL = "v2.2-2.3"      # Has structure, missing config sections
    V2_CURRENT = "v2.4+"         # Current format
    UNKNOWN = "unknown"


@dataclass
class MigrationPlan:
    """What needs to happen during migration."""
    source_version: LegacyVersion
    target_version: str = "2.5"

    # Files to move
    file_moves: list[tuple[Path, Path]] = field(default_factory=list)

    # Directories to create
    dirs_to_create: list[Path] = field(default_factory=list)

    # Config sections to add
    config_additions: dict = field(default_factory=dict)

    # Files to delete after migration
    files_to_delete: list[Path] = field(default_factory=list)

    # Warnings/notes for user
    warnings: list[str] = field(default_factory=list)


def detect_version(project_root: Path) -> LegacyVersion:
    """Detect which version of PairCoder structure exists."""

    # v1.x indicators
    has_legacy_yml = (project_root / ".paircoder.yml").exists()
    has_root_context = (project_root / "context").is_dir()

    # v2.x indicators
    has_paircoder_dir = (project_root / ".paircoder").is_dir()
    has_config_yaml = (project_root / ".paircoder" / "config.yaml").exists()

    if has_legacy_yml or (has_root_context and not has_paircoder_dir):
        return LegacyVersion.V1_LEGACY

    if has_paircoder_dir and has_config_yaml:
        # Check config version
        try:
            config = yaml.safe_load((project_root / ".paircoder" / "config.yaml").read_text(encoding="utf-8"))
            version = str(config.get("version", "1.0"))

            # v2.4+ is current
            if any(version.startswith(v) for v in ["2.4", "2.5", "2.6", "2.7", "2.8", "2.9", "3."]):
                return LegacyVersion.V2_CURRENT
            elif version.startswith("2.2") or version.startswith("2.3"):
                return LegacyVersion.V2_PARTIAL
            else:
                return LegacyVersion.V2_EARLY
        except Exception:
            return LegacyVersion.V2_EARLY

    if has_paircoder_dir and not has_config_yaml:
        return LegacyVersion.V2_EARLY

    return LegacyVersion.UNKNOWN


def plan_migration(project_root: Path, preset: Optional[str] = None) -> MigrationPlan:
    """Create a migration plan based on detected version."""
    version = detect_version(project_root)
    plan = MigrationPlan(source_version=version)

    paircoder_dir = project_root / ".paircoder"
    claude_dir = project_root / ".claude"

    if version == LegacyVersion.V1_LEGACY:
        # Full migration from v1.x
        plan.dirs_to_create = [
            paircoder_dir,
            paircoder_dir / "context",
            paircoder_dir / "flows",
            paircoder_dir / "plans",
            paircoder_dir / "tasks",
            paircoder_dir / "history",
            claude_dir,
            claude_dir / "skills",
            claude_dir / "agents",
        ]

        # Move context files
        if (project_root / "context" / "development.md").exists():
            plan.file_moves.append((
                project_root / "context" / "development.md",
                paircoder_dir / "context" / "state.md"
            ))
            plan.warnings.append(
                "state.md format has changed - manual review recommended"
            )

        if (project_root / "context" / "project.md").exists():
            plan.file_moves.append((
                project_root / "context" / "project.md",
                paircoder_dir / "context" / "project.md"
            ))

        # Mark for deletion after successful migration
        if (project_root / ".paircoder.yml").exists():
            plan.files_to_delete.append(project_root / ".paircoder.yml")
        if (project_root / "context").is_dir():
            plan.files_to_delete.append(project_root / "context")
        if (project_root / "prompts").is_dir():
            plan.files_to_delete.append(project_root / "prompts")

        plan.warnings.append(
            ".paircoder.yml config needs manual conversion to config.yaml"
        )

    elif version == LegacyVersion.V2_EARLY:
        # Add missing directories
        for subdir in ["flows", "plans", "tasks", "history", "context"]:
            path = paircoder_dir / subdir
            if not path.exists():
                plan.dirs_to_create.append(path)

        if not claude_dir.exists():
            plan.dirs_to_create.extend([
                claude_dir,
                claude_dir / "skills",
                claude_dir / "agents",
            ])

    elif version == LegacyVersion.V2_PARTIAL:
        # Check for missing directories
        for subdir in ["flows", "plans", "tasks", "history"]:
            path = paircoder_dir / subdir
            if not path.exists():
                plan.dirs_to_create.append(path)

        if not claude_dir.exists():
            plan.dirs_to_create.extend([
                claude_dir,
                claude_dir / "skills",
                claude_dir / "agents",
            ])

    # For v2.x versions, check config sections
    if version in [LegacyVersion.V2_EARLY, LegacyVersion.V2_PARTIAL]:
        config_path = paircoder_dir / "config.yaml"
        if config_path.exists():
            try:
                config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            except Exception:
                config = {}

            # Check for missing sections
            if "trello" not in config:
                plan.config_additions["trello"] = {
                    "enabled": False,
                    "board_id": "",
                }

            if "hooks" not in config:
                plan.config_additions["hooks"] = {
                    "enabled": True,
                    "on_task_start": ["start_timer", "sync_trello", "update_state"],
                    "on_task_complete": ["stop_timer", "record_metrics", "sync_trello", "update_state", "check_unblocked"],
                }

            if "estimation" not in config:
                plan.config_additions["estimation"] = {
                    "complexity_to_hours": {
                        "xs": {"range": [0, 15], "hours": [0.5, 1.0, 2.0]},
                        "s": {"range": [16, 30], "hours": [1.0, 2.0, 4.0]},
                        "m": {"range": [31, 50], "hours": [2.0, 4.0, 8.0]},
                        "l": {"range": [51, 75], "hours": [4.0, 8.0, 16.0]},
                        "xl": {"range": [76, 100], "hours": [8.0, 16.0, 32.0]},
                    }
                }

            if "metrics" not in config:
                plan.config_additions["metrics"] = {
                    "enabled": True,
                    "store_path": ".paircoder/history/metrics.jsonl",
                }

    # Check for missing root files
    if not (project_root / "CLAUDE.md").exists():
        plan.warnings.append("CLAUDE.md missing - will be created from template")

    if not (project_root / "AGENTS.md").exists():
        plan.warnings.append("AGENTS.md missing - will be created from template")

    return plan


def create_backup(project_root: Path) -> Path:
    """Create timestamped backup of .paircoder/ and related files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_root / f".paircoder_backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    if (project_root / ".paircoder").exists():
        shutil.copytree(project_root / ".paircoder", backup_dir / ".paircoder")

    if (project_root / ".claude").exists():
        shutil.copytree(project_root / ".claude", backup_dir / ".claude")

    # v1.x files
    if (project_root / ".paircoder.yml").exists():
        shutil.copy2(project_root / ".paircoder.yml", backup_dir / ".paircoder.yml")

    if (project_root / "context").is_dir():
        shutil.copytree(project_root / "context", backup_dir / "context")

    return backup_dir


def execute_migration(project_root: Path, plan: MigrationPlan) -> None:
    """Execute the migration plan."""

    # Create directories
    for dir_path in plan.dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Move files
    for src, dst in plan.file_moves:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))

    # Update config
    if plan.config_additions:
        config_path = project_root / ".paircoder" / "config.yaml"
        if config_path.exists():
            try:
                config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            except Exception:
                config = {}
            config.update(plan.config_additions)
            config["version"] = plan.target_version

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Delete old files (only after everything else succeeds)
    for path in plan.files_to_delete:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            path.unlink(missing_ok=True)


# Typer CLI app
migrate_app = typer.Typer(
    help="Migrate legacy PairCoder structures to current version",
    context_settings={"help_option_names": ["-h", "--help"]}
)


@migrate_app.callback(invoke_without_command=True)
def migrate(
    ctx: typer.Context,
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would change without making changes"),
    no_backup: bool = typer.Option(False, "--no-backup", help="Skip backup creation"),
    preset: Optional[str] = typer.Option(None, "--preset", "-p", help="Preset to use for missing config sections"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Migrate legacy PairCoder structure to current version."""
    if ctx.invoked_subcommand is not None:
        return

    project_root = Path.cwd()

    # Detect and plan
    version = detect_version(project_root)
    console.print(f"Detected version: [cyan]{version.value}[/]")

    if version == LegacyVersion.V2_CURRENT:
        console.print("[green]✅ Already at current version. No migration needed.[/]")
        return

    if version == LegacyVersion.UNKNOWN:
        console.print("[red]❌ Could not detect PairCoder structure. Run 'bpsai-pair init' instead.[/]")
        raise typer.Exit(1)

    plan = plan_migration(project_root, preset)

    # Show plan
    console.print("\n[bold]📋 Migration Plan:[/]")

    if plan.dirs_to_create:
        console.print("\n  [bold]Directories to create:[/]")
        for d in plan.dirs_to_create:
            try:
                rel_path = d.relative_to(project_root)
            except ValueError:
                rel_path = d
            console.print(f"    📁 {rel_path}")

    if plan.file_moves:
        console.print("\n  [bold]Files to move:[/]")
        for src, dst in plan.file_moves:
            try:
                src_rel = src.relative_to(project_root)
                dst_rel = dst.relative_to(project_root)
            except ValueError:
                src_rel, dst_rel = src, dst
            console.print(f"    📄 {src_rel} → {dst_rel}")

    if plan.config_additions:
        console.print("\n  [bold]Config sections to add:[/]")
        for section in plan.config_additions:
            console.print(f"    ⚙️  {section}")

    if plan.files_to_delete:
        console.print("\n  [bold]Files to remove after migration:[/]")
        for f in plan.files_to_delete:
            try:
                rel_path = f.relative_to(project_root)
            except ValueError:
                rel_path = f
            console.print(f"    🗑️  {rel_path}")

    if plan.warnings:
        console.print("\n  [yellow]⚠️  Warnings:[/]")
        for w in plan.warnings:
            console.print(f"    • {w}")

    if dry_run:
        console.print("\n[dim]--dry-run specified. No changes made.[/]")
        return

    # Confirm
    if not force:
        proceed = typer.confirm("\nProceed with migration?")
        if not proceed:
            console.print("Aborted.")
            return

    # Backup
    if not no_backup:
        console.print("\n[bold]📦 Creating backup...[/]")
        backup_path = create_backup(project_root)
        console.print(f"   Backup saved to: {backup_path}")

    # Execute
    console.print("\n[bold]🔄 Migrating...[/]")
    execute_migration(project_root, plan)

    console.print("\n[green]✅ Migration complete![/]")
    console.print("\n[bold]Next steps:[/]")
    console.print("  1. Review .paircoder/config.yaml")
    console.print("  2. Run 'bpsai-pair validate' to check structure")
    console.print("  3. Run 'bpsai-pair status' to verify")


@migrate_app.command("status")
def migrate_status():
    """Show current PairCoder version status."""
    project_root = Path.cwd()
    version = detect_version(project_root)

    console.print(f"Detected version: [cyan]{version.value}[/]")

    if version == LegacyVersion.V2_CURRENT:
        console.print("[green]✅ Up to date - no migration needed[/]")
    elif version == LegacyVersion.UNKNOWN:
        console.print("[yellow]⚠️  No PairCoder structure detected[/]")
        console.print("   Run 'bpsai-pair init' to initialize")
    else:
        console.print("[yellow]⚠️  Migration available[/]")
        console.print("   Run 'bpsai-pair migrate --dry-run' to see changes")
