# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""
Configuration Loader - Deprecation Handling

Provides deprecation warnings and error handling for deprecated
commands, arguments, and parameters.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from .models import Deprecation


class DeprecationError(ValueError):
    """Raised when a deprecated item is used in strict mode."""

    def __init__(
        self,
        message: str,
        item_type: str,
        item_name: str,
        deprecation: Deprecation,
    ) -> None:
        self.item_type = item_type
        self.item_name = item_name
        self.deprecation = deprecation
        super().__init__(message)


@dataclass
class DeprecationConfig:
    """Configuration for deprecation handling.

    Attributes:
        strict: If True, deprecated items cause errors instead of warnings.
    """

    strict: bool = False

    @classmethod
    def from_spec(cls, spec: Optional[Dict[str, Any]]) -> DeprecationConfig:
        """Create config from spec's deprecation field."""
        if not spec:
            return cls()
        return cls(strict=spec.get("strict", False))


class DeprecationTracker:
    """Tracks and emits deprecation warnings.

    Ensures each deprecation warning is only emitted once per session
    and supports both warning and strict (error) modes.
    """

    def __init__(self, config: Optional[DeprecationConfig] = None) -> None:
        self.config = config or DeprecationConfig()
        self._emitted: Set[str] = set()
        self._warnings: List[str] = []

    def check_command(
        self,
        command_name: str,
        command_path: List[str],
        deprecation: Optional[Deprecation],
    ) -> None:
        """Check if a command is deprecated and handle accordingly.

        Args:
            command_name: The command name.
            command_path: The full command path.
            deprecation: Deprecation metadata if deprecated.

        Raises:
            DeprecationError: In strict mode when command is deprecated.
        """
        if not deprecation:
            return

        path_str = " ".join(command_path) if command_path else command_name
        key = f"command:{path_str}"

        if key in self._emitted:
            return

        message = self._format_message(
            item_type="Command",
            item_name=path_str,
            deprecation=deprecation,
        )

        self._handle_deprecation(key, message, "command", path_str, deprecation)

    def check_argument(
        self,
        argument_name: str,
        command_path: List[str],
        deprecation: Optional[Deprecation],
    ) -> None:
        """Check if an argument is deprecated and handle accordingly.

        Args:
            argument_name: The argument name.
            command_path: The command path where argument is used.
            deprecation: Deprecation metadata if deprecated.

        Raises:
            DeprecationError: In strict mode when argument is deprecated.
        """
        if not deprecation:
            return

        path_str = " ".join(command_path) if command_path else "(global)"
        key = f"argument:{path_str}:{argument_name}"

        if key in self._emitted:
            return

        full_name = f"--{argument_name} (in '{path_str}')"
        message = self._format_message(
            item_type="Argument",
            item_name=full_name,
            deprecation=deprecation,
        )

        self._handle_deprecation(key, message, "argument", argument_name, deprecation)

    def check_parameter(
        self,
        namespace: Optional[str],
        name: str,
        deprecation: Optional[Deprecation],
    ) -> None:
        """Check if a parameter is deprecated and handle accordingly.

        Args:
            namespace: The parameter namespace.
            name: The parameter name.
            deprecation: Deprecation metadata if deprecated.

        Raises:
            DeprecationError: In strict mode when parameter is deprecated.
        """
        if not deprecation:
            return

        full_name = f"{namespace}.{name}" if namespace else name
        key = f"parameter:{full_name}"

        if key in self._emitted:
            return

        message = self._format_message(
            item_type="Parameter",
            item_name=f"--{full_name}",
            deprecation=deprecation,
        )

        self._handle_deprecation(key, message, "parameter", full_name, deprecation)

    def _format_message(
        self,
        item_type: str,
        item_name: str,
        deprecation: Deprecation,
    ) -> str:
        """Format a deprecation message.

        Args:
            item_type: Type of item (Command, Argument, Parameter).
            item_name: Name of the deprecated item.
            deprecation: Deprecation metadata.

        Returns:
            Formatted deprecation message.
        """
        parts: List[str] = []

        # Use custom message if provided
        if deprecation.message:
            parts.append(deprecation.message)
        else:
            parts.append(f"{item_type} '{item_name}' is deprecated")

            if deprecation.since:
                parts.append(f" since v{deprecation.since}")

        # Add removal notice
        if deprecation.removed_in:
            parts.append(f". Will be removed in v{deprecation.removed_in}")

        # Add replacement suggestion
        if deprecation.replacement:
            parts.append(f". Use '{deprecation.replacement}' instead")

        message = "".join(parts)
        if not message.endswith("."):
            message += "."

        return message

    def _handle_deprecation(
        self,
        key: str,
        message: str,
        item_type: str,
        item_name: str,
        deprecation: Deprecation,
    ) -> None:
        """Handle a deprecation warning or error.

        Args:
            key: Unique key for tracking emitted warnings.
            message: The formatted message.
            item_type: Type of deprecated item.
            item_name: Name of deprecated item.
            deprecation: Deprecation metadata.

        Raises:
            DeprecationError: In strict mode.
        """
        self._emitted.add(key)
        self._warnings.append(message)

        if self.config.strict:
            raise DeprecationError(message, item_type, item_name, deprecation)
        else:
            print(f"DeprecationWarning: {message}", file=sys.stderr)

    def get_warnings(self) -> List[str]:
        """Get list of all deprecation warnings emitted."""
        return self._warnings.copy()

    def clear(self) -> None:
        """Clear emitted warnings tracking."""
        self._emitted.clear()
        self._warnings.clear()


def format_deprecated_help(
    name: str,
    deprecation: Deprecation,
    *,
    prefix: str = "",
) -> str:
    """Format an item for help output with deprecation marker.

    Args:
        name: The item name to display.
        deprecation: Deprecation metadata.
        prefix: Optional prefix (e.g., "  " for indentation).

    Returns:
        Formatted string with [DEPRECATED] marker.
    """
    parts = [prefix, name, " [DEPRECATED]"]

    if deprecation.replacement:
        parts.append(f" -> use '{deprecation.replacement}'")

    if deprecation.removed_in:
        parts.append(f" (removed in v{deprecation.removed_in})")

    return "".join(parts)


def check_deprecation(
    item: Any,
    item_type: str,
    item_name: str,
    tracker: DeprecationTracker,
    command_path: Optional[List[str]] = None,
) -> None:
    """Convenience function to check deprecation on any item.

    Args:
        item: The item to check (must have .deprecated attribute or be None).
        item_type: Type of item ("command", "argument", "parameter").
        item_name: Name of the item.
        tracker: The deprecation tracker.
        command_path: Command path for context.
    """
    deprecation = getattr(item, "deprecated", None)
    if not deprecation:
        return

    if item_type == "command":
        tracker.check_command(item_name, command_path or [], deprecation)
    elif item_type == "argument":
        tracker.check_argument(item_name, command_path or [], deprecation)
    elif item_type == "parameter":
        # For parameters, item_name should be "namespace.name" or just "name"
        if "." in item_name:
            ns, name = item_name.split(".", 1)
            tracker.check_parameter(ns, name, deprecation)
        else:
            tracker.check_parameter(None, item_name, deprecation)
