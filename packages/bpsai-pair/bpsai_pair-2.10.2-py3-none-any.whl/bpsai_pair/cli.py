"""Main CLI module for bpsai-pair.

This module is the entry point for the CLI and handles only:
- App creation and configuration
- Sub-app registration
- Version callback

All command implementations are in the `commands/` package:
- commands/core.py: init, feature, pack, context-sync, status, validate, ci
- commands/preset.py: preset list, show, preview
- commands/config.py: config validate, update, show
- commands/orchestrate.py: orchestrate task, analyze, select-agent, handoff, etc.
- commands/metrics.py: metrics summary, task, breakdown, budget, velocity, etc.
- commands/timer.py: timer start, stop, status, show, summary
- commands/benchmark.py: benchmark run, results, compare, list
- commands/cache.py: cache stats, clear, invalidate
- commands/mcp.py: mcp serve, tools, test
- commands/security.py: security scan-secrets, pre-commit, install-hook, scan-deps
- commands/session.py: session check, status; compaction snapshot, check, recover, cleanup

Architecture refactored in Sprint 22 (EPIC-003 Phase 1).
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from .commands.audit import app as audit_app
from .commands.state import app as state_app

try:
    from . import __version__
    from .planning.commands import (
        plan_app, task_app, intent_app, standup_app
    )
    from .sprint import sprint_app
    from .release import release_app, template_app
    from .skills.cli_commands import skill_app, subagent_app, gaps_app
    from .trello.commands import app as trello_app
    from .trello.task_commands import app as trello_task_app
    from .github.commands import app as github_app
    from .migrate import migrate_app
    from .commands import (
        preset_app, config_app, orchestrate_app, metrics_app,
        timer_app, benchmark_app, cache_app, mcp_app,
        security_app, scan_secrets, scan_deps, register_core_commands,
        session_app, compaction_app, containment_app, upgrade_app, budget_app,
        contained_auto, claude666, enforce_app, arch_app, license_app, wizard_app
    )
except ImportError:
    # For development/testing when running as script
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bpsai_pair import __version__
    from bpsai_pair.planning.commands import (
        plan_app, task_app, intent_app, standup_app
    )
    from bpsai_pair.sprint import sprint_app
    from bpsai_pair.release import release_app, template_app
    from bpsai_pair.skills.cli_commands import skill_app, subagent_app, gaps_app
    from bpsai_pair.trello.commands import app as trello_app
    from bpsai_pair.trello.task_commands import app as trello_task_app
    from bpsai_pair.github.commands import app as github_app
    from bpsai_pair.migrate import migrate_app
    from bpsai_pair.commands import (
        preset_app, config_app, orchestrate_app, metrics_app,
        timer_app, benchmark_app, cache_app, mcp_app,
        security_app, scan_secrets, scan_deps, register_core_commands,
        session_app, compaction_app, containment_app, upgrade_app, budget_app,
        contained_auto, claude666, enforce_app, arch_app, license_app, wizard_app
    )

# Initialize Rich console for version display
console = Console()

# =============================================================================
# Main App Creation
# =============================================================================

app = typer.Typer(
    add_completion=False,
    help="bpsai-pair: AI pair-coding workflow CLI",
    context_settings={"help_option_names": ["-h", "--help"]}
)

# =============================================================================
# Sub-App Registration
# =============================================================================

# Planning system sub-apps
app.add_typer(plan_app, name="plan")
app.add_typer(task_app, name="task")
app.add_typer(intent_app, name="intent")
app.add_typer(standup_app, name="standup")
app.add_typer(sprint_app, name="sprint")
app.add_typer(release_app, name="release")
app.add_typer(template_app, name="template")
app.add_typer(migrate_app, name="migrate")
app.add_typer(skill_app, name="skill")
app.add_typer(subagent_app, name="subagent")
app.add_typer(gaps_app, name="gaps")
app.add_typer(audit_app, name="audit")

# Extracted command sub-apps
app.add_typer(orchestrate_app, name="orchestrate")
app.add_typer(metrics_app, name="metrics")
app.add_typer(preset_app, name="preset")
app.add_typer(config_app, name="config")
app.add_typer(timer_app, name="timer")
app.add_typer(benchmark_app, name="benchmark")
app.add_typer(cache_app, name="cache")
app.add_typer(mcp_app, name="mcp")
app.add_typer(security_app, name="security")
app.add_typer(session_app, name="session")
app.add_typer(compaction_app, name="compaction")
app.add_typer(containment_app, name="containment")
app.add_typer(upgrade_app, name="upgrade")
app.add_typer(budget_app, name="budget")
app.add_typer(state_app, name="state")
app.add_typer(enforce_app, name="enforce")
app.add_typer(arch_app, name="arch")
app.add_typer(license_app, name="license")
app.add_typer(wizard_app, name="wizard")

# Integration sub-apps (optional - may not be installed)
try:
    app.add_typer(trello_app, name="trello")
    app.add_typer(trello_task_app, name="ttask")
except NameError:
    pass  # Trello module not available

try:
    app.add_typer(github_app, name="github")
except NameError:
    pass  # GitHub module not available

# =============================================================================
# Core Commands Registration
# =============================================================================

# Register core commands (init, feature, pack, context-sync, status, validate, ci)
register_core_commands(app)

# Register contained-auto as a top-level command
app.command("contained-auto")(contained_auto)

# Register claude666 alias (undocumented easter egg)
app.command("claude666", hidden=True)(claude666)

# =============================================================================
# Shortcut Commands
# =============================================================================

@app.command("scan-secrets")
def scan_secrets_shortcut(
    path: Optional[str] = typer.Argument(None, help="File or directory to scan"),
    staged: bool = typer.Option(False, "--staged", "-s", help="Scan staged git changes only"),
    diff_ref: Optional[str] = typer.Option(None, "--diff", "-d", help="Scan diff since git reference"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Scan for secrets and credentials (shortcut for 'security scan-secrets')."""
    scan_secrets(path=path, staged=staged, diff_ref=diff_ref, verbose=verbose, json_out=json_out)


