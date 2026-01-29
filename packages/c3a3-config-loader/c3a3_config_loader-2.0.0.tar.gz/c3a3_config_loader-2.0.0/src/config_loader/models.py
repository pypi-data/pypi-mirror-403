# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""
Configuration Loader - Data Models

Defines the data structures used throughout the configuration system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConfigParam:
    """Represents a configuration parameter."""

    namespace: Optional[str]
    name: str
    type: str
    required: bool = False
    default: Any = None
    accepts: Optional[List[Any]] = None
    obfuscated: bool = False
    protocol: Optional[str] = None


@dataclass
class ConfigArg:
    """Represents a positional argument."""

    name: str
    type: str
    required: bool = False
    default: Any = None
    protocol: Optional[str] = None


# ============================================================================
# v2.0 Command System Models
# ============================================================================


@dataclass
class CommandArgument:
    """Argument scoped to a command.

    Attributes:
        name: The argument name (used as --name on CLI).
        type: Value type - 'string', 'number', or 'boolean'.
        short: Optional short flag (e.g., 'r' for -r).
        scope: Visibility scope - 'local', 'inherited', or 'ephemeral'.
        required: Whether the argument must be provided.
        default: Default value if not provided.
        env: Whether to read from environment variables.
        env_name: Custom environment variable name (implies env=True).
        nargs: Argument count - '?', '*', '+', or an integer.
        deprecated: Deprecation metadata if argument is deprecated.
        values_from: Path to a callable that provides valid values.
            Format: "module.path.function_name"
            The function receives (ProviderContext) and returns List[str].
    """

    name: str
    type: str = "string"
    short: Optional[str] = None
    scope: str = "local"
    required: bool = False
    default: Any = None
    env: bool = False
    env_name: Optional[str] = None
    nargs: Optional[str] = None
    deprecated: Optional["Deprecation"] = None
    values_from: Optional[str] = None


@dataclass
class ExclusionGroup:
    """Mutually exclusive argument group.

    Defines a set of arguments where at most one may be provided.

    Attributes:
        name: Identifier for error messages.
        arguments: List of argument names that are mutually exclusive.
        required: If True, at least one argument must be provided.
        message: Custom error message (optional).
    """

    name: str
    arguments: List[str] = field(default_factory=list)
    required: bool = False
    message: Optional[str] = None


@dataclass
class DependencyRule:
    """Inter-argument dependency rule.

    Defines validation rules between arguments.

    Attributes:
        name: Identifier for error messages.
        rule: Rule type - 'if_then', 'requires', or 'conflicts'.
        if_arg: For if_then: the condition argument.
        eq: For if_then: the condition value.
        then_require: For if_then: arguments required when condition is met.
        message: Custom error message (optional).
    """

    name: str
    rule: str
    if_arg: Optional[str] = None
    eq: Any = None
    then_require: Optional[List[str]] = None
    message: Optional[str] = None


@dataclass
class Deprecation:
    """Deprecation metadata for commands or arguments.

    Attributes:
        since: Version when deprecation started.
        removed_in: Version when item will be removed (optional).
        replacement: Suggested alternative (optional).
        message: Custom deprecation message (optional).
    """

    since: str
    removed_in: Optional[str] = None
    replacement: Optional[str] = None
    message: Optional[str] = None


@dataclass
class Command:
    """Hierarchical command definition.

    Represents a node in the command tree. Commands can be terminal
    (executable) or non-terminal (namespace only).

    Attributes:
        name: Command name (no dots allowed).
        aliases: Alternative names for this command.
        terminal: Whether this command is executable.
        ordering: Argument ordering mode - 'strict', 'relaxed', or 'interleaved'.
        arguments: Command-specific arguments.
        exclusion_groups: Mutually exclusive argument groups.
        dependency_rules: Inter-argument validation rules.
        validators: Custom validator definitions.
        subcommands: Child command nodes.
        deprecated: Deprecation metadata if command is deprecated.
    """

    name: str
    aliases: List[str] = field(default_factory=list)
    terminal: bool = False
    ordering: str = "relaxed"
    arguments: List[CommandArgument] = field(default_factory=list)
    exclusion_groups: List[ExclusionGroup] = field(default_factory=list)
    dependency_rules: List[DependencyRule] = field(default_factory=list)
    validators: List[Dict[str, Any]] = field(default_factory=list)
    subcommands: List[Command] = field(default_factory=list)
    deprecated: Optional[Deprecation] = None
