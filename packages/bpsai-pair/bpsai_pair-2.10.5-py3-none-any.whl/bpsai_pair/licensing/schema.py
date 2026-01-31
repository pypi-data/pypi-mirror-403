"""License schema models for PairCoder licensing system.

This module defines the Pydantic models that match the API's license format,
along with category-to-feature mappings and helper functions.
"""

import re
from datetime import datetime
from enum import Enum
from typing import Annotated, Union
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field

# Simple email regex - basic validation without email-validator dependency
_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def _validate_email(value: str) -> str:
    """Validate email format."""
    if not _EMAIL_REGEX.match(value):
        raise ValueError("Invalid email format")
    return value


# Email type with validation
Email = Annotated[str, AfterValidator(_validate_email)]


class LicenseTier(str, Enum):
    """License tier levels."""

    SOLO = "solo"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class LicenseType(str, Enum):
    """License type (duration model)."""

    PERPETUAL = "perpetual"
    SUBSCRIPTION = "subscription"
    TRIAL = "trial"


class LicensePayload(BaseModel):
    """License payload data from the API.

    This model matches the API's license format exactly.
    """

    version: str
    license_id: UUID
    email: Email
    name: str
    tier: str  # Keep as string for flexibility, enum validation separate
    type: str  # Keep as string for flexibility
    issued_at: datetime
    expires_at: datetime | None = None
    founder_number: int | None = None
    features: list[str] = Field(default_factory=list)


class SignedLicense(BaseModel):
    """A signed license containing payload and RSA-PSS signature.

    The signature is a Base64-encoded RSA-PSS signature of the JSON-serialized
    payload.
    """

    payload: LicensePayload
    signature: str = Field(..., min_length=1)


# Category to granular CLI features mapping
# These map the API's feature categories to specific CLI features
CATEGORY_TO_FEATURES: dict[str, set[str]] = {
    "basic_features": {
        "core",
        "skills",
        "planning",
        "state",
        "enforcement",
        "containment",
        "guided_setup",
        "metrics_basic",
        "slash_commands",
    },
    "pro_features": {
        "trello",
        "trello_native",
        "github",
        "mcp",
        "timer",
        "token_budget",
        "cost_tracking",
        "model_routing",
        "metrics_velocity",
        "metrics_burndown",
    },
    "team_features": set(),  # Reserved for future use
    "enterprise_features": {
        "remote_access",
        "background_tasks",
        "notifications",
        "multi_workspace",
        "cross_repo_contracts",
        "team_management",
        "sso",
    },
}

# Marketing display names for tiers
_TIER_DISPLAY_NAMES: dict[str, str] = {
    "solo": "Solo",
    "pro": "Pro",
    "team": "Team",
    "enterprise": "Enterprise",
}


def get_tier_display_name(tier: Union[str, LicenseTier]) -> str:
    """Get the marketing display name for a tier.

    Args:
        tier: The tier value (string or LicenseTier enum)

    Returns:
        The marketing display name (e.g., "solo" -> "Solo", "pro" -> "Pro")
    """
    tier_str = tier.value if isinstance(tier, LicenseTier) else tier
    return _TIER_DISPLAY_NAMES.get(tier_str, tier_str.title())


def has_feature(license_features: list[str], feature: str) -> bool:
    """Check if a feature is available based on license feature categories.

    Args:
        license_features: List of feature category names from the license
                         (e.g., ["basic_features", "pro_features"])
        feature: The specific feature to check for (e.g., "trello", "core")

    Returns:
        True if the feature is available, False otherwise
    """
    for category in license_features:
        if category in CATEGORY_TO_FEATURES:
            if feature in CATEGORY_TO_FEATURES[category]:
                return True
    return False


def get_all_features(license_features: list[str]) -> set[str]:
    """Expand license feature categories into a set of all available features.

    Args:
        license_features: List of feature category names from the license
                         (e.g., ["basic_features", "pro_features"])

    Returns:
        Set of all individual features available
    """
    all_features: set[str] = set()
    for category in license_features:
        if category in CATEGORY_TO_FEATURES:
            all_features |= CATEGORY_TO_FEATURES[category]
    return all_features
