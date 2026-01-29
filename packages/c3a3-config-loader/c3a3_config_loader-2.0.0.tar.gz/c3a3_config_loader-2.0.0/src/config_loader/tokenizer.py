# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""
Configuration Loader - Token Classifier

Implements token classification for command line argument parsing.
Classifies input tokens as commands, options, or positional arguments.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple

from .models import Command


class TokenType(Enum):
    """Classification of command line tokens."""

    LONG_OPTION = auto()  # --name or --name=value
    SHORT_OPTION = auto()  # -x or -xyz (bundled)
    OPTIONS_END = auto()  # -- (marks end of options)
    COMMAND = auto()  # matches command tree
    POSITIONAL = auto()  # everything else


@dataclass
class Token:
    """A classified command line token.

    Attributes:
        type: The classification of this token.
        value: The extracted value (e.g., 'region' from '--region').
        original: The original token string.
        position: Position in the argument list (0-indexed).
        option_value: For options with =, the value part (e.g., 'us-east' from '--region=us-east').
        short_flags: For bundled short options, the individual flags (e.g., ['v', 'f'] from '-vf').
    """

    type: TokenType
    value: str
    original: str
    position: int
    option_value: Optional[str] = None
    short_flags: Optional[List[str]] = None


class Tokenizer:
    """Classifies command line tokens for three-phase parsing.

    The tokenizer performs the first pass over command line arguments,
    classifying each token without yet knowing the full context.
    Classification follows these rules (from §34):

    1. '--' marks end of options; all following tokens are positional
    2. '--name' or '--name=value' is a long option
    3. '-x' or '-xyz' is short option(s)
    4. A token matching a command name at the current level is a command
    5. Everything else is a positional argument

    The tokenizer builds a command name index to efficiently check if
    a token is a command at any level of the tree.
    """

    def __init__(self, command_tree: List[Command]) -> None:
        """Initialize the tokenizer with a command tree.

        Args:
            command_tree: List of root-level commands.
        """
        self.command_tree = command_tree
        self._command_names: Set[str] = set()
        self._alias_to_name: Dict[str, str] = {}
        self._build_command_index(command_tree)

    def _build_command_index(self, commands: List[Command]) -> None:
        """Build index of all command names and aliases at all levels."""
        for cmd in commands:
            self._command_names.add(cmd.name)
            for alias in cmd.aliases:
                self._command_names.add(alias)
                self._alias_to_name[alias] = cmd.name
            if cmd.subcommands:
                self._build_command_index(cmd.subcommands)

    def tokenize(self, args: List[str]) -> List[Token]:
        """Tokenize a list of command line arguments.

        Args:
            args: List of command line arguments (typically sys.argv[1:]).

        Returns:
            List of classified tokens in order.
        """
        tokens: List[Token] = []
        options_ended = False

        for position, arg in enumerate(args):
            if options_ended:
                # After --, everything is positional
                tokens.append(
                    Token(
                        type=TokenType.POSITIONAL,
                        value=arg,
                        original=arg,
                        position=position,
                    )
                )
            elif arg == "--":
                # Options terminator
                tokens.append(
                    Token(
                        type=TokenType.OPTIONS_END,
                        value="",
                        original=arg,
                        position=position,
                    )
                )
                options_ended = True
            elif arg.startswith("--"):
                # Long option
                token = self._parse_long_option(arg, position)
                tokens.append(token)
            elif arg.startswith("-") and len(arg) > 1 and not arg[1:].isdigit():
                # Short option(s) - but not negative numbers like -1
                token = self._parse_short_option(arg, position)
                tokens.append(token)
            elif self._is_potential_command(arg):
                # Potential command (may be reclassified during parsing)
                tokens.append(
                    Token(
                        type=TokenType.COMMAND,
                        value=arg,
                        original=arg,
                        position=position,
                    )
                )
            else:
                # Positional argument
                tokens.append(
                    Token(
                        type=TokenType.POSITIONAL,
                        value=arg,
                        original=arg,
                        position=position,
                    )
                )

        return tokens

    def _parse_long_option(self, arg: str, position: int) -> Token:
        """Parse a long option (--name or --name=value)."""
        # Remove leading --
        content = arg[2:]

        if "=" in content:
            name, value = content.split("=", 1)
            return Token(
                type=TokenType.LONG_OPTION,
                value=name,
                original=arg,
                position=position,
                option_value=value,
            )
        else:
            return Token(
                type=TokenType.LONG_OPTION,
                value=content,
                original=arg,
                position=position,
            )

    def _parse_short_option(self, arg: str, position: int) -> Token:
        """Parse short option(s) (-x or -xyz for bundled)."""
        # Remove leading -
        content = arg[1:]

        if len(content) == 1:
            # Single short flag
            return Token(
                type=TokenType.SHORT_OPTION,
                value=content,
                original=arg,
                position=position,
            )
        else:
            # Bundled short flags (e.g., -vvv or -abc)
            # Could also be -xvalue format, but we can't know without context
            # For now, treat as bundled flags; parser will handle value consumption
            flags = list(content)
            return Token(
                type=TokenType.SHORT_OPTION,
                value=content[0],  # Primary flag
                original=arg,
                position=position,
                short_flags=flags,
            )

    def _is_potential_command(self, arg: str) -> bool:
        """Check if a token could be a command.

        This is a preliminary check - the actual command resolution
        happens during parsing when we know the current position in
        the command tree.
        """
        return arg in self._command_names

    def resolve_alias(self, name: str) -> str:
        """Resolve an alias to its primary command name.

        Returns the original name if it's not an alias.
        """
        return self._alias_to_name.get(name, name)

    def get_commands_at_level(
        self, path: List[str]
    ) -> Tuple[Dict[str, Command], Dict[str, str]]:
        """Get available commands and aliases at a specific path in the tree.

        Args:
            path: Current command path (empty for root level).

        Returns:
            Tuple of (name -> Command mapping, alias -> primary name mapping)
        """
        commands = self.command_tree

        # Navigate to the current level
        for name in path:
            found = None
            for cmd in commands:
                if cmd.name == name or name in cmd.aliases:
                    found = cmd
                    break
            if found is None:
                return {}, {}
            commands = found.subcommands

        # Build mappings for this level
        name_to_cmd: Dict[str, Command] = {}
        alias_to_name: Dict[str, str] = {}

        for cmd in commands:
            name_to_cmd[cmd.name] = cmd
            for alias in cmd.aliases:
                alias_to_name[alias] = cmd.name

        return name_to_cmd, alias_to_name

    def is_command_at_level(self, token: str, path: List[str]) -> Optional[Command]:
        """Check if a token is a valid command at the given path level.

        Args:
            token: The token to check.
            path: Current command path.

        Returns:
            The Command if token is valid at this level, None otherwise.
        """
        name_to_cmd, alias_to_name = self.get_commands_at_level(path)

        # Check primary names first
        if token in name_to_cmd:
            return name_to_cmd[token]

        # Check aliases
        if token in alias_to_name:
            primary = alias_to_name[token]
            return name_to_cmd.get(primary)

        return None
