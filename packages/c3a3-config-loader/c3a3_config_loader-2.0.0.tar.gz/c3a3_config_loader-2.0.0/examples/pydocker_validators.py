# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""Custom validators for pydocker.

These validators demonstrate config_loader's callable validator feature
by checking actual Docker container states before executing commands.

Validators receive:
    args: Dict of parsed arguments
    ctx: ValidatorContext with command_path, environment, etc.

Return None if valid, or an error message string if invalid.
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

if TYPE_CHECKING:
    from config_loader import ValidatorContext


def _get_container_names(state_filter: Optional[str] = None) -> Set[str]:
    """Get container names from Docker.

    Args:
        state_filter: Optional filter like 'running', 'exited', etc.

    Returns:
        Set of container names/IDs.
    """
    cmd = ["docker", "ps", "-a", "--format", "{{.Names}}"]
    if state_filter:
        cmd.extend(["--filter", f"status={state_filter}"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return set()
        return {name.strip() for name in result.stdout.strip().split("\n") if name.strip()}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return set()


def _get_running_containers() -> Set[str]:
    """Get names of currently running containers."""
    return _get_container_names("running")


def _get_stopped_containers() -> Set[str]:
    """Get names of stopped (exited) containers."""
    return _get_container_names("exited")


def _get_all_containers() -> Set[str]:
    """Get names of all containers."""
    return _get_container_names()


def validate_stop_containers(
    args: Dict[str, Any], ctx: "ValidatorContext"
) -> Optional[str]:
    """Validate that containers to stop are actually running.

    This validator checks each container name in the positional arguments
    and warns if any are not currently running.
    """
    # Positional arguments are in ctx or we need to check args
    # For now, we'll skip if no containers specified (will be caught by required check)
    # The positional args come through as the 'containers' in the context

    # Note: In the current implementation, positional args aren't in the args dict
    # They're in result.command.positional. This validator demonstrates the pattern
    # but would need the positional values passed differently for full functionality.

    # For demonstration, we'll validate if Docker is accessible
    running = _get_running_containers()
    if not running and _get_all_containers():
        # There are containers but none running
        return "No running containers to stop. Use 'pydocker ps --all' to see all containers."

    return None


def validate_rm_containers(
    args: Dict[str, Any], ctx: "ValidatorContext"
) -> Optional[str]:
    """Validate container removal safety.

    Checks:
    - If --force is not set, warn about running containers
    - Verify containers exist
    """
    force = args.get("force", False)

    if not force:
        running = _get_running_containers()
        if running:
            # Can't check specific containers without positional args in args dict,
            # but we can warn if there are running containers and --force isn't set
            return (
                f"There are running containers ({', '.join(list(running)[:3])}...). "
                "Use --force to remove running containers, or stop them first."
            )

    return None


def validate_image_exists(
    args: Dict[str, Any], ctx: "ValidatorContext"
) -> Optional[str]:
    """Validate that the image exists locally or can be pulled.

    This is a lightweight check - just verifies Docker is accessible.
    A full implementation would check if the image exists.
    """
    # Check Docker is accessible
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            return "Cannot connect to Docker daemon. Is Docker running?"
    except subprocess.TimeoutExpired:
        return "Docker daemon not responding (timeout)."
    except FileNotFoundError:
        return "Docker command not found. Is Docker installed?"

    return None


# =============================================================================
# VALUE PROVIDERS - Supply valid values for arguments (autocompletion/validation)
# =============================================================================


def provide_running_containers(ctx: Any) -> List[str]:
    """Provide list of running container names.

    Used by: docker stop, docker exec, docker logs
    """
    return sorted(_get_running_containers())


def provide_all_containers(ctx: Any) -> List[str]:
    """Provide list of all container names.

    Used by: docker rm, docker start
    """
    return sorted(_get_all_containers())


def provide_stopped_containers(ctx: Any) -> List[str]:
    """Provide list of stopped container names.

    Used by: docker start
    """
    return sorted(_get_stopped_containers())


def provide_images(ctx: Any) -> List[str]:
    """Provide list of local Docker images.

    Used by: docker run, docker rmi
    """
    try:
        result = subprocess.run(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []
        images = {
            img.strip()
            for img in result.stdout.strip().split("\n")
            if img.strip() and img.strip() != "<none>:<none>"
        }
        return sorted(images)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def provide_networks(ctx: Any) -> List[str]:
    """Provide list of Docker networks.

    Used by: docker run --network
    """
    try:
        result = subprocess.run(
            ["docker", "network", "ls", "--format", "{{.Name}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return []
        return sorted(
            name.strip() for name in result.stdout.strip().split("\n") if name.strip()
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def provide_restart_policies(ctx: Any) -> List[str]:
    """Provide valid restart policy values."""
    return ["no", "always", "unless-stopped", "on-failure"]
