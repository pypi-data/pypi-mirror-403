"""
Sandbox data structures for Docker container execution.

This module contains the core data classes used by the sandbox system:
- MountConfig: Configuration for volume mounts
- FileChange: Represents a file change in the sandbox
- SandboxResult: Result of running a command in the sandbox
- SandboxConfig: Configuration for the Docker sandbox

Extracted from sandbox.py as part of EPIC-005 module decomposition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml


@dataclass
class MountConfig:
    """Configuration for a volume mount.

    Attributes:
        source: Host path to mount (ignored for tmpfs mounts)
        target: Container path to mount to
        readonly: Whether mount is read-only
        mount_type: Type of mount - "bind" (default) or "tmpfs"
    """

    source: str
    target: str
    readonly: bool = False
    mount_type: str = "bind"  # "bind" or "tmpfs"

    def to_docker_mount(self) -> dict[str, str]:
        """Convert to Docker mount configuration dict for bind mounts.

        Returns:
            Dictionary with 'bind' and 'mode' keys for Docker volumes
        """
        return {
            "bind": self.target,
            "mode": "ro" if self.readonly else "rw"
        }

    def is_tmpfs(self) -> bool:
        """Check if this is a tmpfs mount.

        Returns:
            True if mount_type is "tmpfs"
        """
        return self.mount_type == "tmpfs"


@dataclass
class FileChange:
    """Represents a file change in the sandbox.

    Attributes:
        path: Path to the changed file (relative to workspace)
        action: Type of change (created, modified, deleted)
    """

    path: str
    action: Literal["created", "modified", "deleted"]


@dataclass
class SandboxResult:
    """Result of running a command in the sandbox.

    Attributes:
        exit_code: Command exit code
        stdout: Standard output
        stderr: Standard error
        changes: List of file changes detected
    """

    exit_code: int
    stdout: str
    stderr: str
    changes: list[FileChange] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if command succeeded (exit code 0).

        Returns:
            True if exit_code is 0
        """
        return self.exit_code == 0

    @property
    def has_changes(self) -> bool:
        """Check if any file changes were detected.

        Returns:
            True if changes list is non-empty
        """
        return len(self.changes) > 0


@dataclass
class SandboxConfig:
    """Configuration for the Docker sandbox.

    Attributes:
        enabled: Whether sandbox is enabled
        image: Docker image to use
        memory_limit: Memory limit (e.g., "2g")
        cpu_limit: CPU limit (number of CPUs)
        network: Network mode (none, bridge, host)
        mounts: List of volume mounts
        env_passthrough: Environment variables to pass through
    """

    enabled: bool = True
    image: str = "paircoder/sandbox:latest"
    memory_limit: str = "2g"
    cpu_limit: float = 2.0
    network: str = "none"
    mounts: list[MountConfig] = field(default_factory=list)
    env_passthrough: list[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> "SandboxConfig":
        """Load configuration from YAML file.

        Args:
            path: Path to YAML config file

        Returns:
            SandboxConfig instance
        """
        with open(path, encoding='utf-8') as f:
            data = yaml.safe_load(f)

        sandbox_data = data.get("sandbox", {})

        mounts = []
        for mount_data in sandbox_data.get("mounts", []):
            mounts.append(MountConfig(
                source=mount_data.get("source", ""),
                target=mount_data.get("target", ""),
                readonly=mount_data.get("readonly", False)
            ))

        return cls(
            enabled=sandbox_data.get("enabled", True),
            image=sandbox_data.get("image", cls.image),
            memory_limit=sandbox_data.get("memory_limit", cls.memory_limit),
            cpu_limit=sandbox_data.get("cpu_limit", cls.cpu_limit),
            network=sandbox_data.get("network", cls.network),
            mounts=mounts,
            env_passthrough=sandbox_data.get("env_passthrough", [])
        )

    def to_docker_kwargs(self) -> dict[str, Any]:
        """Convert config to Docker run kwargs.

        Returns:
            Dict of kwargs for docker.containers.run()
        """
        return {
            "mem_limit": self.memory_limit,
            "nano_cpus": int(self.cpu_limit * 1e9),
            "network_mode": self.network,
        }


# Docker diff kind values
DIFF_MODIFIED = 0
DIFF_CREATED = 1
DIFF_DELETED = 2

DIFF_KIND_TO_ACTION = {
    DIFF_MODIFIED: "modified",
    DIFF_CREATED: "created",
    DIFF_DELETED: "deleted",
}
