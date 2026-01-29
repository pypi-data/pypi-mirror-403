# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""Test suite for deprecation warnings and strict mode.

Tests deprecated commands, arguments, and parameters with both
warning mode and strict mode (errors).

Run with:
    pytest tests/test_deprecation.py -v
"""

from __future__ import annotations

import pytest
from config_loader import (
    Configuration,
    DeprecationConfig,
    DeprecationError,
    DeprecationTracker,
)
from config_loader.deprecation import format_deprecated_help
from config_loader.models import Deprecation


# ============================================================================
# Deprecation Tracker Tests
# ============================================================================


class TestDeprecationTracker:
    """Tests for DeprecationTracker functionality."""

    def test_check_command_emits_warning(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that using a deprecated command emits a warning."""
        tracker = DeprecationTracker()
        deprecation = Deprecation(
            since="1.0",
            removed_in="2.0",
            replacement="new-command",
        )

        tracker.check_command("old-command", ["old-command"], deprecation)

        captured = capsys.readouterr()
        assert "DeprecationWarning" in captured.err
        assert "old-command" in captured.err
        assert "deprecated" in captured.err.lower()

    def test_check_command_strict_mode_raises(self) -> None:
        """Test that strict mode raises DeprecationError."""
        config = DeprecationConfig(strict=True)
        tracker = DeprecationTracker(config)
        deprecation = Deprecation(since="1.0")

        with pytest.raises(DeprecationError) as exc_info:
            tracker.check_command("old-command", ["old-command"], deprecation)

        assert exc_info.value.item_type == "command"
        assert exc_info.value.item_name == "old-command"

    def test_check_argument_emits_warning(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that using a deprecated argument emits a warning."""
        tracker = DeprecationTracker()
        deprecation = Deprecation(since="1.5", replacement="new-arg")

        tracker.check_argument("old-arg", ["deploy"], deprecation)

        captured = capsys.readouterr()
        assert "DeprecationWarning" in captured.err
        assert "old-arg" in captured.err

    def test_check_parameter_emits_warning(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that using a deprecated parameter emits a warning."""
        tracker = DeprecationTracker()
        deprecation = Deprecation(since="0.9", message="Use new.param instead")

        tracker.check_parameter("old", "param", deprecation)

        captured = capsys.readouterr()
        assert "DeprecationWarning" in captured.err
        assert "Use new.param instead" in captured.err

    def test_warning_emitted_only_once(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that the same deprecation warning is only emitted once."""
        tracker = DeprecationTracker()
        deprecation = Deprecation(since="1.0")

        # Emit twice
        tracker.check_command("cmd", ["cmd"], deprecation)
        tracker.check_command("cmd", ["cmd"], deprecation)

        captured = capsys.readouterr()
        # Should only appear once
        assert captured.err.count("DeprecationWarning") == 1

    def test_get_warnings_returns_all(self) -> None:
        """Test get_warnings returns all emitted warnings."""
        tracker = DeprecationTracker()

        tracker.check_command("cmd1", ["cmd1"], Deprecation(since="1.0"))
        tracker.check_argument("arg1", ["cmd"], Deprecation(since="1.0"))

        warnings = tracker.get_warnings()
        assert len(warnings) == 2

    def test_clear_resets_tracker(self) -> None:
        """Test clear removes tracked warnings."""
        tracker = DeprecationTracker()
        tracker.check_command("cmd", ["cmd"], Deprecation(since="1.0"))

        tracker.clear()

        assert len(tracker.get_warnings()) == 0


# ============================================================================
# Deprecation Config Tests
# ============================================================================


class TestDeprecationConfig:
    """Tests for DeprecationConfig creation."""

    def test_from_spec_default(self) -> None:
        """Test default config when no spec provided."""
        config = DeprecationConfig.from_spec(None)
        assert config.strict is False

    def test_from_spec_strict(self) -> None:
        """Test strict mode from spec."""
        config = DeprecationConfig.from_spec({"strict": True})
        assert config.strict is True


# ============================================================================
# Deprecation Message Formatting
# ============================================================================


class TestDeprecationFormatting:
    """Tests for deprecation message formatting."""

    def test_format_basic_message(self) -> None:
        """Test basic deprecation message format."""
        tracker = DeprecationTracker()
        deprecation = Deprecation(since="1.0")

        # Access internal method indirectly through check
        tracker.check_command("test", ["test"], deprecation)
        warnings = tracker.get_warnings()

        assert "deprecated" in warnings[0].lower()
        assert "v1.0" in warnings[0]

    def test_format_with_replacement(self) -> None:
        """Test deprecation message includes replacement."""
        tracker = DeprecationTracker()
        deprecation = Deprecation(since="1.0", replacement="new-cmd")

        tracker.check_command("old", ["old"], deprecation)
        warnings = tracker.get_warnings()

        assert "new-cmd" in warnings[0]

    def test_format_with_removal_version(self) -> None:
        """Test deprecation message includes removal version."""
        tracker = DeprecationTracker()
        deprecation = Deprecation(since="1.0", removed_in="2.0")

        tracker.check_command("old", ["old"], deprecation)
        warnings = tracker.get_warnings()

        assert "v2.0" in warnings[0]

    def test_format_deprecated_help(self) -> None:
        """Test format_deprecated_help function."""
        deprecation = Deprecation(
            since="1.0",
            removed_in="2.0",
            replacement="new-name",
        )

        result = format_deprecated_help("old-name", deprecation)

        assert "[DEPRECATED]" in result
        assert "old-name" in result
        assert "new-name" in result
        assert "v2.0" in result


# ============================================================================
# Integration Tests
# ============================================================================


class TestDeprecationIntegration:
    """Tests for deprecation in full configuration processing."""

    def test_deprecated_command_emits_warning(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test using a deprecated command in a spec."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [
                {
                    "name": "old-deploy",
                    "terminal": True,
                    "deprecated": {
                        "since": "1.0",
                        "replacement": "deploy",
                    },
                }
            ],
        }
        cfg = Configuration(spec)

        result = cfg.process(["old-deploy"])

        assert result.command is not None
        captured = capsys.readouterr()
        assert "DeprecationWarning" in captured.err

    def test_result_contains_warnings(self) -> None:
        """Test ProcessingResult.warnings contains deprecation warnings."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [
                {
                    "name": "old-cmd",
                    "terminal": True,
                    "deprecated": {"since": "1.0"},
                }
            ],
        }
        cfg = Configuration(spec)

        result = cfg.process(["old-cmd"])

        assert len(result.warnings) > 0
        assert any("deprecated" in w.lower() for w in result.warnings)


# ============================================================================
# Edge Cases
# ============================================================================


class TestDeprecationEdgeCases:
    """Tests for edge cases in deprecation handling."""

    def test_none_deprecation_no_warning(self) -> None:
        """Test no warning when deprecation is None."""
        tracker = DeprecationTracker()

        # Should not raise or emit
        tracker.check_command("cmd", ["cmd"], None)

        assert len(tracker.get_warnings()) == 0

    def test_custom_message_used(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test custom message is used when provided."""
        tracker = DeprecationTracker()
        deprecation = Deprecation(
            since="1.0",
            message="Please migrate to the new API",
        )

        tracker.check_command("old", ["old"], deprecation)

        captured = capsys.readouterr()
        assert "Please migrate to the new API" in captured.err
