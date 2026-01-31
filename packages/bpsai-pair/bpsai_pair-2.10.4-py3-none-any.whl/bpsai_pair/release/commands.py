"""Release CLI commands for PairCoder.

Provides commands for release management including
creating release plans, checklists, and preparation checks.

Extracted from planning/cli_commands.py as part of EPIC-003 Phase 2.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

# Import from planning module
from ..planning.state import StateManager

console = Console()

app = typer.Typer(
    help="Release management commands",
    context_settings={"help_option_names": ["-h", "--help"]}
)


def find_paircoder_dir() -> Path:
    """Find .paircoder directory in current or parent directories."""
    from ..core.ops import find_paircoder_dir as _find_paircoder_dir
    return _find_paircoder_dir()


def get_state_manager() -> StateManager:
    """Get a StateManager instance for the current project."""
    return StateManager(find_paircoder_dir())


def get_template_path(paircoder_dir: Path) -> Optional[Path]:
    """Get the cookie cutter template path from config or default."""
    import yaml

    config_path = paircoder_dir / "config.yaml"
    template_path = None

    if config_path.exists():
        with open(config_path, encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            release_config = config.get("release", {})
            cookie_cutter = release_config.get("cookie_cutter", {})
            template_path = cookie_cutter.get("template_path")

    if template_path:
        # Resolve relative to project root
        project_root = paircoder_dir.parent
        resolved = project_root / template_path
        if resolved.exists():
            return resolved

    # Try default location: tools/cli/bpsai_pair/data/cookiecutter-paircoder
    project_root = paircoder_dir.parent
    default_path = project_root / "tools" / "cli" / "bpsai_pair" / "data" / "cookiecutter-paircoder"
    if default_path.exists():
        return default_path

    return None


@app.command("plan")
def release_plan(
    sprint_id: Optional[str] = typer.Option(None, "--sprint", "-s", help="Sprint to create release tasks for"),
    version: Optional[str] = typer.Option(None, "--version", "-v", help="Target version (e.g., v2.6.0)"),
    create_tasks: bool = typer.Option(False, "--create", "-c", help="Actually create the tasks"),
):
    """Generate release preparation tasks.

    Creates tasks for common release activities:
    - Sync cookie cutter template
    - Update CHANGELOG.md
    - Bump version number
    - Update documentation

    Examples:
        # Preview release tasks
        bpsai-pair release plan --sprint sprint-17

        # Create release tasks
        bpsai-pair release plan --sprint sprint-17 --create

        # With specific version
        bpsai-pair release plan --version v2.6.0 --create
    """
    paircoder_dir = find_paircoder_dir()

    # Get active plan
    state_manager = get_state_manager()
    state = state_manager.load_state()
    plan_id = state.active_plan_id if state else None

    if not plan_id:
        console.print("[yellow]No active plan. Release tasks will be standalone.[/yellow]")

    # Define release tasks
    release_tasks = [
        {
            "id": "REL-001",
            "title": "Sync cookie cutter template with project changes",
            "type": "chore",
            "priority": "P1",
            "complexity": 25,
            "description": """
Ensure the cookie cutter template reflects all recent changes:
- New configuration options
- New skills and commands
- Updated documentation
- New directory structure

Files to check:
- tools/cli/bpsai_pair/data/cookiecutter-paircoder/
""".strip(),
        },
        {
            "id": "REL-002",
            "title": "Update CHANGELOG.md",
            "type": "docs",
            "priority": "P1",
            "complexity": 15,
            "description": """
Add release notes for the new version:
- New features
- Bug fixes
- Breaking changes
- Migration guide (if needed)

Run: bpsai-pair task changelog-preview
""".strip(),
        },
        {
            "id": "REL-003",
            "title": "Bump version number",
            "type": "chore",
            "priority": "P1",
            "complexity": 10,
            "description": f"""
Update version to {version or 'vX.Y.Z'} in:
- pyproject.toml
- __init__.py (if applicable)
- README.md (if version mentioned)
""".strip(),
        },
        {
            "id": "REL-004",
            "title": "Update documentation",
            "type": "docs",
            "priority": "P2",
            "complexity": 20,
            "description": """
Ensure documentation reflects new features:
- README.md
- USER_GUIDE.md
- FEATURE_MATRIX.md
- MCP_SETUP.md (if MCP changes)
""".strip(),
        },
        {
            "id": "REL-005",
            "title": "Run full test suite",
            "type": "chore",
            "priority": "P1",
            "complexity": 15,
            "description": """
