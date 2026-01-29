"""Configuration management for PairCoder.

This module serves as the main public API for configuration management.
It re-exports all public symbols from the decomposed modules:

- config_defaults: Default values and constants
- config_helpers: Validation utilities
- config_validator: Validation dataclasses and functions
- config_loader: Config class and YAML loading/saving

For direct imports from specific modules, use:
- bpsai_pair.core.config_defaults
- bpsai_pair.core.config_helpers
- bpsai_pair.core.config_validator
- bpsai_pair.core.config_loader
"""
from __future__ import annotations

# Re-export from config_defaults
from .config_defaults import (
    CONFIG_SCHEMA_VERSION,
    CURRENT_CONFIG_VERSION,  # Backwards compat alias for CONFIG_SCHEMA_VERSION
    REQUIRED_SECTIONS,
    DEFAULT_CONTAINMENT_NETWORK_ALLOWLIST,
    DEFAULT_PROJECT_NAME,
    DEFAULT_PRIMARY_GOAL,
    DEFAULT_COVERAGE_TARGET,
    DEFAULT_BRANCH_TYPE,
    DEFAULT_MAIN_BRANCH,
    DEFAULT_CONTEXT_DIR,
    DEFAULT_PACK_NAME,
    DEFAULT_PACK_EXCLUDES,
    DEFAULT_PYTHON_FORMATTER,
    DEFAULT_NODE_FORMATTER,
    ENV_MAPPINGS,
)

# Re-export from config_helpers
from .config_helpers import (
    ConfigError,
    validate_path,
    validate_domain,
    validate_no_unrendered_templates,
    validate_path_list,
    validate_domain_list,
)

# Backward compatibility: provide _validate_no_unrendered_templates alias
_validate_no_unrendered_templates = validate_no_unrendered_templates

# Backward compatibility: private validation functions
_validate_path = validate_path
_validate_domain = validate_domain

# Re-export from config_validator
from .config_validator import (
    ContainmentConfig,
    SandboxConfig,
    ArchitectureConfig,
    ConfigValidationResult,
    validate_config,
    update_config,
)

# Re-export from config_loader
from .config_loader import (
    Config,
    load_raw_config,
    save_raw_config,
)

# Import ContextTemplate class inline (kept in this module for simplicity)
from .config_templates import ContextTemplate


# Public API
__all__ = [
    # Defaults and constants
    "CONFIG_SCHEMA_VERSION",
    "CURRENT_CONFIG_VERSION",  # Backwards compat alias
    "REQUIRED_SECTIONS",
    "DEFAULT_CONTAINMENT_NETWORK_ALLOWLIST",
    "DEFAULT_PROJECT_NAME",
    "DEFAULT_PRIMARY_GOAL",
    "DEFAULT_COVERAGE_TARGET",
    "DEFAULT_BRANCH_TYPE",
    "DEFAULT_MAIN_BRANCH",
    "DEFAULT_CONTEXT_DIR",
    "DEFAULT_PACK_NAME",
    "DEFAULT_PACK_EXCLUDES",
    "DEFAULT_PYTHON_FORMATTER",
    "DEFAULT_NODE_FORMATTER",
    "ENV_MAPPINGS",
    # Exceptions
    "ConfigError",
    # Validation helpers
    "validate_path",
    "validate_domain",
    "validate_no_unrendered_templates",
    "validate_path_list",
    "validate_domain_list",
    # Dataclasses
    "Config",
    "ContainmentConfig",
    "SandboxConfig",
    "ArchitectureConfig",
    "ConfigValidationResult",
    # Functions
    "validate_config",
    "update_config",
    "load_raw_config",
    "save_raw_config",
    # Templates
    "ContextTemplate",
]
