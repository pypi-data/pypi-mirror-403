# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""Test suite for callable validators.

Tests custom validation functions, if_then, requires, and conflicts
rules for command arguments.

Run with:
    pytest tests/test_validators.py -v
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pytest
from config_loader import ValidatorContext, ValidatorError
from config_loader.callable_validators import (
    CallableValidatorRunner,
    ValidatorSpec,
    parse_validator_spec,
    validate_command_with_validators,
)


# ============================================================================
# ValidatorSpec Parsing Tests
# ============================================================================


class TestValidatorSpecParsing:
    """Tests for parsing validator specifications."""

    def test_parse_basic_spec(self) -> None:
        """Test parsing a basic validator spec."""
        spec_dict = {
            "name": "test-validator",
            "rule": "if_then",
        }
        spec = parse_validator_spec(spec_dict)

        assert spec.name == "test-validator"
        assert spec.rule == "if_then"

    def test_parse_callable_spec(self) -> None:
        """Test parsing a callable validator spec."""
        spec_dict = {
            "name": "custom",
            "rule": "callable",
            "function": "myapp.validators.check_args",
        }
        spec = parse_validator_spec(spec_dict)

        assert spec.rule == "callable"
        assert spec.function_path == "myapp.validators.check_args"

    def test_parse_if_then_spec(self) -> None:
        """Test parsing an if_then validator spec."""
        spec_dict = {
            "name": "prod-check",
            "rule": "if_then",
            "if": {"arg": "production", "eq": True},
            "then": {"require": ["api-key"]},
            "message": "Production requires API key",
        }
        spec = parse_validator_spec(spec_dict)

        assert spec.rule == "if_then"
        assert spec.if_condition == {"arg": "production", "eq": True}
        assert spec.then_action == {"require": ["api-key"]}
        assert spec.message == "Production requires API key"

    def test_parse_unnamed_spec(self) -> None:
        """Test parsing spec without name defaults to (unnamed)."""
        spec_dict = {"rule": "requires"}
        spec = parse_validator_spec(spec_dict)

        assert spec.name == "(unnamed)"


# ============================================================================
# ValidatorContext Tests
# ============================================================================


class TestValidatorContext:
    """Tests for ValidatorContext data class."""

    def test_context_defaults(self) -> None:
        """Test ValidatorContext default values."""
        ctx = ValidatorContext()

        assert ctx.command_path == []
        assert ctx.arguments == {}
        assert ctx.environment == {}
        assert ctx.config is None

    def test_context_with_values(self) -> None:
        """Test ValidatorContext with provided values."""
        ctx = ValidatorContext(
            command_path=["deploy", "staging"],
            arguments={"region": "us-east-1"},
            environment={"HOME": "/home/user"},
        )

        assert ctx.command_path == ["deploy", "staging"]
        assert ctx.arguments["region"] == "us-east-1"
        assert ctx.environment["HOME"] == "/home/user"


# ============================================================================
# CallableValidatorRunner Tests
# ============================================================================


class TestCallableValidatorRunner:
    """Tests for CallableValidatorRunner class."""

    def test_if_then_validator_passes(self) -> None:
        """Test if_then validator passes when condition not met."""
        runner = CallableValidatorRunner()
        spec = ValidatorSpec(
            name="test",
            rule="if_then",
            if_condition={"arg": "production", "eq": True},
            then_action={"require": ["api-key"]},
        )

        # Production is False, so condition not met - should pass
        runner.validate(spec, {"production": False}, ValidatorContext())

    def test_if_then_validator_fails(self) -> None:
        """Test if_then validator fails when requirement missing."""
        runner = CallableValidatorRunner()
        spec = ValidatorSpec(
            name="test",
            rule="if_then",
            if_condition={"arg": "production", "eq": True},
            then_action={"require": ["api-key"]},
        )

        with pytest.raises(ValidatorError):
            runner.validate(
                spec,
                {"production": True},  # Condition met, but api-key missing
                ValidatorContext(),
            )

    def test_if_then_with_forbid(self) -> None:
        """Test if_then validator with forbid action."""
        runner = CallableValidatorRunner()
        spec = ValidatorSpec(
            name="test",
            rule="if_then",
            if_condition={"arg": "quiet"},
            then_action={"forbid": ["verbose"]},
        )

        # quiet=True with verbose=True should fail
        with pytest.raises(ValidatorError, match="cannot be used"):
            runner.validate(
                spec,
                {"quiet": True, "verbose": True},
                ValidatorContext(),
            )

    def test_requires_validator(self) -> None:
        """Test requires validator rule."""
        runner = CallableValidatorRunner()
        spec = ValidatorSpec(
            name="test",
            rule="requires",
            if_condition={"arg": "username"},
            then_action={"require": ["password"]},
        )

        # username provided without password should fail
        with pytest.raises(ValidatorError, match="requires"):
            runner.validate(
                spec,
                {"username": "admin"},
                ValidatorContext(),
            )

    def test_conflicts_validator(self) -> None:
        """Test conflicts validator rule."""
        runner = CallableValidatorRunner()
        spec = ValidatorSpec(
            name="test",
            rule="conflicts",
            if_condition={"arg": "input-file"},
            then_action={"forbid": ["input-stdin"]},
        )

        # Both input-file and input-stdin should fail
        with pytest.raises(ValidatorError, match="conflicts"):
            runner.validate(
                spec,
                {"input-file": "data.txt", "input-stdin": True},
                ValidatorContext(),
            )

    def test_validate_all_collects_errors(self) -> None:
        """Test validate_all runs all validators."""
        runner = CallableValidatorRunner()
        specs = [
            ValidatorSpec(name="v1", rule="if_then"),
            ValidatorSpec(name="v2", rule="requires"),
        ]

        # Should complete without error when specs have no conditions
        warnings = runner.validate_all(specs, {}, ValidatorContext())
        assert warnings == []