Verify all tests pass before release:
- pytest -v
- Check coverage
- Manual smoke tests
""".strip(),
        },
    ]

    # Display tasks
    console.print("\n[bold]Release Preparation Tasks[/bold]")
    if sprint_id:
        console.print(f"Sprint: {sprint_id}")
    if version:
        console.print(f"Target Version: {version}")
    console.print()

    table = Table()
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Priority")
    table.add_column("Points", justify="right")

    for task in release_tasks:
        table.add_row(
            task["id"],
            task["title"],
            task["type"],
            task["priority"],
            str(task["complexity"]),
        )

    console.print(table)
    console.print(f"\nTotal: {len(release_tasks)} tasks, {sum(t['complexity'] for t in release_tasks)} points")

    if not create_tasks:
        console.print("\n[dim]Run with --create to create these tasks[/dim]")
        return

    # Create the tasks
    console.print("\n[bold]Creating tasks...[/bold]")

    tasks_dir = paircoder_dir / "tasks"
    tasks_dir.mkdir(exist_ok=True)

    for task_def in release_tasks:
        task_id = f"TASK-{task_def['id']}"
        task_file = tasks_dir / f"{task_id}.task.md"

        content = f"""---
id: {task_id}
title: "{task_def['title']}"
plan: {plan_id or 'release'}
sprint: {sprint_id or 'release'}
type: {task_def['type']}
priority: {task_def['priority']}
complexity: {task_def['complexity']}
status: pending
depends_on: []
---

# {task_id}: {task_def['title']}

## Description

{task_def['description']}

## Acceptance Criteria

