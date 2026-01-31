"""License installation utilities for the wizard.

This module handles license verification and installation from JSON data.
"""

from __future__ import annotations

import json
from pathlib import Path


def _parse_license_json(license_json: str) -> dict:
    """Parse license JSON string."""
    try:
        return json.loads(license_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")


def _validate_license_structure(data: dict):
    """Validate license data structure and return SignedLicense."""
    from bpsai_pair.licensing import SignedLicense

    try:
        return SignedLicense(**data)
    except Exception as e:
        raise ValueError(f"Invalid license format: {e}")


def _verify_license_signature(license_obj) -> bool:
    """Verify the license signature."""
    from bpsai_pair.licensing import verify_signature

    return verify_signature(license_obj)


def _check_license_expiration(license_obj) -> bool:
    """Check if license has expired."""
    from bpsai_pair.licensing import is_expired

    return is_expired(license_obj)


def _install_license_file(license_json: str) -> Path:
    """Install license JSON to the user's home directory."""
    dest_file = Path.home() / ".paircoder" / "license.json"
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    dest_file.write_text(license_json)
    return dest_file


def _validate_license(license_json: str) -> tuple[object, str | None]:
    """Validate license JSON and return license object or error.

    Returns:
        Tuple of (license_obj, error_message). If valid, error is None.
    """
    # Parse JSON
    try:
        data = _parse_license_json(license_json)
    except ValueError as e:
        return None, str(e)

    # Validate license structure
    try:
        license_obj = _validate_license_structure(data)
    except ValueError as e:
        return None, str(e)

    # Verify signature
    if not _verify_license_signature(license_obj):
        return None, "Invalid license signature"

    # Check expiration
    if _check_license_expiration(license_obj):
        return None, "License has expired"

    return license_obj, None


def _build_success_response(license_obj) -> dict:
    """Build success response from validated license."""
    from bpsai_pair.licensing import get_tier_display_name

    tier = license_obj.payload.tier
    tier_display = get_tier_display_name(tier)

    return {
        "success": True,
        "tier": tier,
        "tier_display": tier_display,
        "message": f"License installed successfully. Welcome to {tier_display}!",
    }


def verify_and_install_license(license_json: str) -> dict:
    """Verify and install a license from JSON string.

    Args:
        license_json: JSON string containing the signed license

    Returns:
        Dict with success status, tier info, and message
    """
    try:
        from bpsai_pair.licensing import clear_license_cache
    except ImportError:
        return {"success": False, "error": "Licensing module not available"}

    # Validate the license
    license_obj, error = _validate_license(license_json)
    if error:
        return {"success": False, "error": error}

    # Install to ~/.paircoder/license.json
    _install_license_file(license_json)

    # Clear cache to reload new license
    clear_license_cache()

    return _build_success_response(license_obj)
