"""Centralized bypass audit logging.

Every workflow enforcement bypass MUST be logged through this module.
Review bypasses with: bpsai-pair audit bypasses

Location: tools/cli/bpsai_pair/core/bypass_log.py
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

console = Console()


def get_bypass_log_path() -> Path:
    """Get path to bypass log file."""
    from .ops import find_paircoder_dir
    paircoder_dir = find_paircoder_dir()
    if paircoder_dir:
        return paircoder_dir / "history" / "bypass_log.jsonl"
    return Path(".paircoder/history/bypass_log.jsonl")


def log_bypass(
    command: str,
    target: str,
    reason: str,
    bypass_type: str = "user_override",
    metadata: Optional[dict] = None,
    silent: bool = False,
) -> None:
    """Log a workflow bypass.

    Args:
        command: The command being bypassed (e.g., "ttask_done_strict")
        target: The task/card being affected (e.g., "T27.1", "TRELLO-94")
        reason: Reason for bypass
        bypass_type: Type of bypass (user_override, no_strict, local_only, budget_override)
        metadata: Additional context
        silent: If True, don't print warning to console
    """
    log_path = get_bypass_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "command": command,
        "target": target,
        "reason": reason,
        "bypass_type": bypass_type,
        "user": os.environ.get("USER", "unknown"),
        "session_id": os.environ.get("CLAUDE_SESSION_ID", ""),
        "cwd": os.getcwd(),
        "metadata": metadata or {},
    }

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    if not silent:
        console.print(f"[yellow]⚠️ BYPASS LOGGED:[/yellow] {command} on {target}")
        console.print(f"[dim]   Reason: {reason}[/dim]")


def get_bypasses(
    since_days: Optional[int] = None,
    limit: int = 50,
    bypass_type: Optional[str] = None,
) -> list[dict]:
    """Get recent bypasses from log.

    Args:
        since_days: Only return bypasses from last N days
        limit: Maximum number to return
        bypass_type: Filter by bypass type

    Returns:
        List of bypass entries, newest first
    """
    log_path = get_bypass_log_path()
    if not log_path.exists():
        return []

    cutoff = None
    if since_days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    bypasses = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Filter by time
                if cutoff:
                    entry_time = datetime.fromisoformat(entry["timestamp"].rstrip("Z")).replace(tzinfo=timezone.utc)
                    if entry_time < cutoff:
                        continue

                # Filter by type
                if bypass_type and entry.get("bypass_type") != bypass_type:
                    continue

                bypasses.append(entry)

    # Return newest first
    bypasses.reverse()
    return bypasses[:limit]


def show_bypasses(
    since_days: int = 7,
    limit: int = 50,
    bypass_type: Optional[str] = None,
) -> None:
    """Display bypasses in a formatted table."""
    bypasses = get_bypasses(since_days=since_days, limit=limit, bypass_type=bypass_type)

    if not bypasses:
        console.print(f"[green]✓ No bypasses in the last {since_days} days.[/green]")
        return

    table = Table(title=f"Workflow Bypasses (last {since_days} days)")
    table.add_column("Time", style="dim", width=16)
    table.add_column("Command", width=20)
    table.add_column("Target", width=12)
    table.add_column("Type", width=14)
    table.add_column("Reason", width=40)

    for entry in bypasses:
        ts = entry["timestamp"][:16].replace("T", " ")
        reason = entry.get("reason", "")
        if len(reason) > 40:
            reason = reason[:37] + "..."

        table.add_row(
            ts,
            entry.get("command", "unknown"),
            entry.get("target", ""),
            entry.get("bypass_type", ""),
            reason,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(bypasses)} bypasses[/dim]")


def get_bypass_summary(since_days: int = 7) -> dict:
    """Get summary statistics of bypasses.

    Returns:
        Dict with counts by type and command
    """
    from collections import Counter

    bypasses = get_bypasses(since_days=since_days, limit=1000)

    return {
        "total": len(bypasses),
        "by_type": dict(Counter(b.get("bypass_type", "unknown") for b in bypasses)),
        "by_command": dict(Counter(b.get("command", "unknown") for b in bypasses)),
        "since_days": since_days,
    }
