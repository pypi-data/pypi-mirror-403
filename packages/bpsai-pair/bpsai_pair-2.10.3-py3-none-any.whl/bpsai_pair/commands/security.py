"""Security commands for secret scanning and vulnerability detection.

Extracted from cli.py as part of EPIC-003 CLI Architecture Refactor.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

# Initialize Rich console
console = Console()


def print_json(data: dict) -> None:
    """Print JSON to stdout without Rich formatting."""
    sys.stdout.write(json.dumps(data, indent=2))
    sys.stdout.write("\n")
    sys.stdout.flush()


# Try relative imports first, fall back to absolute
try:
    from ..core import ops
except ImportError:
    from bpsai_pair.core import ops


def repo_root() -> Path:
    """Get repo root with better error message."""
    p = ops.find_project_root()
    if not ops.GitOps.is_repo(p):
        console.print(
            "[red]✗ Not in a git repository.[/red]\n"
            "Please run from your project root directory (where .git exists).\n"
            "[dim]Hint: cd to your project directory first[/dim]"
        )
        raise typer.Exit(1)
    return p


# Security sub-app
app = typer.Typer(
    help="Security tools for secret scanning and vulnerability detection",
    context_settings={"help_option_names": ["-h", "--help"]}
)


def _get_secret_scanner():
    """Get a SecretScanner instance with project allowlist."""
    try:
        from ..security import SecretScanner, AllowlistConfig
    except ImportError:
        from bpsai_pair.security import SecretScanner, AllowlistConfig

    root = repo_root()
    allowlist_path = root / ".paircoder" / "security" / "secret-allowlist.yaml"
    allowlist = AllowlistConfig.load(allowlist_path)
    return SecretScanner(allowlist), root


@app.command("scan-secrets")
def scan_secrets(
    path: Optional[str] = typer.Argument(None, help="File or directory to scan"),
    staged: bool = typer.Option(False, "--staged", "-s", help="Scan staged git changes only"),
    diff_ref: Optional[str] = typer.Option(None, "--diff", "-d", help="Scan diff since git reference (e.g., HEAD~1)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Scan for secrets and credentials in code.

    By default, scans all files in the current directory.

    Examples:

        bpsai-pair security scan-secrets              # Scan all files

        bpsai-pair security scan-secrets --staged    # Scan staged changes

        bpsai-pair security scan-secrets --diff HEAD~1  # Scan since last commit

        bpsai-pair security scan-secrets src/        # Scan specific directory
    """
    try:
        from ..security import format_scan_results
    except ImportError:
        from bpsai_pair.security import format_scan_results

    scanner, root = _get_secret_scanner()

    matches = []

    if staged:
        # Scan staged changes
        matches = scanner.scan_staged(root)
        scan_target = "staged changes"
    elif diff_ref:
        # Scan since reference
        matches = scanner.scan_commit_range(diff_ref, root)
        scan_target = f"changes since {diff_ref}"
    elif path:
        # Scan specific path
        target = Path(path)
        if target.is_file():
            matches = scanner.scan_file(target)
            scan_target = str(target)
        elif target.is_dir():
            matches = scanner.scan_directory(target)
            scan_target = f"directory {target}"
        else:
            console.print(f"[red]Path not found: {path}[/red]")
            raise typer.Exit(1)
    else:
        # Scan entire project
        matches = scanner.scan_directory(root)
        scan_target = "project"

    if json_out:
        result = {
            "target": scan_target,
            "secrets_found": len(matches),
            "matches": [m.to_dict() for m in matches],
        }
        print_json(result)
    else:
        if matches:
            console.print(f"[red]Found {len(matches)} potential secret(s) in {scan_target}[/red]\n")
            console.print(format_scan_results(matches, verbose=verbose))
            console.print("\n[dim]Review these findings and remove any real secrets before committing.[/dim]")
            raise typer.Exit(1)
        else:
            console.print(f"[green]No secrets detected in {scan_target}[/green]")


