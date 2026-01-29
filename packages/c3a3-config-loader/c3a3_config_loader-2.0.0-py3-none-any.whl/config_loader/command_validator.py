# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""
Configuration Loader - Command Validator

Validates command tree specifications for correctness and consistency.
"""

from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING, Dict, List, Set, Tuple

from .models import Command

if TYPE_CHECKING:
    from .main import Configuration


class CommandValidationError(ValueError):
    """Raised when command validation fails."""

    pass


class CommandValidator:
    """Validates command tree specifications.

    Performs comprehensive validation of the command tree including:
    - Command name format (no dots, alphanumeric + dash/underscore)
    - Alias uniqueness within each command level
    - No command argument shadows parameter namespace
    - Exclusion group references valid arguments
    - Dependency rules reference valid arguments
    - Short flag collision detection (warnings)
    - Deprecated structure validation
    """

    # Valid name pattern: lowercase alphanumeric, dash, underscore
    NAME_PATTERN = re.compile(r"^[a-z0-9_-]+$")

    def __init__(self, config: "Configuration") -> None:
        self.config = config
        self._errors: List[str] = []
        self._warnings: List[str] = []

    def validate_commands(self) -> None:
        """Validate the entire command tree.

        Raises:
            CommandValidationError: If validation fails.
        """
        self._errors = []
        self._warnings = []

        commands = getattr(self.config, "commands", [])
        if not commands:
            return

        # Collect parameter namespaces for conflict checking
        param_namespaces = self._collect_param_namespaces()

        # Validate the command tree recursively
        self._validate_command_level(commands, [], param_namespaces)

        # Emit warnings to stderr
        for warning in self._warnings:
            print(f"Warning: {warning}", file=sys.stderr)

        # Raise if there are errors
        if self._errors:
            raise CommandValidationError(
                "Command specification errors:\n" + "\n".join(f"  - {e}" for e in self._errors)
            )

    def _collect_param_namespaces(self) -> Set[str]:
        """Collect all parameter namespaces from the spec."""
        namespaces: Set[str] = set()
        for param in self.config.parameters:
            if param.namespace:
                namespaces.add(param.namespace)
        return namespaces

    def _validate_command_level(
        self,
        commands: List[Command],
        path: List[str],
        param_namespaces: Set[str],
    ) -> None:
        """Validate a level of commands (siblings)."""
        # Track names and aliases at this level for uniqueness
        seen_names: Dict[str, str] = {}  # name/alias -> primary command name
        seen_short_flags: Dict[str, Tuple[str, str]] = {}  # short -> (command, arg)

        for cmd in commands:
            cmd_path = path + [cmd.name]
            path_str = " -> ".join(cmd_path) if cmd_path else "(root)"

            # Validate command name format
            self._validate_name(cmd.name, f"Command '{path_str}'")

            # Check for duplicate command name at this level
            if cmd.name in seen_names:
                self._errors.append(
                    f"Duplicate command name '{cmd.name}' at level: {path_str}"
                )
            else:
                seen_names[cmd.name] = cmd.name

            # Validate and check aliases
            for alias in cmd.aliases:
                self._validate_name(alias, f"Alias '{alias}' for command '{path_str}'")

                if alias in seen_names:
                    self._errors.append(
                        f"Alias '{alias}' for '{cmd.name}' conflicts with "
                        f"'{seen_names[alias]}' at level: {path_str}"
                    )
                else:
                    seen_names[alias] = cmd.name

            # Validate ordering value
            if cmd.ordering not in ("strict", "relaxed", "interleaved"):
                self._errors.append(
                    f"Invalid ordering '{cmd.ordering}' for command '{path_str}'. "
                    f"Must be 'strict', 'relaxed', or 'interleaved'."
                )

            # Validate command arguments
            self._validate_command_arguments(
                cmd, cmd_path, param_namespaces, seen_short_flags
            )

            # Validate exclusion groups
            self._validate_exclusion_groups(cmd, cmd_path)

            # Validate dependency rules
            self._validate_dependency_rules(cmd, cmd_path)

            # Validate validators
            self._validate_validators(cmd, cmd_path)

            # Validate deprecation structure
            if cmd.deprecated:
                self._validate_deprecation(cmd.deprecated, f"Command '{path_str}'")

            # Recursively validate subcommands
            if cmd.subcommands:
                self._validate_command_level(cmd.subcommands, cmd_path, param_namespaces)

    def _validate_name(self, name: str, context: str) -> None:
        """Validate a command or alias name format."""
        if not self.NAME_PATTERN.match(name):
            self._errors.append(
                f"{context}: Invalid name '{name}'. "
                f"Must be lowercase alphanumeric with dashes or underscores."
            )

        if "." in name:
            self._errors.append(
                f"{context}: Name '{name}' contains a dot. "
                f"Dots are reserved for parameter namespacing."
            )

    def _validate_command_arguments(
        self,
        cmd: Command,
        path: List[str],
        param_namespaces: Set[str],
        seen_short_flags: Dict[str, Tuple[str, str]],
    ) -> None:
        """Validate arguments for a command."""
        path_str = " -> ".join(path)
        seen_args: Set[str] = set()

        for arg in cmd.arguments:
            # Validate argument name format
            self._validate_name(arg.name, f"Argument '--{arg.name}' in '{path_str}'")

            # Check for duplicate argument names in this command
            if arg.name in seen_args:
                self._errors.append(
                    f"Duplicate argument '--{arg.name}' in command '{path_str}'"
                )
            seen_args.add(arg.name)

            # Check if argument name shadows a parameter namespace
            for ns in param_namespaces:
                if arg.name.startswith(f"{ns}.") or arg.name == ns:
                    self._errors.append(
                        f"Argument '--{arg.name}' in '{path_str}' conflicts with "
                        f"parameter namespace '{ns}'"
                    )

            # Validate argument type
            if arg.type not in ("string", "number", "boolean"):
                self._errors.append(
                    f"Invalid type '{arg.type}' for argument '--{arg.name}' in '{path_str}'. "
                    f"Must be 'string', 'number', or 'boolean'."
                )

            # Validate scope
            if arg.scope not in ("local", "inherited", "ephemeral"):
                self._errors.append(
                    f"Invalid scope '{arg.scope}' for argument '--{arg.name}' in '{path_str}'. "
                    f"Must be 'local', 'inherited', or 'ephemeral'."
                )

            # Validate short flag format and check for collisions
            if arg.short:
                if not re.match(r"^[a-zA-Z]$", arg.short):
                    self._errors.append(
                        f"Invalid short flag '-{arg.short}' for '--{arg.name}' in '{path_str}'. "
                        f"Must be a single letter."
                    )
                else:
                    # Check for short flag collision at this command level
                    if arg.short in seen_short_flags:
                        prev_cmd, prev_arg = seen_short_flags[arg.short]
                        self._warnings.append(
                            f"Short flag '-{arg.short}' for '--{arg.name}' in '{path_str}' "
                            f"shadows '-{arg.short}' for '--{prev_arg}' in '{prev_cmd}'"
                        )
                    seen_short_flags[arg.short] = (path_str, arg.name)

            # Validate nargs
            if arg.nargs is not None:
                valid_nargs = ("?", "*", "+")
                if isinstance(arg.nargs, str) and arg.nargs not in valid_nargs:
                    self._errors.append(
                        f"Invalid nargs '{arg.nargs}' for '--{arg.name}' in '{path_str}'. "
                        f"Must be '?', '*', '+', or a positive integer."
                    )

            # Validate required + default conflict
            if arg.required and arg.default is not None:
                self._errors.append(
                    f"Required argument '--{arg.name}' in '{path_str}' cannot have a default value"
                )

            # Validate deprecation
            if arg.deprecated:
                self._validate_deprecation(
                    arg.deprecated, f"Argument '--{arg.name}' in '{path_str}'"
                )

    def _validate_exclusion_groups(self, cmd: Command, path: List[str]) -> None:
        """Validate exclusion groups reference valid arguments."""
        path_str = " -> ".join(path)
        arg_names = {arg.name for arg in cmd.arguments}

        for group in cmd.exclusion_groups:
            if not group.name:
                self._errors.append(
                    f"Exclusion group in '{path_str}' is missing a name"
                )

            if len(group.arguments) < 2:
                self._errors.append(
                    f"Exclusion group '{group.name}' in '{path_str}' must have at least 2 arguments"
                )

            for arg_name in group.arguments:
                if arg_name not in arg_names:
                    self._errors.append(
                        f"Exclusion group '{group.name}' in '{path_str}' references "
                        f"unknown argument '{arg_name}'"
                    )

    def _validate_dependency_rules(self, cmd: Command, path: List[str]) -> None:
        """Validate dependency rules reference valid arguments."""
        path_str = " -> ".join(path)
        arg_names = {arg.name for arg in cmd.arguments}

        for rule in cmd.dependency_rules:
            if not rule.name:
                self._errors.append(
                    f"Dependency rule in '{path_str}' is missing a name"
                )

            if rule.rule not in ("if_then", "requires", "conflicts"):
                self._errors.append(
                    f"Invalid rule type '{rule.rule}' for dependency '{rule.name}' in '{path_str}'. "
                    f"Must be 'if_then', 'requires', or 'conflicts'."
                )

            # Validate if_arg reference
            if rule.if_arg and rule.if_arg not in arg_names:
                self._errors.append(
                    f"Dependency rule '{rule.name}' in '{path_str}' references "
                    f"unknown argument '{rule.if_arg}'"
                )

            # Validate then_require references
            if rule.then_require:
                for arg_name in rule.then_require:
                    if arg_name not in arg_names:
                        self._errors.append(
                            f"Dependency rule '{rule.name}' in '{path_str}' requires "
                            f"unknown argument '{arg_name}'"
                        )

    def _validate_validators(self, cmd: Command, path: List[str]) -> None:
        """Validate custom validators."""
        path_str = " -> ".join(path)
        arg_names = {arg.name for arg in cmd.arguments}

        for validator in cmd.validators:
            name = validator.get("name", "(unnamed)")
            rule = validator.get("rule")

            if not rule:
                self._errors.append(
                    f"Validator '{name}' in '{path_str}' is missing 'rule' field"
                )
                continue

            if rule not in ("if_then", "requires", "conflicts", "callable"):
                self._errors.append(
                    f"Invalid rule type '{rule}' for validator '{name}' in '{path_str}'"
                )

            # For callable validators, check function is specified
            if rule == "callable" and not validator.get("function"):
                self._errors.append(
                    f"Callable validator '{name}' in '{path_str}' is missing 'function' field"
                )

            # Validate 'if' condition references
            if_cond = validator.get("if")
            if if_cond and isinstance(if_cond, dict):
                if_arg = if_cond.get("arg")
                if if_arg and if_arg not in arg_names:
                    self._errors.append(
                        f"Validator '{name}' in '{path_str}' references "
                        f"unknown argument '{if_arg}' in condition"
                    )

            # Validate 'then' action references
            then_action = validator.get("then")
            if then_action and isinstance(then_action, dict):
                for key in ("require", "forbid"):
                    refs = then_action.get(key, [])
                    for arg_name in refs:
                        if arg_name not in arg_names:
                            self._errors.append(
                                f"Validator '{name}' in '{path_str}' references "
                                f"unknown argument '{arg_name}' in '{key}'"
                            )

    def _validate_deprecation(self, deprecation: object, context: str) -> None:
        """Validate deprecation metadata structure."""
        from .models import Deprecation

        if not isinstance(deprecation, Deprecation):
            self._errors.append(f"{context}: Invalid deprecation structure")
            return

        if not deprecation.since:
            self._errors.append(f"{context}: Deprecation missing 'since' field")


def validate_reserved_names(config: "Configuration") -> List[str]:
    """Check for conflicts with reserved argument names.

    Returns a list of error messages if conflicts are found.
    """
    errors: List[str] = []
    reserved = getattr(config, "reserved", {"help": True, "version": True, "debug": True})

    reserved_names = {
        "help": ["help", "h"],
        "version": ["version", "V"],
        "debug": ["debug"],
    }

    # Check parameters
    for param in config.parameters:
        for reserved_key, names in reserved_names.items():
            if reserved.get(reserved_key, True):
                if param.name in names:
                    errors.append(
                        f"Parameter '{param.name}' conflicts with reserved name "
                        f"(disable with reserved.{reserved_key}=false)"
                    )

    # Check command arguments
    commands = getattr(config, "commands", [])

    def check_command_args(cmds: List[Command], path: List[str]) -> None:
        for cmd in cmds:
            cmd_path = path + [cmd.name]
            for arg in cmd.arguments:
                for reserved_key, names in reserved_names.items():
                    if reserved.get(reserved_key, True):
                        if arg.name in names:
                            errors.append(
                                f"Command argument '--{arg.name}' in '{' -> '.join(cmd_path)}' "
                                f"conflicts with reserved name "
                                f"(disable with reserved.{reserved_key}=false)"
                            )
                        if arg.short and arg.short in names:
                            errors.append(
                                f"Short flag '-{arg.short}' in '{' -> '.join(cmd_path)}' "
                                f"conflicts with reserved name "
                                f"(disable with reserved.{reserved_key}=false)"
                            )
            if cmd.subcommands:
                check_command_args(cmd.subcommands, cmd_path)

    check_command_args(commands, [])

    return errors
