"""Docker sandbox runner for isolated command execution.

This module is the hub that re-exports from decomposed modules:
- data_classes: Data structures (MountConfig, FileChange, SandboxResult, SandboxConfig)
- runner: Execution (SandboxRunner)
- network_control: Network isolation (setup_network_allowlist)
- containment_config: Config conversion (containment_config_to_mounts)

Public API:
- MountConfig: Configuration for volume mounts
- FileChange: Represents a file change in sandbox
- SandboxResult: Result of running a command
- SandboxConfig: Configuration for Docker sandbox
- SandboxRunner: Execute commands in isolated containers
- containment_config_to_mounts: Convert ContainmentConfig to Docker mounts

Decomposed in Sprint 29.6 (EPIC-005 Phase 3).
"""

from __future__ import annotations

# Re-export data structures from data_classes
from .data_classes import (
    MountConfig,
    FileChange,
    SandboxResult,
    SandboxConfig,
    DIFF_MODIFIED,
    DIFF_CREATED,
    DIFF_DELETED,
    DIFF_KIND_TO_ACTION,
)

# Re-export SandboxRunner from runner
from .runner import (
    SandboxRunner,
    CONTAINMENT_IMAGE_REPO,
)

# Re-export containment_config_to_mounts
from .containment_config import containment_config_to_mounts

# Re-export network control (for direct usage if needed)
from .network_control import setup_network_allowlist


# Public API
__all__ = [
    # Data structures
    "MountConfig",
    "FileChange",
    "SandboxResult",
    "SandboxConfig",
    # Constants
    "DIFF_MODIFIED",
    "DIFF_CREATED",
    "DIFF_DELETED",
    "DIFF_KIND_TO_ACTION",
    "CONTAINMENT_IMAGE_REPO",
    # Classes
    "SandboxRunner",
    # Functions
    "containment_config_to_mounts",
    "setup_network_allowlist",
]
