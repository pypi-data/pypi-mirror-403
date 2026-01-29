# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""
Configuration Loader - Error Recovery

Provides intelligent error messages with fuzzy matching suggestions
and helpful guidance for command line errors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ErrorRecoveryConfig:
    """Configuration for error recovery behavior.

    Attributes:
        suggest_distance: Maximum Levenshtein distance for suggestions (default: 2).
        max_suggestions: Maximum number of suggestions to show (default: 3).
        show_available: Whether to show available options in errors (default: True).
    """

    suggest_distance: int = 2
    max_suggestions: int = 3
    show_available: bool = True

    @classmethod
    def from_spec(cls, spec: Optional[Dict[str, Any]]) -> ErrorRecoveryConfig:
        """Create config from spec's error_recovery field."""
        if not spec:
            return cls()

        return cls(
            suggest_distance=spec.get("suggest_distance", 2),
            max_suggestions=spec.get("max_suggestions", 3),
            show_available=spec.get("show_available", True),
        )


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate the Levenshtein (edit) distance between two strings.

    The Levenshtein distance is the minimum number of single-character
    edits (insertions, deletions, substitutions) required to transform
    one string into another.

    Args:
        s1: First string.
        s2: Second string.

    Returns:
        The edit distance between s1 and s2.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost is 0 if characters match, 1 otherwise
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def find_similar(
    target: str,
    candidates: List[str],
    max_distance: int = 2,
    max_results: int = 3,
) -> List[Tuple[str, int]]:
    """Find candidates similar to the target string.

    Uses Levenshtein distance to find strings that are close to
    the target, useful for "did you mean?" suggestions.

    Args:
        target: The string to match against.
        candidates: List of possible matches.
        max_distance: Maximum edit distance to consider (default: 2).
        max_results: Maximum number of results to return (default: 3).

    Returns:
        List of (candidate, distance) tuples, sorted by distance.
    """
    if not candidates:
        return []

    matches: List[Tuple[str, int]] = []

    for candidate in candidates:
        distance = levenshtein_distance(target.lower(), candidate.lower())
        if distance <= max_distance:
            matches.append((candidate, distance))

    # Sort by distance, then alphabetically for ties
    matches.sort(key=lambda x: (x[1], x[0]))

    return matches[:max_results]


