# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""Test suite for v2.0 command system.

Tests command tree parsing, alias resolution, command validation,
and hierarchical command structure.

Run with:
    pytest tests/test_commands.py -v
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest
from config_loader import (
    Command,
    Configuration,
    ProcessingResult,
)
from config_loader.tokenizer import Tokenizer, TokenType


# ============================================================================
# Helper Functions
# ============================================================================


def _make_v2_spec(
    commands: List[Dict[str, Any]],
    parameters: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Create a v2.0 spec with commands."""
    return {
        "schema_version": "2.0",
        "app_name": "testapp",
        "parameters": parameters or [],
        "commands": commands,
    }


def _parse_commands(commands_spec: List[Dict[str, Any]]) -> List[Command]:
    """Parse command specs into Command objects."""
    from config_loader.main import Configuration

    spec = _make_v2_spec(commands_spec)
    cfg = Configuration(spec)
    return cfg.commands


# ============================================================================
# Tokenizer Tests
# ============================================================================


class TestTokenizer:
    """Tests for token classification."""

    def test_long_option_with_equals(self) -> None:
        """Test --name=value tokenization."""
        commands = _parse_commands([{"name": "deploy", "terminal": True}])
        tokenizer = Tokenizer(commands)
        tokens = tokenizer.tokenize(["--host=localhost"])

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LONG_OPTION
        assert tokens[0].value == "host"
        assert tokens[0].option_value == "localhost"

    def test_long_option_without_value(self) -> None:
        """Test --name tokenization."""
        commands = _parse_commands([{"name": "deploy", "terminal": True}])
        tokenizer = Tokenizer(commands)
        tokens = tokenizer.tokenize(["--verbose"])

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LONG_OPTION
        assert tokens[0].value == "verbose"

    def test_short_option(self) -> None:
        """Test -x tokenization."""
        commands = _parse_commands([{"name": "deploy", "terminal": True}])
        tokenizer = Tokenizer(commands)
        tokens = tokenizer.tokenize(["-v"])

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.SHORT_OPTION
        assert tokens[0].value == "v"

    def test_short_option_cluster(self) -> None:
        """Test -xyz stores flags in short_flags."""
        commands = _parse_commands([{"name": "deploy", "terminal": True}])
        tokenizer = Tokenizer(commands)
        tokens = tokenizer.tokenize(["-abc"])

        # Bundled flags stored in single token with short_flags
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.SHORT_OPTION
        assert tokens[0].value == "a"  # First flag
        assert tokens[0].short_flags == ["a", "b", "c"]

    def test_options_end_marker(self) -> None:
        """Test -- marker ends option parsing."""
        commands = _parse_commands([{"name": "run", "terminal": True}])
        tokenizer = Tokenizer(commands)
        tokens = tokenizer.tokenize(["--", "--not-an-option"])

        assert len(tokens) == 2
        assert tokens[0].type == TokenType.OPTIONS_END
        assert tokens[1].type == TokenType.POSITIONAL
        assert tokens[1].value == "--not-an-option"

    def test_command_token(self) -> None:
        """Test command name recognition."""
        commands = _parse_commands([{"name": "deploy", "terminal": True}])
        tokenizer = Tokenizer(commands)
        tokens = tokenizer.tokenize(["deploy"])

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.COMMAND
        assert tokens[0].value == "deploy"

    def test_alias_recognized_as_command(self) -> None:
        """Test alias recognized as command."""
        commands = _parse_commands(
            [{"name": "deploy", "aliases": ["d"], "terminal": True}]
        )
        tokenizer = Tokenizer(commands)
        tokens = tokenizer.tokenize(["d"])

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.COMMAND
        assert tokens[0].value == "d"

    def test_positional_argument(self) -> None:
        """Test non-command, non-option as positional."""
        commands = _parse_commands([{"name": "deploy", "terminal": True}])
        tokenizer = Tokenizer(commands)
        tokens = tokenizer.tokenize(["myfile.txt"])

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.POSITIONAL
        assert tokens[0].value == "myfile.txt"


# ============================================================================
# Command Validator Tests
# ============================================================================


class TestCommandValidator:
    """Tests for command tree validation."""

    def test_valid_command_tree(self) -> None:
        """Test validation passes for valid command tree."""
        spec = _make_v2_spec(
            [
                {
                    "name": "deploy",
                    "terminal": True,
                    "arguments": [{"name": "region", "type": "string"}],
                }
            ]
        )
        cfg = Configuration(spec)
        # If no exception, validation passed
        assert len(cfg.commands) == 1

    def test_invalid_command_name_with_dots(self) -> None:
        """Test command name with dots rejected."""
        spec = _make_v2_spec([{"name": "deploy.staging", "terminal": True}])

        with pytest.raises(ValueError, match="Invalid name|contains a dot"):
            Configuration(spec)

    def test_invalid_command_name_with_spaces(self) -> None:
        """Test command name with spaces rejected."""
        spec = _make_v2_spec([{"name": "deploy staging", "terminal": True}])

        with pytest.raises(ValueError, match="Invalid name"):
            Configuration(spec)

    def test_duplicate_alias_rejected(self) -> None:
        """Test duplicate aliases at same level rejected."""
        spec = _make_v2_spec(
            [
                {"name": "deploy", "aliases": ["d"], "terminal": True},
                {"name": "destroy", "aliases": ["d"], "terminal": True},
            ]
        )

        with pytest.raises(ValueError, match="conflicts with"):
            Configuration(spec)

    def test_alias_shadows_command_name(self) -> None:
        """Test alias that shadows command name rejected."""
        spec = _make_v2_spec(
            [
                {"name": "deploy", "terminal": True},
                {"name": "destroy", "aliases": ["deploy"], "terminal": True},
            ]
        )

        with pytest.raises(ValueError, match="conflicts with"):
            Configuration(spec)


# ============================================================================
# Command Parser Tests
# ============================================================================


class TestCommandParser:
    """Tests for three-phase command parsing."""

    def test_simple_command_resolution(self) -> None:
        """Test basic command is resolved."""
        spec = _make_v2_spec([{"name": "deploy", "terminal": True}])
        cfg = Configuration(spec)

        result = cfg.process(["deploy"])

        assert isinstance(result, ProcessingResult)
        assert result.command is not None
        assert result.command.path == ["deploy"]
        assert result.command.terminal is True

    def test_nested_command_resolution(self) -> None:
        """Test nested subcommand resolution."""
        spec = _make_v2_spec(
            [
                {
                    "name": "deploy",
                    "subcommands": [
                        {"name": "staging", "terminal": True},
                        {"name": "production", "terminal": True},
                    ],
                }
            ]
        )
        cfg = Configuration(spec)

        result = cfg.process(["deploy", "staging"])

        assert result.command is not None
        assert result.command.path == ["deploy", "staging"]
        assert result.command.terminal is True

    def test_alias_resolution(self) -> None:
        """Test command resolved via alias."""
        spec = _make_v2_spec(
            [{"name": "deploy", "aliases": ["d", "dep"], "terminal": True}]
        )
        cfg = Configuration(spec)

        result = cfg.process(["d"])

        assert result.command is not None
        assert result.command.path == ["deploy"]  # Resolved to canonical name

    def test_command_with_arguments(self) -> None:
        """Test command arguments are bound."""
        spec = _make_v2_spec(
            [
                {
                    "name": "deploy",
                    "terminal": True,
                    "arguments": [
                        {"name": "region", "type": "string", "required": True},
                        {"name": "dry-run", "type": "boolean", "default": False},
                    ],
                }
            ]
        )
        cfg = Configuration(spec)

        result = cfg.process(["deploy", "--region", "us-east-1", "--dry-run"])

        assert result.command is not None
        assert result.command.arguments["region"] == "us-east-1"
        assert result.command.arguments["dry-run"] is True

    def test_command_short_flags(self) -> None:
        """Test short flag -r maps to --region."""
        spec = _make_v2_spec(
            [
                {
                    "name": "deploy",
                    "terminal": True,
                    "arguments": [
                        {"name": "region", "short": "r", "type": "string"},
                    ],
                }
            ]
        )
        cfg = Configuration(spec)

        result = cfg.process(["deploy", "-r", "us-west-2"])

        assert result.command is not None
        assert result.command.arguments["region"] == "us-west-2"

    def test_global_params_with_commands(self) -> None:
        """Test global parameters extracted before command."""
        spec = _make_v2_spec(
            [{"name": "deploy", "terminal": True}],
            parameters=[
                {"namespace": "db", "name": "host", "type": "string", "default": "localhost"}
            ],
        )
        cfg = Configuration(spec)

        result = cfg.process(["--db.host", "myhost", "deploy"])

        assert result.command is not None
        assert result.command.path == ["deploy"]
        assert result._config["db"]["host"] == "myhost"

    def test_positional_arguments(self) -> None:
        """Test positional arguments after command."""
        spec = _make_v2_spec([{"name": "run", "terminal": True}])
        cfg = Configuration(spec)

        result = cfg.process(["run", "--", "script.py", "arg1"])

        assert result.command is not None
        assert result.command.positional == ["script.py", "arg1"]

    def test_unknown_command_error(self) -> None:
        """Test error for unknown command."""
        spec = _make_v2_spec([{"name": "deploy", "terminal": True}])
        cfg = Configuration(spec)

        with pytest.raises(ValueError, match="Unknown command"):
            cfg.process(["unknown"])

    def test_non_terminal_command_returns_non_terminal(self) -> None:
        """Test stopping at non-terminal command returns terminal=False.

        The parser allows stopping at non-terminal commands, returning
        terminal=False so the caller can decide how to handle it
        (e.g., show help, or use validate_terminal() to raise).
        """
        spec = _make_v2_spec(
            [
                {
                    "name": "deploy",
                    "terminal": False,
                    "subcommands": [{"name": "staging", "terminal": True}],
                }
            ]
        )
        cfg = Configuration(spec)

        result = cfg.process(["deploy"])

        assert result.command is not None
        assert result.command.path == ["deploy"]
        assert result.command.terminal is False


# ============================================================================
# Argument Inheritance Tests
# ============================================================================


class TestArgumentInheritance:
    """Tests for command argument scoping and inheritance."""

    def test_inherited_argument_available_in_subcommand(self) -> None:
        """Test inherited argument visible in subcommand."""
        spec = _make_v2_spec(
            [
                {
                    "name": "deploy",
                    "arguments": [
                        {"name": "region", "type": "string", "scope": "inherited"}
                    ],
                    "subcommands": [{"name": "staging", "terminal": True}],
                }
            ]
        )
        cfg = Configuration(spec)

        result = cfg.process(["deploy", "staging", "--region", "eu-west-1"])

        assert result.command is not None
        assert result.command.arguments["region"] == "eu-west-1"

    def test_local_argument_not_inherited(self) -> None:
        """Test local argument not available in subcommand."""
        spec = _make_v2_spec(
            [
                {
                    "name": "deploy",
                    "arguments": [
                        {"name": "verbose", "type": "boolean", "scope": "local"}
                    ],
                    "subcommands": [{"name": "staging", "terminal": True}],
                }
            ]
        )
        cfg = Configuration(spec)

        # --verbose should not be recognized for staging
        with pytest.raises(ValueError, match="Unknown argument"):
            cfg.process(["deploy", "staging", "--verbose"])

    def test_child_overrides_inherited(self) -> None:
        """Test child can override inherited argument."""
        spec = _make_v2_spec(
            [
                {
                    "name": "deploy",
                    "arguments": [
                        {
                            "name": "timeout",
                            "type": "number",
                            "scope": "inherited",
                            "default": 30,
                        }
                    ],
                    "subcommands": [
                        {
                            "name": "staging",
                            "terminal": True,
                            "arguments": [
                                {"name": "timeout", "type": "number", "default": 60}
                            ],
                        }
                    ],
                }
            ]
        )
        cfg = Configuration(spec)

        # Child default should override parent
        result = cfg.process(["deploy", "staging"])

        assert result.command is not None
        assert result.command.arguments["timeout"] == 60


# ============================================================================
# Ordering Mode Tests
# ============================================================================


class TestOrderingModes:
    """Tests for argument ordering enforcement."""

    def test_relaxed_ordering_accepts_args_before_command(self) -> None:
        """Test relaxed mode accepts arguments anywhere."""
        spec = _make_v2_spec(
            [
                {
                    "name": "deploy",
                    "terminal": True,
                    "ordering": "relaxed",
                    "arguments": [{"name": "region", "type": "string"}],
                }
            ]
        )
        cfg = Configuration(spec)

        # Should work: args before command in relaxed mode
        result = cfg.process(["--region", "us-east-1", "deploy"])

        assert result.command is not None
        # In relaxed mode, --region before deploy should still be bound

    def test_strict_ordering_rejects_args_before_command(self) -> None:
        """Test strict mode rejects arguments before command."""
        spec = _make_v2_spec(
            [
                {
                    "name": "deploy",
                    "terminal": True,
                    "ordering": "strict",
                    "arguments": [{"name": "region", "type": "string"}],
                }
            ]
        )
        cfg = Configuration(spec)

        # In strict mode, --region must come after deploy
        with pytest.raises(ValueError, match="appears before command"):
            cfg.process(["--region", "us-east-1", "deploy"])


# ============================================================================
# ProcessingResult Tests
# ============================================================================


class TestProcessingResult:
    """Tests for ProcessingResult structure."""

    def test_result_to_dict(self) -> None:
        """Test ProcessingResult serializes to dict."""
        spec = _make_v2_spec(
            [
                {
                    "name": "deploy",
                    "terminal": True,
                    "arguments": [{"name": "region", "type": "string"}],
                }
            ]
        )
        cfg = Configuration(spec)
        result = cfg.process(["deploy", "--region", "us-east-1"])

        data = result.to_dict()

        assert data["schema_version"] == "2.0"
        assert "config" in data
        assert "command" in data
        assert data["command"]["path"] == ["deploy"]
        assert data["command"]["arguments"]["region"] == "us-east-1"

    def test_result_from_dict_roundtrip(self) -> None:
        """Test ProcessingResult round-trip through dict."""
        spec = _make_v2_spec([{"name": "deploy", "terminal": True}])
        cfg = Configuration(spec)
        result = cfg.process(["deploy"])

        data = result.to_dict()
        restored = ProcessingResult.from_dict(data)

        assert restored.command is not None
        assert restored.command.path == ["deploy"]

    def test_backward_compat_config_access(self) -> None:
        """Test existing code patterns still work."""
        spec = _make_v2_spec(
            [{"name": "deploy", "terminal": True}],
            parameters=[{"namespace": "db", "name": "host", "type": "string", "default": "localhost"}],
        )
        cfg = Configuration(spec)
        result = cfg.process(["deploy"])

        # Old-style access should still work
        assert result._config["db"]["host"] == "localhost"
        assert result.db.host == "localhost"


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_command_list(self) -> None:
        """Test spec with no commands behaves as v1.x."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "parameters": [
                {"namespace": "db", "name": "host", "type": "string", "default": "localhost"}
            ],
            "commands": [],
        }
        cfg = Configuration(spec)

        result = cfg.process([])

        assert result.command is None
        assert result._config["db"]["host"] == "localhost"

    def test_command_with_no_args(self) -> None:
        """Test command with no arguments defined."""
        spec = _make_v2_spec([{"name": "status", "terminal": True}])
        cfg = Configuration(spec)

        result = cfg.process(["status"])

        assert result.command is not None
        assert result.command.arguments == {}

    def test_deeply_nested_commands(self) -> None:
        """Test deeply nested command hierarchy."""
        spec = _make_v2_spec(
            [
                {
                    "name": "level1",
                    "subcommands": [
                        {
                            "name": "level2",
                            "subcommands": [
                                {
                                    "name": "level3",
                                    "subcommands": [{"name": "level4", "terminal": True}],
                                }
                            ],
                        }
                    ],
                }
            ]
        )
        cfg = Configuration(spec)

        result = cfg.process(["level1", "level2", "level3", "level4"])

        assert result.command is not None
        assert result.command.path == ["level1", "level2", "level3", "level4"]

    def test_boolean_argument_defaults(self) -> None:
        """Test boolean argument default values."""
        spec = _make_v2_spec(
            [
                {
                    "name": "run",
                    "terminal": True,
                    "arguments": [
                        {"name": "verbose", "type": "boolean", "default": False},
                        {"name": "quiet", "type": "boolean"},
                    ],
                }
            ]
        )
        cfg = Configuration(spec)

        result = cfg.process(["run"])

        assert result.command is not None
        assert result.command.arguments.get("verbose") is False
        assert result.command.arguments.get("quiet") is None

    def test_number_argument_parsing(self) -> None:
        """Test number argument type coercion."""
        spec = _make_v2_spec(
            [
                {
                    "name": "scale",
                    "terminal": True,
                    "arguments": [
                        {"name": "replicas", "type": "number", "required": True}
                    ],
                }
            ]
        )
        cfg = Configuration(spec)

        result = cfg.process(["scale", "--replicas", "5"])

        assert result.command is not None
        assert result.command.arguments["replicas"] == 5
        assert isinstance(result.command.arguments["replicas"], int)
