"""Containment configuration to Docker mount conversion.

This module provides functions for converting ContainmentConfig
access control settings to Docker mount configurations.

Functions:
    containment_config_to_mounts: Convert ContainmentConfig to Docker mounts

Extracted from sandbox.py as part of EPIC-005 module decomposition.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.config import ContainmentConfig

from .data_classes import MountConfig


def containment_config_to_mounts(
    config: "ContainmentConfig",
    project_root: Path,
) -> tuple[list[MountConfig], list[str]]:
    """Convert ContainmentConfig to Docker mount configuration.

    Maps the three-tier access control to Docker volumes:
    - Blocked paths: Overlaid with empty tmpfs (content hidden/inaccessible)
    - Readonly paths: Mounted with readonly=True (OS-enforced)
    - Everything else: Part of workspace mount (read-write)

    The mount order matters! Docker processes mounts in order, so:
    1. Base workspace mount (everything visible)
    2. Blocked paths overlaid with tmpfs (hides original content)
    3. Readonly paths overlaid with ro bind mount (protects from writes)

    Args:
        config: ContainmentConfig with path restrictions
        project_root: Root directory of the project

    Returns:
        Tuple of (mounts, blocked_paths):
        - mounts: List of MountConfig for Docker volumes (includes tmpfs for blocked)
        - blocked_paths: List of paths that are blocked (for reference/logging)

    Example:
        >>> from bpsai_pair.core.config import ContainmentConfig
        >>> config = ContainmentConfig(
        ...     blocked_directories=["secrets"],
        ...     readonly_directories=["docs"],
        ... )
        >>> mounts, blocked = containment_config_to_mounts(config, Path("/project"))
        >>> len(mounts)  # workspace + secrets (tmpfs) + docs (ro)
        3
    """
    mounts = []
    blocked = []

    # Base workspace mount (read-write for everything not specifically restricted)
    # Note: We mount the full workspace, then overlay with other mounts
    mounts.append(MountConfig(
        source=str(project_root.resolve()),
        target="/workspace",
        readonly=False
    ))

    # Blocked directories (Tier 1 - overlaid with empty tmpfs)
    # tmpfs mount hides the original directory content
    # Only mount paths that actually exist to avoid creating phantom files
    for dir_path in config.blocked_directories:
        dir_path = dir_path.rstrip("/")
        full_path = project_root / dir_path
        if full_path.exists():
            blocked.append(dir_path)
            mounts.append(MountConfig(
                source="",  # Not used for tmpfs
                target=f"/workspace/{dir_path}",
                readonly=False,  # tmpfs is writable but empty
                mount_type="tmpfs"
            ))

    # Blocked files (Tier 1 - overlaid with /dev/null bind mount)
    # Note: tmpfs can only mount over directories, not files.
    # For files, we bind mount /dev/null to make them inaccessible.
    # Only mount paths that actually exist to avoid creating phantom files
    for file_path in config.blocked_files:
        full_path = project_root / file_path
        if full_path.exists():
            blocked.append(file_path)
            mounts.append(MountConfig(
                source="/dev/null",
                target=f"/workspace/{file_path}",
                readonly=True,
                mount_type="bind"
            ))

    # Readonly directories (Tier 2 - mounted read-only)
    # These overlay the base workspace mount
    for dir_path in config.readonly_directories:
        dir_path = dir_path.rstrip("/")
        full_path = project_root / dir_path
        if full_path.exists():
            mounts.append(MountConfig(
                source=str(full_path.resolve()),
                target=f"/workspace/{dir_path}",
                readonly=True  # OS-enforced read-only!
            ))

    # Readonly files (Tier 2 - mounted read-only)
    for file_path in config.readonly_files:
        full_path = project_root / file_path
        if full_path.exists():
            mounts.append(MountConfig(
                source=str(full_path.resolve()),
                target=f"/workspace/{file_path}",
                readonly=True  # OS-enforced read-only!
            ))

    return mounts, blocked
