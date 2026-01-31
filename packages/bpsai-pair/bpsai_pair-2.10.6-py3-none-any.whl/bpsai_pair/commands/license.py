"""License management CLI commands.

Provides commands for checking license status, viewing available features,
and installing license files.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from bpsai_pair.licensing import (
    CATEGORY_TO_FEATURES,
    SignedLicense,
    clear_license_cache,
    get_all_features_api,
    get_tier,
    get_tier_display_name,
    load_license,
)

console = Console()


def _print_json(data: dict) -> None:
    """Print JSON to stdout without Rich formatting."""
    sys.stdout.write(json.dumps(data, indent=2))
    sys.stdout.write("\n")
    sys.stdout.flush()


def _get_license_file_path() -> Path | None:
    """Get the path to the currently loaded license file."""
    env_path = os.environ.get("PAIRCODER_LICENSE")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path

    home_license = Path.home() / ".paircoder" / "license.json"
    if home_license.exists():
        return home_license

    cwd_license = Path.cwd() / ".paircoder" / "license.json"
    if cwd_license.exists():
        return cwd_license

    return None


def _format_expiry(license_data: SignedLicense | None) -> str:
    """Format expiration date for display."""
    if license_data is None:
        return "N/A"
    expires = license_data.payload.expires_at
    if expires is None:
        return "Never (Perpetual)"
    return expires.strftime("%Y-%m-%d")


def _build_status_json(license_data, tier, tier_display, features) -> dict:
    """Build JSON dict for status output."""
    if license_data:
        return {
            "tier": tier,
            "tier_display": tier_display,
            "type": license_data.payload.type,
            "email": license_data.payload.email,
            "name": license_data.payload.name,
            "expires_at": (
                license_data.payload.expires_at.isoformat()
                if license_data.payload.expires_at
                else None
            ),
            "founder_number": license_data.payload.founder_number,
            "feature_count": len(features),
            "features": sorted(features),
        }
    return {
        "tier": tier,
        "tier_display": tier_display,
        "type": None,
        "email": None,
        "name": None,
        "expires_at": None,
        "founder_number": None,
        "feature_count": len(features),
        "features": sorted(features),
    }


def _print_status_rich(license_data, tier_display, features) -> None:
    """Print status in Rich format."""
    console.print()
    if license_data is None:
        _print_solo_status(features)
    else:
        _print_licensed_status(license_data, tier_display, features)
    console.print()


def _print_solo_status(features) -> None:
    """Print Solo tier status panel."""
    panel = Panel(
        f"[bold]Tier:[/bold]     Solo (Free)\n"
        f"[bold]Features:[/bold] {len(features)} available\n"
        f"\n"
        f"[dim]No license file found.[/dim]\n"
        f"[dim]Using free tier with basic features.[/dim]",
        title="[bold blue]License Status[/bold blue]",
        border_style="blue",
    )
    console.print(panel)
    console.print()
    console.print("[yellow]Upgrade at:[/yellow] https://paircoder.ai/pricing")


def _print_licensed_status(license_data, tier_display, features) -> None:
    """Print licensed status panel."""
    founder_info = ""
    if license_data.payload.founder_number:
        founder_info = f"\n[bold]Founder #:[/bold] {license_data.payload.founder_number}"
    panel = Panel(
        f"[bold]Tier:[/bold]     {tier_display}\n"
        f"[bold]Type:[/bold]     {license_data.payload.type.title()}\n"
        f"[bold]Email:[/bold]    {license_data.payload.email}\n"
        f"[bold]Expires:[/bold]  {_format_expiry(license_data)}\n"
        f"[bold]Features:[/bold] {len(features)} available{founder_info}",
        title="[bold green]License Status[/bold green]",
        border_style="green",
    )
    console.print(panel)


def _print_features_rich(tier, tier_display, license_data) -> None:
    """Print features in Rich format."""
    console.print()
    console.print(f"[bold]Available Features ({tier_display})[/bold]")
    console.print("─" * 40)
    console.print()

    licensed_categories = license_data.payload.features if license_data else ["basic_features"]
    for category in licensed_categories:
        if category in CATEGORY_TO_FEATURES:
            cat_features = CATEGORY_TO_FEATURES[category]
            if cat_features:
                cat_name = category.replace("_", " ").title()
                features_str = ", ".join(sorted(cat_features))
                console.print(f"[bold cyan]{cat_name}:[/bold cyan]")
                console.print(f"  {features_str}")
                console.print()

    if tier == "solo":
        _print_locked_features()
    console.print()


def _print_locked_features() -> None:
    """Print locked features section for solo tier."""
    console.print("[dim]━" * 40 + "[/dim]")
    console.print()
    console.print("[yellow]Locked Features (Pro tier):[/yellow]")
    pro_features = CATEGORY_TO_FEATURES.get("pro_features", set())
    if pro_features:
        console.print(f"  [dim]{', '.join(sorted(pro_features))}[/dim]")
    console.print()
    console.print("[dim]Upgrade at: https://paircoder.ai/pricing[/dim]")


def _is_wsl() -> bool:
    """Check if running in Windows Subsystem for Linux."""
    try:
        return "microsoft" in platform.uname().release.lower()
    except Exception:
        return False


def _validate_license_file(license_file: Path) -> SignedLicense:
    """Validate and parse a license file. Raises typer.Exit on error."""
    if not license_file.exists():
        console.print(f"[red]Error:[/red] License file not found: {license_file}")

        # Add WSL-specific hint
        if _is_wsl():
            console.print()
            console.print("[yellow]WSL Tip:[/yellow] Windows downloads are typically at:")
            console.print("  /mnt/c/Users/<YourName>/Downloads/")
            console.print()
            console.print("Example:")
            console.print("  [cyan]bpsai-pair license install /mnt/c/Users/kevin/Downloads/license.json[/cyan]")

        raise typer.Exit(1)

    try:
        content = license_file.read_text()
        data = json.loads(content)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON in license file: {e}")
        raise typer.Exit(1)

    try:
        return SignedLicense(**data)
    except Exception as e:
        console.print(f"[red]Error:[/red] Invalid license format: {e}")
        raise typer.Exit(1)


def _install_license_file(license_file: Path, dest_file: Path) -> None:
    """Copy license file to destination."""
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(license_file, dest_file)
    clear_license_cache()


# License command group
app = typer.Typer(
    help="License management commands",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command("status")
def license_status(
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show current license status."""
    license_data = load_license()
    tier = get_tier()
    tier_display = get_tier_display_name(tier)
    features = get_all_features_api()

    if json_out:
        _print_json(_build_status_json(license_data, tier, tier_display, features))
    else:
        _print_status_rich(license_data, tier_display, features)


