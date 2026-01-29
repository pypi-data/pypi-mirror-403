# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""
Configuration Loader - Callable Validators

Supports custom validation functions referenced in command specs.
Enables complex inter-argument validation logic beyond built-in rules.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, cast


class ValidatorError(ValueError):
    """Raised when a custom validator fails."""

    def __init__(
        self,
        message: str,
        validator_name: str,
        details: Optional[str] = None,
    ) -> None:
        self.validator_name = validator_name
        self.details = details
        super().__init__(message)


@dataclass
class ValidatorContext:
    """Context passed to custom validator functions.

    Attributes:
        command_path: The resolved command path.
        arguments: All bound argument values.
        environment: Current environment variables.
        config: Reference to the full configuration (for advanced validators).
    """

    command_path: List[str] = field(default_factory=list)
    arguments: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    config: Optional[Any] = None  # Configuration reference


class ValidatorFunction(Protocol):
    """Protocol for custom validator functions.

    A validator function receives the arguments dict and context,
    and returns None if valid or an error message string if invalid.

    Example:
        def check_deploy_args(args: Dict[str, Any], ctx: ValidatorContext) -> Optional[str]:
            if args.get("output") == "json" and args.get("verbose"):
                return "--output=json is incompatible with --verbose"
            return None
    """

    def __call__(
        self, args: Dict[str, Any], ctx: ValidatorContext
    ) -> Optional[str]:
        """Validate arguments.

        Args:
            args: The bound argument values.
            ctx: Validation context with command path and environment.

        Returns:
            None if valid, or an error message string if invalid.
        """
        ...


