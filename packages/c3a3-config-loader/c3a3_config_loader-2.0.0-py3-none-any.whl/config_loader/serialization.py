# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""
Configuration Loader - Serialization

Provides serialization utilities for ProcessingResult including
YAML support and sensitive value filtering.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Optional, Set, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .result import ProcessingResult


# Pattern for detecting obfuscated values
OBFUSCATED_PATTERN = re.compile(r"^obfuscated:[a-fA-F0-9]+$")


def filter_sensitive_values(
    data: Dict[str, Any],
    sensitive_keys: Optional[Set[str]] = None,
    replacement: str = "[REDACTED]",
) -> Dict[str, Any]:
    """Filter sensitive values from a dictionary.

    Removes or replaces values that appear to be sensitive based on:
    - Key names containing common sensitive patterns
    - Values matching the obfuscated format
    - Explicitly listed sensitive keys

    Args:
        data: The dictionary to filter.
        sensitive_keys: Optional set of key names to always filter.
        replacement: String to replace sensitive values with.

    Returns:
        New dictionary with sensitive values replaced.
    """
    # Common patterns for sensitive key names
    sensitive_patterns = {
        "password",
        "secret",
        "token",
        "key",
        "api_key",
        "apikey",
        "auth",
        "credential",
        "private",
    }

    def is_sensitive_key(key: str) -> bool:
        key_lower = key.lower()
        if sensitive_keys and key_lower in sensitive_keys:
            return True
        return any(pattern in key_lower for pattern in sensitive_patterns)

    def is_obfuscated_value(value: Any) -> bool:
        if isinstance(value, str):
            return bool(OBFUSCATED_PATTERN.match(value))
        return False

    def filter_recursive(obj: Any, parent_key: str = "") -> Any:
        if isinstance(obj, dict):
            result = {}
            for key, value in obj.items():
                full_key = f"{parent_key}.{key}" if parent_key else key
                if is_sensitive_key(key) or is_obfuscated_value(value):
                    result[key] = replacement
                else:
                    result[key] = filter_recursive(value, full_key)
            return result
        elif isinstance(obj, list):
            return [filter_recursive(item, parent_key) for item in obj]
        else:
            return obj

    return cast(Dict[str, Any], filter_recursive(data))


def to_yaml(result: "ProcessingResult", filter_sensitive: bool = False) -> str:
    """Serialize ProcessingResult to YAML format.

    Args:
        result: The ProcessingResult to serialize.
        filter_sensitive: If True, filter sensitive values.

    Returns:
        YAML string representation.

    Raises:
        ImportError: If PyYAML is not installed.
    """
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        raise ImportError(
            "PyYAML is required for YAML serialization. "
            "Install it with: pip install pyyaml"
        )

    data = result.to_dict()
    if filter_sensitive:
        data = filter_sensitive_values(data)

    yaml_str: str = yaml.dump(data, default_flow_style=False, sort_keys=False)
    return yaml_str


def from_yaml(yaml_str: str) -> Dict[str, Any]:
    """Parse a YAML string to a dictionary.

    The result can be passed to ProcessingResult.from_dict().

    Args:
        yaml_str: The YAML string to parse.

    Returns:
        Parsed dictionary.

    Raises:
        ImportError: If PyYAML is not installed.
    """
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required for YAML deserialization. "
            "Install it with: pip install pyyaml"
        )

    result: Dict[str, Any] = yaml.safe_load(yaml_str)
    return result


def to_json_safe(
    result: "ProcessingResult",
    indent: int = 2,
    filter_sensitive: bool = True,
) -> str:
    """Serialize ProcessingResult to JSON with sensitive values filtered.

    This is a safer version of to_json() for logging and debugging.

    Args:
        result: The ProcessingResult to serialize.
        indent: JSON indentation level.
        filter_sensitive: If True (default), filter sensitive values.

    Returns:
        JSON string with sensitive values replaced.
    """
    import json

    data = result.to_dict()
    if filter_sensitive:
        data = filter_sensitive_values(data)

    return json.dumps(data, indent=indent)