# ============================================================================
# Convenience Function Tests
# ============================================================================


class TestValidateCommandWithValidators:
    """Tests for validate_command_with_validators function."""

    def test_empty_validators_passes(self) -> None:
        """Test empty validators list passes."""
        validate_command_with_validators([], {}, ["run"])

    def test_valid_validators_pass(self) -> None:
        """Test valid arguments pass all validators."""
        validators = [
            {
                "name": "test",
                "rule": "if_then",
                "if": {"arg": "verbose"},
                "then": {"forbid": ["quiet"]},
            }
        ]

        # verbose without quiet should pass
        validate_command_with_validators(
            validators,
            {"verbose": True, "quiet": False},
            ["run"],
        )

    def test_invalid_raises_error(self) -> None:
        """Test invalid arguments raise ValidatorError."""
        validators = [
            {
                "name": "test",
                "rule": "requires",
                "if": {"arg": "username"},
                "then": {"require": ["password"]},
            }
        ]

        with pytest.raises(ValidatorError):
            validate_command_with_validators(
                validators,
                {"username": "admin"},  # No password
                ["auth"],
            )


# ============================================================================
# Custom Validator Function Tests
# ============================================================================


# Define a test validator function in this module
def example_validator(
    args: Dict[str, Any], ctx: ValidatorContext
) -> Optional[str]:
    """Example validator that checks region is valid."""
    region = args.get("region")
    if region and region not in ["us-east-1", "us-west-2", "eu-west-1"]:
        return f"Invalid region: {region}"
    return None


class TestCallableValidator:
    """Tests for callable validator functions."""

    def test_callable_validator_loads(self) -> None:
        """Test callable validator function is loaded and executed."""
        runner = CallableValidatorRunner()
        spec = ValidatorSpec(
            name="region-check",
            rule="callable",
            function_path="tests.test_validators.example_validator",
        )

        # Valid region should pass
        runner.validate(spec, {"region": "us-east-1"}, ValidatorContext())

    def test_callable_validator_fails(self) -> None:
        """Test callable validator returns error message."""
        runner = CallableValidatorRunner()
        spec = ValidatorSpec(
            name="region-check",
            rule="callable",
            function_path="tests.test_validators.example_validator",
        )

        # Invalid region should fail
        with pytest.raises(ValidatorError, match="Invalid region"):
            runner.validate(spec, {"region": "invalid-region"}, ValidatorContext())

    def test_callable_validator_custom_message(self) -> None:
        """Test callable validator uses custom message when provided."""
        runner = CallableValidatorRunner()
        spec = ValidatorSpec(
            name="region-check",
            rule="callable",
            function_path="tests.test_validators.example_validator",
            message="Region must be a valid AWS region",
        )

        # Custom message should be used
        with pytest.raises(ValidatorError, match="valid AWS region"):
            runner.validate(spec, {"region": "invalid"}, ValidatorContext())

    def test_callable_missing_function_path(self) -> None:
        """Test callable without function_path raises error."""
        runner = CallableValidatorRunner()
        spec = ValidatorSpec(
            name="broken",
            rule="callable",
            function_path=None,
        )

        with pytest.raises(ValidatorError, match="missing function path"):
            runner.validate(spec, {}, ValidatorContext())

    def test_callable_invalid_module(self) -> None:
        """Test callable with invalid module raises error."""
        runner = CallableValidatorRunner()
        spec = ValidatorSpec(
            name="broken",
            rule="callable",
            function_path="nonexistent.module.func",
        )

        with pytest.raises(ValidatorError, match="Could not import"):
            runner.validate(spec, {}, ValidatorContext())

    def test_callable_invalid_function(self) -> None:
        """Test callable with invalid function name raises error."""
        runner = CallableValidatorRunner()
        spec = ValidatorSpec(
            name="broken",
            rule="callable",
            function_path="tests.test_validators.nonexistent_func",
        )

        with pytest.raises(ValidatorError, match="not found"):
            runner.validate(spec, {}, ValidatorContext())