@app.command("path")
def license_path(
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show license file location."""
    current_path = _get_license_file_path()

    if json_out:
        search_paths = [
            os.environ.get("PAIRCODER_LICENSE", "(not set)"),
            str(Path.home() / ".paircoder" / "license.json"),
            str(Path.cwd() / ".paircoder" / "license.json"),
        ]
        _print_json({"current_path": str(current_path) if current_path else None, "search_paths": search_paths})
        return

    console.print()
    if current_path:
        console.print(f"[bold green]License file:[/bold green] {current_path}")
    else:
        console.print("[yellow]No license file found.[/yellow]")
        console.print()
        console.print("[bold]Search locations (in order):[/bold]")
        env_path = os.environ.get("PAIRCODER_LICENSE")
        if env_path:
            console.print(f"  1. PAIRCODER_LICENSE: {env_path}")
        else:
            console.print("  1. PAIRCODER_LICENSE: [dim](not set)[/dim]")
        console.print(f"  2. {Path.home() / '.paircoder' / 'license.json'}")
        console.print(f"  3. {Path.cwd() / '.paircoder' / 'license.json'}")
    console.print()


@app.command("features")
def license_features(
    json_out: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List available features for current tier."""
    license_data = load_license()
    tier = get_tier()
    tier_display = get_tier_display_name(tier)
    available_features = get_all_features_api()

    if json_out:
        _print_json({
            "tier": tier,
            "tier_display": tier_display,
            "feature_count": len(available_features),
            "features": sorted(available_features),
        })
    else:
        _print_features_rich(tier, tier_display, license_data)


@app.command("install")
def license_install(
    license_file: Path = typer.Argument(
        ...,
        help="Path to license file. WSL users: Windows files are at /mnt/c/Users/<name>/Downloads/",
        exists=False,
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing license"),
):
    """Install a license file to ~/.paircoder/license.json."""
    _validate_license_file(license_file)

    dest_file = Path.home() / ".paircoder" / "license.json"
    if dest_file.exists() and not force:
        console.print(f"[yellow]Warning:[/yellow] License already exists at {dest_file}")
        console.print("Use --force to overwrite.")
        raise typer.Exit(1)

    _install_license_file(license_file, dest_file)

    console.print()
    console.print(f"[green]✓[/green] Copied: {license_file} → {dest_file}")

    new_license = load_license()
    if new_license:
        tier_display = get_tier_display_name(new_license.payload.tier)
        console.print(f"[green]✓[/green] Signature verified")
        console.print()
        console.print(f"  [bold]Tier:[/bold]  {tier_display}")
        console.print(f"  [bold]Email:[/bold] {new_license.payload.email}")
    else:
        console.print()
        console.print("[yellow]⚠ Signature verification failed[/yellow]")
        console.print("  License may be invalid or signed with wrong key.")
        console.print("  The file was copied but may not work correctly.")
    console.print()
