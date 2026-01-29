# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""Tests for the CommandBuilder API.

The builder pattern allows incremental command construction with
suggestions at each step - useful for autocompletion, IDE integrations,
and interactive CLI wizards.
"""

from __future__ import annotations

import pytest
from typing import Any, Dict, List

from config_loader import (
    Configuration,
    CommandBuilder,
    ValueSuggestions,
)


# =============================================================================
# Helper Functions
# =============================================================================


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


def _make_config(commands: List[Dict[str, Any]]) -> Configuration:
    """Create a Configuration from a commands list."""
    spec = _make_v2_spec(commands)
    return Configuration(spec)


@pytest.fixture
def simple_commands() -> List[Dict[str, Any]]:
    """Simple commands with one terminal command."""
    return [
        {
            "name": "deploy",
            "terminal": True,
            "arguments": [
                {"name": "region", "type": "string", "required": True},
                {"name": "force", "type": "boolean", "short": "f"},
                {"name": "count", "type": "number", "default": 1},
            ],
        }
    ]


@pytest.fixture
def nested_commands() -> List[Dict[str, Any]]:
    """Commands with nested subcommands."""
    return [
        {
            "name": "db",
            "aliases": ["database"],
            "subcommands": [
                {
                    "name": "migrate",
                    "terminal": True,
                    "arguments": [
                        {"name": "target", "type": "string"},
                    ],
                },
                {
                    "name": "seed",
                    "terminal": True,
                },
            ],
        },
        {
            "name": "server",
            "terminal": True,
            "arguments": [
                {"name": "port", "type": "number", "short": "p"},
            ],
        },
    ]


@pytest.fixture
def value_provider_commands() -> List[Dict[str, Any]]:
    """Commands with value providers."""
    return [
        {
            "name": "deploy",
            "terminal": True,
            "arguments": [
                {
                    "name": "env",
                    "type": "string",
                    "values_from": "tests.test_builder.provide_environments",
                },
                {
                    "name": "region",
                    "type": "string",
                    "values_from": "tests.test_builder.provide_regions",
                },
            ],
        }
    ]


# Value provider functions for testing
def provide_environments(ctx: Any) -> List[str]:
    """Provide environment values for testing."""
    return ["development", "staging", "production"]


def provide_regions(ctx: Any) -> List[str]:
    """Provide region values based on parsed args."""
    # Demonstrate context-aware suggestions
    env = ctx.parsed_args.get("env") if ctx else None
    if env == "production":
        return ["us-east-1", "eu-west-1", "ap-southeast-1"]
    return ["us-east-1", "local"]


# =============================================================================
# Test: Builder Creation
# =============================================================================


class TestBuilderCreation:
    """Test builder instantiation."""

    def test_create_builder_from_config(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Configuration.builder() returns a CommandBuilder."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder()
        assert isinstance(builder, CommandBuilder)

    def test_builder_requires_commands(self) -> None:
        """Builder cannot be created without commands."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "parameters": [{"namespace": "db", "name": "host", "type": "string"}],
            "commands": [],
        }
        cfg = Configuration(spec)
        with pytest.raises(ValueError, match="requires commands"):
            cfg.builder()

    def test_builder_initial_state(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """New builder has empty state."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder()
        assert builder.command_path == []
        assert builder.arguments == {}
        assert builder.positional == []


# =============================================================================
# Test: check_next() Suggestions
# =============================================================================


class TestCheckNext:
    """Test the check_next() method for suggestions."""

    def test_root_level_shows_commands(
        self, nested_commands: List[Dict[str, Any]]
    ) -> None:
        """At root level, shows available top-level commands."""
        cfg = _make_config(nested_commands)
        builder = cfg.builder()
        suggestions = builder.check_next()

        assert not suggestions.is_valid
        assert len(suggestions.commands) == 2
        names = [c.name for c in suggestions.commands]
        assert "db" in names
        assert "server" in names

    def test_command_suggestion_includes_aliases(
        self, nested_commands: List[Dict[str, Any]]
    ) -> None:
        """Command suggestions include aliases."""
        cfg = _make_config(nested_commands)
        builder = cfg.builder()
        suggestions = builder.check_next()

        db_cmd = next(c for c in suggestions.commands if c.name == "db")
        assert "database" in db_cmd.aliases

    def test_command_suggestion_includes_terminal_flag(
        self, nested_commands: List[Dict[str, Any]]
    ) -> None:
        """Command suggestions indicate if terminal."""
        cfg = _make_config(nested_commands)
        builder = cfg.builder()
        suggestions = builder.check_next()

        db_cmd = next(c for c in suggestions.commands if c.name == "db")
        server_cmd = next(c for c in suggestions.commands if c.name == "server")
        assert not db_cmd.terminal
        assert server_cmd.terminal

    def test_terminal_command_is_valid(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Terminal command with all required args is valid."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy").add_argument("region", "us-east")
        suggestions = builder.check_next()

        assert suggestions.is_valid
        assert suggestions.errors == []

    def test_missing_required_arg_not_valid(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Terminal command missing required args is not valid."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy")
        suggestions = builder.check_next()

        assert not suggestions.is_valid
        assert any("region" in err for err in suggestions.errors)

    def test_shows_available_arguments(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """After command, shows available arguments."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy")
        suggestions = builder.check_next()

        assert len(suggestions.arguments) == 3
        names = [a.name for a in suggestions.arguments]
        assert "region" in names
        assert "force" in names
        assert "count" in names

    def test_argument_suggestion_details(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Argument suggestions include type and required info."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy")
        suggestions = builder.check_next()

        region = next(a for a in suggestions.arguments if a.name == "region")
        assert region.required is True
        assert region.arg_type == "string"
        assert region.expects_value is True

        force = next(a for a in suggestions.arguments if a.name == "force")
        assert force.required is False
        assert force.arg_type == "boolean"
        assert force.expects_value is False
        assert force.short == "f"

    def test_used_arguments_not_suggested(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Arguments already set are not suggested again."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy").add_argument("region", "us-east")
        suggestions = builder.check_next()

        names = [a.name for a in suggestions.arguments]
        assert "region" not in names
        assert "force" in names

    def test_shows_subcommands(self, nested_commands: List[Dict[str, Any]]) -> None:
        """Non-terminal command shows subcommands."""
        cfg = _make_config(nested_commands)
        builder = cfg.builder().add_command("db")
        suggestions = builder.check_next()

        assert not suggestions.is_valid
        assert len(suggestions.commands) == 2
        names = [c.name for c in suggestions.commands]
        assert "migrate" in names
        assert "seed" in names

    def test_is_terminal_method(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """is_terminal() is an alias for is_valid."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy").add_argument("region", "us-east")
        suggestions = builder.check_next()

        assert suggestions.is_terminal() == suggestions.is_valid


# =============================================================================
# Test: add_command()
# =============================================================================


class TestAddCommand:
    """Test adding commands to the builder."""

    def test_add_command_by_name(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Can add command by its name."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy")
        assert builder.command_path == ["deploy"]

    def test_add_command_by_alias(
        self, nested_commands: List[Dict[str, Any]]
    ) -> None:
        """Can add command by its alias."""
        cfg = _make_config(nested_commands)
        builder = cfg.builder().add_command("database")
        # Resolves to canonical name
        assert builder.command_path == ["db"]

    def test_add_subcommand(self, nested_commands: List[Dict[str, Any]]) -> None:
        """Can add subcommands after parent command."""
        cfg = _make_config(nested_commands)
        builder = cfg.builder().add_command("db").add_command("migrate")
        assert builder.command_path == ["db", "migrate"]

    def test_add_unknown_command_raises(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Adding unknown command raises ValueError."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder()
        with pytest.raises(ValueError, match="Unknown command 'unknown'"):
            builder.add_command("unknown")

    def test_add_command_returns_new_builder(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """add_command() returns a new builder (immutable pattern)."""
        cfg = _make_config(simple_commands)
        builder1 = cfg.builder()
        builder2 = builder1.add_command("deploy")

        assert builder1 is not builder2
        assert builder1.command_path == []
        assert builder2.command_path == ["deploy"]


# =============================================================================
# Test: add_argument()
# =============================================================================


class TestAddArgument:
    """Test adding arguments to the builder."""

    def test_add_string_argument(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Can add string argument with value."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy").add_argument("region", "us-east")
        assert builder.arguments == {"region": "us-east"}

    def test_add_boolean_flag(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Boolean args default to True when no value given."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy").add_argument("force")
        assert builder.arguments == {"force": True}

    def test_add_boolean_with_explicit_value(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Boolean args accept explicit True/False."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy").add_argument("force", False)
        assert builder.arguments == {"force": False}

    def test_add_number_argument(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Number arguments are parsed correctly."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy").add_argument("count", "5")
        assert builder.arguments == {"count": 5}

    def test_add_argument_by_short_name(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Can add argument by its short flag."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy").add_argument("f")
        # Stored under canonical name
        assert builder.arguments == {"force": True}

    def test_add_unknown_argument_raises(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Adding unknown argument raises ValueError."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy")
        with pytest.raises(ValueError, match="Unknown argument 'unknown'"):
            builder.add_argument("unknown", "value")

    def test_add_argument_without_command_raises(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Cannot add argument without selecting command first."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder()
        with pytest.raises(ValueError, match="No command selected"):
            builder.add_argument("region", "us-east")

    def test_non_boolean_requires_value(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Non-boolean arguments require a value."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy")
        with pytest.raises(ValueError, match="requires a value"):
            builder.add_argument("region")

    def test_add_argument_returns_new_builder(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """add_argument() returns a new builder (immutable pattern)."""
        cfg = _make_config(simple_commands)
        builder1 = cfg.builder().add_command("deploy")
        builder2 = builder1.add_argument("force")

        assert builder1 is not builder2
        assert builder1.arguments == {}
        assert builder2.arguments == {"force": True}

    def test_invalid_number_raises(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Invalid number value raises ValueError."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy")
        with pytest.raises(ValueError, match="Invalid number"):
            builder.add_argument("count", "not-a-number")


# =============================================================================
# Test: add_positional()
# =============================================================================


class TestAddPositional:
    """Test adding positional arguments."""

    def test_add_positional(self, simple_commands: List[Dict[str, Any]]) -> None:
        """Can add positional arguments."""
        cfg = _make_config(simple_commands)
        builder = (
            cfg.builder()
            .add_command("deploy")
            .add_positional("arg1")
            .add_positional("arg2")
        )
        assert builder.positional == ["arg1", "arg2"]

    def test_positional_returns_new_builder(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """add_positional() returns a new builder (immutable pattern)."""
        cfg = _make_config(simple_commands)
        builder1 = cfg.builder().add_command("deploy")
        builder2 = builder1.add_positional("arg1")

        assert builder1 is not builder2
        assert builder1.positional == []
        assert builder2.positional == ["arg1"]


# =============================================================================
# Test: build()
# =============================================================================


class TestBuild:
    """Test building the final result."""

    def test_build_returns_processing_result(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """build() returns ProcessingResult with command context."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy").add_argument("region", "us-east")
        result = builder.build()

        assert result.command is not None
        assert result.command.path == ["deploy"]
        assert result.command.arguments == {"region": "us-east"}
        assert result.command.terminal is True

    def test_build_includes_positional(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """build() includes positional arguments."""
        cfg = _make_config(simple_commands)
        builder = (
            cfg.builder()
            .add_command("deploy")
            .add_argument("region", "us-east")
            .add_positional("extra")
        )
        result = builder.build()

        assert result.command.positional == ["extra"]

    def test_build_invalid_raises(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """build() raises if command is not valid."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy")  # Missing required 'region'
        with pytest.raises(ValueError, match="region"):
            builder.build()

    def test_build_non_terminal_raises(
        self, nested_commands: List[Dict[str, Any]]
    ) -> None:
        """build() raises for non-terminal command."""
        cfg = _make_config(nested_commands)
        builder = cfg.builder().add_command("db")  # Has subcommands, not terminal
        with pytest.raises(ValueError, match="not complete"):
            builder.build()


# =============================================================================
# Test: Value Providers
# =============================================================================


class TestValueProviders:
    """Test value provider integration."""

    def test_argument_suggestion_includes_values(
        self, value_provider_commands: List[Dict[str, Any]]
    ) -> None:
        """ArgumentSuggestion includes values from provider."""
        cfg = _make_config(value_provider_commands)
        builder = cfg.builder().add_command("deploy")
        suggestions = builder.check_next()

        env_arg = next(a for a in suggestions.arguments if a.name == "env")
        assert env_arg.value_suggestions == [
            "development",
            "staging",
            "production",
        ]

    def test_value_builder_suggestions(
        self, value_provider_commands: List[Dict[str, Any]]
    ) -> None:
        """ArgumentValueBuilder.check_next() returns ValueSuggestions."""
        cfg = _make_config(value_provider_commands)
        builder = cfg.builder().add_command("deploy")
        arg_builder = builder.add_argument_builder("env")
        suggestions = arg_builder.check_next()

        assert isinstance(suggestions, ValueSuggestions)
        assert suggestions.argument_name == "env"
        assert suggestions.values == ["development", "staging", "production"]
        assert suggestions.accepts_any is False  # Restricted to provider values

    def test_value_builder_context_aware(
        self, value_provider_commands: List[Dict[str, Any]]
    ) -> None:
        """Value providers receive context with parsed args."""
        cfg = _make_config(value_provider_commands)
        # First set env to production
        builder = (
            cfg.builder().add_command("deploy").add_argument("env", "production")
        )
        # Then get region suggestions
        arg_builder = builder.add_argument_builder("region")
        suggestions = arg_builder.check_next()

        # Production regions are different
        assert "us-east-1" in suggestions.values
        assert "eu-west-1" in suggestions.values

    def test_missing_provider_returns_empty(self) -> None:
        """Missing provider function returns empty suggestions."""
        commands = [
            {
                "name": "test",
                "terminal": True,
                "arguments": [
                    {
                        "name": "opt",
                        "type": "string",
                        "values_from": "nonexistent.module.func",
                    }
                ],
            }
        ]
        cfg = _make_config(commands)
        builder = cfg.builder().add_command("test")
        suggestions = builder.check_next()

        opt_arg = next(a for a in suggestions.arguments if a.name == "opt")
        assert opt_arg.value_suggestions == []


# =============================================================================
# Test: ArgumentValueBuilder
# =============================================================================


class TestArgumentValueBuilder:
    """Test the ArgumentValueBuilder for setting values with suggestions."""

    def test_set_value_and_build(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """ArgumentValueBuilder.set_value().build() returns to parent."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy")
        arg_builder = builder.add_argument_builder("region")

        # Set value and build
        new_builder = arg_builder.set_value("us-west").build()

        assert new_builder.arguments == {"region": "us-west"}

    def test_build_without_value_returns_unchanged(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """build() without set_value() returns unchanged parent."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy")
        arg_builder = builder.add_argument_builder("region")

        # Build without setting value
        new_builder = arg_builder.build()

        assert new_builder.arguments == {}

    def test_boolean_value_suggestions(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Boolean arguments suggest true/false."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy")
        arg_builder = builder.add_argument_builder("force")
        suggestions = arg_builder.check_next()

        assert suggestions.values == ["true", "false"]
        assert suggestions.accepts_any is False
        assert suggestions.arg_type == "boolean"

    def test_unknown_argument_raises(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """add_argument_builder() with unknown arg raises."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy")
        with pytest.raises(ValueError, match="Unknown argument"):
            builder.add_argument_builder("unknown")


# =============================================================================
# Test: State Immutability
# =============================================================================


class TestImmutability:
    """Test that builder operations are immutable."""

    def test_chained_operations_immutable(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Each operation returns new builder, original unchanged."""
        cfg = _make_config(simple_commands)
        b1 = cfg.builder()
        b2 = b1.add_command("deploy")
        b3 = b2.add_argument("region", "us-east")
        b4 = b3.add_argument("force")
        b5 = b4.add_positional("extra")

        # All builders are different objects
        assert b1 is not b2 is not b3 is not b4 is not b5

        # Each has its own state
        assert b1.command_path == []
        assert b2.command_path == ["deploy"]
        assert b3.arguments == {"region": "us-east"}
        assert b4.arguments == {"region": "us-east", "force": True}
        assert b5.positional == ["extra"]

    def test_arguments_are_copied(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """arguments property returns a copy."""
        cfg = _make_config(simple_commands)
        builder = cfg.builder().add_command("deploy").add_argument("force")

        args1 = builder.arguments
        args1["modified"] = True

        args2 = builder.arguments
        assert "modified" not in args2


# =============================================================================
# Test: Complex Scenarios
# =============================================================================


class TestComplexScenarios:
    """Test complex usage patterns."""

    def test_full_nested_command_flow(
        self, nested_commands: List[Dict[str, Any]]
    ) -> None:
        """Complete flow through nested commands."""
        cfg = _make_config(nested_commands)

        # Start at root
        builder = cfg.builder()
        assert not builder.check_next().is_valid

        # Add parent command
        builder = builder.add_command("db")
        assert not builder.check_next().is_valid
        assert len(builder.check_next().commands) == 2

        # Add subcommand
        builder = builder.add_command("migrate")
        assert builder.check_next().is_valid

        # Add optional argument
        builder = builder.add_argument("target", "v2")

        # Build
        result = builder.build()
        assert result.command.path == ["db", "migrate"]
        assert result.command.arguments == {"target": "v2"}

    def test_multiple_arguments(
        self, simple_commands: List[Dict[str, Any]]
    ) -> None:
        """Can add multiple arguments in sequence."""
        cfg = _make_config(simple_commands)
        builder = (
            cfg.builder()
            .add_command("deploy")
            .add_argument("region", "us-east")
            .add_argument("force")
            .add_argument("count", 3)
        )

        assert builder.arguments == {
            "region": "us-east",
            "force": True,
            "count": 3,
        }

        result = builder.build()
        assert result.command.arguments == builder.arguments
