# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""
Configuration Loader - Command Builder

Provides a builder pattern API for incremental command construction
with suggestions at each step. Useful for autocompletion, IDE integrations,
and interactive CLI wizards.

Example:
    cfg = Configuration(spec)
    builder = cfg.builder()

    # Check what can be added
    suggestions = builder.check_next()
    print(suggestions.commands)  # Available commands
    print(suggestions.is_valid)  # Can we build now?

    # Add a command
    builder = builder.add_command("deploy")

    # Add arguments
    builder = builder.add_argument("region", "us-east-1")
    builder = builder.add_argument("force")  # Boolean flag

    # Build the result
    if builder.check_next().is_valid:
        result = builder.build()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .models import Command, CommandArgument
from .result import CommandContext, ConfigurationResult, ProcessingResult
from .value_provider import ProviderContext

if TYPE_CHECKING:
    from .main import Configuration


@dataclass
class ArgumentSuggestion:
    """Suggestion for an argument.

    Attributes:
        name: The argument name (without --).
        short: Short flag if available (without -).
        arg_type: The argument type (string, number, boolean).
        required: Whether this argument is required.
        description: Human-readable description.
        expects_value: Whether this argument expects a value.
        default: Default value if any.
        value_suggestions: Suggested values from value provider.
    """

    name: str
    short: Optional[str] = None
    arg_type: str = "string"
    required: bool = False
    description: Optional[str] = None
    expects_value: bool = True
    default: Any = None
    value_suggestions: List[str] = field(default_factory=list)


@dataclass
class CommandSuggestion:
    """Suggestion for a command or subcommand.

    Attributes:
        name: The command name.
        aliases: Alternative names for this command.
        description: Human-readable description.
        terminal: Whether this is a terminal (executable) command.
    """

    name: str
    aliases: List[str] = field(default_factory=list)
    description: Optional[str] = None
    terminal: bool = False


@dataclass
class Suggestions:
    """Result of checking what can be added next.

    Attributes:
        is_valid: Whether the current state is a valid terminal command.
        commands: Available subcommands at this point.
        arguments: Available arguments at this point.
        positional_expected: Whether positional arguments are expected.
        positional_description: Description of expected positional args.
        errors: Any validation errors with current state.
    """

    is_valid: bool = False
    commands: List[CommandSuggestion] = field(default_factory=list)
    arguments: List[ArgumentSuggestion] = field(default_factory=list)
    positional_expected: bool = False
    positional_description: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    def is_terminal(self) -> bool:
        """Check if we're at a terminal command (can be executed)."""
        return self.is_valid


@dataclass
class ValueSuggestions:
    """Suggestions for argument values.

    Attributes:
        argument_name: The argument being set.
        values: Suggested values.
        accepts_any: Whether any value is accepted (not just suggestions).
        arg_type: The expected type (string, number, boolean).
    """

    argument_name: str
    values: List[str] = field(default_factory=list)
    accepts_any: bool = True
    arg_type: str = "string"


class ArgumentValueBuilder:
    """Builder for setting an argument value with suggestions.

    Use this when you want to get value suggestions before setting.
    """

    def __init__(
        self,
        parent: "CommandBuilder",
        argument_name: str,
        arg_def: CommandArgument,
    ) -> None:
        self._parent = parent
        self._argument_name = argument_name
        self._arg_def = arg_def
        self._value: Optional[Any] = None

    def check_next(self) -> ValueSuggestions:
        """Get suggestions for this argument's value."""
        values: List[str] = []
        accepts_any = True

        # Get values from value provider if available
        if self._arg_def.values_from:
            provider_fn = self._parent._load_provider_function(
                self._arg_def.values_from
            )
            if provider_fn:
                ctx = ProviderContext(
                    command_path=self._parent._command_path,
                    parsed_args=self._parent._arguments.copy(),
                )
                try:
                    values = provider_fn(ctx)
                    accepts_any = False  # Restricted to provider values
                except Exception:
                    pass

        # For booleans, suggest true/false
        if self._arg_def.type == "boolean":
            values = ["true", "false"]
            accepts_any = False

        return ValueSuggestions(
            argument_name=self._argument_name,
            values=values,
            accepts_any=accepts_any,
            arg_type=self._arg_def.type,
        )

    def set_value(self, value: Any) -> "ArgumentValueBuilder":
        """Set the argument value."""
        self._value = value
        return self

    def build(self) -> "CommandBuilder":
        """Return to the parent builder with the value set."""
        if self._value is not None:
            return self._parent.add_argument(self._argument_name, self._value)
        return self._parent