class ErrorRecovery:
    """Provides intelligent error recovery and suggestions.

    Generates helpful error messages with:
    - "Did you mean?" suggestions using fuzzy matching
    - Lists of available commands/arguments
    - Guidance for non-terminal commands
    """

    def __init__(self, config: Optional[ErrorRecoveryConfig] = None) -> None:
        self.config = config or ErrorRecoveryConfig()

    def suggest_command(
        self,
        unknown: str,
        available: List[str],
        path: List[str],
    ) -> str:
        """Generate error message for an unknown command.

        Args:
            unknown: The unrecognized command.
            available: List of valid commands at this level.
            path: Current command path (for context).

        Returns:
            Formatted error message with suggestions.
        """
        lines: List[str] = []
        path_str = " ".join(path) if path else "(root)"

        lines.append(f"Unknown command '{unknown}'")
        if path:
            lines.append(f"  at: {path_str}")

        # Find similar commands
        similar = find_similar(
            unknown,
            available,
            max_distance=self.config.suggest_distance,
            max_results=self.config.max_suggestions,
        )

        if similar:
            lines.append("")
            lines.append("Did you mean?")
            for cmd, distance in similar:
                lines.append(f"  {cmd}")

        # Show available commands
        if self.config.show_available and available:
            lines.append("")
            lines.append("Available commands:")
            for cmd in sorted(available):
                lines.append(f"  {cmd}")

        return "\n".join(lines)

    def suggest_argument(
        self,
        unknown: str,
        available: List[str],
        path: List[str],
    ) -> str:
        """Generate error message for an unknown argument.

        Args:
            unknown: The unrecognized argument (with -- prefix).
            available: List of valid argument names (without --).
            path: Current command path.

        Returns:
            Formatted error message with suggestions.
        """
        lines: List[str] = []
        path_str = " ".join(path) if path else "(global)"

        # Strip -- prefix for matching
        clean_unknown = unknown.lstrip("-")

        lines.append(f"Unknown argument '{unknown}'")
        lines.append(f"  for command: {path_str}")

        # Find similar arguments
        similar = find_similar(
            clean_unknown,
            available,
            max_distance=self.config.suggest_distance,
            max_results=self.config.max_suggestions,
        )

        if similar:
            lines.append("")
            lines.append("Did you mean?")
            for arg, distance in similar:
                lines.append(f"  --{arg}")

        # Show available arguments
        if self.config.show_available and available:
            lines.append("")
            lines.append("Available arguments:")
            for arg in sorted(available):
                lines.append(f"  --{arg}")

        return "\n".join(lines)

    def non_terminal_guidance(
        self,
        path: List[str],
        subcommands: List[str],
    ) -> str:
        """Generate guidance for stopping at a non-terminal command.

        Args:
            path: The current (incomplete) command path.
            subcommands: Available subcommands to continue with.

        Returns:
            Formatted guidance message.
        """
        lines: List[str] = []
        path_str = " ".join(path)

        lines.append(f"'{path_str}' is not a complete command")
        lines.append("")
        lines.append("To continue, use one of:")

        for cmd in sorted(subcommands):
            lines.append(f"  {path_str} {cmd}")

        return "\n".join(lines)

    def missing_required(
        self,
        argument: str,
        path: List[str],
    ) -> str:
        """Generate error message for missing required argument.

        Args:
            argument: The missing argument name.
            path: The command path.

        Returns:
            Formatted error message.
        """
        path_str = " ".join(path) if path else "(global)"
        return f"Required argument '--{argument}' not provided for '{path_str}'"

    def invalid_value(
        self,
        argument: str,
        value: str,
        expected_type: str,
        valid_values: Optional[List[str]] = None,
    ) -> str:
        """Generate error message for invalid argument value.

        Args:
            argument: The argument name.
            value: The invalid value provided.
            expected_type: The expected type (string, number, boolean).
            valid_values: Optional list of valid values.

        Returns:
            Formatted error message.
        """
        lines: List[str] = []

        lines.append(f"Invalid value '{value}' for argument '--{argument}'")
        lines.append(f"  expected: {expected_type}")

        if valid_values:
            # Find similar valid values
            similar = find_similar(
                value,
                valid_values,
                max_distance=self.config.suggest_distance,
                max_results=self.config.max_suggestions,
            )

            if similar:
                lines.append("")
                lines.append("Did you mean?")
                for val, _ in similar:
                    lines.append(f"  {val}")

            if self.config.show_available:
                lines.append("")
                lines.append("Valid values:")
                for val in sorted(valid_values):
                    lines.append(f"  {val}")

        return "\n".join(lines)

    def ordering_violation(
        self,
        argument: str,
        command: str,
        mode: str,
    ) -> str:
        """Generate error message for argument ordering violation.

        Args:
            argument: The argument that appeared in wrong position.
            command: The command with the ordering constraint.
            mode: The ordering mode (strict).

        Returns:
            Formatted error message.
        """
        lines: List[str] = []

        lines.append(f"Argument '{argument}' appears before command '{command}'")
        lines.append(f"  ordering mode: {mode}")
        lines.append("")
        lines.append(f"In '{mode}' mode, arguments must appear after their command.")
        lines.append(f"Move '{argument}' after '{command}' in the command line.")

        return "\n".join(lines)


def format_error_with_recovery(
    error_type: str,
    config: Optional[ErrorRecoveryConfig] = None,
    **kwargs: Any,
) -> str:
    """Convenience function to format errors with recovery suggestions.

    Args:
        error_type: Type of error (unknown_command, unknown_argument,
                   non_terminal, missing_required, invalid_value, ordering).
        config: Error recovery configuration.
        **kwargs: Arguments specific to the error type.

    Returns:
        Formatted error message.
    """
    recovery = ErrorRecovery(config)

    if error_type == "unknown_command":
        return recovery.suggest_command(
            kwargs["unknown"],
            kwargs.get("available", []),
            kwargs.get("path", []),
        )
    elif error_type == "unknown_argument":
        return recovery.suggest_argument(
            kwargs["unknown"],
            kwargs.get("available", []),
            kwargs.get("path", []),
        )
    elif error_type == "non_terminal":
        return recovery.non_terminal_guidance(
            kwargs["path"],
            kwargs.get("subcommands", []),
        )
    elif error_type == "missing_required":
        return recovery.missing_required(
            kwargs["argument"],
            kwargs.get("path", []),
        )
    elif error_type == "invalid_value":
        return recovery.invalid_value(
            kwargs["argument"],
            kwargs["value"],
            kwargs.get("expected_type", "string"),
            kwargs.get("valid_values"),
        )
    elif error_type == "ordering":
        return recovery.ordering_violation(
            kwargs["argument"],
            kwargs["command"],
            kwargs.get("mode", "strict"),
        )
    else:
        return f"Error: {error_type}"
