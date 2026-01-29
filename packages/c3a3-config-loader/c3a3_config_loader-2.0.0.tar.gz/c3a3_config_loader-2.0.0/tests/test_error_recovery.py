# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""Test suite for error recovery and suggestions.

Tests Levenshtein distance calculations and "Did you mean?" suggestions
for unknown commands and arguments.

Run with:
    pytest tests/test_error_recovery.py -v
"""

from __future__ import annotations

from config_loader import ErrorRecovery, ErrorRecoveryConfig
from config_loader.error_recovery import (
    find_similar,
    format_error_with_recovery,
    levenshtein_distance,
)


# ============================================================================
# Levenshtein Distance Tests
# ============================================================================


class TestLevenshteinDistance:
    """Tests for Levenshtein distance calculation."""

    def test_identical_strings(self) -> None:
        """Test distance is 0 for identical strings."""
        assert levenshtein_distance("hello", "hello") == 0

    def test_empty_string(self) -> None:
        """Test distance equals length when one string is empty."""
        assert levenshtein_distance("hello", "") == 5
        assert levenshtein_distance("", "world") == 5

    def test_single_insertion(self) -> None:
        """Test distance is 1 for single character insertion."""
        assert levenshtein_distance("helo", "hello") == 1

    def test_single_deletion(self) -> None:
        """Test distance is 1 for single character deletion."""
        assert levenshtein_distance("hello", "helo") == 1

    def test_single_substitution(self) -> None:
        """Test distance is 1 for single character substitution."""
        assert levenshtein_distance("hello", "hallo") == 1

    def test_multiple_operations(self) -> None:
        """Test distance for multiple operations."""
        assert levenshtein_distance("kitten", "sitting") == 3

    def test_case_sensitive(self) -> None:
        """Test that comparison is case sensitive."""
        assert levenshtein_distance("Hello", "hello") == 1


# ============================================================================
# Find Similar Tests
# ============================================================================


class TestFindSimilar:
    """Tests for finding similar candidates."""

    def test_exact_match_has_distance_zero(self) -> None:
        """Test exact match returns distance 0."""
        candidates = ["deploy", "destroy", "debug"]
        results = find_similar("deploy", candidates, max_distance=2)

        assert len(results) >= 1
        assert results[0] == ("deploy", 0)

    def test_close_match_found(self) -> None:
        """Test close matches are found."""
        candidates = ["deploy", "destroy", "debug"]
        results = find_similar("deploi", candidates, max_distance=2)

        assert len(results) >= 1
        assert "deploy" in [r[0] for r in results]

    def test_no_match_when_distance_too_high(self) -> None:
        """Test no results when all candidates are too far."""
        candidates = ["xyz", "abc", "123"]
        results = find_similar("deploy", candidates, max_distance=2)

        assert len(results) == 0

    def test_max_results_limit(self) -> None:
        """Test max_results limits output."""
        candidates = ["a", "aa", "aaa", "aaaa", "aaaaa"]
        results = find_similar("a", candidates, max_distance=5, max_results=2)

        assert len(results) <= 2

    def test_sorted_by_distance(self) -> None:
        """Test results are sorted by distance."""
        candidates = ["deployx", "deploy", "deployxx"]
        results = find_similar("deploy", candidates, max_distance=3)

        # Exact match should be first
        assert results[0][0] == "deploy"
        assert results[0][1] == 0

    def test_case_insensitive_matching(self) -> None:
        """Test matching is case insensitive."""
        candidates = ["Deploy", "DEPLOY", "deploy"]
        results = find_similar("DEPLOY", candidates, max_distance=0)

        assert len(results) == 3  # All should match


# ============================================================================
# Error Recovery Tests
# ============================================================================


class TestErrorRecovery:
    """Tests for ErrorRecovery class."""

    def test_suggest_command_with_similar(self) -> None:
        """Test command suggestion with similar commands."""
        recovery = ErrorRecovery()
        result = recovery.suggest_command(
            unknown="deploi",
            available=["deploy", "destroy", "status"],
            path=[],
        )

        assert "Unknown command" in result
        assert "deploi" in result
        assert "Did you mean?" in result
        assert "deploy" in result

    def test_suggest_command_no_similar(self) -> None:
        """Test command suggestion when no similar commands."""
        recovery = ErrorRecovery()
        result = recovery.suggest_command(
            unknown="xyz",
            available=["deploy", "destroy"],
            path=[],
        )

        assert "Unknown command" in result
        assert "xyz" in result
        assert "Did you mean?" not in result

    def test_suggest_command_shows_available(self) -> None:
        """Test that available commands are listed."""
        config = ErrorRecoveryConfig(show_available=True)
        recovery = ErrorRecovery(config)
        result = recovery.suggest_command(
            unknown="unknown",
            available=["deploy", "status"],
            path=[],
        )

        assert "Available commands" in result
        assert "deploy" in result
        assert "status" in result

    def test_suggest_argument_with_similar(self) -> None:
        """Test argument suggestion with similar arguments."""
        recovery = ErrorRecovery()
        result = recovery.suggest_argument(
            unknown="--verbos",
            available=["verbose", "version", "value"],
            path=["run"],
        )

        assert "Unknown argument" in result
        assert "verbos" in result
        assert "Did you mean?" in result
        assert "verbose" in result

    def test_non_terminal_guidance(self) -> None:
        """Test guidance for non-terminal commands."""
        recovery = ErrorRecovery()
        result = recovery.non_terminal_guidance(
            path=["deploy"],
            subcommands=["staging", "production"],
        )

        assert "not a complete command" in result
        assert "deploy staging" in result
        assert "deploy production" in result

    def test_missing_required_message(self) -> None:
        """Test missing required argument message."""
        recovery = ErrorRecovery()
        result = recovery.missing_required(
            argument="config",
            path=["run"],
        )

        assert "Required argument" in result
        assert "--config" in result
        assert "run" in result

    def test_invalid_value_with_suggestions(self) -> None:
        """Test invalid value message with suggestions."""
        recovery = ErrorRecovery()
        result = recovery.invalid_value(
            argument="format",
            value="jsn",
            expected_type="string",
            valid_values=["json", "yaml", "text"],
        )

        assert "Invalid value" in result
        assert "jsn" in result
        assert "Did you mean?" in result
        assert "json" in result

    def test_ordering_violation_message(self) -> None:
        """Test ordering violation message."""
        recovery = ErrorRecovery()
        result = recovery.ordering_violation(
            argument="--region",
            command="deploy",
            mode="strict",
        )

        assert "appears before command" in result
        assert "--region" in result
        assert "deploy" in result
        assert "strict" in result


# ============================================================================
# Error Recovery Config Tests
# ============================================================================


class TestErrorRecoveryConfig:
    """Tests for ErrorRecoveryConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ErrorRecoveryConfig()

        assert config.suggest_distance == 2
        assert config.max_suggestions == 3
        assert config.show_available is True

    def test_from_spec(self) -> None:
        """Test configuration from spec dict."""
        config = ErrorRecoveryConfig.from_spec({
            "suggest_distance": 3,
            "max_suggestions": 5,
            "show_available": False,
        })

        assert config.suggest_distance == 3
        assert config.max_suggestions == 5
        assert config.show_available is False

    def test_from_spec_none(self) -> None:
        """Test default config when spec is None."""
        config = ErrorRecoveryConfig.from_spec(None)

        assert config.suggest_distance == 2


