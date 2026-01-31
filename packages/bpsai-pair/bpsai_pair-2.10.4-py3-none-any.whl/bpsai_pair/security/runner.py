"""
Docker sandbox runner for isolated command execution.

This module provides the SandboxRunner class that executes commands
in isolated Docker containers with resource limits and network control.

Classes:
    SandboxRunner: Execute commands in isolated Docker containers

Extracted from sandbox.py as part of EPIC-005 module decomposition.
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

from .data_classes import (
    FileChange,
    MountConfig,
    SandboxConfig,
    SandboxResult,
    DIFF_KIND_TO_ACTION,
)
from .image_manager import ensure_containment_image as _ensure_image, CONTAINMENT_IMAGE_REPO

logger = logging.getLogger(__name__)

try:
    import docker
except ImportError:
    docker = None


class SandboxRunner:
    """Runs commands in isolated Docker containers.

    Provides secure command execution with:
    - Network isolation (disabled by default)
    - Resource limits (memory, CPU)
    - File change tracking
    - Cleanup on completion

    Attributes:
        workspace: Path to workspace directory
        config: Sandbox configuration
    """

    def __init__(
        self,
        workspace: Path,
        config: Optional[SandboxConfig] = None
    ):
        """Initialize the sandbox runner.

        Args:
            workspace: Path to workspace directory to mount
            config: Sandbox configuration (uses default if None)
        """
        self.workspace = workspace
        self.config = config or SandboxConfig()
        self._current_container = None

    @staticmethod
    def is_docker_available() -> bool:
        """Check if Docker is available.

        Returns:
            True if Docker is available and running
        """
        if docker is None:
            return False

        try:
            client = docker.from_env()
            client.ping()
            return True
        except Exception:
            return False

    def _get_docker_client(self):
        """Get Docker client, raising error if not available."""
        if docker is None:
            raise RuntimeError("Docker Python SDK not installed. Install with: pip install docker")

        try:
            return docker.from_env()
        except Exception as e:
            raise RuntimeError(f"Docker not available: {e}")

    def ensure_containment_image(self) -> str:
        """Ensure containment image is available.

        Delegates to image_manager.ensure_containment_image().

        Returns:
            Image tag string to use for container creation

        Raises:
            RuntimeError: If image cannot be obtained by any method
        """
        return _ensure_image(self._get_docker_client)

    def _build_volumes(self) -> tuple[dict, dict]:
        """Build volumes and tmpfs dicts for Docker run.

        Returns:
            Tuple of (volumes, tmpfs):
            - volumes: Dict of bind mounts {source: {bind: target, mode: ro/rw}}
            - tmpfs: Dict of tmpfs mounts {target: "size=1m"}
        """
        volumes = {
            str(self.workspace): {
                "bind": "/workspace",
                "mode": "rw"
            }
        }
        tmpfs_mounts = {}

        for mount in self.config.mounts:
            if mount.is_tmpfs():
                # tmpfs mount - hide the original content with empty filesystem
                tmpfs_mounts[mount.target] = "size=1m"
            else:
                # Regular bind mount
                volumes[mount.source] = mount.to_docker_mount()

        return volumes, tmpfs_mounts

    def _build_environment(self) -> dict[str, str]:
        """Build environment dict from passthrough config.

        Returns:
            Dictionary of environment variables to set in container
        """
        env = {}
        for var_name in self.config.env_passthrough:
            value = os.environ.get(var_name)
            if value is not None:
                env[var_name] = value
        return env

    def _parse_diff(self, diff_output: list) -> list[FileChange]:
        """Parse Docker diff output to FileChange list.

        Args:
            diff_output: List of diff entries from container.diff()

        Returns:
            List of FileChange objects
        """
        changes = []
        workspace_prefix = "/workspace"

        for entry in diff_output:
            path = entry.get("Path", "")
            kind = entry.get("Kind", 0)

            # Only track changes in workspace
            if path.startswith(workspace_prefix):
                relative_path = path[len(workspace_prefix):].lstrip("/")
                action = DIFF_KIND_TO_ACTION.get(kind, "modified")
                changes.append(FileChange(path=relative_path, action=action))

        return changes

    def run_command(self, command: str) -> SandboxResult:
        """Run a command in the sandbox.

        Args:
            command: Command string to execute

        Returns:
            SandboxResult with exit code, output, and file changes

        Raises:
            RuntimeError: If Docker is not available
        """
        if not self.config.enabled:
            return self._run_local(command)

        client = self._get_docker_client()

        # Build volumes and tmpfs mounts
        volumes, tmpfs_mounts = self._build_volumes()

        # Build Docker run kwargs
        run_kwargs = self.config.to_docker_kwargs()
        run_kwargs.update({
            "image": self.config.image,
            "command": "sleep infinity",  # Keep container running
            "volumes": volumes,
            "environment": self._build_environment(),
            "working_dir": "/workspace",
            "detach": True,
            "remove": False,  # We'll remove manually after getting diff
        })

        # Add tmpfs mounts if any (for blocked paths)
        if tmpfs_mounts:
            run_kwargs["tmpfs"] = tmpfs_mounts

        container = None
        try:
            # Create and start container
            container = client.containers.run(**run_kwargs)
            self._current_container = container

            # Execute command in container
            exec_result = container.exec_run(
                cmd=["sh", "-c", command],
                workdir="/workspace"
            )

            # Get file changes before removing container
            try:
                diff = container.diff() or []
            except Exception:
                diff = []

            changes = self._parse_diff(diff)

            # Decode output
            stdout = exec_result.output.decode("utf-8", errors="replace") if exec_result.output else ""

            return SandboxResult(
                exit_code=exec_result.exit_code,
                stdout=stdout,
                stderr="",  # Docker exec_run combines stdout/stderr
                changes=changes
            )

        finally:
            # Always cleanup container
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            self._current_container = None

    def _run_local(self, command: str) -> SandboxResult:
        """Run command locally when sandbox is disabled.

        Args:
            command: Command to execute

        Returns:
            SandboxResult with exit code and output
        """
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(self.workspace),
            capture_output=True,
            text=True
        )

        return SandboxResult(
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            changes=[]  # No change tracking in local mode
        )

    def apply_changes(self, result: SandboxResult) -> None:
        """Apply changes from sandbox to host filesystem.

        Args:
            result: SandboxResult containing changes to apply

        Note:
            When using bind mounts (default), changes are already
            applied to the host filesystem. This method is for
            copy-based workflows.
        """
        # With bind mounts, changes are already on the host
        # This method exists for future copy-based sandbox modes
        pass

    def discard_changes(self, result: SandboxResult) -> None:
        """Discard changes from sandbox.

        Args:
            result: SandboxResult containing changes to discard

        Note:
            Container is already removed in run_command().
            With bind mounts, changes cannot be discarded after execution.
            This method is for future copy-based sandbox modes.
        """
        # Container already removed in run_command()
        # With bind mounts, changes are already on the host
        pass

    def run_interactive(
        self,
        command: list[str],
        env: Optional[dict[str, str]] = None,
        network_allowlist: Optional[list[str]] = None
    ) -> int:
        """Run an interactive command in the sandbox container.

        Delegates to interactive_runner module for the actual execution.

        Args:
            command: Command to run as a list (e.g., ["claude", "--flag"])
            env: Additional environment variables to set
            network_allowlist: List of domains to allow network access to.

        Returns:
            Exit code from the command

        Raises:
            RuntimeError: If Docker is not available
        """
        from .interactive_runner import run_interactive_in_docker, run_interactive_local

        if not self.config.enabled:
            return run_interactive_local(self.workspace, command, env)

        return run_interactive_in_docker(
            workspace=self.workspace,
            config=self.config,
            command=command,
            get_docker_client_func=self._get_docker_client,
            ensure_image_func=self.ensure_containment_image,
            build_volumes_func=self._build_volumes,
            build_environment_func=self._build_environment,
            env=env,
            network_allowlist=network_allowlist,
        )
