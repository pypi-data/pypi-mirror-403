"""Context commands for bpsai-pair CLI.

Contains the pack and context-sync commands extracted from core.py:
- pack: Create agent context package
- context-sync: Update the Context Loop in state.md

Also contains helper functions:
- print_json: Print JSON to stdout without Rich formatting
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console

# Try relative imports first, fall back to absolute
try:
    from ..core import ops
except ImportError:
    from bpsai_pair.core import ops


# Initialize Rich console
console = Console()

# Environment variable support
CONTEXT_DIR = os.getenv("PAIRCODER_CONTEXT_DIR", ".paircoder/context")


def print_json(data: dict) -> None:
    """Print JSON to stdout without Rich formatting."""
    sys.stdout.write(json.dumps(data, indent=2))
    sys.stdout.write("\n")
    sys.stdout.flush()


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


def pack_command(
    output: str = typer.Option("agent_pack.tgz", "--out", "-o", help="Output archive name"),
    extra: Optional[List[str]] = typer.Option(None, "--extra", "-e", help="Additional paths to include"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview files without creating archive"),
    list_only: bool = typer.Option(False, "--list", "-l", help="List files to be included"),
    lite: bool = typer.Option(False, "--lite", help="Minimal pack for Codex CLI (< 32KB)"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Create agent context package (cross-platform)."""
    root = repo_root()
    output_path = root / output

    # Use Python ops for packing
    files = ops.ContextPacker.pack(
        root=root,
        output=output_path,
        extra_files=extra,
        dry_run=(dry_run or list_only),
        lite=lite,
    )

    if json_out:
        result = {
            "files": [str(f.relative_to(root)) for f in files],
            "count": len(files),
            "dry_run": dry_run,
            "list_only": list_only
        }
        if not (dry_run or list_only):
            result["output"] = str(output)
            result["size"] = output_path.stat().st_size if output_path.exists() else 0
        print_json(result)
    elif list_only:
        for f in files:
            console.print(str(f.relative_to(root)))
    elif dry_run:
        console.print(f"[yellow]Would pack {len(files)} files:[/yellow]")
        for f in files[:10]:  # Show first 10
            console.print(f"  - {f.relative_to(root)}")
        if len(files) > 10:
            console.print(f"  [dim]... and {len(files) - 10} more[/dim]")
    else:
        console.print(f"[green]![/green] Created [bold]{output}[/bold]")
        size_kb = output_path.stat().st_size / 1024
        console.print(f"  Size: {size_kb:.1f} KB")
        console.print(f"  Files: {len(files)}")
        console.print("[dim]Upload this archive to your agent session[/dim]")


def context_sync_command(
    overall: Optional[str] = typer.Option(None, "--overall", help="Overall goal override"),
    last: Optional[str] = typer.Option(None, "--last", "-l", help="What changed and why"),
    next_step: Optional[str] = typer.Option(None, "--next", "--nxt", "-n", help="Next smallest valuable step"),
    blockers: str = typer.Option("", "--blockers", "-b", help="Blockers/Risks"),
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
    auto: bool = typer.Option(False, "--auto", help="Auto-mode: skip silently if no explicit values (for hooks)"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress errors and always exit 0 (for hooks)"),
):
    """Update the Context Loop in /context/state.md.

    Use --auto for cross-platform hooks (instead of '2>/dev/null || true').
    In auto mode, the command exits silently if --last and --next are not provided.
    """
    # In auto/quiet mode with no values provided, just exit silently
    if (auto or quiet) and not last and not next_step:
        return

    # Require --last and --next in non-auto mode
    if not last or not next_step:
        if quiet:
            return
        console.print("[red]x --last and --next are required[/red]")
        console.print("[dim]Use --auto for hook mode that exits silently[/dim]")
        raise typer.Exit(1)

    try:
        root = repo_root()
    except (SystemExit, typer.Exit):
        if quiet or auto:
            return
        raise
    context_dir = root / CONTEXT_DIR

    state_file = context_dir / "state.md"

    if not state_file.exists():
        if quiet or auto:
            return
        console.print(
            "[red]x No state.md found[/red]\n"
            "Run 'bpsai-pair init' first to set up the project structure"
        )
        raise typer.Exit(1)

    try:
        # Update context
        content = state_file.read_text(encoding="utf-8")

        # Update "What Was Just Done" section
        content = re.sub(
            r'(## What Was Just Done\n\n).*?(?=\n## |\Z)',
            f'\\1- {last}\n\n',
            content,
            flags=re.DOTALL
        )
        # Update "What's Next" section
        content = re.sub(
            r"(## What's Next\n\n).*?(?=\n## |\Z)",
            f'\\g<1>1. {next_step}\n\n',
            content,
            flags=re.DOTALL
        )
        # Update "Blockers" section if provided
        if blockers:
            content = re.sub(
                r'(## Blockers\n\n).*?(?=\n## |\Z)',
                f'\\1{blockers if blockers else "None"}\n\n',
                content,
                flags=re.DOTALL
            )
        # Update "Active Plan" if overall provided
        if overall:
            content = re.sub(
                r'(\*\*Plan:\*\*) .*',
                f'\\1 {overall}',
                content
            )

        state_file.write_text(content, encoding="utf-8")

        if json_out:
            result = {
                "updated": True,
                "file": str(state_file.relative_to(root)),
                "context": {
                    "overall": overall,
                    "last": last,
                    "next": next_step,
                    "blockers": blockers
                }
            }
            print_json(result)
        else:
            console.print("[green]![/green] Context Sync updated")
            console.print(f"  [dim]Last: {last}[/dim]")
            console.print(f"  [dim]Next: {next_step}[/dim]")
    except Exception:
        if quiet or auto:
            return
        raise
