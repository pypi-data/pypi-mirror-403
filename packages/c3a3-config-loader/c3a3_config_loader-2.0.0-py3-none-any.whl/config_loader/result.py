# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""
Configuration Loader - Result Object

Contains processed configuration values with convenient access methods.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, cast


class ConfigurationResult:
    """Result object containing processed configuration values."""

    def __init__(self, config_dict: Dict[str, Any], debug_info: Dict[str, str]):
        self._config = config_dict
        self._debug_info = debug_info

        # Create namespace objects dynamically
        for namespace, values in config_dict.items():
            if not hasattr(self, namespace):
                setattr(self, namespace, type("ConfigNamespace", (), values)())

    def export_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return self._config.copy()

    def export_json(self) -> str:
        """Export configuration as JSON string."""
        return json.dumps(self._config, indent=2)

    def debug(self) -> None:
        """Print debug information about configuration sources."""
        print("Configuration Debug Information:")
        print("=" * 40)
        for key, source in self._debug_info.items():
            value = self._get_nested_value(key)
            print(f"{key}: {value} (from {source})")

    def _get_nested_value(self, key: str) -> Any:
        """Get nested value using dot notation."""
        parts = key.split(".")
        value = self._config
        for part in parts:
            value = value.get(part, {})
        return value


# ============================================================================
# v2.0 Command Context and Processing Result
# ============================================================================


@dataclass
class CommandContext:
    """Result of command path resolution.

    Represents the parsed command context after three-phase parsing.

    Attributes:
        path: The resolved command path (e.g., ["deploy", "staging"]).
        arguments: Command-specific arguments bound during parsing.
        positional: Positional arguments following the command.
        terminal: Whether the resolved command is terminal (executable).
    """

    path: List[str] = field(default_factory=list)
    arguments: Dict[str, Any] = field(default_factory=dict)
    positional: List[Any] = field(default_factory=list)
    terminal: bool = False


class ProcessingResult:
    """Combined result with config and command context.

    This is the primary result type for v2.0 specs. It wraps the
    ConfigurationResult and optionally includes CommandContext.

    For backward compatibility, attribute access is delegated to the
    underlying ConfigurationResult, so existing code like
    `result.db.host` continues to work.

    Attributes:
        config: The processed configuration parameters.
        command: The resolved command context (None if no commands in spec).
    """

    def __init__(
        self,
        config: ConfigurationResult,
        command: Optional[CommandContext] = None,
        *,
        warnings: Optional[List[str]] = None,
        sources: Optional[Dict[str, str]] = None,
    ):
        # Store the ConfigurationResult internally with different name
        # to avoid conflict with _config property for backward compat
        object.__setattr__(self, "_config_result", config)
        object.__setattr__(self, "_command", command)
        object.__setattr__(self, "_warnings", warnings or [])
        object.__setattr__(self, "_sources", sources or {})

    @property
    def _config(self) -> Dict[str, Any]:
        """Backward compatibility: access the config dict directly.

        This allows existing code that does `result._config["namespace"]["key"]`
        to continue working.
        """
        config_result = cast(ConfigurationResult, object.__getattribute__(self, "_config_result"))
        return config_result._config

    @property
    def _debug_info(self) -> Dict[str, str]:
        """Backward compatibility: access debug info dict."""
        config_result = cast(ConfigurationResult, object.__getattribute__(self, "_config_result"))
        return config_result._debug_info

    @property
    def config(self) -> ConfigurationResult:
        """Access the configuration result."""
        return cast(ConfigurationResult, object.__getattribute__(self, "_config_result"))

    @property
    def command(self) -> Optional[CommandContext]:
        """Access the command context (None if no commands)."""
        return cast(Optional[CommandContext], object.__getattribute__(self, "_command"))

    @property
    def warnings(self) -> List[str]:
        """Access any warnings (e.g., deprecation warnings)."""
        return cast(List[str], object.__getattribute__(self, "_warnings"))

    @property
    def sources(self) -> Dict[str, str]:
        """Map of parameter/argument names to their sources."""
        return cast(Dict[str, str], object.__getattribute__(self, "_sources"))

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to ConfigurationResult for backward compat.

        This allows `result.db.host` to work as it did with ConfigurationResult.
        """
        # Avoid infinite recursion - check internal attributes
        if name in ("_config_result", "_command", "_warnings", "_sources"):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
        return getattr(self._config_result, name)

    def to_dict(self) -> Dict[str, Any]:
        """Export result as a dictionary.

        Suitable for JSON serialization, logging, or replay.
        """
        result: Dict[str, Any] = {
            "schema_version": "2.0",
            "config": self._config_result.export_dict(),
        }

        if self._command is not None:
            result["command"] = {
                "path": self._command.path,
                "arguments": self._command.arguments,
                "positional": self._command.positional,
                "terminal": self._command.terminal,
            }

        if self._sources:
            result["sources"] = self._sources

        if self._warnings:
            result["warnings"] = self._warnings

        return result

    def to_json(self, indent: int = 2) -> str:
        """Export result as JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProcessingResult:
        """Reconstruct a ProcessingResult from a dictionary.

        Useful for replaying saved execution state.
        """
        config_data = data.get("config", {})
        sources = data.get("sources", {})

        # Reconstruct ConfigurationResult
        config = ConfigurationResult(config_data, sources)

        # Reconstruct CommandContext if present
        command: Optional[CommandContext] = None
        if "command" in data:
            cmd_data = data["command"]
            command = CommandContext(
                path=cmd_data.get("path", []),
                arguments=cmd_data.get("arguments", {}),
                positional=cmd_data.get("positional", []),
                terminal=cmd_data.get("terminal", False),
            )

        return cls(
            config=config,
            command=command,
            warnings=data.get("warnings", []),
            sources=sources,
        )

    def debug(self) -> None:
        """Print debug information about configuration and command."""
        print("Processing Result Debug Information:")
        print("=" * 50)

        # Show configuration sources
        print("\nConfiguration Sources:")
        self._config_result.debug()

        # Show command context if present
        if self._command:
            print("\nCommand Context:")
            print(f"  Path: {' -> '.join(self._command.path) or '(none)'}")
            print(f"  Terminal: {self._command.terminal}")
            if self._command.arguments:
                print("  Arguments:")
                for name, value in self._command.arguments.items():
                    print(f"    {name}: {value}")
            if self._command.positional:
                print(f"  Positional: {self._command.positional}")

        # Show warnings if any
        if self._warnings:
            print("\nWarnings:")
            for warning in self._warnings:
                print(f"  - {warning}")
