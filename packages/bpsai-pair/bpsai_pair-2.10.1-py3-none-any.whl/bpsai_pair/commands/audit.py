"""Audit commands for reviewing workflow compliance.

Location: tools/cli/bpsai_pair/commands/audit.py
"""
import typer
from typing import Optional

app = typer.Typer(help="Audit workflow compliance")


@app.command("bypasses")
def audit_bypasses(
    days: int = typer.Option(7, "--days", "-d", help="Show bypasses from last N days"),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum entries to show"),
    bypass_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by type (no_strict, budget_override, local_only, etc.)"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show recent workflow bypasses.
    
    Examples:
        bpsai-pair audit bypasses
        bpsai-pair audit bypasses --days 30
        bpsai-pair audit bypasses --type budget_override
        bpsai-pair audit bypasses --json
    """
    from ..core.bypass_log import show_bypasses, get_bypasses
    import json
    
    if json_out:
        bypasses = get_bypasses(since_days=days, limit=limit, bypass_type=bypass_type)
        typer.echo(json.dumps(bypasses, indent=2))
    else:
        show_bypasses(since_days=days, limit=limit, bypass_type=bypass_type)


@app.command("summary")
def audit_summary(
    days: int = typer.Option(7, "--days", "-d", help="Summarize last N days"),
):
    """Show bypass summary by type and command."""
    from collections import Counter
    from rich.console import Console
    from rich.table import Table
    
    from ..core.bypass_log import get_bypasses
    
    console = Console()
    bypasses = get_bypasses(since_days=days, limit=1000)
    
    if not bypasses:
        console.print(f"[green]✓ No bypasses in the last {days} days.[/green]")
        return
    
    # Count by type
    type_counts = Counter(b.get("bypass_type", "unknown") for b in bypasses)
    cmd_counts = Counter(b.get("command", "unknown") for b in bypasses)
    
    table = Table(title=f"Bypass Summary (last {days} days)")
    table.add_column("Category", style="bold")
    table.add_column("Item")
    table.add_column("Count", justify="right")
    
    console.print(f"\n[bold]Total bypasses:[/bold] {len(bypasses)}\n")
    
    # By type
    console.print("[bold]By Type:[/bold]")
    for bypass_type, count in type_counts.most_common():
        color = "red" if count > 10 else "yellow" if count > 3 else "dim"
        console.print(f"  [{color}]{bypass_type}:[/{color}] {count}")
    
    console.print("\n[bold]By Command:[/bold]")
    for cmd, count in cmd_counts.most_common(10):
        color = "red" if count > 10 else "yellow" if count > 3 else "dim"
        console.print(f"  [{color}]{cmd}:[/{color}] {count}")
    
    # Warning if too many bypasses
    if len(bypasses) > 20:
        console.print(f"\n[red]⚠️ High bypass count ({len(bypasses)} in {days} days). Review workflow compliance.[/red]")


@app.command("clear")
def audit_clear(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Clear bypass log (for development/testing only)."""
    from ..core.bypass_log import get_bypass_log_path
    
    log_path = get_bypass_log_path()
    
    if not log_path.exists():
        typer.echo("No bypass log to clear.")
        return
    
    if not confirm:
        typer.confirm("Clear all bypass logs? This cannot be undone.", abort=True)
    
    log_path.unlink()
    typer.echo("✓ Bypass log cleared.")
