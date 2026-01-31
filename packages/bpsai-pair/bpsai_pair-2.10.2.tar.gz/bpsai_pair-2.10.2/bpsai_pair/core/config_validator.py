"""Configuration validation for PairCoder.

This module contains dataclasses and functions for validating
PairCoder configuration files.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import yaml

from .config_defaults import (
    CURRENT_CONFIG_VERSION,
    REQUIRED_SECTIONS,
    DEFAULT_CONTAINMENT_NETWORK_ALLOWLIST,
)
from .config_helpers import (
    validate_path_list,
    validate_domain_list,
    validate_no_unrendered_templates,
    ConfigError,
)


@dataclass
class ContainmentConfig:
    """Configuration for contained autonomy mode with three-tier access control.

    Access tiers:
    - Blocked: No read, no write (secrets, credentials, .env files)
    - Read-only: Can read, cannot write (CLAUDE.md, skills, enforcement code)
    - Read-write: Normal access (everything else - the working area)

    This configuration controls containment mode behavior, including
    which directories and files are in each tier, which network
    domains are allowed, and checkpoint/rollback behavior.

    Note: This is separate from the Docker sandbox system (security.sandbox).
    """

    enabled: bool = False
    """Enable containment mode for contained autonomy."""

    mode: str = "advisory"
    """Containment enforcement mode:
    - 'advisory': Log violations but don't block (default)
    - 'strict': Docker-based enforcement with read-only mounts
    """

    # Tier 1: Blocked (no read, no write)
    blocked_directories: List[str] = field(default_factory=list)
    """Directories that cannot be read or written (secrets, credentials)."""

    blocked_files: List[str] = field(default_factory=list)
    """Files that cannot be read or written (e.g., .env, credentials.json)."""

    # Tier 2: Read-only (can read, cannot write)
    readonly_directories: List[str] = field(default_factory=list)
    """Directories that can be read but not written (enforcement code, skills)."""

    readonly_files: List[str] = field(default_factory=list)
    """Files that can be read but not written (CLAUDE.md, config files)."""

    allow_network: List[str] = field(
        default_factory=lambda: DEFAULT_CONTAINMENT_NETWORK_ALLOWLIST.copy()
    )
    """Network domains allowed in containment mode."""

    auto_checkpoint: bool = True
    """Create git checkpoint on containment entry."""

    rollback_on_violation: bool = False
    """Rollback to checkpoint on containment violation attempts."""

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Validate mode
        valid_modes = ("advisory", "strict")
        if self.mode not in valid_modes:
            raise ValueError(
                f"Invalid containment mode: {self.mode!r}. "
                f"Must be one of: {', '.join(valid_modes)}"
            )

        # Validate blocked_directories
        self.blocked_directories = validate_path_list(
            self.blocked_directories, "blocked_directories"
        )

        # Validate blocked_files
        self.blocked_files = validate_path_list(self.blocked_files, "blocked_files")

        # Validate readonly_directories
        self.readonly_directories = validate_path_list(
            self.readonly_directories, "readonly_directories"
        )

        # Validate readonly_files
        self.readonly_files = validate_path_list(self.readonly_files, "readonly_files")

        # Validate allow_network
        self.allow_network = validate_domain_list(self.allow_network)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the config.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContainmentConfig":
        """Create ContainmentConfig from dictionary.

        Supports backward compatibility with old 'locked_*' field names
        by mapping them to 'readonly_*'.

        Args:
            data: Dictionary with config values.

        Returns:
            ContainmentConfig instance.
        """
        # Handle backward compatibility: locked_* -> readonly_*
        if "locked_directories" in data and "readonly_directories" not in data:
            data["readonly_directories"] = data.pop("locked_directories")
        elif "locked_directories" in data:
            data.pop("locked_directories")  # Prefer new name if both present

        if "locked_files" in data and "readonly_files" not in data:
            data["readonly_files"] = data.pop("locked_files")
        elif "locked_files" in data:
            data.pop("locked_files")  # Prefer new name if both present

        # Only pass keys that are valid for ContainmentConfig
        valid_keys = {
            "enabled",
            "mode",
            "blocked_directories",
            "blocked_files",
            "readonly_directories",
            "readonly_files",
            "allow_network",
            "auto_checkpoint",
            "rollback_on_violation",
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)


# Backwards compatibility alias
SandboxConfig = ContainmentConfig


@dataclass
class ArchitectureConfig:
    """Configuration for architecture enforcement.

    Controls thresholds and behavior for architecture checks including
    file size limits, function length limits, and exclude patterns.

    Attributes:
        enabled: Whether architecture enforcement is enabled
        max_file_lines: Maximum lines before error (default: 400)
        warning_file_lines: Lines before warning (default: 200)
        max_function_lines: Maximum lines per function (default: 50)
        max_functions_per_file: Maximum functions per file (default: 15)
        max_imports: Maximum import statements (default: 20)
        exclude_patterns: Glob patterns to exclude from checks
        enforce_on_commit: Enable pre-commit hook enforcement
        enforce_on_pr: Enable PR check enforcement
        enforce_on_ci: Enable CI pipeline enforcement
    """

    enabled: bool = True
    """Enable architecture enforcement."""

    max_file_lines: int = 400
    """Maximum lines before error."""

    warning_file_lines: int = 200
    """Lines before warning."""

    max_function_lines: int = 50
    """Maximum lines per function."""

    max_functions_per_file: int = 15
    """Maximum functions per file."""

    max_imports: int = 20
    """Maximum import statements."""

    exclude_patterns: List[str] = field(default_factory=list)
    """Glob patterns to exclude from checks."""

    enforce_on_commit: bool = True
    """Enable pre-commit hook enforcement."""

    enforce_on_pr: bool = True
    """Enable PR check enforcement."""

    enforce_on_ci: bool = True
    """Enable CI pipeline enforcement."""

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Validate thresholds are positive
        if self.max_file_lines <= 0:
            raise ValueError("max_file_lines must be positive")
        if self.warning_file_lines <= 0:
            raise ValueError("warning_file_lines must be positive")
        if self.max_function_lines <= 0:
            raise ValueError("max_function_lines must be positive")
        if self.max_functions_per_file <= 0:
            raise ValueError("max_functions_per_file must be positive")
        if self.max_imports <= 0:
            raise ValueError("max_imports must be positive")

        # Validate warning < max
        if self.warning_file_lines > self.max_file_lines:
            raise ValueError(
                f"warning_file_lines ({self.warning_file_lines}) cannot exceed "
                f"max_file_lines ({self.max_file_lines})"
            )

        # Validate exclude patterns
        for i, pattern in enumerate(self.exclude_patterns):
            if not pattern or not isinstance(pattern, str):
                raise ValueError(
                    f"Invalid exclude pattern at index {i}: patterns must be non-empty strings"
                )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the config.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArchitectureConfig":
        """Create ArchitectureConfig from dictionary.

        Args:
            data: Dictionary with config values.

        Returns:
            ArchitectureConfig instance.
        """
        # Map old 'thresholds' nested dict to flat keys if present
        if "thresholds" in data and isinstance(data["thresholds"], dict):
            thresholds = data.pop("thresholds")
            for key, value in thresholds.items():
                if key not in data:
                    data[key] = value

        # Map old 'exclude' key to 'exclude_patterns' if present
        if "exclude" in data and "exclude_patterns" not in data:
            data["exclude_patterns"] = data.pop("exclude")
        elif "exclude" in data:
            data.pop("exclude")

        # Map enforce_on dict to flat keys if present
        if "enforce_on" in data and isinstance(data["enforce_on"], dict):
            enforce_on = data.pop("enforce_on")
            if "commit" in enforce_on and "enforce_on_commit" not in data:
                data["enforce_on_commit"] = enforce_on["commit"]
            if "pr" in enforce_on and "enforce_on_pr" not in data:
                data["enforce_on_pr"] = enforce_on["pr"]
            if "ci" in enforce_on and "enforce_on_ci" not in data:
                data["enforce_on_ci"] = enforce_on["ci"]

        # Only pass keys that are valid for ArchitectureConfig
        valid_keys = {
            "enabled",
            "max_file_lines",
            "warning_file_lines",
            "max_function_lines",
            "max_functions_per_file",
            "max_imports",
            "exclude_patterns",
            "enforce_on_commit",
            "enforce_on_pr",
            "enforce_on_ci",
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)


@dataclass
class ConfigValidationResult:
    """Result of config validation."""

    is_valid: bool
    current_version: Optional[str]
    target_version: str
    missing_sections: List[str]
    missing_keys: Dict[str, List[str]]  # section -> missing keys
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "current_version": self.current_version,
            "target_version": self.target_version,
            "missing_sections": self.missing_sections,
            "missing_keys": self.missing_keys,
            "warnings": self.warnings,
        }


def _load_raw_config_for_validation(
    root: Path,
) -> Tuple[Optional[Dict[str, Any]], Optional[Path]]:
    """Load raw config for validation purposes.

    Args:
        root: Project root directory

    Returns:
        Tuple of (config dict, config file path) or (None, None) if not found
    """
    # Check for config files in order of preference
    v2_config = root / ".paircoder" / "config.yaml"
    v2_config_yml = root / ".paircoder" / "config.yml"
    legacy_config = root / ".paircoder.yml"

    config_file = None
    if v2_config.exists():
        config_file = v2_config
    elif v2_config_yml.exists():
        config_file = v2_config_yml
    elif legacy_config.exists():
        config_file = legacy_config

    if not config_file:
        return None, None

    # Validate no unrendered templates before loading
    validate_no_unrendered_templates(config_file)

    with open(config_file, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data, config_file


def validate_config(
    root: Path, preset_name: str = "minimal"
) -> ConfigValidationResult:
    """Validate config against preset template.

    Args:
        root: Project root directory
        preset_name: Preset to validate against

    Returns:
        ConfigValidationResult with validation details
    """
    from .presets import get_preset

    raw_config, config_file = _load_raw_config_for_validation(root)

    if raw_config is None:
        return ConfigValidationResult(
            is_valid=False,
            current_version=None,
            target_version=CURRENT_CONFIG_VERSION,
            missing_sections=REQUIRED_SECTIONS,
            missing_keys={},
            warnings=["No config file found. Run 'bpsai-pair init' to create one."],
        )

    # Get template from preset
    preset = get_preset(preset_name)
    if not preset:
        preset = get_preset("minimal")

    template = preset.to_config_dict("Project", "Build software")

    # Check version
    current_version = raw_config.get("version")
    warnings = []

    if current_version and current_version != CURRENT_CONFIG_VERSION:
        warnings.append(
            f"Config version {current_version} is outdated (current: {CURRENT_CONFIG_VERSION})"
        )

    # Check missing sections
    missing_sections = []
    for section in REQUIRED_SECTIONS:
        if section not in raw_config:
            missing_sections.append(section)

    # Check missing keys within existing sections
    missing_keys = {}
    for section, section_template in template.items():
        if (
            section in raw_config
            and isinstance(section_template, dict)
            and isinstance(raw_config[section], dict)
        ):
            section_missing = []
            for key in section_template:
                if key not in raw_config[section]:
                    section_missing.append(key)
            if section_missing:
                missing_keys[section] = section_missing

    is_valid = not missing_sections and not missing_keys and not warnings

    return ConfigValidationResult(
        is_valid=is_valid,
        current_version=current_version,
        target_version=CURRENT_CONFIG_VERSION,
        missing_sections=missing_sections,
        missing_keys=missing_keys,
        warnings=warnings,
    )


def update_config(
    root: Path, preset_name: str = "minimal"
) -> Tuple[Dict[str, Any], List[str]]:
    """Update config with missing sections from preset.

    Args:
        root: Project root directory
        preset_name: Preset to use for defaults

    Returns:
        Tuple of (updated config dict, list of changes made)
    """
    from .presets import get_preset

    raw_config, config_file = _load_raw_config_for_validation(root)

    if raw_config is None:
        raise ValueError("No config file found. Run 'bpsai-pair init' first.")

    # Get template from preset
    preset = get_preset(preset_name)
    if not preset:
        preset = get_preset("minimal")

    # Get project name and goal from existing config
    project_name = raw_config.get("project", {}).get("name", "My Project")
    primary_goal = raw_config.get("project", {}).get(
        "primary_goal", "Build software"
    )

    template = preset.to_config_dict(project_name, primary_goal)

    changes = []

    # Update version
    old_version = raw_config.get("version")
    if old_version != CURRENT_CONFIG_VERSION:
        raw_config["version"] = CURRENT_CONFIG_VERSION
        changes.append(f"Updated version: {old_version} → {CURRENT_CONFIG_VERSION}")

    # Add missing sections
    for section in REQUIRED_SECTIONS:
        if section not in raw_config and section in template:
            raw_config[section] = template[section]
            changes.append(f"Added section: {section}")

    # Add missing keys within existing sections (preserve existing values)
    for section, section_template in template.items():
        if (
            section in raw_config
            and isinstance(section_template, dict)
            and isinstance(raw_config[section], dict)
        ):
            for key, value in section_template.items():
                if key not in raw_config[section]:
                    raw_config[section][key] = value
                    changes.append(f"Added key: {section}.{key}")

    return raw_config, changes