- [ ] Task completed
- [ ] Changes verified
"""

        task_file.write_text(content, encoding="utf-8")
        console.print(f"  [green]✓[/green] Created {task_id}")

    console.print(f"\n[green]Created {len(release_tasks)} release tasks[/green]")
    console.print("\n[dim]View tasks: bpsai-pair task list[/dim]")


@app.command("checklist")
def release_checklist():
    """Show the release preparation checklist.

    Displays the standard checklist items that should be completed
    before any release.
    """
    console.print("\n[bold]Release Preparation Checklist[/bold]\n")

    checklist_items = [
        ("Pre-Release", [
            "All sprint tasks completed or deferred",
            "Tests passing (pytest -v)",
            "No critical bugs open",
            "Code reviewed and approved",
        ]),
        ("Documentation", [
            "CHANGELOG.md updated with release notes",
            "README.md reflects current features",
            "USER_GUIDE.md up to date",
            "FEATURE_MATRIX.md accurate",
        ]),
        ("Template Sync", [
            "Cookie cutter template synced",
            "New skills/commands in template",
            "Config options in template",
            "Documentation in template",
        ]),
        ("Version & Release", [
            "Version bumped in pyproject.toml",
            "Git tag created",
            "Package published (pip)",
            "Release notes on GitHub",
        ]),
    ]

    for section, items in checklist_items:
        console.print(f"[bold cyan]{section}[/bold cyan]")
        for item in items:
            console.print(f"  [ ] {item}")
        console.print()


@app.command("prep")
def release_prep(
    since: Optional[str] = typer.Option(None, "--since", "-s", help="Git tag/commit for baseline comparison"),
    create_tasks: bool = typer.Option(False, "--create-tasks", "-c", help="Generate tasks for missing items"),
    skip_tests: bool = typer.Option(False, "--skip-tests", help="Skip running test suite check"),
):
    """Verify release readiness and generate tasks for missing items.

    Runs a series of checks to ensure the project is ready for release:
    - Version consistency (pyproject.toml matches package __version__)
    - CHANGELOG has entry for current version
    - Git working tree is clean
    - Tests passing
    - Documentation freshness

    Examples:
        # Check release readiness
        bpsai-pair release prep

        # Check since last release
        bpsai-pair release prep --since v2.5.0

        # Generate tasks for missing items
        bpsai-pair release prep --create-tasks
    """
    paircoder_dir = find_paircoder_dir()

    # Load release config
    config_path = paircoder_dir / "config.yaml"
    release_config = {
        "version_source": "pyproject.toml",
        "documentation": ["CHANGELOG.md", "README.md", ".paircoder/docs/FEATURE_MATRIX.md"],
        "freshness_days": 7,
    }

    if config_path.exists():
        import yaml
        with open(config_path, encoding='utf-8') as f:
            full_config = yaml.safe_load(f) or {}
            if "release" in full_config:
                release_config.update(full_config["release"])

    console.print("\n[bold]Release Preparation Check[/bold]")
    if since:
        console.print(f"Comparing since: {since}")
    console.print()

    checks = []
    tasks_needed = []

    # Find project root (parent of .paircoder)
    project_root = paircoder_dir.parent

    # Check 1: Version consistency
    # Search for pyproject.toml in multiple locations
    pyproject_candidates = [
        project_root / "pyproject.toml",
        project_root / "tools" / "cli" / "pyproject.toml",  # PairCoder structure
    ]
    pyproject_path = None
    for candidate in pyproject_candidates:
        if candidate.exists():
            pyproject_path = candidate
            break

    pyproject_version = None
    package_version = None

    if pyproject_path and pyproject_path.exists():
        pyproject_content = pyproject_path.read_text(encoding="utf-8")
        version_match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', pyproject_content, re.MULTILINE)
        if version_match:
            pyproject_version = version_match.group(1)

    # Try to find package __version__
    for init_path in project_root.glob("*/__init__.py"):
        if init_path.parent.name.startswith("."):
            continue
        init_content = init_path.read_text(encoding="utf-8")
        ver_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_content)
        if ver_match:
            package_version = ver_match.group(1)
            break

    if pyproject_version:
        if package_version and pyproject_version != package_version:
            checks.append(("Version consistency", "❌", f"Mismatch: pyproject.toml={pyproject_version}, __init__.py={package_version}"))
            tasks_needed.append({
                "id": "REL-VER",
                "title": "Fix version mismatch",
                "description": f"pyproject.toml has {pyproject_version} but __init__.py has {package_version}",
            })
        else:
            checks.append(("Version consistency", "✅", f"v{pyproject_version}"))
    else:
        checks.append(("Version consistency", "⚠️", "Could not find version in pyproject.toml"))

    # Check 2: CHANGELOG entry
    changelog_path = project_root / "CHANGELOG.md"
    if changelog_path.exists() and pyproject_version:
        changelog_content = changelog_path.read_text(encoding="utf-8")
        # Look for version in changelog (formats: [2.6.0], v2.6.0, 2.6.0)
        version_patterns = [
            rf"\[{re.escape(pyproject_version)}\]",
            rf"v{re.escape(pyproject_version)}",
            rf"## {re.escape(pyproject_version)}",
        ]
        has_entry = any(re.search(p, changelog_content) for p in version_patterns)
        if has_entry:
            checks.append(("CHANGELOG entry", "✅", f"Found entry for v{pyproject_version}"))
        else:
            checks.append(("CHANGELOG entry", "❌", f"Missing entry for v{pyproject_version}"))
            tasks_needed.append({
                "id": "REL-CHANGELOG",
                "title": f"Update CHANGELOG.md for v{pyproject_version}",
                "description": "Add release notes for the new version",
            })
    elif not changelog_path.exists():
        checks.append(("CHANGELOG entry", "⚠️", "CHANGELOG.md not found"))
    else:
        checks.append(("CHANGELOG entry", "⚠️", "Could not determine version to check"))

    # Check 3: Git status (uncommitted changes)
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            if result.stdout.strip():
                changes_count = len(result.stdout.strip().split("\n"))
                checks.append(("Git status", "❌", f"{changes_count} uncommitted change(s)"))
                tasks_needed.append({
                    "id": "REL-GIT",
                    "title": "Commit or stash uncommitted changes",
                    "description": f"Found {changes_count} uncommitted file(s)",
                })
            else:
                checks.append(("Git status", "✅", "Working tree clean"))
        else:
            checks.append(("Git status", "⚠️", "Not a git repository"))
    except FileNotFoundError:
        checks.append(("Git status", "⚠️", "git command not found"))

    # Check 4: Tests passing (if not skipped)
    if not skip_tests:
        try:
            # Check if pytest is available and there are tests
            result = subprocess.run(
                ["python", "-m", "pytest", "--collect-only", "-q"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                # Count collected tests
                lines = result.stdout.strip().split("\n")
                test_count = 0
                for line in lines:
                    if "test" in line.lower() and "::" in line:
                        test_count += 1
                if test_count > 0:
                    checks.append(("Test suite", "✅", f"{test_count} tests collected"))
                else:
                    checks.append(("Test suite", "⚠️", "No tests found"))
            elif "no tests" in result.stderr.lower() or "no tests" in result.stdout.lower():
                checks.append(("Test suite", "⚠️", "No tests found"))
            else:
                checks.append(("Test suite", "❌", "Test collection failed"))
                tasks_needed.append({
                    "id": "REL-TESTS",
                    "title": "Fix failing tests",
                    "description": "Test collection failed - run pytest to diagnose",
                })
        except subprocess.TimeoutExpired:
            checks.append(("Test suite", "⚠️", "Test collection timed out"))
        except FileNotFoundError:
            checks.append(("Test suite", "⚠️", "pytest not found"))
    else:
        checks.append(("Test suite", "⚠️", "Skipped (--skip-tests)"))

    # Check 5: Documentation freshness
    for doc_file in release_config.get("documentation", []):
        doc_path = project_root / doc_file
        if doc_path.exists():
            import os
            from datetime import datetime

            mtime = datetime.fromtimestamp(os.path.getmtime(doc_path))
            days_old = (datetime.now() - mtime).days
            freshness_days = release_config.get("freshness_days", 7)

            if days_old > freshness_days:
                checks.append((f"Doc: {doc_file}", "⚠️", f"Last updated {days_old} days ago"))
            else:
                checks.append((f"Doc: {doc_file}", "✅", f"Updated {days_old} days ago"))
        else:
            if doc_file == "CHANGELOG.md":
                # Already checked above
                pass
            else:
                checks.append((f"Doc: {doc_file}", "⚠️", "Not found"))

    # Check 6: Cookie cutter template drift
    cookie_cutter_config = release_config.get("cookie_cutter", {})
    if cookie_cutter_config.get("sync_required", True):
        template_path = get_template_path(paircoder_dir)
        if template_path:
            template_project_dir = template_path / "{{cookiecutter.project_slug}}"
            if template_project_dir.exists():
                # Check a few key files for drift
                drift_count = 0
                files_to_check = [
                    ".paircoder/config.yaml",
                    "CLAUDE.md",
                    ".paircoder/capabilities.yaml",
                ]
                for rel_path in files_to_check:
                    source = project_root / rel_path
                    template = template_project_dir / rel_path
                    if source.exists() and template.exists():
                        if source.read_text(encoding="utf-8") != template.read_text(encoding="utf-8"):
                            drift_count += 1

                if drift_count > 0:
                    checks.append(("Template drift", "⚠️", f"{drift_count} file(s) need sync"))
                    tasks_needed.append({
                        "id": "REL-TEMPLATE",
                        "title": "Sync cookie cutter template",
                        "description": f"{drift_count} file(s) have drifted. Run: bpsai-pair template check --fix",
                    })
                else:
                    checks.append(("Template drift", "✅", "All files in sync"))
            else:
                checks.append(("Template drift", "⚠️", "Template directory not found"))
        else:
            checks.append(("Template drift", "⚠️", "Template not configured"))

    # Display results
    from rich.table import Table as RichTable
    table = RichTable(title=None, show_header=True, header_style="bold")
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Details")

    for check_name, status, details in checks:
        table.add_row(check_name, status, details)

    console.print(table)

    # Summary
    passed = sum(1 for _, s, _ in checks if s == "✅")
    failed = sum(1 for _, s, _ in checks if s == "❌")
    warned = sum(1 for _, s, _ in checks if s == "⚠️")

    console.print()
    console.print(f"[bold]Summary:[/bold] {passed} passed, {failed} failed, {warned} warnings")

    # Generate tasks if requested
    if tasks_needed:
        console.print(f"\n[bold]Tasks needed ({len(tasks_needed)}):[/bold]")
        for task in tasks_needed:
            console.print(f"  • {task['id']}: {task['title']}")

        if create_tasks:
            console.print("\n[bold]Creating tasks...[/bold]")
            tasks_dir = paircoder_dir / "tasks"
            tasks_dir.mkdir(exist_ok=True)

            # Get active plan
            state_manager = get_state_manager()
            state = state_manager.load_state()
            plan_id = state.active_plan_id if state else "release"

            for task_def in tasks_needed:
                task_id = task_def["id"]
                task_file = tasks_dir / f"{task_id}.task.md"

                content = f"""---
id: {task_id}
title: "{task_def['title']}"
plan: {plan_id}
type: chore
priority: P1
complexity: 10
status: pending
depends_on: []
tags:
  - release
---

# {task_def['title']}

## Description

{task_def['description']}

## Acceptance Criteria

- [ ] Issue resolved
- [ ] Changes verified
"""
                task_file.write_text(content, encoding="utf-8")
                console.print(f"  [green]✓[/green] Created {task_id}")

            console.print(f"\n[green]Generated {len(tasks_needed)} task(s)[/green]")
        else:
            console.print("\n[dim]Run with --create-tasks to generate these tasks[/dim]")
    else:
        console.print("\n[green]✓ All checks passed - ready for release![/green]")
