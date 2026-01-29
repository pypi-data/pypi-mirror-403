# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""
Configuration Loader - Command Parser

Implements three-phase parsing for hierarchical commands:
1. Extract global parameters
2. Resolve command path
3. Bind command arguments
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from .models import Command, CommandArgument
from .result import CommandContext
from .tokenizer import Token, Tokenizer, TokenType
from .exclusion_validator import validate_command_arguments
from .callable_validators import validate_command_with_validators

if TYPE_CHECKING:
    from .main import Configuration


class CommandParseError(ValueError):
    """Raised when command parsing fails."""

    pass


class UnknownCommandError(CommandParseError):
    """Raised when an unknown command is encountered."""

    def __init__(self, command: str, available: List[str], path: List[str]) -> None:
        self.command = command
        self.available = available
        self.path = path
        path_str = " ".join(path) if path else "(root)"
        avail_str = ", ".join(available) if available else "(none)"
        super().__init__(
            f"Unknown command '{command}' at {path_str}. Available: {avail_str}"
        )


class NonTerminalCommandError(CommandParseError):
    """Raised when execution stops at a non-terminal command."""

    def __init__(self, path: List[str], subcommands: List[str]) -> None:
        self.path = path
        self.subcommands = subcommands
        path_str = " ".join(path)
        sub_str = ", ".join(subcommands)
        super().__init__(
            f"'{path_str}' is not a complete command. Continue with: {sub_str}"
        )


class InvalidArgumentError(CommandParseError):
    """Raised when an invalid argument is encountered."""

    def __init__(self, argument: str, path: List[str], available: List[str]) -> None:
        self.argument = argument
        self.path = path
        self.available = available
        path_str = " ".join(path) if path else "(root)"
        avail_str = ", ".join(f"--{a}" for a in available) if available else "(none)"
        super().__init__(
            f"Unknown argument '{argument}' for command '{path_str}'. Available: {avail_str}"
        )


class OrderingViolationError(CommandParseError):
    """Raised when argument ordering rules are violated."""

    def __init__(self, argument: str, command: str, mode: str) -> None:
        self.argument = argument
        self.command = command
        self.mode = mode
        super().__init__(
            f"Argument '{argument}' appears before command '{command}' "
            f"(ordering mode: {mode})"
        )


class MissingRequiredArgumentError(CommandParseError):
    """Raised when a required argument is missing."""

    def __init__(self, argument: str, path: List[str]) -> None:
        self.argument = argument
        self.path = path
        path_str = " ".join(path)
        super().__init__(
            f"Required argument '--{argument}' not provided for command '{path_str}'"
        )


@dataclass
class ArgumentScope:
    """Tracks arguments available at a point in the command tree.

    Maintains the set of arguments that are visible based on
    inheritance rules and the current command path.
    """

    # Arguments by name with their definitions
    arguments: Dict[str, CommandArgument] = field(default_factory=dict)

    # Track which command defined each argument (for env var naming)
    defining_command: Dict[str, List[str]] = field(default_factory=dict)

    # Track short flag mappings
    short_to_name: Dict[str, str] = field(default_factory=dict)

    def add_arguments(
        self, args: List[CommandArgument], command_path: List[str]
    ) -> None:
        """Add arguments from a command to the scope."""
        for arg in args:
            # Child definitions override parent definitions
            self.arguments[arg.name] = arg
            self.defining_command[arg.name] = command_path

            if arg.short:
                self.short_to_name[arg.short] = arg.name

    def get_argument(self, name: str) -> Optional[CommandArgument]:
        """Get an argument by long name."""
        return self.arguments.get(name)

    def get_argument_by_short(self, short: str) -> Optional[CommandArgument]:
        """Get an argument by short flag."""
        name = self.short_to_name.get(short)
        if name:
            return self.arguments.get(name)
        return None

    def get_available_names(self) -> List[str]:
        """Get list of available argument names."""
        return list(self.arguments.keys())


