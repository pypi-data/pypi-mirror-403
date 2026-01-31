"""Default configuration values and constants for PairCoder.

This module contains all default values, constants, and configuration
presets used throughout the config system.
"""
from __future__ import annotations

from typing import Dict, List

# Config schema version - static value that only changes when config structure changes
# This is DECOUPLED from the package version. Patch releases (2.9.4 → 2.9.5) don't
# require config schema changes. Only bump this when the config.yaml structure changes.
CONFIG_SCHEMA_VERSION = "2.9.3"

# Backwards compatibility alias (deprecated, use CONFIG_SCHEMA_VERSION)
CURRENT_CONFIG_VERSION = CONFIG_SCHEMA_VERSION

# Required top-level sections for a complete config
# Note: 'flows' was removed - deprecated in favor of skills
# Note: 'security' is optional - not all projects need it
REQUIRED_SECTIONS: List[str] = [
    "version",
    "project",
    "workflow",
    "pack",
    "routing",
    "trello",
    "estimation",
    "metrics",
    "hooks",
]

# Default network domains allowed in containment mode
DEFAULT_CONTAINMENT_NETWORK_ALLOWLIST: List[str] = [
    "api.anthropic.com",
    "api.trello.com",
    "github.com",
    "pypi.org",
]

# Default project settings
DEFAULT_PROJECT_NAME = "My Project"
DEFAULT_PRIMARY_GOAL = "Build awesome software"
DEFAULT_COVERAGE_TARGET = 80

# Default branch settings
DEFAULT_BRANCH_TYPE = "feature"
DEFAULT_MAIN_BRANCH = "main"

# Default context settings
DEFAULT_CONTEXT_DIR = "context"

# Default pack settings
DEFAULT_PACK_NAME = "agent_pack.tgz"
DEFAULT_PACK_EXCLUDES: List[str] = [
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "*.log",
    "*.bak",
]

# Default CI settings
DEFAULT_PYTHON_FORMATTER = "ruff"
DEFAULT_NODE_FORMATTER = "prettier"

# Environment variable mappings
# Maps environment variable names to config field names
ENV_MAPPINGS: Dict[str, str] = {
    "PAIRCODER_MAIN_BRANCH": "main_branch",
    "PAIRCODER_CONTEXT_DIR": "context_dir",
    "PAIRCODER_DEFAULT_BRANCH": "default_branch_type",
    "PAIRCODER_PROJECT_NAME": "project_name",
}
