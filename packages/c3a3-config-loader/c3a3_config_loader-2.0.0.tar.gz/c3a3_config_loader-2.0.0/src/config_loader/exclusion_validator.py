# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""
Configuration Loader - Exclusion Validator

Validates mutually exclusive argument groups and dependency rules
after argument binding.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .models import Command, DependencyRule, ExclusionGroup


class ExclusionValidationError(ValueError):
    """Raised when exclusion group validation fails."""

    def __init__(self, group_name: str, message: str) -> None:
        self.group_name = group_name
        super().__init__(message)


class DependencyValidationError(ValueError):
    """Raised when dependency rule validation fails."""

    def __init__(self, rule_name: str, message: str) -> None:
        self.rule_name = rule_name
        super().__init__(message)


class ExclusionValidator:
    """Validates exclusion groups and dependency rules.

    After argument binding, this validator checks:
    - Mutually exclusive groups: at most one argument from each group
    - Required groups: at least one argument must be provided
    - Dependency rules: if_then, requires, conflicts
    """

    def validate(
        self,
        command: Command,
        arguments: Dict[str, Any],
        command_path: List[str],
    ) -> List[str]:
        """Validate arguments against exclusion groups and dependency rules.

        Args:
            command: The command definition with groups and rules.
            arguments: The bound argument values.
            command_path: The command path (for error messages).

        Returns:
            List of warning messages (empty if validation passes).

        Raises:
            ExclusionValidationError: If exclusion group validation fails.
            DependencyValidationError: If dependency rule validation fails.
        """
        warnings: List[str] = []
        path_str = " ".join(command_path)

        # Validate exclusion groups
        for group in command.exclusion_groups:
            self._validate_exclusion_group(group, arguments, path_str)

        # Validate dependency rules
        for rule in command.dependency_rules:
            self._validate_dependency_rule(rule, arguments, path_str)

        return warnings

    def _validate_exclusion_group(
        self,
        group: ExclusionGroup,
        arguments: Dict[str, Any],
        path_str: str,
    ) -> None:
        """Validate a single exclusion group."""
        # Find which arguments from the group were provided
        provided: List[str] = []
        for arg_name in group.arguments:
            if arg_name in arguments and arguments[arg_name] is not None:
                # For booleans, check if True
                value = arguments[arg_name]
                if isinstance(value, bool):
                    if value:
                        provided.append(arg_name)
                else:
                    provided.append(arg_name)

        # Check mutual exclusion
        if len(provided) > 1:
            message = group.message or (
                f"Arguments {', '.join(f'--{a}' for a in provided)} "
                f"are mutually exclusive (group: {group.name})"
            )
            raise ExclusionValidationError(group.name, message)

        # Check required group
        if group.required and len(provided) == 0:
            message = group.message or (
                f"One of {', '.join(f'--{a}' for a in group.arguments)} "
                f"is required (group: {group.name})"
            )
            raise ExclusionValidationError(group.name, message)

    def _validate_dependency_rule(
        self,
        rule: DependencyRule,
        arguments: Dict[str, Any],
        path_str: str,
    ) -> None:
        """Validate a single dependency rule."""
        if rule.rule == "if_then":
            self._validate_if_then(rule, arguments, path_str)
        elif rule.rule == "requires":
            self._validate_requires(rule, arguments, path_str)
        elif rule.rule == "conflicts":
            self._validate_conflicts(rule, arguments, path_str)

    def _validate_if_then(
        self,
        rule: DependencyRule,
        arguments: Dict[str, Any],
        path_str: str,
    ) -> None:
        """Validate an if_then dependency rule.

        If the condition argument equals the specified value,
        then the required arguments must be present.
        """
        if not rule.if_arg:
            return

        # Check if the condition argument is present and matches
        if rule.if_arg not in arguments:
            return

        value = arguments[rule.if_arg]
        condition_met = False

        if rule.eq is not None:
            # Check for equality
            condition_met = value == rule.eq
        else:
            # Check for truthiness
            condition_met = bool(value)

        if not condition_met:
            return

        # Condition is met - check required arguments
        if rule.then_require:
            missing: List[str] = []
            for req_arg in rule.then_require:
                if req_arg not in arguments or arguments[req_arg] is None:
                    missing.append(req_arg)

            if missing:
                message = rule.message or (
                    f"When '--{rule.if_arg}' is set, "
                    f"{', '.join(f'--{a}' for a in missing)} "
                    f"must also be provided (rule: {rule.name})"
                )
                raise DependencyValidationError(rule.name, message)

    def _validate_requires(
        self,
        rule: DependencyRule,
        arguments: Dict[str, Any],
        path_str: str,
    ) -> None:
        """Validate a requires dependency rule.

        If the source argument is present, the required arguments
        must also be present.
        """
        if not rule.if_arg or not rule.then_require:
            return

        # Check if source argument is present
        if rule.if_arg not in arguments:
            return

        value = arguments[rule.if_arg]
        if value is None or (isinstance(value, bool) and not value):
            return

        # Source is present - check required arguments
        missing: List[str] = []
        for req_arg in rule.then_require:
            if req_arg not in arguments or arguments[req_arg] is None:
                missing.append(req_arg)

        if missing:
            message = rule.message or (
                f"'--{rule.if_arg}' requires "
                f"{', '.join(f'--{a}' for a in missing)} "
                f"(rule: {rule.name})"
            )
            raise DependencyValidationError(rule.name, message)

    def _validate_conflicts(
        self,
        rule: DependencyRule,
        arguments: Dict[str, Any],
        path_str: str,
    ) -> None:
        """Validate a conflicts dependency rule.

        If the source argument is present, the conflicting arguments
        must NOT be present.
        """
        if not rule.if_arg or not rule.then_require:
            return

        # Check if source argument is present
        if rule.if_arg not in arguments:
            return

        value = arguments[rule.if_arg]
        if value is None or (isinstance(value, bool) and not value):
            return

        # Source is present - check conflicting arguments
        conflicts: List[str] = []
        for conflict_arg in rule.then_require:
            if conflict_arg in arguments:
                conflict_value = arguments[conflict_arg]
                if conflict_value is not None:
                    if not isinstance(conflict_value, bool) or conflict_value:
                        conflicts.append(conflict_arg)

        if conflicts:
            message = rule.message or (
                f"'--{rule.if_arg}' conflicts with "
                f"{', '.join(f'--{a}' for a in conflicts)} "
                f"(rule: {rule.name})"
            )
            raise DependencyValidationError(rule.name, message)


def validate_command_arguments(
    command: Command,
    arguments: Dict[str, Any],
    command_path: List[str],
) -> List[str]:
    """Convenience function to validate command arguments.

    Args:
        command: The command definition.
        arguments: The bound argument values.
        command_path: The command path for error messages.

    Returns:
        List of warning messages.

    Raises:
        ExclusionValidationError: If exclusion group validation fails.
        DependencyValidationError: If dependency rule validation fails.
    """
    validator = ExclusionValidator()
    return validator.validate(command, arguments, command_path)