@app.command("scan-deps")
def scan_deps_shortcut(
    path: Optional[str] = typer.Argument(None, help="Directory to scan for dependencies"),
    fail_on: Optional[str] = typer.Option(None, "--fail-on", "-f", help="Fail if severity >= value"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Disable caching"),
):
    """Scan dependencies for vulnerabilities (shortcut for 'security scan-deps')."""
    scan_deps(path=path, fail_on=fail_on, verbose=verbose, json_out=json_out, no_cache=no_cache)

# =============================================================================
# App Callback (Version)
# =============================================================================

def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"[bold blue]bpsai-pair[/bold blue] version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        help="Show version and exit"
    )
):
    """bpsai-pair: AI pair-coding workflow CLI"""
    pass

# =============================================================================
# Entry Point
# =============================================================================

def _show_upgrade_prompt(exc: "FeatureNotAvailable") -> None:
    """Show a graceful upgrade prompt when a feature is not available."""
    from .licensing.core import FeatureNotAvailable
    from .licensing.schema import get_tier_display_name

    feature = exc.feature
    tier = exc.tier
    tier_display = get_tier_display_name(tier)

    # Feature-specific messages
    feature_messages = {
        "trello": "Trello integration is available with Pro.",
        "github": "GitHub integration is available with Pro.",
        "token_budget": "Token budget tracking is available with Pro.",
        "mcp": "MCP server is available with Pro.",
        "timer": "Time tracking is available with Pro.",
    }

    feature_msg = feature_messages.get(feature, f"The '{feature}' feature is available with Pro.")

    console.print()
    console.print("┌─────────────────────────────────────────────────┐")
    console.print("│  [bold]This feature requires Pro tier[/bold]                 │")
    console.print("│                                                 │")
    console.print(f"│  {feature_msg:<47} │")
    console.print("│                                                 │")
    console.print("│  Upgrade at: [cyan]paircoder.ai/pricing[/cyan]              │")
    console.print("│  Or install a license: [cyan]bpsai-pair license install[/cyan] │")
    console.print("└─────────────────────────────────────────────────┘")
    console.print()


def run():
    """Entry point for the CLI."""
    from .licensing.core import FeatureNotAvailable
    import sys

    try:
        app()
    except FeatureNotAvailable as exc:
        _show_upgrade_prompt(exc)
        sys.exit(1)


if __name__ == "__main__":
    run()
