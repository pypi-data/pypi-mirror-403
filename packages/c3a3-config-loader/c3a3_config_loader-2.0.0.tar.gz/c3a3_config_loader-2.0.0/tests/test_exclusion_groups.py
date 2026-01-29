# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""Test suite for mutually exclusive argument groups.

Tests exclusion groups where only one argument from a group can be provided,
and dependency rules that define relationships between arguments.

Run with:
    pytest tests/test_exclusion_groups.py -v
"""

from __future__ import annotations

import pytest
from config_loader import Configuration
from config_loader.exclusion_validator import (
    DependencyValidationError,
    ExclusionValidationError,
    ExclusionValidator,
    validate_command_arguments,
)
from config_loader.models import Command, CommandArgument, DependencyRule, ExclusionGroup


# ============================================================================
# Exclusion Group Tests
# ============================================================================


class TestExclusionGroups:
    """Tests for mutually exclusive argument groups."""

    def test_single_argument_from_group_allowed(self) -> None:
        """Test that providing one argument from an exclusion group is allowed."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [
                {
                    "name": "output",
                    "terminal": True,
                    "arguments": [
                        {"name": "json", "type": "boolean", "default": False},
                        {"name": "yaml", "type": "boolean", "default": False},
                        {"name": "text", "type": "boolean", "default": False},
                    ],
                    "exclusion_groups": [
                        {
                            "name": "format",
                            "arguments": ["json", "yaml", "text"],
                        }
                    ],
                }
            ],
        }
        cfg = Configuration(spec)

        # Single argument should work
        result = cfg.process(["output", "--json"])
        assert result.command is not None
        assert result.command.arguments["json"] is True

    def test_multiple_arguments_from_group_raises_error(self) -> None:
        """Test that providing multiple arguments from an exclusion group fails."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [
                {
                    "name": "output",
                    "terminal": True,
                    "arguments": [
                        {"name": "json", "type": "boolean", "default": False},
                        {"name": "yaml", "type": "boolean", "default": False},
                    ],
                    "exclusion_groups": [
                        {
                            "name": "format",
                            "arguments": ["json", "yaml"],
                        }
                    ],
                }
            ],
        }
        cfg = Configuration(spec)

        with pytest.raises(ExclusionValidationError, match="mutually exclusive"):
            cfg.process(["output", "--json", "--yaml"])

    def test_required_exclusion_group(self) -> None:
        """Test that required exclusion group must have one argument."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [
                {
                    "name": "output",
                    "terminal": True,
                    "arguments": [
                        {"name": "json", "type": "boolean", "default": False},
                        {"name": "yaml", "type": "boolean", "default": False},
                    ],
                    "exclusion_groups": [
                        {
                            "name": "format",
                            "arguments": ["json", "yaml"],
                            "required": True,
                        }
                    ],
                }
            ],
        }
        cfg = Configuration(spec)

        with pytest.raises(ExclusionValidationError, match="is required"):
            cfg.process(["output"])

    def test_custom_error_message(self) -> None:
        """Test custom error message for exclusion group."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [
                {
                    "name": "output",
                    "terminal": True,
                    "arguments": [
                        {"name": "json", "type": "boolean", "default": False},
                        {"name": "yaml", "type": "boolean", "default": False},
                    ],
                    "exclusion_groups": [
                        {
                            "name": "format",
                            "arguments": ["json", "yaml"],
                            "message": "Choose only one output format!",
                        }
                    ],
                }
            ],
        }
        cfg = Configuration(spec)

        with pytest.raises(ExclusionValidationError, match="Choose only one output format"):
            cfg.process(["output", "--json", "--yaml"])


# ============================================================================
# Dependency Rule Tests
# ============================================================================


class TestDependencyRules:
    """Tests for inter-argument dependency rules."""

    def test_if_then_rule_satisfied(self) -> None:
        """Test if_then rule when condition and requirements are met."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [
                {
                    "name": "deploy",
                    "terminal": True,
                    "arguments": [
                        {"name": "production", "type": "boolean", "default": False},
                        {"name": "confirm-code", "type": "string"},  # Required when prod
                    ],
                    "dependency_rules": [
                        {
                            "name": "prod-confirm",
                            "rule": "if_then",
                            "if_arg": "production",
                            "then_require": ["confirm-code"],
                        }
                    ],
                }
            ],
        }
        cfg = Configuration(spec)

        # Production with confirm-code should work
        result = cfg.process(["deploy", "--production", "--confirm-code", "ABC123"])
        assert result.command is not None
        assert result.command.arguments["production"] is True
        assert result.command.arguments["confirm-code"] == "ABC123"

    def test_if_then_rule_violated(self) -> None:
        """Test if_then rule when condition is met but requirement is missing.

        Note: Arguments with defaults (even False) are considered "present".
        To test a truly missing argument, don't provide a default.
        """
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [
                {
                    "name": "deploy",
                    "terminal": True,
                    "arguments": [
                        {"name": "production", "type": "boolean", "default": False},
                        {"name": "confirm-code", "type": "string"},  # No default
                    ],
                    "dependency_rules": [
                        {
                            "name": "prod-confirm",
                            "rule": "if_then",
                            "if_arg": "production",
                            "then_require": ["confirm-code"],
                        }
                    ],
                }
            ],
        }
        cfg = Configuration(spec)

        with pytest.raises(DependencyValidationError, match="must also be provided"):
            cfg.process(["deploy", "--production"])

    def test_if_then_with_value_condition(self) -> None:
        """Test if_then rule with specific value condition."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [
                {
                    "name": "run",
                    "terminal": True,
                    "arguments": [
                        {"name": "mode", "type": "string", "default": "dev"},
                        {"name": "api-key", "type": "string"},
                    ],
                    "dependency_rules": [
                        {
                            "name": "prod-api-key",
                            "rule": "if_then",
                            "if_arg": "mode",
                            "eq": "production",
                            "then_require": ["api-key"],
                        }
                    ],
                }
            ],
        }
        cfg = Configuration(spec)

        # Dev mode without api-key should work
        result = cfg.process(["run", "--mode", "dev"])
        assert result.command is not None

        # Production mode without api-key should fail
        with pytest.raises(DependencyValidationError):
            cfg.process(["run", "--mode", "production"])

    def test_requires_rule(self) -> None:
        """Test requires dependency rule."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [
                {
                    "name": "auth",
                    "terminal": True,
                    "arguments": [
                        {"name": "username", "type": "string"},
                        {"name": "password", "type": "string"},
                    ],
                    "dependency_rules": [
                        {
                            "name": "user-needs-pass",
                            "rule": "requires",
                            "if_arg": "username",
                            "then_require": ["password"],
                        }
                    ],
                }
            ],
        }
        cfg = Configuration(spec)

        # Username without password should fail
        with pytest.raises(DependencyValidationError, match="requires"):
            cfg.process(["auth", "--username", "admin"])

        # Both should work
        result = cfg.process(["auth", "--username", "admin", "--password", "secret"])
        assert result.command is not None

    def test_conflicts_rule(self) -> None:
        """Test conflicts dependency rule."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [
                {
                    "name": "run",
                    "terminal": True,
                    "arguments": [
                        {"name": "quiet", "type": "boolean", "default": False},
                        {"name": "verbose", "type": "boolean", "default": False},
                    ],
                    "dependency_rules": [
                        {
                            "name": "quiet-verbose-conflict",
                            "rule": "conflicts",
                            "if_arg": "quiet",
                            "then_require": ["verbose"],  # These conflict
                        }
                    ],
                }
            ],
        }
        cfg = Configuration(spec)

        # Quiet and verbose together should fail
        with pytest.raises(DependencyValidationError, match="conflicts"):
            cfg.process(["run", "--quiet", "--verbose"])

        # Just quiet should work
        result = cfg.process(["run", "--quiet"])
        assert result.command is not None


# ============================================================================
# Unit Tests for ExclusionValidator
# ============================================================================


class TestExclusionValidatorUnit:
    """Unit tests for ExclusionValidator class."""

    def test_validate_exclusion_group_passes(self) -> None:
        """Test validation passes with single argument from group."""
        group = ExclusionGroup(name="format", arguments=["json", "yaml", "text"])
        cmd = Command(
            name="test",
            terminal=True,
            arguments=[
                CommandArgument(name="json", type="boolean"),
                CommandArgument(name="yaml", type="boolean"),
                CommandArgument(name="text", type="boolean"),
            ],
            exclusion_groups=[group],
        )

        validator = ExclusionValidator()
        # Should not raise
        validator.validate(cmd, {"json": True, "yaml": False}, ["test"])

    def test_validate_dependency_rule_passes(self) -> None:
        """Test validation passes when dependency is satisfied."""
        rule = DependencyRule(
            name="test-rule",
            rule="requires",
            if_arg="a",
            then_require=["b"],
        )
        cmd = Command(
            name="test",
            terminal=True,
            arguments=[
                CommandArgument(name="a", type="boolean"),
                CommandArgument(name="b", type="boolean"),
            ],
            dependency_rules=[rule],
        )

        validator = ExclusionValidator()
        # Should not raise
        validator.validate(cmd, {"a": True, "b": True}, ["test"])

    def test_convenience_function(self) -> None:
        """Test validate_command_arguments convenience function."""
        cmd = Command(
            name="test",
            terminal=True,
            arguments=[],
            exclusion_groups=[],
            dependency_rules=[],
        )

        # Should return empty warnings list
        warnings = validate_command_arguments(cmd, {}, ["test"])
        assert warnings == []
