# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""
Configuration Loader - Value Provider Protocol

Defines the protocol for dynamic value providers that supply
valid values for arguments (used for autocompletion, validation,
and help generation).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


class ValueProviderError(Exception):
    """Raised when a value provider fails.

    This exception provides context about which provider failed
    and why, enabling clear error messages to users.
    """

    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        argument_name: Optional[str] = None,
    ) -> None:
        self.provider_name = provider_name
        self.argument_name = argument_name
        super().__init__(message)


@dataclass
class ProviderContext:
    """Context available to value providers.

    This context is passed to value providers during their lifecycle
    methods, giving them access to the current parsing state.

    Attributes:
        command_path: The current command path being executed.
        parsed_args: Arguments that have been parsed so far.
        environment: Current environment variables.
        partial_value: For autocompletion, the partial input to complete.
    """

    command_path: List[str] = field(default_factory=list)
    parsed_args: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    partial_value: Optional[str] = None


@runtime_checkable
class ValueProvider(Protocol):
    """Protocol for dynamic value providers.

    Value providers supply valid values for arguments dynamically.
    They are used in multiple phases:

    1. **Autocompletion**: `get_values()` with `partial_value` set
       returns completions matching the partial input.

    2. **Help generation**: `get_values()` returns possible values
       to display (may be truncated in output).

    3. **Parsing/Validation**: `validate()` checks if a user-provided
       value is valid.

    4. **Error recovery**: `get_values()` returns alternatives for
       "did you mean?" suggestions.

    Implementations should be mindful of performance:
    - `get_values()` should return within 100ms for autocompletion
    - Large result sets should filter using `partial_value`
    - Use `cacheable=True` for expensive but stable value sets

    Example implementation:
        class RegionProvider:
            def get_values(self, ctx: ProviderContext) -> List[str]:
                regions = ["us-east-1", "us-west-2", "eu-west-1"]
                if ctx.partial_value:
                    return [r for r in regions if r.startswith(ctx.partial_value)]
                return regions

            def validate(self, value: str, ctx: ProviderContext) -> bool:
                return value in self.get_values(ctx)

            @property
            def cacheable(self) -> bool:
                return True
    """

    def get_values(self, ctx: ProviderContext) -> List[str]:
        """Return list of valid values.

        For autocompletion, filter results using `ctx.partial_value`.
        For help and error recovery, return all valid values.

        Args:
            ctx: The provider context with current state.

        Returns:
            List of valid string values.

        Raises:
            ValueProviderError: If fetching values fails.
        """
        ...

    def validate(self, value: str, ctx: ProviderContext) -> bool:
        """Check if a value is valid.

        Args:
            value: The value to validate.
            ctx: The provider context with current state.

        Returns:
            True if the value is valid, False otherwise.

        Raises:
            ValueProviderError: If validation fails unexpectedly.
        """
        ...

    @property
    def cacheable(self) -> bool:
        """Whether results may be cached for the session.

        If True, `get_values()` will be called once and results
        reused. Use for expensive but stable value sets.

        Returns:
            True if results can be cached.
        """
        ...


class StaticValueProvider:
    """A simple value provider with a fixed list of values.

    Useful for arguments with a known set of valid values that
    don't change during execution.

    Example:
        provider = StaticValueProvider(["debug", "info", "warning", "error"])
    """

    def __init__(self, values: List[str]) -> None:
        self._values = values

    def get_values(self, ctx: ProviderContext) -> List[str]:
        """Return values, filtered by partial_value if present."""
        if ctx.partial_value:
            return [v for v in self._values if v.startswith(ctx.partial_value)]
        return self._values.copy()

    def validate(self, value: str, ctx: ProviderContext) -> bool:
        """Check if value is in the allowed list."""
        return value in self._values

    @property
    def cacheable(self) -> bool:
        """Static values are always cacheable."""
        return True


class CallableValueProvider:
    """A value provider that delegates to a callable.

    Wraps a function that returns valid values, making it easy
    to create providers from existing functions.

    Example:
        def fetch_regions(ctx):
            return ["us-east-1", "us-west-2", "eu-west-1"]

        provider = CallableValueProvider(fetch_regions, cacheable=True)
    """

    def __init__(
        self,
        get_values_fn: Any,  # Callable[[ProviderContext], List[str]]
        *,
        validate_fn: Optional[Any] = None,  # Callable[[str, ProviderContext], bool]
        cacheable: bool = False,
    ) -> None:
        self._get_values_fn = get_values_fn
        self._validate_fn = validate_fn
        self._cacheable = cacheable
        self._cache: Optional[List[str]] = None

    def get_values(self, ctx: ProviderContext) -> List[str]:
        """Get values from the wrapped callable."""
        if self._cacheable and self._cache is not None:
            values = self._cache
        else:
            values = self._get_values_fn(ctx)
            if self._cacheable:
                self._cache = values

        if ctx.partial_value:
            return [v for v in values if v.startswith(ctx.partial_value)]
        return values

    def validate(self, value: str, ctx: ProviderContext) -> bool:
        """Validate using custom function or membership check."""
        if self._validate_fn:
            return bool(self._validate_fn(value, ctx))
        return value in self.get_values(ctx)

    @property
    def cacheable(self) -> bool:
        """Return the configured cacheability."""
        return self._cacheable


class ProviderRegistry:
    """Registry for named value providers.

    Allows registering providers by name so they can be referenced
    in spec files and resolved at runtime.

    Example:
        registry = ProviderRegistry()
        registry.register("regions", RegionProvider())

        # Later, in parsing:
        provider = registry.get("regions")
        values = provider.get_values(ctx)
    """

    def __init__(self) -> None:
        self._providers: Dict[str, ValueProvider] = {}

    def register(self, name: str, provider: ValueProvider) -> None:
        """Register a provider by name."""
        self._providers[name] = provider

    def get(self, name: str) -> Optional[ValueProvider]:
        """Get a provider by name, or None if not found."""
        return self._providers.get(name)

    def has(self, name: str) -> bool:
        """Check if a provider is registered."""
        return name in self._providers

    def list_providers(self) -> List[str]:
        """List all registered provider names."""
        return list(self._providers.keys())


def invoke_provider_safely(
    provider: ValueProvider,
    method: str,
    ctx: ProviderContext,
    value: Optional[str] = None,
    *,
    default_on_error: Any = None,
    silent: bool = False,
) -> Any:
    """Safely invoke a provider method with error handling.

    Different contexts require different error handling:
    - Autocompletion: silently return empty list
    - Help: return "(dynamic)" placeholder
    - Validation: propagate error with context

    Args:
        provider: The value provider to invoke.
        method: Either "get_values" or "validate".
        ctx: The provider context.
        value: For validate, the value to check.
        default_on_error: Value to return if provider fails.
        silent: If True, suppress error output.

    Returns:
        The result from the provider, or default_on_error on failure.
    """
    try:
        if method == "get_values":
            return provider.get_values(ctx)
        elif method == "validate" and value is not None:
            return provider.validate(value, ctx)
        else:
            return default_on_error
    except ValueProviderError:
        raise  # Re-raise our own errors
    except Exception as e:
        if not silent:
            import sys

            print(f"Warning: Value provider failed: {e}", file=sys.stderr)
        return default_on_error