# ============================================================================
# Convenience Function Tests
# ============================================================================


class TestFormatErrorWithRecovery:
    """Tests for format_error_with_recovery convenience function."""

    def test_unknown_command(self) -> None:
        """Test formatting unknown command error."""
        result = format_error_with_recovery(
            "unknown_command",
            unknown="deploi",
            available=["deploy", "destroy"],
            path=[],
        )

        assert "Unknown command" in result

    def test_unknown_argument(self) -> None:
        """Test formatting unknown argument error."""
        result = format_error_with_recovery(
            "unknown_argument",
            unknown="--verbos",
            available=["verbose", "version"],
            path=["run"],
        )

        assert "Unknown argument" in result

    def test_non_terminal(self) -> None:
        """Test formatting non-terminal error."""
        result = format_error_with_recovery(
            "non_terminal",
            path=["deploy"],
            subcommands=["staging"],
        )

        assert "not a complete command" in result

    def test_missing_required(self) -> None:
        """Test formatting missing required error."""
        result = format_error_with_recovery(
            "missing_required",
            argument="config",
            path=["run"],
        )

        assert "Required" in result

    def test_invalid_value(self) -> None:
        """Test formatting invalid value error."""
        result = format_error_with_recovery(
            "invalid_value",
            argument="level",
            value="xyz",
            expected_type="string",
        )

        assert "Invalid value" in result

    def test_ordering_error(self) -> None:
        """Test formatting ordering error."""
        result = format_error_with_recovery(
            "ordering",
            argument="--flag",
            command="deploy",
            mode="strict",
        )

        assert "appears before" in result

    def test_unknown_error_type(self) -> None:
        """Test unknown error type returns generic message."""
        result = format_error_with_recovery("unknown_type")

        assert "Error:" in result