class CommandBuilder:
    """Builder for constructing commands incrementally.

    Provides a fluent API for building commands with suggestions
    at each step.
    """

    def __init__(
        self,
        config: "Configuration",
        command_path: Optional[List[str]] = None,
        arguments: Optional[Dict[str, Any]] = None,
        positional: Optional[List[Any]] = None,
    ) -> None:
        self._config = config
        self._command_path = command_path or []
        self._arguments = arguments or {}
        self._positional = positional or []

    def check_next(self) -> Suggestions:
        """Check what can be added next.

        Returns suggestions for commands, arguments, and whether
        the current state is valid (can be built).
        """
        suggestions = Suggestions()

        # Get current command (if any)
        current_cmd = self._get_current_command()

        # Check if we're at a valid terminal command
        if current_cmd and current_cmd.terminal:
            suggestions.is_valid = True
            # Check for missing required arguments
            missing = self._get_missing_required_arguments(current_cmd)
            if missing:
                suggestions.is_valid = False
                suggestions.errors = [
                    f"Missing required argument: --{name}" for name in missing
                ]

        # Get available subcommands
        if current_cmd:
            for subcmd in current_cmd.subcommands:
                suggestions.commands.append(
                    CommandSuggestion(
                        name=subcmd.name,
                        aliases=subcmd.aliases,
                        terminal=subcmd.terminal,
                    )
                )
        elif not self._command_path:
            # At root level - show top-level commands
            for cmd in self._config.commands:
                suggestions.commands.append(
                    CommandSuggestion(
                        name=cmd.name,
                        aliases=cmd.aliases,
                        terminal=cmd.terminal,
                    )
                )

        # Get available arguments
        if current_cmd:
            for arg in current_cmd.arguments:
                if arg.name not in self._arguments:
                    arg_suggestion = self._make_argument_suggestion(arg)
                    suggestions.arguments.append(arg_suggestion)

        # Check for positional arguments
        suggestions.positional_expected = bool(
            current_cmd and current_cmd.terminal
        )

        return suggestions

    def add_command(self, name: str) -> "CommandBuilder":
        """Add a command or subcommand.

        Args:
            name: The command name (or alias).

        Returns:
            New builder with the command added.

        Raises:
            ValueError: If the command is not valid at this point.
        """
        # Find the command
        current = self._get_current_command()
        commands = (
            current.subcommands
            if current is not None
            else self._config.commands
        )

        cmd = None
        resolved_name = name
        for c in commands:
            if c.name == name or name in c.aliases:
                cmd = c
                resolved_name = c.name
                break

        if cmd is None:
            available = [c.name for c in commands]
            raise ValueError(
                f"Unknown command '{name}'. Available: {', '.join(available)}"
            )

        return CommandBuilder(
            config=self._config,
            command_path=self._command_path + [resolved_name],
            arguments=self._arguments.copy(),
            positional=self._positional.copy(),
        )

    def add_argument(
        self, name: str, value: Optional[Any] = None
    ) -> "CommandBuilder":
        """Add an argument.

        Args:
            name: The argument name (without --).
            value: The argument value. For booleans, omit for True.

        Returns:
            New builder with the argument added.

        Raises:
            ValueError: If the argument is not valid.
        """
        current_cmd = self._get_current_command()
        if not current_cmd:
            raise ValueError("No command selected. Add a command first.")

        # Find the argument definition
        arg_def = None
        for arg in current_cmd.arguments:
            if arg.name == name or arg.short == name:
                arg_def = arg
                break

        if arg_def is None:
            available = [a.name for a in current_cmd.arguments]
            raise ValueError(
                f"Unknown argument '{name}'. Available: {', '.join(available)}"
            )

        # Handle value
        if arg_def.type == "boolean":
            parsed_value = True if value is None else bool(value)
        elif value is None:
            raise ValueError(f"Argument '{name}' requires a value.")
        else:
            parsed_value = self._parse_value(value, arg_def.type)

        new_arguments = self._arguments.copy()
        new_arguments[arg_def.name] = parsed_value

        return CommandBuilder(
            config=self._config,
            command_path=self._command_path.copy(),
            arguments=new_arguments,
            positional=self._positional.copy(),
        )

    def add_argument_builder(self, name: str) -> ArgumentValueBuilder:
        """Get a builder for setting an argument with value suggestions.

        Args:
            name: The argument name (without --).

        Returns:
            ArgumentValueBuilder for setting the value.
        """
        current_cmd = self._get_current_command()
        if not current_cmd:
            raise ValueError("No command selected. Add a command first.")

        arg_def = None
        for arg in current_cmd.arguments:
            if arg.name == name or arg.short == name:
                arg_def = arg
                break

        if arg_def is None:
            raise ValueError(f"Unknown argument '{name}'.")

        return ArgumentValueBuilder(self, name, arg_def)

    def add_positional(self, value: Any) -> "CommandBuilder":
        """Add a positional argument.

        Args:
            value: The positional argument value.

        Returns:
            New builder with the positional added.
        """
        return CommandBuilder(
            config=self._config,
            command_path=self._command_path.copy(),
            arguments=self._arguments.copy(),
            positional=self._positional + [value],
        )

    def build(self) -> ProcessingResult:
        """Build the final ProcessingResult.

        Returns:
            The processing result.

        Raises:
            ValueError: If the current state is not valid.
        """
        suggestions = self.check_next()
        if not suggestions.is_valid:
            errors = suggestions.errors or ["Command is not complete."]
            raise ValueError("; ".join(errors))

        # Build command context
        current_cmd = self._get_current_command()
        command_context = CommandContext(
            path=self._command_path,
            arguments=self._arguments,
            positional=self._positional,
            terminal=current_cmd.terminal if current_cmd else False,
        )

        # Build the config result - use empty config for builder-only usage
        # Full config processing would require calling self._config.process()
        config_result = ConfigurationResult({}, {})

        return ProcessingResult(
            config=config_result,
            command=command_context,
        )

    def _get_current_command(self) -> Optional[Command]:
        """Get the command at the current path."""
        if not self._command_path:
            return None

        commands = self._config.commands
        cmd = None
        for name in self._command_path:
            for c in commands:
                if c.name == name:
                    cmd = c
                    commands = c.subcommands
                    break

        return cmd

    def _get_missing_required_arguments(self, cmd: Command) -> List[str]:
        """Get names of required arguments that are missing."""
        missing = []
        for arg in cmd.arguments:
            if arg.required and arg.name not in self._arguments:
                missing.append(arg.name)
        return missing

    def _make_argument_suggestion(self, arg: CommandArgument) -> ArgumentSuggestion:
        """Create an ArgumentSuggestion from a CommandArgument."""
        value_suggestions: List[str] = []

        # Get suggestions from value provider
        if arg.values_from:
            provider_fn = self._load_provider_function(arg.values_from)
            if provider_fn:
                ctx = ProviderContext(
                    command_path=self._command_path,
                    parsed_args=self._arguments.copy(),
                )
                try:
                    value_suggestions = provider_fn(ctx)[:10]  # Limit to 10
                except Exception:
                    pass

        return ArgumentSuggestion(
            name=arg.name,
            short=arg.short,
            arg_type=arg.type,
            required=arg.required,
            expects_value=arg.type != "boolean",
            default=arg.default,
            value_suggestions=value_suggestions,
        )

    def _load_provider_function(self, function_path: str) -> Optional[Any]:
        """Load a value provider function from a dotted path."""
        try:
            module_path, func_name = function_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[func_name])
            return getattr(module, func_name, None)
        except (ImportError, AttributeError, ValueError):
            return None

    def _parse_value(self, value: Any, arg_type: str) -> Any:
        """Parse a value according to argument type."""
        if arg_type == "number":
            if isinstance(value, (int, float)):
                return value
            try:
                return int(value) if "." not in str(value) else float(value)
            except ValueError:
                raise ValueError(f"Invalid number: {value}")
        elif arg_type == "boolean":
            if isinstance(value, bool):
                return value
            return str(value).lower() in ("true", "1", "yes", "on")
        return value

    # State inspection methods
    @property
    def command_path(self) -> List[str]:
        """Current command path."""
        return self._command_path.copy()

    @property
    def arguments(self) -> Dict[str, Any]:
        """Currently set arguments."""
        return self._arguments.copy()

    @property
    def positional(self) -> List[Any]:
        """Currently set positional arguments."""
        return self._positional.copy()
