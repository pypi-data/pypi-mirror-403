"""Docker containment image management.

This module provides functions for managing the Docker containment image
used by the sandbox runner.

Functions:
    ensure_containment_image: Ensure containment image is available

Extracted from runner.py as part of EPIC-005 module decomposition.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from importlib.metadata import version as get_version

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

CONTAINMENT_IMAGE_REPO = "bpsai/paircoder-containment"


def ensure_containment_image(get_docker_client_func) -> str:
    """Ensure containment image is available.

    Attempts to:
    1. Use existing local image (fastest)
    2. Pull from Docker Hub (fast for most users)
    3. Build locally from Dockerfile (fallback for offline)

    Args:
        get_docker_client_func: Function that returns Docker client

    Returns:
        Image tag string to use for container creation

    Raises:
        RuntimeError: If image cannot be obtained by any method

    Example:
        >>> def get_client():
        ...     import docker
        ...     return docker.from_env()
        >>> image_tag = ensure_containment_image(get_client)
        >>> print(image_tag)  # e.g., "bpsai/paircoder-containment:2.9.6"
    """
    from rich.console import Console

    console = Console()

    try:
        pkg_version = get_version("bpsai-pair")
    except Exception:
        pkg_version = "latest"

    # Image tags to try (in order of preference)
    image_tags = [
        f"{CONTAINMENT_IMAGE_REPO}:{pkg_version}",  # Versioned
        f"{CONTAINMENT_IMAGE_REPO}:latest",  # Latest
        "paircoder/containment:latest",  # Legacy local name
    ]

    # Check if any image already exists locally
    for tag in image_tags:
        try:
            get_docker_client_func().images.get(tag)
            return tag
        except Exception:
            continue

    # Try to pull from Docker Hub
    console.print(f"[cyan]Pulling containment image ({CONTAINMENT_IMAGE_REPO}:{pkg_version})...[/cyan]")
    try:
        get_docker_client_func().images.pull(CONTAINMENT_IMAGE_REPO, tag=pkg_version)
        return f"{CONTAINMENT_IMAGE_REPO}:{pkg_version}"
    except Exception as pull_error:
        console.print(f"[yellow]Pull failed: {pull_error}[/yellow]")

    # Try pulling latest as fallback
    try:
        console.print("[cyan]Trying latest tag...[/cyan]")
        get_docker_client_func().images.pull(CONTAINMENT_IMAGE_REPO, tag="latest")
        return f"{CONTAINMENT_IMAGE_REPO}:latest"
    except Exception:
        pass

    # Fall back to local build
    console.print("[yellow]Building containment image locally (this may take a few minutes)...[/yellow]")
    try:
        dockerfile_path = Path(__file__).parent / "Dockerfile.containment"
        if not dockerfile_path.exists():
            raise FileNotFoundError(f"Dockerfile not found at {dockerfile_path}")

        image, logs = get_docker_client_func().images.build(
            path=str(dockerfile_path.parent),
            dockerfile="Dockerfile.containment",
            tag="paircoder/containment:latest",
            rm=True,  # Remove intermediate containers
        )
        console.print("[green]✓ Containment image built successfully[/green]")
        return "paircoder/containment:latest"
    except Exception as build_error:
        raise RuntimeError(
            f"Failed to obtain containment image.\n"
            f"Pull failed and local build failed: {build_error}\n"
            f"Ensure Docker is running and try: docker pull {CONTAINMENT_IMAGE_REPO}:latest"
        )
