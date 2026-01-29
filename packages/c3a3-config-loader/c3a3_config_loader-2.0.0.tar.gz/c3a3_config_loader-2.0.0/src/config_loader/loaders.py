# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""
Configuration Loader - Source Loaders

Handles loading configuration from different sources:
- Command line arguments
- Environment variables
- RC files (TOML format)
- Command argument environment variables (v2.0)
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import tomllib

from .models import CommandArgument, ConfigParam

if TYPE_CHECKING:
    from .main import Configuration



class ArgumentLoader:
    """Loads configuration from command line arguments."""

    def __init__(self, config: "Configuration") -> None:
        self.config = config

    def load(self, args: List[str]) -> Dict[str, Any]:
        """Load configuration from command line arguments."""
        parser = argparse.ArgumentParser(add_help=False)

        # Add configuration parameters
        for param in self.config.parameters:
            arg_name = f"--{self._get_arg_name(param)}"
            parser.add_argument(
                arg_name, dest=f"param_{param.namespace or 'default'}_{param.name}"
            )

        # Add positional arguments
        for arg in self.config.arguments:
            if arg.required:
                parser.add_argument(arg.name)
            else:
                parser.add_argument(arg.name, nargs="?", default=arg.default)

        # Add debug flag
        parser.add_argument("--debug", action="store_true")

        parsed, _ = parser.parse_known_args(args)
        return vars(parsed)

    def _get_arg_name(self, param: ConfigParam) -> str:
        """Get command line argument name."""
        if param.namespace:
            return f"{param.namespace}.{param.name}"
        return param.name


class EnvironmentLoader:
    """Loads configuration from environment variables."""

    def __init__(self, config: "Configuration") -> None:
        self.config = config

    def load(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config: Dict[str, Dict[str, Any]] = {}
        for param in self.config.parameters:
            env_name = self._get_env_name(param)
            if env_name in os.environ:
                namespace = param.namespace or "default"
                if namespace not in config:
                    config[namespace] = {}
                config[namespace][param.name] = os.environ[env_name]
        return config

    def _get_env_name(self, param: ConfigParam) -> str:
        """Get environment variable name."""
        app = self.config.app_name.upper().replace("-", "_")
        namespace = (
            param.namespace.upper().replace("-", "_") if param.namespace else None
        )
        name = param.name.upper().replace("-", "_")

        if namespace:
            return f"{app}_{namespace}_{name}"
        return f"{app}_{name}"


class RCLoader:
    """Loads configuration from RC files."""

    def __init__(self, config: "Configuration") -> None:
        self.config = config

    def load(self) -> Dict[str, Any]:
        """Load configuration from RC file."""
        rc_file = Path.home() / f".{self.config.app_name.lower()}rc"
        if not rc_file.exists():
            return {}

        try:
            with open(rc_file, "rb") as f:
                data = tomllib.load(f)
            if not isinstance(data, dict):
                return {}
            return dict(data)
        except Exception as e:
            print(f"Warning: Could not load RC file {rc_file}: {e}")
            return {}


# ============================================================================
# v2.0 Command Argument Environment Loader
# ============================================================================


class CommandArgumentEnvLoader:
    """Loads command argument values from environment variables.

    For command arguments with `env: true` or `env_name` set, this loader
    retrieves values from environment variables.

    Environment variable naming:
    - `env: true`: Auto-generate name as {APP}_{COMMAND_PATH}_{ARG}
    - `env_name: "CUSTOM"`: Use the specified name

    For inherited arguments, the environment variable name uses the
    *defining* command's path, not the executing command's path.
    This allows a single env var to apply across all child commands.
    """

    def __init__(self, config: "Configuration") -> None:
        self.config = config
        self.app_name = config.app_name.upper().replace("-", "_")

    def load_argument_value(
        self,
        arg: CommandArgument,
        defining_path: List[str],
    ) -> Optional[str]:
        """Load a single argument value from environment.

        Args:
            arg: The command argument definition.
            defining_path: The command path where this argument is defined
                          (for inherited args, this is the parent path).

        Returns:
            The environment variable value if set, None otherwise.
        """
        if not arg.env and not arg.env_name:
            return None

        env_name = self._get_env_name(arg, defining_path)
        return os.environ.get(env_name)

    def load_all_argument_values(
        self,
        arguments: Dict[str, CommandArgument],
        defining_paths: Dict[str, List[str]],
    ) -> Dict[str, str]:
        """Load all argument values from environment.

        Args:
            arguments: Map of argument name to definition.
            defining_paths: Map of argument name to defining command path.

        Returns:
            Dict of argument name to value (only for env-enabled args with values).
        """
        result: Dict[str, str] = {}

        for name, arg in arguments.items():
            defining_path = defining_paths.get(name, [])
            value = self.load_argument_value(arg, defining_path)
            if value is not None:
                result[name] = value

        return result

    def _get_env_name(
        self,
        arg: CommandArgument,
        defining_path: List[str],
    ) -> str:
        """Get the environment variable name for an argument.

        Args:
            arg: The command argument definition.
            defining_path: The command path where this argument is defined.

        Returns:
            The environment variable name.
        """
        # Use explicit env_name if provided
        if arg.env_name:
            return arg.env_name

        # Auto-generate: {APP}_{COMMAND_PATH}_{ARG}
        parts = [self.app_name]

        # Add command path components
        for cmd in defining_path:
            parts.append(cmd.upper().replace("-", "_"))

        # Add argument name
        parts.append(arg.name.upper().replace("-", "_"))

        return "_".join(parts)

    def get_env_name_for_help(
        self,
        arg: CommandArgument,
        defining_path: List[str],
    ) -> Optional[str]:
        """Get the environment variable name for display in help.

        Returns None if the argument doesn't support env vars.
        """
        if not arg.env and not arg.env_name:
            return None
        return self._get_env_name(arg, defining_path)


def parse_variadic_args(
    values: List[str],
    nargs: Optional[str],
    arg_name: str,
) -> List[Any]:
    """Parse variadic positional argument values.

    Args:
        values: The input values to parse.
        nargs: The nargs specification ('?', '*', '+', or int as string).
        arg_name: The argument name for error messages.

    Returns:
        List of parsed values.

    Raises:
        ValueError: If the number of values doesn't match nargs.
    """
    if nargs is None:
        # Default: exactly one value
        if len(values) != 1:
            raise ValueError(f"Argument '{arg_name}' expects exactly 1 value")
        return values

    if nargs == "?":
        # Zero or one
        if len(values) > 1:
            raise ValueError(f"Argument '{arg_name}' expects at most 1 value")
        return values

    if nargs == "*":
        # Zero or more - any count is valid
        return values

    if nargs == "+":
        # One or more
        if len(values) < 1:
            raise ValueError(f"Argument '{arg_name}' requires at least 1 value")
        return values

    # Try parsing as integer
    try:
        count = int(nargs)
        if len(values) != count:
            raise ValueError(
                f"Argument '{arg_name}' expects exactly {count} values, got {len(values)}"
            )
        return values
    except ValueError:
        raise ValueError(f"Invalid nargs value '{nargs}' for argument '{arg_name}'")