class CommandParser:
    """Three-phase parser for hierarchical commands.

    Implements the parsing model from §16:
    - Phase 1: Extract global parameters (can appear anywhere)
    - Phase 2: Resolve command path through the tree
    - Phase 3: Bind command-specific arguments

    The parser respects ordering modes per command:
    - strict: arguments must appear after their command
    - relaxed: arguments may appear before or after (default)
    - interleaved: arguments may appear anywhere
    """

    def __init__(self, config: "Configuration") -> None:
        self.config = config
        self.commands = getattr(config, "commands", [])
        self.tokenizer = Tokenizer(self.commands)

        # Build set of global parameter patterns for Phase 1
        self._global_params = self._build_global_param_set()

    def _build_global_param_set(self) -> Set[str]:
        """Build set of global parameter names (with namespaces)."""
        params = set()
        for param in self.config.parameters:
            if param.namespace:
                params.add(f"{param.namespace}.{param.name}")
            else:
                params.add(param.name)
        return params

    def parse(
        self, args: List[str]
    ) -> Tuple[Dict[str, Any], Optional[CommandContext]]:
        """Parse command line arguments using three-phase parsing.

        Args:
            args: Command line arguments (typically sys.argv[1:]).

        Returns:
            Tuple of:
            - Global parameters dict (for existing parameter processing)
            - CommandContext with resolved command path and arguments

        Raises:
            CommandParseError: On parsing failures.
        """
        if not self.commands:
            # No commands defined, return empty context
            return {}, None

        tokens = self.tokenizer.tokenize(args)

        # Phase 1: Extract global parameters
        global_tokens, remaining_tokens = self._extract_global_params(tokens)

        # Phase 2: Resolve command path
        command_path, command_args_tokens, positional_tokens = (
            self._resolve_command_path(remaining_tokens)
        )

        # If no command was found but we have commands defined,
        # check if user just passed global params
        if not command_path and remaining_tokens:
            # Check if first non-global token looks like a command attempt
            for token in remaining_tokens:
                if token.type == TokenType.COMMAND:
                    # Unknown command
                    available = [cmd.name for cmd in self.commands]
                    raise UnknownCommandError(token.value, available, [])
                elif token.type == TokenType.POSITIONAL:
                    # Could be attempted command
                    available = [cmd.name for cmd in self.commands]
                    raise UnknownCommandError(token.value, available, [])

        # Phase 3: Bind command arguments
        command_arguments, positional = self._bind_command_args(
            command_path, command_args_tokens, positional_tokens
        )

        # Validate exclusion groups and dependency rules
        if command_path:
            cmd = self._get_command_at_path(command_path)
            if cmd:
                # Validate exclusion groups and dependency rules
                validate_command_arguments(cmd, command_arguments, command_path)

                # Run callable validators if defined
                if cmd.validators:
                    import os

                    validate_command_with_validators(
                        cmd.validators,
                        command_arguments,
                        command_path,
                        dict(os.environ),
                    )

                # Check for deprecated arguments
                self._check_argument_deprecation(cmd, command_arguments, command_path)

                # Validate arguments with value providers
                self._validate_value_providers(cmd, command_arguments, command_path)

        # Build global params dict for existing processing
        global_params = self._tokens_to_params(global_tokens)

        # Build command context
        terminal = self._is_terminal(command_path)
        context = CommandContext(
            path=command_path,
            arguments=command_arguments,
            positional=positional,
            terminal=terminal,
        )

        return global_params, context

    def _extract_global_params(
        self, tokens: List[Token]
    ) -> Tuple[List[Token], List[Token]]:
        """Phase 1: Extract global parameters from token stream.

        Global parameters (--namespace.name or --name for unnamespaced params)
        can appear anywhere in the token stream.

        Returns:
            Tuple of (global param tokens, remaining tokens)
        """
        global_tokens: List[Token] = []
        remaining: List[Token] = []
        skip_next = False

        for i, token in enumerate(tokens):
            if skip_next:
                skip_next = False
                global_tokens.append(token)  # Value token
                continue

            if token.type == TokenType.LONG_OPTION:
                if token.value in self._global_params:
                    global_tokens.append(token)
                    # Check if next token is the value (no = in option)
                    if token.option_value is None and i + 1 < len(tokens):
                        next_token = tokens[i + 1]
                        if next_token.type == TokenType.POSITIONAL:
                            skip_next = True
                else:
                    remaining.append(token)
            elif token.type == TokenType.OPTIONS_END:
                # Pass through, affects remaining tokens
                remaining.append(token)
            else:
                remaining.append(token)

        return global_tokens, remaining

    def _resolve_command_path(
        self, tokens: List[Token]
    ) -> Tuple[List[str], List[Token], List[Token]]:
        """Phase 2: Resolve command path through the tree.

        Consumes command tokens to build the path, collecting
        argument tokens and positional tokens along the way.

        Returns:
            Tuple of (command path, argument tokens, positional tokens)
        """
        path: List[str] = []
        arg_tokens: List[Token] = []
        positional_tokens: List[Token] = []
        current_commands = self.commands
        options_ended = False
        pending_args: List[Token] = []  # Args before command (for ordering check)

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token.type == TokenType.OPTIONS_END:
                options_ended = True
                i += 1
                continue

            if options_ended:
                # After --, everything is positional
                positional_tokens.append(token)
                i += 1
                continue

            if token.type in (TokenType.LONG_OPTION, TokenType.SHORT_OPTION):
                # Collect as potential command argument
                # Note: We don't consume the next token here as a value,
                # because we don't know the argument type yet. The value
                # binding happens in _bind_command_args where we can check
                # if the argument is a boolean (no value) or takes a value.
                pending_args.append(token)
                i += 1
                continue

            # Check if this token is a command at the current level
            cmd = self._find_command(token.value, current_commands)

            if cmd is not None:
                # Found a command - check ordering for pending args
                if pending_args:
                    if cmd.ordering == "strict":
                        # Args before command in strict mode is an error
                        raise OrderingViolationError(
                            pending_args[0].original, cmd.name, "strict"
                        )
                    # In relaxed/interleaved mode, keep pending args
                    arg_tokens.extend(pending_args)
                    pending_args = []

                # Resolve alias to primary name
                resolved_name = self.tokenizer.resolve_alias(token.value)
                if resolved_name != token.value:
                    # Find the command again with resolved name
                    cmd = self._find_command(resolved_name, current_commands)
                    if cmd is None:
                        cmd = self._find_command(token.value, current_commands)
                        resolved_name = token.value

                path.append(cmd.name if cmd else resolved_name)
                current_commands = cmd.subcommands if cmd else []
                i += 1
            elif token.type == TokenType.COMMAND:
                # Token was classified as command but not valid here
                available = [c.name for c in current_commands]
                raise UnknownCommandError(token.value, available, path)
            elif token.type == TokenType.POSITIONAL:
                # Check if it could be a command we don't recognize
                # But only if we haven't seen any options yet - otherwise
                # it might be a value for one of the pending options
                if current_commands and not path and not pending_args:
                    # At root level with no path yet and no pending args
                    # - likely unknown command
                    available = [c.name for c in current_commands]
                    raise UnknownCommandError(token.value, available, path)
                # Otherwise it's a positional argument (or arg value)
                positional_tokens.append(token)
                i += 1
            else:
                i += 1

        # Add any remaining pending args
        arg_tokens.extend(pending_args)

        return path, arg_tokens, positional_tokens

    def _find_command(
        self, name: str, commands: List[Command]
    ) -> Optional[Command]:
        """Find a command by name or alias."""
        for cmd in commands:
            if cmd.name == name:
                return cmd
            if name in cmd.aliases:
                return cmd
        return None

    def _bind_command_args(
        self,
        path: List[str],
        arg_tokens: List[Token],
        positional_tokens: List[Token],
    ) -> Tuple[Dict[str, Any], List[Any]]:
        """Phase 3: Bind command arguments.

        Resolves argument tokens against the scope built from
        the command path (including inherited arguments).

        Returns:
            Tuple of (argument values dict, positional values list)
        """
        if not path:
            return {}, [t.value for t in positional_tokens]

        # Build argument scope from command path
        scope = self._build_argument_scope(path)

        # Parse argument tokens
        # We track consumed positional tokens separately, as non-boolean args
        # may need to consume values from positional_tokens when not in arg_tokens
        arguments: Dict[str, Any] = {}
        consumed_positional = 0  # How many positional_tokens used as arg values
        i = 0
        while i < len(arg_tokens):
            token = arg_tokens[i]

            if token.type == TokenType.LONG_OPTION:
                arg_def = scope.get_argument(token.value)
                if arg_def is None:
                    raise InvalidArgumentError(
                        f"--{token.value}", path, scope.get_available_names()
                    )

                # Get value
                if token.option_value is not None:
                    value = token.option_value
                elif arg_def.type == "boolean":
                    value = "true"
                elif (
                    i + 1 < len(arg_tokens)
                    and arg_tokens[i + 1].type == TokenType.POSITIONAL
                ):
                    # Next token in arg_tokens is a value (not another option)
                    i += 1
                    value = arg_tokens[i].value
                elif consumed_positional < len(positional_tokens):
                    # Consume from positional tokens if available
                    value = positional_tokens[consumed_positional].value
                    consumed_positional += 1
                else:
                    raise CommandParseError(
                        f"Argument '--{token.value}' requires a value"
                    )

                arguments[arg_def.name] = self._parse_arg_value(value, arg_def)

            elif token.type == TokenType.SHORT_OPTION:
                # Handle short flags (possibly bundled)
                if token.short_flags:
                    # Bundled flags like -vvv or -abc
                    for flag in token.short_flags:
                        arg_def = scope.get_argument_by_short(flag)
                        if arg_def is None:
                            raise InvalidArgumentError(
                                f"-{flag}", path, scope.get_available_names()
                            )
                        if arg_def.type == "boolean":
                            # Count occurrences for flags like -vvv
                            current = arguments.get(arg_def.name, 0)
                            if isinstance(current, bool):
                                current = 1 if current else 0
                            arguments[arg_def.name] = current + 1
                        else:
                            # Non-boolean in bundle - rest is value
                            # This is complex, skip for now
                            arguments[arg_def.name] = True
                else:
                    arg_def = scope.get_argument_by_short(token.value)
                    if arg_def is None:
                        raise InvalidArgumentError(
                            f"-{token.value}", path, scope.get_available_names()
                        )

                    if arg_def.type == "boolean":
                        arguments[arg_def.name] = True
                    elif (
                        i + 1 < len(arg_tokens)
                        and arg_tokens[i + 1].type == TokenType.POSITIONAL
                    ):
                        # Next token in arg_tokens is a value (not another option)
                        i += 1
                        value = arg_tokens[i].value
                        arguments[arg_def.name] = self._parse_arg_value(value, arg_def)
                    elif consumed_positional < len(positional_tokens):
                        # Consume from positional tokens if available
                        value = positional_tokens[consumed_positional].value
                        consumed_positional += 1
                        arguments[arg_def.name] = self._parse_arg_value(value, arg_def)
                    else:
                        raise CommandParseError(
                            f"Argument '-{token.value}' requires a value"
                        )

            i += 1

        # Load environment variables for arguments not provided via CLI
        from .loaders import CommandArgumentEnvLoader

        env_loader = CommandArgumentEnvLoader(self.config)
        for name, arg_def in scope.arguments.items():
            if name not in arguments and (arg_def.env or arg_def.env_name):
                defining_path = scope.defining_command.get(name, [])
                env_value = env_loader.load_argument_value(arg_def, defining_path)
                if env_value is not None:
                    arguments[name] = self._parse_arg_value(env_value, arg_def)

        # Apply defaults for arguments not provided
        for name, arg_def in scope.arguments.items():
            if name not in arguments:
                if arg_def.default is not None:
                    arguments[name] = arg_def.default
                elif arg_def.required:
                    raise MissingRequiredArgumentError(name, path)

        # Process positional tokens (skip ones consumed as argument values)
        positional = [t.value for t in positional_tokens[consumed_positional:]]

        return arguments, positional

    def _build_argument_scope(self, path: List[str]) -> ArgumentScope:
        """Build the argument scope for a command path.

        Walks the command tree, collecting inherited arguments
        as we go deeper into the path.
        """
        scope = ArgumentScope()
        commands = self.commands
        current_path: List[str] = []

        for name in path:
            cmd = self._find_command(name, commands)
            if cmd is None:
                break

            current_path.append(cmd.name)

            # Add inherited arguments from this command
            inherited = [a for a in cmd.arguments if a.scope == "inherited"]
            scope.add_arguments(inherited, current_path.copy())

            commands = cmd.subcommands

        # Add local arguments from the final command
        if path:
            final_cmd = self._get_command_at_path(path)
            if final_cmd:
                local = [a for a in final_cmd.arguments if a.scope == "local"]
                scope.add_arguments(local, path.copy())

                # Also add inherited args defined at this level
                # (they're available to this command too)
                inherited = [a for a in final_cmd.arguments if a.scope == "inherited"]
                scope.add_arguments(inherited, path.copy())

        return scope

    def _get_command_at_path(self, path: List[str]) -> Optional[Command]:
        """Get the command at a specific path."""
        commands = self.commands
        cmd = None

        for name in path:
            cmd = self._find_command(name, commands)
            if cmd is None:
                return None
            commands = cmd.subcommands

        return cmd

    def _is_terminal(self, path: List[str]) -> bool:
        """Check if a command path ends at a terminal command."""
        if not path:
            return False

        cmd = self._get_command_at_path(path)
        return cmd.terminal if cmd else False

    def _check_argument_deprecation(
        self,
        cmd: Command,
        arguments: Dict[str, Any],
        path: List[str],
    ) -> None:
        """Check for deprecated arguments and emit warnings."""
        # Build a map of argument names to their definitions
        arg_defs = {arg.name: arg for arg in cmd.arguments}

        for arg_name, value in arguments.items():
            # Skip if argument wasn't actually provided (just has default)
            if value is None:
                continue

            arg_def = arg_defs.get(arg_name)
            if arg_def and arg_def.deprecated:
                # Use the deprecation tracker from the config
                self.config.deprecation_tracker.check_argument(
                    arg_name, path, arg_def.deprecated
                )

    def _validate_value_providers(
        self,
        cmd: Command,
        arguments: Dict[str, Any],
        path: List[str],
    ) -> None:
        """Validate argument values against their value providers."""
        from .value_provider import ProviderContext

        arg_defs = {arg.name: arg for arg in cmd.arguments}

        for arg_name, value in arguments.items():
            if value is None:
                continue

            arg_def = arg_defs.get(arg_name)
            if not arg_def or not arg_def.values_from:
                continue

            # Load the provider function
            provider_fn = self._load_provider_function(arg_def.values_from)
            if provider_fn is None:
                continue

            # Create context and get valid values
            ctx = ProviderContext(
                command_path=path,
                parsed_args=arguments,
                environment=dict(__import__("os").environ),
            )

            try:
                valid_values = provider_fn(ctx)
            except Exception:
                # Provider failed - skip validation
                continue

            # Validate the value(s)
            values_to_check = value if isinstance(value, list) else [value]
            for v in values_to_check:
                if v not in valid_values:
                    # Show suggestions
                    suggestions = ", ".join(valid_values[:5])
                    if len(valid_values) > 5:
                        suggestions += f" ... ({len(valid_values)} total)"
                    raise InvalidArgumentError(
                        f"Invalid value '{v}' for --{arg_name}. "
                        f"Valid values: {suggestions}",
                        path,
                        valid_values[:10],
                    )

    def _load_provider_function(self, function_path: str) -> Optional[Any]:
        """Load a value provider function from a dotted path."""
        try:
            module_path, func_name = function_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[func_name])
            return getattr(module, func_name, None)
        except (ImportError, AttributeError, ValueError):
            return None

    def _parse_arg_value(self, value: str, arg_def: CommandArgument) -> Any:
        """Parse an argument value according to its type."""
        if arg_def.type == "boolean":
            return value.lower() in ("true", "1", "yes", "on")
        elif arg_def.type == "number":
            try:
                if "." in value:
                    return float(value)
                return int(value)
            except ValueError:
                raise CommandParseError(
                    f"Invalid number '{value}' for argument '--{arg_def.name}'"
                )
        return value

    def _tokens_to_params(self, tokens: List[Token]) -> Dict[str, Any]:
        """Convert global parameter tokens to a params dict.

        Returns a dict suitable for merging with the existing
        argument loader output.
        """
        params: Dict[str, Any] = {}
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == TokenType.LONG_OPTION:
                # Find the parameter definition
                param_key = token.value
                value: Any = None

                if token.option_value is not None:
                    value = token.option_value
                elif i + 1 < len(tokens):
                    i += 1
                    value = tokens[i].value
                else:
                    # Boolean flag
                    value = "true"

                # Convert to the format expected by process()
                # --namespace.name -> param_namespace_name
                if "." in param_key:
                    ns, name = param_key.split(".", 1)
                    params[f"param_{ns}_{name}"] = value
                else:
                    params[f"param_default_{param_key}"] = value

            i += 1

        return params

    def validate_terminal(self, path: List[str]) -> None:
        """Validate that a command path ends at a terminal command.

        Raises NonTerminalCommandError if the path is non-terminal.
        """
        if not path:
            return

        cmd = self._get_command_at_path(path)
        if cmd and not cmd.terminal:
            subcommands = [c.name for c in cmd.subcommands]
            raise NonTerminalCommandError(path, subcommands)
