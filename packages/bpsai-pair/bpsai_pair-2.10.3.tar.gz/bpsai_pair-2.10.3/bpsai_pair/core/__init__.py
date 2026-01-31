"""Core infrastructure modules for bpsai-pair CLI.

This module consolidates shared utilities that were previously scattered
at the package root level:
- config: Configuration loading and management
- constants: Application constants
- hooks: Hook system for task lifecycle events
- ops: Git and file operations
- presets: Preset system for common configurations
- utils: General utilities (merged from utils, pyutils, jsonio)
"""

from . import config
from . import constants
from . import hooks
from . import ops
from . import presets
from . import utils

# Re-export commonly used classes for convenience
from .config import (
    Config,
    ConfigValidationResult,
    ContextTemplate,
    CONFIG_SCHEMA_VERSION,
    CURRENT_CONFIG_VERSION,  # Backwards compat alias
    load_raw_config,
    validate_config,
    update_config,
    save_raw_config,
)

from .constants import (
    TASK_ID_PATTERN,
    TASK_ID_REGEX,
    TASK_FILE_GLOBS,
    is_valid_task_id,
    extract_task_id,
    extract_task_id_from_card_name,
)

from .presets import (
    Preset,
    PRESETS,
    get_preset,
    list_presets,
    get_preset_names,
    PresetManager,
)

from .utils import (
    repo_root,
    ensure_executable,
    project_files,
    dump,
)

from .ops import (
    find_project_root,
    find_paircoder_dir,
    ProjectRootNotFoundError,
)

__all__ = [
    # Modules
    "config",
    "constants",
    "hooks",
    "ops",
    "presets",
    "utils",
    # Config classes and functions
    "Config",
    "ConfigValidationResult",
    "ContextTemplate",
    "CONFIG_SCHEMA_VERSION",
    "CURRENT_CONFIG_VERSION",  # Backwards compat alias
    "load_raw_config",
    "validate_config",
    "update_config",
    "save_raw_config",
    # Constants
    "TASK_ID_PATTERN",
    "TASK_ID_REGEX",
    "TASK_FILE_GLOBS",
    "is_valid_task_id",
    "extract_task_id",
    "extract_task_id_from_card_name",
    # Presets
    "Preset",
    "PRESETS",
    "get_preset",
    "list_presets",
    "get_preset_names",
    "PresetManager",
    # Utils
    "repo_root",
    "ensure_executable",
    "project_files",
    "dump",
    # Ops helpers
    "find_project_root",
    "find_paircoder_dir",
    "ProjectRootNotFoundError",
]