@dataclass
class ValidatorSpec:
    """Parsed validator specification from command definition.

    Supports both built-in rules (if_then, requires, conflicts) and
    callable validators that reference Python functions.
    """

    name: str
    rule: str
    function_path: Optional[str] = None
    if_condition: Optional[Dict[str, Any]] = None
    then_action: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class CallableValidatorRunner:
    """Executes custom callable validators.

    Handles loading validator functions from module paths and
    executing them with proper error handling.
    """

    def __init__(self) -> None:
        self._function_cache: Dict[str, ValidatorFunction] = {}

    def validate(
        self,
        validator: ValidatorSpec,
        arguments: Dict[str, Any],
        ctx: ValidatorContext,
    ) -> None:
        """Run a single validator.

        Args:
            validator: The validator specification.
            arguments: The bound argument values.
            ctx: The validation context.

        Raises:
            ValidatorError: If validation fails.
        """
        if validator.rule == "callable":
            self._run_callable_validator(validator, arguments, ctx)
        elif validator.rule == "if_then":
            self._run_if_then_validator(validator, arguments)
        elif validator.rule == "requires":
            self._run_requires_validator(validator, arguments)
        elif validator.rule == "conflicts":
            self._run_conflicts_validator(validator, arguments)

    def validate_all(
        self,
        validators: List[ValidatorSpec],
        arguments: Dict[str, Any],
        ctx: ValidatorContext,
    ) -> List[str]:
        """Run all validators, collecting warnings.

        Args:
            validators: List of validator specifications.
            arguments: The bound argument values.
            ctx: The validation context.

        Returns:
            List of warning messages (errors are raised).

        Raises:
            ValidatorError: If any validator fails.
        """
        warnings: List[str] = []

        for validator in validators:
            self.validate(validator, arguments, ctx)

        return warnings

    def _run_callable_validator(
        self,
        validator: ValidatorSpec,
        arguments: Dict[str, Any],
        ctx: ValidatorContext,
    ) -> None:
        """Execute a callable validator function."""
        if not validator.function_path:
            raise ValidatorError(
                f"Validator '{validator.name}' is missing function path",
                validator.name,
            )

        func = self._load_function(validator.function_path, validator.name)
        result = func(arguments, ctx)

        if result is not None:
            message = validator.message or result
            raise ValidatorError(message, validator.name, details=result)

    def _load_function(
        self, function_path: str, validator_name: str
    ) -> ValidatorFunction:
        """Load a validator function from a module path.

        Args:
            function_path: Dotted path like "myapp.validators.check_args".
            validator_name: Name of the validator (for error messages).

        Returns:
            The loaded function.

        Raises:
            ValidatorError: If function cannot be loaded.
        """
        if function_path in self._function_cache:
            return self._function_cache[function_path]

        try:
            # Split module path and function name
            parts = function_path.rsplit(".", 1)
            if len(parts) != 2:
                raise ValidatorError(
                    f"Invalid function path '{function_path}' for validator '{validator_name}'. "
                    f"Expected format: 'module.function'",
                    validator_name,
                )

            module_path, func_name = parts
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)

            if not callable(func):
                raise ValidatorError(
                    f"'{function_path}' is not callable",
                    validator_name,
                )

            typed_func = cast(ValidatorFunction, func)
            self._function_cache[function_path] = typed_func
            return typed_func

        except ImportError as e:
            raise ValidatorError(
                f"Could not import module for validator '{validator_name}': {e}",
                validator_name,
            )
        except AttributeError:
            raise ValidatorError(
                f"Function '{func_name}' not found in module '{module_path}' "
                f"for validator '{validator_name}'",
                validator_name,
            )

    def _run_if_then_validator(
        self,
        validator: ValidatorSpec,
        arguments: Dict[str, Any],
    ) -> None:
        """Execute an if_then validator rule."""
        if not validator.if_condition or not validator.then_action:
            return

        # Check condition
        arg_name = validator.if_condition.get("arg")
        expected_value = validator.if_condition.get("eq")

        if not arg_name or arg_name not in arguments:
            return

        actual_value = arguments[arg_name]

        # Check if condition is met
        condition_met = False
        if expected_value is not None:
            condition_met = actual_value == expected_value
        else:
            condition_met = bool(actual_value)

        if not condition_met:
            return

        # Check required arguments
        required = validator.then_action.get("require", [])
        missing: List[str] = []
        for req_arg in required:
            if req_arg not in arguments or arguments[req_arg] is None:
                missing.append(req_arg)

        if missing:
            message = validator.message or (
                f"When '--{arg_name}' is set, "
                f"{', '.join(f'--{a}' for a in missing)} must also be provided"
            )
            raise ValidatorError(message, validator.name)

        # Check forbidden arguments
        forbidden = validator.then_action.get("forbid", [])
        present: List[str] = []
        for forbid_arg in forbidden:
            if forbid_arg in arguments:
                val = arguments[forbid_arg]
                if val is not None and (not isinstance(val, bool) or val):
                    present.append(forbid_arg)

        if present:
            message = validator.message or (
                f"When '--{arg_name}' is set, "
                f"{', '.join(f'--{a}' for a in present)} cannot be used"
            )
            raise ValidatorError(message, validator.name)

    def _run_requires_validator(
        self,
        validator: ValidatorSpec,
        arguments: Dict[str, Any],
    ) -> None:
        """Execute a requires validator rule."""
        if not validator.if_condition:
            return

        arg_name = validator.if_condition.get("arg")
        if not arg_name or arg_name not in arguments:
            return

        value = arguments[arg_name]
        if value is None or (isinstance(value, bool) and not value):
            return

        # Check required arguments from then_action
        if not validator.then_action:
            return

        required = validator.then_action.get("require", [])
        missing: List[str] = []
        for req_arg in required:
            if req_arg not in arguments or arguments[req_arg] is None:
                missing.append(req_arg)

        if missing:
            message = validator.message or (
                f"'--{arg_name}' requires {', '.join(f'--{a}' for a in missing)}"
            )
            raise ValidatorError(message, validator.name)

    def _run_conflicts_validator(
        self,
        validator: ValidatorSpec,
        arguments: Dict[str, Any],
    ) -> None:
        """Execute a conflicts validator rule."""
        if not validator.if_condition:
            return

        arg_name = validator.if_condition.get("arg")
        if not arg_name or arg_name not in arguments:
            return

        value = arguments[arg_name]
        if value is None or (isinstance(value, bool) and not value):
            return

        # Check conflicting arguments from then_action
        if not validator.then_action:
            return

        conflicts_with = validator.then_action.get("forbid", [])
        present: List[str] = []
        for conflict_arg in conflicts_with:
            if conflict_arg in arguments:
                val = arguments[conflict_arg]
                if val is not None and (not isinstance(val, bool) or val):
                    present.append(conflict_arg)

        if present:
            message = validator.message or (
                f"'--{arg_name}' conflicts with {', '.join(f'--{a}' for a in present)}"
            )
            raise ValidatorError(message, validator.name)


def parse_validator_spec(spec_dict: Dict[str, Any]) -> ValidatorSpec:
    """Parse a validator specification from a dictionary.

    Args:
        spec_dict: The validator definition from the command spec.

    Returns:
        Parsed ValidatorSpec.
    """
    return ValidatorSpec(
        name=spec_dict.get("name", "(unnamed)"),
        rule=spec_dict.get("rule", ""),
        function_path=spec_dict.get("function"),
        if_condition=spec_dict.get("if"),
        then_action=spec_dict.get("then"),
        message=spec_dict.get("message"),
    )


def validate_command_with_validators(
    validators: List[Dict[str, Any]],
    arguments: Dict[str, Any],
    command_path: List[str],
    environment: Optional[Dict[str, str]] = None,
) -> None:
    """Convenience function to run all validators for a command.

    Args:
        validators: List of validator definitions from command spec.
        arguments: The bound argument values.
        command_path: The resolved command path.
        environment: Current environment variables.

    Raises:
        ValidatorError: If any validator fails.
    """
    if not validators:
        return

    runner = CallableValidatorRunner()
    ctx = ValidatorContext(
        command_path=command_path,
        arguments=arguments,
        environment=environment or {},
    )

    specs = [parse_validator_spec(v) for v in validators]
    runner.validate_all(specs, arguments, ctx)
