"""PairCoder Licensing Module.

This module handles license loading, validation, and feature gating.

Key locations:
- Public key (embedded): bpsai_pair/licensing/public_key.pem
- Private key (secure): ~/.paircoder/keys/license_private_key.pem
  - Only accessible to license generation script
  - NOT included in the package or repository

Usage:
    from bpsai_pair.licensing import get_tier, has_feature, require_feature

    # Check current tier
    tier = get_tier()  # "solo", "pro", "team", "enterprise"

    # Check if a feature is available
    if has_feature("trello"):
        # Use trello integration
        pass

    # Require a feature via decorator
    @require_feature("github")
    def sync_with_github():
        pass
"""

from bpsai_pair.licensing.core import (
    FeatureNotAvailable,
    clear_license_cache,
    get_all_features_api,
    get_current_tier_display_name,
    get_tier,
    has_feature_api,
    is_expired,
    load_license,
    require_feature,
    verify_license,
    verify_signature,
)
from bpsai_pair.licensing.schema import (
    CATEGORY_TO_FEATURES,
    LicensePayload,
    LicenseTier,
    LicenseType,
    SignedLicense,
    get_all_features,
    get_tier_display_name,
    has_feature,
)

__all__ = [
    # Enums
    "LicenseTier",
    "LicenseType",
    # Models
    "LicensePayload",
    "SignedLicense",
    # Constants
    "CATEGORY_TO_FEATURES",
    # Exceptions
    "FeatureNotAvailable",
    # Schema Functions (low-level)
    "get_tier_display_name",
    "has_feature",
    "get_all_features",
    # Core API Functions (high-level)
    "load_license",
    "verify_signature",
    "verify_license",
    "is_expired",
    "get_tier",
    "get_current_tier_display_name",
    "has_feature_api",
    "get_all_features_api",
    "require_feature",
    "clear_license_cache",
]