@app.command("pre-commit")
def pre_commit_hook(
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Run secret scan as a pre-commit hook.

    This command is designed to be used in git hooks:

        # .git/hooks/pre-commit
        #!/bin/bash
        bpsai-pair security pre-commit

    Exit codes:
        0 - No secrets found
        1 - Secrets found (blocks commit)
    """
    try:
        from ..security import format_scan_results
    except ImportError:
        from bpsai_pair.security import format_scan_results

    scanner, root = _get_secret_scanner()
    matches = scanner.scan_staged(root)

    if json_out:
        print_json({
            "blocked": len(matches) > 0,
            "secrets_found": len(matches),
            "matches": [m.to_dict() for m in matches],
        })
    else:
        if matches:
            console.print("[red]BLOCKED: Secrets detected in staged changes[/red]\n")
            console.print(format_scan_results(matches, verbose=True))
            console.print("\n[yellow]Remove secrets before committing.[/yellow]")
            console.print("[dim]Use environment variables or a secrets manager instead.[/dim]")
            raise typer.Exit(1)
        else:
            console.print("[green]Pre-commit secret scan passed[/green]")


@app.command("install-hook")
def install_hook(
    overwrite: bool = typer.Option(False, "--overwrite", "-o", help="Overwrite existing hook"),
):
    """Install pre-commit hook for secret scanning.

    Creates .git/hooks/pre-commit to run secret scanning
    before each commit.
    """
    root = repo_root()
    hooks_dir = root / ".git" / "hooks"
    hook_path = hooks_dir / "pre-commit"

    hook_content = '''#!/bin/bash
# PairCoder secret scanning pre-commit hook
# Installed by: bpsai-pair security install-hook

set -e

echo "Running secret scan on staged changes..."
bpsai-pair security pre-commit

# Add other pre-commit checks below if needed
'''

    if hook_path.exists() and not overwrite:
        console.print("[yellow]Pre-commit hook already exists[/yellow]")
        console.print("[dim]Use --force to overwrite[/dim]")

        # Check if our hook is already in there
        existing = hook_path.read_text(encoding="utf-8")
        if "bpsai-pair security pre-commit" in existing:
            console.print("[green]Secret scanning already configured in hook[/green]")
            return

        console.print("\n[dim]You can manually add this line to your existing hook:[/dim]")
        console.print("  bpsai-pair security pre-commit")
        raise typer.Exit(1)

    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(hook_content, encoding="utf-8")
    hook_path.chmod(0o755)

    console.print("[green]Installed pre-commit hook for secret scanning[/green]")
    console.print(f"  Location: {hook_path}")


@app.command("scan-deps")
def scan_deps(
    path: Optional[str] = typer.Argument(None, help="Directory to scan for dependencies"),
    fail_on: Optional[str] = typer.Option(None, "--fail-on", "-f", help="Fail if severity >= value (low, medium, high, critical)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Disable caching of scan results"),
):
    """Scan dependencies for known vulnerabilities.

    Scans Python (pip-audit) and npm (npm audit) dependencies for CVEs.

    Examples:

        bpsai-pair security scan-deps             # Scan all dependencies

        bpsai-pair security scan-deps --fail-on high  # Fail on high+ severity

        bpsai-pair security scan-deps --verbose   # Show detailed CVE info
    """
    try:
        from ..security import DependencyScanner, Severity, format_scan_report
    except ImportError:
        from bpsai_pair.security import DependencyScanner, Severity, format_scan_report

    root = Path(path) if path else repo_root()
    scanner = DependencyScanner()

    report = scanner.scan_all(root, use_cache=not no_cache)

    if json_out:
        print_json(report.to_dict())
    else:
        console.print(format_scan_report(report, verbose=verbose))

        if fail_on:
            min_severity = Severity.from_string(fail_on)
            if report.has_severity(min_severity):
                console.print(f"\n[red]FAILED: Found vulnerabilities with severity >= {fail_on}[/red]")
                raise typer.Exit(1)

        if report.has_critical():
            console.print("\n[yellow]Warning: Critical vulnerabilities found![/yellow]")