def replay_from_dict(
    data: Dict[str, Any],
    validator: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> "ProcessingResult":
    """Replay a saved ProcessingResult from a dictionary.

    Useful for debugging or testing by replaying a saved execution state.

    Args:
        data: The dictionary representation (from to_dict() or YAML/JSON).
        validator: Optional callback to validate the data before replay.

    Returns:
        Reconstructed ProcessingResult.

    Raises:
        ValueError: If the data is invalid or validation fails.
    """
    from .result import ProcessingResult

    if validator:
        validator(data)

    # Check schema version compatibility
    schema_version = data.get("schema_version", "1.0")
    if schema_version not in ("1.0", "2.0"):
        raise ValueError(f"Unsupported schema version: {schema_version}")

    return ProcessingResult.from_dict(data)


def create_replay_file(
    result: "ProcessingResult",
    filepath: str,
    format: str = "json",
    filter_sensitive: bool = True,
) -> None:
    """Save ProcessingResult to a file for later replay.

    Args:
        result: The ProcessingResult to save.
        filepath: Path to save to.
        format: Output format ("json" or "yaml").
        filter_sensitive: If True (default), filter sensitive values.

    Raises:
        ValueError: If format is not supported.
        ImportError: If YAML format requested but PyYAML not installed.
    """
    if format == "json":
        content = to_json_safe(result, filter_sensitive=filter_sensitive)
    elif format == "yaml":
        if filter_sensitive:
            data = filter_sensitive_values(result.to_dict())
            try:
                import yaml

                content = str(yaml.dump(data, default_flow_style=False, sort_keys=False))
            except ImportError:
                raise ImportError(
                    "PyYAML is required for YAML serialization. "
                    "Install it with: pip install pyyaml"
                )
        else:
            content = to_yaml(result, filter_sensitive=False)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'json' or 'yaml'.")

    with open(filepath, "w") as f:
        f.write(content)


def load_replay_file(filepath: str) -> "ProcessingResult":
    """Load a ProcessingResult from a replay file.

    Automatically detects format based on file extension.

    Args:
        filepath: Path to the replay file.

    Returns:
        Reconstructed ProcessingResult.

    Raises:
        ValueError: If file extension is not recognized.
        ImportError: If YAML file but PyYAML not installed.
    """
    if filepath.endswith(".yaml") or filepath.endswith(".yml"):
        with open(filepath) as f:
            data = from_yaml(f.read())
    elif filepath.endswith(".json"):
        import json

        with open(filepath) as f:
            data = json.load(f)
    else:
        raise ValueError(
            f"Cannot determine format for {filepath}. "
            "Use .json, .yaml, or .yml extension."
        )

    return replay_from_dict(data)


class SerializationContext:
    """Context manager for serialization with custom options.

    Allows configuring serialization behavior across multiple operations.

    Example:
        ctx = SerializationContext(filter_sensitive=True, additional_sensitive={"my_key"})
        safe_json = ctx.to_json(result)
        ctx.save(result, "debug.json")
    """

    def __init__(
        self,
        filter_sensitive: bool = True,
        additional_sensitive: Optional[Set[str]] = None,
        replacement: str = "[REDACTED]",
    ) -> None:
        self.filter_sensitive = filter_sensitive
        self.sensitive_keys = additional_sensitive or set()
        self.replacement = replacement

    def _filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.filter_sensitive:
            return filter_sensitive_values(
                data,
                sensitive_keys=self.sensitive_keys,
                replacement=self.replacement,
            )
        return data

    def to_dict(self, result: "ProcessingResult") -> Dict[str, Any]:
        """Export to dictionary with configured filtering."""
        return self._filter(result.to_dict())

    def to_json(self, result: "ProcessingResult", indent: int = 2) -> str:
        """Export to JSON with configured filtering."""
        import json

        return json.dumps(self.to_dict(result), indent=indent)

    def to_yaml(self, result: "ProcessingResult") -> str:
        """Export to YAML with configured filtering."""
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required for YAML serialization. "
                "Install it with: pip install pyyaml"
            )

        yaml_str: str = yaml.dump(self.to_dict(result), default_flow_style=False, sort_keys=False)
        return yaml_str

    def save(
        self,
        result: "ProcessingResult",
        filepath: str,
        format: Optional[str] = None,
    ) -> None:
        """Save to file with configured filtering.

        Args:
            result: The ProcessingResult to save.
            filepath: Path to save to.
            format: Format to use. If None, determined from extension.
        """
        if format is None:
            if filepath.endswith(".yaml") or filepath.endswith(".yml"):
                format = "yaml"
            else:
                format = "json"

        if format == "yaml":
            content = self.to_yaml(result)
        else:
            content = self.to_json(result)

        with open(filepath, "w") as f:
            f.write(content)
