"""Core license loading, validation, and feature checking.

This module provides the main API for license operations:
- Loading licenses from filesystem
- Verifying signatures
- Checking feature availability
- Requiring features via decorator
"""

import base64
import functools
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TypeVar

from bpsai_pair.licensing.schema import (
    CATEGORY_TO_FEATURES,
    SignedLicense,
    get_all_features,
    get_tier_display_name as _get_tier_display_name,
    has_feature,
)

logger = logging.getLogger(__name__)

# Module-level cache for loaded license
_license_cache: SignedLicense | None = None
_license_cache_loaded: bool = False

# Type variable for decorator return type
F = TypeVar("F", bound=Callable)


class FeatureNotAvailable(Exception):
    """Raised when a required feature is not available."""

    def __init__(self, feature: str, tier: str = "solo"):
        self.feature = feature
        self.tier = tier
        super().__init__(
            f"Feature '{feature}' is not available in the {_get_tier_display_name(tier)} tier. "
            f"Upgrade your license to access this feature."
        )


def _get_public_key_path() -> Path:
    """Get the path to the embedded public key."""
    return Path(__file__).parent / "public_key.pem"


def _get_license_paths() -> list[Path]:
    """Get ordered list of paths to search for license file.

    Returns paths in priority order:
    1. PAIRCODER_LICENSE env var (if set)
    2. ~/.paircoder/license.json
    3. ./.paircoder/license.json (current directory)
    """
    paths: list[Path] = []

    # 1. Environment variable takes highest precedence
    env_path = os.environ.get("PAIRCODER_LICENSE")
    if env_path:
        paths.append(Path(env_path))

    # 2. User home directory
    home_license = Path.home() / ".paircoder" / "license.json"
    paths.append(home_license)

    # 3. Current working directory
    cwd_license = Path.cwd() / ".paircoder" / "license.json"
    paths.append(cwd_license)

    return paths


def clear_license_cache() -> None:
    """Clear the cached license.

    Call this if you need to reload the license from disk.
    """
    global _license_cache, _license_cache_loaded
    _license_cache = None
    _license_cache_loaded = False


def _try_load_from_path(path: Path) -> SignedLicense | None:
    """Try to load and verify a license from a specific path.

    SECURITY: Verifies signature and expiration before returning.
    """
    try:
        data = json.loads(path.read_text())
        license_obj = SignedLicense(**data)

        # SECURITY: Verify signature before accepting
        if not verify_signature(license_obj):
            logger.warning(f"License signature verification failed: {path}")
            return None

        # Check expiration
        if is_expired(license_obj):
            logger.warning(f"License has expired: {path}")
            return None

        logger.debug(f"Loaded and verified license from {path}")
        return license_obj
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in license file {path}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Failed to parse license from {path}: {e}")
        return None


def load_license() -> SignedLicense | None:
    """Load and verify license from filesystem.

    Searches in priority order: PAIRCODER_LICENSE env, ~/.paircoder/, ./.paircoder/

    SECURITY: Signature is verified before accepting. Invalid licenses are rejected.

    Returns:
        SignedLicense if found, valid, and not expired. None otherwise. Cached.
    """
    global _license_cache, _license_cache_loaded

    if _license_cache_loaded:
        return _license_cache

    for path in _get_license_paths():
        if path.exists():
            license_obj = _try_load_from_path(path)
            if license_obj:
                _license_cache = license_obj
                _license_cache_loaded = True
                return license_obj

    _license_cache = None
    _license_cache_loaded = True
    return None


def verify_signature(
    license_data: SignedLicense, public_key_pem: bytes | None = None
) -> bool:
    """Verify the RSA-PSS signature of a license.

    Args:
        license_data: The signed license to verify
        public_key_pem: PEM-encoded public key bytes. If None, loads from embedded key.

    Returns:
        True if signature is valid, False otherwise.
    """
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError:
        logger.error("cryptography package not installed, cannot verify signature")
        return False

    try:
        # Load public key
        if public_key_pem is None:
            public_key_pem = _get_public_key_path().read_bytes()

        public_key = serialization.load_pem_public_key(public_key_pem)

        # Reconstruct canonical JSON from payload
        payload_dict = license_data.payload.model_dump(mode="json")
        data_bytes = json.dumps(
            payload_dict, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

        # Decode signature
        signature = base64.b64decode(license_data.signature)

        # Verify with RSA-PSS SHA-256
        public_key.verify(
            signature,
            data_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return True

    except Exception as e:
        logger.debug(f"Signature verification failed: {e}")
        return False


def is_expired(license_data: SignedLicense) -> bool:
    """Check if a license has expired.

    Args:
        license_data: The license to check

    Returns:
        True if expired, False if still valid or never expires (expires_at is None)
    """
    expires_at = license_data.payload.expires_at
    if expires_at is None:
        return False  # Perpetual license never expires

    # Ensure we compare timezone-aware datetimes
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return now > expires_at


def verify_license(
    license_data: SignedLicense, public_key_path: Path | None = None
) -> bool:
    """Fully verify a license (signature and expiration).

    Args:
        license_data: The license to verify
        public_key_path: Path to public key file. If None, uses embedded key.

    Returns:
        True if license is valid and not expired, False otherwise.
    """
    # Check expiration first (cheaper check)
    if is_expired(license_data):
        logger.debug("License has expired")
        return False

    # Verify signature
    public_key_pem = None
    if public_key_path:
        public_key_pem = public_key_path.read_bytes()

    if not verify_signature(license_data, public_key_pem):
        logger.debug("License signature verification failed")
        return False

    return True


def get_tier() -> str:
    """Get the current license tier.

    Returns:
        Tier string ("solo", "pro", "team", "enterprise").
        Returns "solo" if no valid license is loaded.
    """
    license_data = load_license()
    if license_data is None:
        return "solo"
    return license_data.payload.tier


def get_current_tier_display_name() -> str:
    """Get the marketing display name for the current tier.

    Returns:
        Display name like "Solo", "Pro", "Team", "Enterprise"
    """
    return _get_tier_display_name(get_tier())


def has_feature_api(feature: str) -> bool:
    """Check if a feature is available with current license.

    Args:
        feature: The granular feature name (e.g., "trello", "core")

    Returns:
        True if feature is available, False otherwise.
    """
    license_data = load_license()

    if license_data is None:
        # No license = solo tier = basic features only
        return has_feature(["basic_features"], feature)

    return has_feature(license_data.payload.features, feature)


def get_all_features_api() -> set[str]:
    """Get all features available with current license.

    Returns:
        Set of all available granular feature names.
    """
    license_data = load_license()

    if license_data is None:
        # No license = solo tier = basic features only
        return get_all_features(["basic_features"])

    return get_all_features(license_data.payload.features)


def require_feature(feature: str) -> Callable[[F], F]:
    """Decorator that requires a feature to be available.

    Args:
        feature: The granular feature name required

    Returns:
        Decorator function

    Raises:
        FeatureNotAvailable: If the feature is not available

    Example:
        @require_feature("trello")
        def sync_with_trello():
            # Only runs if trello feature is available
            pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not has_feature_api(feature):
                raise FeatureNotAvailable(feature, get_tier())
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator
