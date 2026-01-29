#!/usr/bin/env python3
# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""pydocker - Docker CLI wrapper demonstrating config_loader v2.0 features.

This example wraps common Docker container lifecycle commands to showcase:

    LIBRARY FEATURES DEMONSTRATED
    =============================
    1. Hierarchical commands      - run, stop, rm, ps as terminal commands
    2. Exclusion groups           - --detach vs --interactive (mutually exclusive)
    3. Dependency rules           - --interactive requires --tty
    4. Variadic arguments         - --env, --port accept multiple values
    5. Positional arguments       - image name, container IDs
    6. Short flags                - -d, -i, -t, -p, -e, -v
    7. Environment variables      - DOCKER_HOST for --host
    8. Deprecation warnings       - --link shows deprecation message
    9. Error recovery             - "Did you mean?" suggestions for typos
    10. YAML configuration        - Spec loaded from pydocker.yaml

    TRY THESE EXAMPLES
    ==================
    # Basic usage
    python pydocker.py run --detach --name web -p 8080:80 nginx
    python pydocker.py run -it ubuntu bash
    python pydocker.py stop web
    python pydocker.py rm --force web
    python pydocker.py ps --all

    # Exclusion group error (--detach and --interactive conflict)
    python pydocker.py run --detach --interactive nginx

    # Dependency rule error (--interactive requires --tty)
    python pydocker.py run --interactive nginx

    # Deprecation warning
    python pydocker.py run --link db:db nginx

    # Error recovery / typo suggestions
    python pydocker.py rn nginx          # Did you mean 'run'?
    python pydocker.py run --detatch nginx  # Did you mean '--detach'?

    # Help
    python pydocker.py --help
    python pydocker.py run --help

Requirements: Docker must be installed for commands to execute.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from config_loader import Configuration, ProcessingResult

# Directory containing this script and its config files
EXAMPLES_DIR = Path(__file__).parent


def _setup_validator_imports() -> None:
    """Add examples directory to path so validators module can be imported."""
    if str(EXAMPLES_DIR) not in sys.path:
        sys.path.insert(0, str(EXAMPLES_DIR))


def load_spec() -> dict[str, Any]:
    """Load the configuration spec from pydocker.yaml."""
    # Ensure validators are importable before loading spec
    _setup_validator_imports()

    spec_path = EXAMPLES_DIR / "pydocker.yaml"
    with open(spec_path) as f:
        return yaml.safe_load(f)


# =============================================================================
# COMMAND BUILDER - Converts ProcessingResult to Docker CLI arguments
# =============================================================================


def build_docker_command(result: ProcessingResult) -> list[str]:
    """Convert a ProcessingResult into a Docker command array.

    This maps config_loader argument names back to Docker's flag format.
    """
    if result.command is None:
        return ["docker", "--help"]

    cmd = ["docker"] + result.command.path
    args = result.command.arguments
    positional = result.command.positional

    # Add global host option if specified
    if result.config.docker.host:
        cmd.insert(1, f"--host={result.config.docker.host}")

    # Map arguments to Docker flags based on command
    command_name = result.command.path[0] if result.command.path else ""

    if command_name == "run":
        cmd.extend(_build_run_args(args))
    elif command_name == "stop":
        cmd.extend(_build_stop_args(args))
    elif command_name == "rm":
        cmd.extend(_build_rm_args(args))
    elif command_name == "ps":
        cmd.extend(_build_ps_args(args))

    # Add positional arguments
    cmd.extend(positional)

    return cmd


def _ensure_list(value: Any) -> list[Any]:
    """Ensure a value is a list (handles single values from nargs='*')."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _build_run_args(args: dict[str, Any]) -> list[str]:
    """Build Docker run arguments."""
    result: list[str] = []

    # Boolean flags
    if args.get("detach"):
        result.append("--detach")
    if args.get("interactive"):
        result.append("--interactive")
    if args.get("tty"):
        result.append("--tty")
    if args.get("rm"):
        result.append("--rm")

    # String options
    if args.get("name"):
        result.extend(["--name", args["name"]])
    if args.get("network"):
        result.extend(["--network", args["network"]])
    if args.get("workdir"):
        result.extend(["--workdir", args["workdir"]])
    if args.get("user"):
        result.extend(["--user", args["user"]])
    if args.get("restart"):
        result.extend(["--restart", args["restart"]])

    # Variadic options (can be specified multiple times)
    # Note: nargs="*" may return a string if only one value provided
    for env_var in _ensure_list(args.get("env")):
        result.extend(["--env", env_var])
    for port in _ensure_list(args.get("port")):
        result.extend(["--publish", port])
    for volume in _ensure_list(args.get("volume")):
        result.extend(["--volume", volume])
    for link in _ensure_list(args.get("link")):
        result.extend(["--link", link])

    return result


def _build_stop_args(args: dict[str, Any]) -> list[str]:
    """Build Docker stop arguments."""
    result: list[str] = []

    if args.get("time") is not None:
        result.extend(["--time", str(int(args["time"]))])
    if args.get("signal"):
        result.extend(["--signal", args["signal"]])

    return result


def _build_rm_args(args: dict[str, Any]) -> list[str]:
    """Build Docker rm arguments."""
    result: list[str] = []

    if args.get("force"):
        result.append("--force")
    if args.get("volumes"):
        result.append("--volumes")

    return result


def _build_ps_args(args: dict[str, Any]) -> list[str]:
    """Build Docker ps arguments."""
    result: list[str] = []

    if args.get("all"):
        result.append("--all")
    if args.get("quiet"):
        result.append("--quiet")
    if args.get("size"):
        result.append("--size")
    if args.get("format"):
        result.extend(["--format", args["format"]])
    if args.get("last") is not None:
        result.extend(["--last", str(int(args["last"]))])

    for f in args.get("filter") or []:
        result.extend(["--filter", f])

    return result


# =============================================================================
# MAIN - Parse arguments and execute Docker
# =============================================================================


def main() -> int:
    """Main entry point."""
    spec = load_spec()
    cfg = Configuration(spec)

    try:
        result = cfg.process(sys.argv[1:])
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Print any warnings (e.g., deprecation warnings are also shown to stderr)
    for warning in result.warnings:
        print(f"Warning: {warning}", file=sys.stderr)

    # Build and execute the Docker command
    docker_cmd = build_docker_command(result)

    # Show what we're executing (for demonstration)
    print(f"Executing: {' '.join(docker_cmd)}", file=sys.stderr)

    # Execute Docker
    try:
        proc = subprocess.run(docker_cmd)
        return proc.returncode
    except FileNotFoundError:
        print("Error: 'docker' command not found. Is Docker installed?", file=sys.stderr)
        return 127


if __name__ == "__main__":
    sys.exit(main())
