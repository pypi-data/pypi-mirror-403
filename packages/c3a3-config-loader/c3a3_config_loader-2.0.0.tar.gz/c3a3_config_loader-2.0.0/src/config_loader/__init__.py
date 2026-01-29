# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""
Configuration Loader Package

A seamless configuration loading system that supports:
- Command line arguments
- Environment variables
- RC files (TOML format)
- Configurable precedence
- Type validation and restrictions
- AES256 obfuscation for sensitive values
- Plugin system for protocol-based value loading
- Hierarchical command system (v2.0)
"""

from .main import Configuration, load_config, load_configs
from .models import (
    ConfigParam,
    ConfigArg,
    # v2.0 command system
    Command,
    CommandArgument,
    ExclusionGroup,
    DependencyRule,
    Deprecation,
)
from .plugin_interface import ConfigPlugin, PluginManifest
from .result import ConfigurationResult, ProcessingResult, CommandContext
from .callable_validators import ValidatorError, ValidatorContext
from .deprecation import DeprecationError, DeprecationConfig, DeprecationTracker
from .error_recovery import ErrorRecovery, ErrorRecoveryConfig
from .serialization import (
    SerializationContext,
    filter_sensitive_values,
    to_yaml,
    to_json_safe,
    create_replay_file,
    load_replay_file,
)
from .builder import (
    CommandBuilder,
    ArgumentValueBuilder,
    Suggestions,
    ValueSuggestions,
    ArgumentSuggestion,
    CommandSuggestion,
)

__version__ = "2.0.0"
__all__ = [
    # Core
    "Configuration",
    "ConfigParam",
    "ConfigArg",
    "ConfigurationResult",
    "ConfigPlugin",
    "PluginManifest",
    "load_config",
    "load_configs",
    # v2.0 Command System
    "Command",
    "CommandArgument",
    "ExclusionGroup",
    "DependencyRule",
    "Deprecation",
    "ProcessingResult",
    "CommandContext",
    # Validation
    "ValidatorError",
    "ValidatorContext",
    # Deprecation
    "DeprecationError",
    "DeprecationConfig",
    "DeprecationTracker",
    # Error Recovery
    "ErrorRecovery",
    "ErrorRecoveryConfig",
    # Serialization
    "SerializationContext",
    "filter_sensitive_values",
    "to_yaml",
    "to_json_safe",
    "create_replay_file",
    "load_replay_file",
    # Builder Pattern
    "CommandBuilder",
    "ArgumentValueBuilder",
    "Suggestions",
    "ValueSuggestions",
    "ArgumentSuggestion",
    "CommandSuggestion",
]
