"""Interactive Docker sandbox execution.

This module provides functions for running interactive commands in Docker
containers with TTY support, suitable for running Claude Code or other
terminal-based tools.

Functions:
    run_interactive_in_docker: Run interactive command in Docker container
    run_interactive_local: Run interactive command locally

Extracted from runner.py as part of EPIC-005 module decomposition.
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .data_classes import SandboxConfig

logger = logging.getLogger(__name__)


def run_interactive_in_docker(
    workspace: Path,
    config: "SandboxConfig",
    command: list[str],
    get_docker_client_func,
    ensure_image_func,
    build_volumes_func,
    build_environment_func,
    env: Optional[dict[str, str]] = None,
    network_allowlist: Optional[list[str]] = None,
) -> int:
    """Run an interactive command in a Docker container.

    This function runs a command with TTY support for interactive sessions,
    suitable for running Claude Code or other terminal-based tools.

    Args:
        workspace: Path to workspace directory
        config: Sandbox configuration
        command: Command to run as a list (e.g., ["claude", "--flag"])
        get_docker_client_func: Function to get Docker client
        ensure_image_func: Function to ensure containment image exists
        build_volumes_func: Function to build volume configuration
        build_environment_func: Function to build environment dict
        env: Additional environment variables to set
        network_allowlist: List of domains to allow network access to.
                         If None, uses config.network setting.
                         If provided, sets up iptables rules.

    Returns:
        Exit code from the command

    Raises:
        RuntimeError: If Docker is not available
    """
    client = get_docker_client_func()

    # Get or build the containment image
    image_tag = ensure_image_func()

    # Build environment
    container_env = build_environment_func()
    if env:
        container_env.update(env)

    # Add network allowlist to environment if specified
    if network_allowlist:
        container_env["PAIRCODER_NETWORK_ALLOWLIST"] = " ".join(network_allowlist)

    # Build volumes and tmpfs mounts
    volumes, tmpfs_mounts = build_volumes_func()

    # Mount host's Claude credentials so Claude Code can authenticate
    home_dir = Path.home()
    claude_config_dir = home_dir / ".claude"
    if claude_config_dir.exists():
        volumes[str(claude_config_dir)] = {
            "bind": "/home/sandbox/.claude",
            "mode": "rw"
        }

    # Build create kwargs for containers.create()
    create_kwargs = {
        "image": image_tag,
        "volumes": volumes,
        "environment": container_env,
        "working_dir": "/workspace",
        "stdin_open": True,
        "tty": True,
    }

    # Add resource limits
    create_kwargs.update(config.to_docker_kwargs())

    # Determine network mode and command based on allowlist
    if network_allowlist:
        # With allowlist: use keep-alive command, configure iptables, then exec
        create_kwargs["network_mode"] = "bridge"
        create_kwargs["cap_add"] = ["NET_ADMIN"]
        create_kwargs["command"] = ["sleep", "infinity"]
    else:
        # Without allowlist: run user command directly
        create_kwargs["command"] = command

    # Add tmpfs mounts if any (for blocked paths)
    if tmpfs_mounts:
        create_kwargs["tmpfs"] = tmpfs_mounts

    container = None
    try:
        # Create container but DON'T start it yet
        container = client.containers.create(**create_kwargs)

        if network_allowlist:
            # Start container with keep-alive command
            container.start()
            # Configure iptables rules while container is running
            from .network_control import setup_network_allowlist
            setup_network_allowlist(container, network_allowlist)
            # Now exec the actual user command interactively
            import dockerpty
            exit_code = dockerpty.exec_command(client.api, container.id, command)
            return exit_code
        else:
            # Normal case: let dockerpty start AND attach in one operation
            import dockerpty
            dockerpty.start(client.api, container.id)

            # Get exit code after container finishes
            container.reload()
            exit_code = container.attrs.get("State", {}).get("ExitCode", 1)
            return exit_code

    except ImportError:
        # dockerpty not available, fall back to exec_run
        if container:
            exec_result = container.exec_run(
                cmd=command,
                workdir="/workspace",
                tty=True,
                stdin=True,
            )
            return exec_result.exit_code
        return 1

    finally:
        if container:
            try:
                container.stop(timeout=5)
                container.remove(force=True)
            except Exception:
                pass


def run_interactive_local(
    workspace: Path,
    command: list[str],
    env: Optional[dict[str, str]] = None,
) -> int:
    """Run interactive command locally when sandbox is disabled.

    Args:
        workspace: Path to workspace directory
        command: Command to run as a list
        env: Additional environment variables

    Returns:
        Exit code from the command
    """
    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    result = subprocess.run(
        command,
        cwd=str(workspace),
        env=run_env,
    )
    return result.returncode
