# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""Test suite for three-phase parsing integration.

Tests the complete parsing flow:
- Phase 1: Global parameter extraction
- Phase 2: Command path resolution
- Phase 3: Command argument binding

Run with:
    pytest tests/test_three_phase_parsing.py -v
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest
from config_loader import Configuration, ProcessingResult


# ============================================================================
# Helper Functions
# ============================================================================


def _make_spec(
    parameters: List[Dict[str, Any]],
    commands: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Create a v2.0 spec with both parameters and commands."""
    return {
        "schema_version": "2.0",
        "app_name": "testapp",
        "parameters": parameters,
        "commands": commands,
    }


# ============================================================================
# Phase 1: Global Parameter Extraction
# ============================================================================


class TestGlobalParameterExtraction:
    """Tests for Phase 1: extracting global parameters."""

    def test_global_params_before_command(self) -> None:
        """Test global params extracted when they appear before command."""
        spec = _make_spec(
            parameters=[
                {"namespace": "db", "name": "host", "type": "string", "default": "localhost"},
                {"namespace": "db", "name": "port", "type": "number", "default": 5432},
            ],
            commands=[{"name": "migrate", "terminal": True}],
        )
        cfg = Configuration(spec)

        result = cfg.process(["--db.host", "myhost", "--db.port", "3306", "migrate"])

        assert result._config["db"]["host"] == "myhost"
        assert result._config["db"]["port"] == 3306
        assert result.command is not None
        assert result.command.path == ["migrate"]

    def test_global_params_after_command(self) -> None:
        """Test global params extracted when they appear after command.

        In relaxed mode, global params can appear anywhere.
        """
        spec = _make_spec(
            parameters=[
                {"namespace": "app", "name": "verbose", "type": "boolean", "default": False}
            ],
            commands=[{"name": "run", "terminal": True}],
        )
        cfg = Configuration(spec)

        result = cfg.process(["run", "--app.verbose", "true"])

        assert result._config["app"]["verbose"] is True
        assert result.command is not None
        assert result.command.path == ["run"]

    def test_global_params_mixed_with_command_args(self) -> None:
        """Test global params and command args can be interleaved."""
        spec = _make_spec(
            parameters=[
                {"namespace": "log", "name": "level", "type": "string", "default": "info"}
            ],
            commands=[
                {
                    "name": "serve",
                    "terminal": True,
                    "arguments": [{"name": "port", "type": "number", "default": 8080}],
                }
            ],
        )
        cfg = Configuration(spec)

        result = cfg.process(["--log.level", "debug", "serve", "--port", "3000"])

        assert result._config["log"]["level"] == "debug"
        assert result.command is not None
        assert result.command.arguments["port"] == 3000

    def test_global_params_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test global params loaded from environment variables.

        Environment variables are automatically checked by the EnvironmentLoader
        using the format: APPNAME_NAMESPACE_NAME (uppercase).
        """
        spec = _make_spec(
            parameters=[
                {"namespace": "db", "name": "password", "type": "string"}
            ],
            commands=[{"name": "connect", "terminal": True}],
        )

        # EnvironmentLoader uses TESTAPP_DB_PASSWORD format
        monkeypatch.setenv("TESTAPP_DB_PASSWORD", "secret123")

        cfg = Configuration(spec)
        result = cfg.process(["connect"])

        assert result._config["db"]["password"] == "secret123"

    def test_global_params_defaults_when_no_args(self) -> None:
        """Test global params use defaults when not provided."""
        spec = _make_spec(
            parameters=[
                {"namespace": "cache", "name": "ttl", "type": "number", "default": 300}
            ],
            commands=[{"name": "flush", "terminal": True}],
        )
        cfg = Configuration(spec)

        result = cfg.process(["flush"])

        assert result._config["cache"]["ttl"] == 300


# ============================================================================
# Phase 2: Command Path Resolution
# ============================================================================


class TestCommandPathResolution:
    """Tests for Phase 2: resolving command paths."""

    def test_simple_command_after_global_params(self) -> None:
        """Test command resolved after global params."""
        spec = _make_spec(
            parameters=[{"namespace": "app", "name": "env", "type": "string", "default": "dev"}],
            commands=[{"name": "deploy", "terminal": True}],
        )
        cfg = Configuration(spec)

        result = cfg.process(["--app.env", "prod", "deploy"])

        assert result.command is not None
        assert result.command.path == ["deploy"]

    def test_nested_command_with_global_params(self) -> None:
        """Test nested command resolved with global params present."""
        spec = _make_spec(
            parameters=[{"namespace": "config", "name": "file", "type": "string"}],
            commands=[
                {
                    "name": "db",
                    "subcommands": [
                        {"name": "migrate", "terminal": True},
                        {"name": "seed", "terminal": True},
                    ],
                }
            ],
        )
        cfg = Configuration(spec)

        result = cfg.process(["--config.file", "custom.yaml", "db", "migrate"])

        assert result.command is not None
        assert result.command.path == ["db", "migrate"]
        assert result._config["config"]["file"] == "custom.yaml"

    def test_alias_resolved_with_global_params(self) -> None:
        """Test alias resolved alongside global params."""
        spec = _make_spec(
            parameters=[{"namespace": "verbose", "name": "level", "type": "number", "default": 0}],
            commands=[{"name": "compile", "aliases": ["c"], "terminal": True}],
        )
        cfg = Configuration(spec)

        result = cfg.process(["--verbose.level", "2", "c"])

        assert result.command is not None
        assert result.command.path == ["compile"]  # Resolved to canonical name


# ============================================================================
# Phase 3: Command Argument Binding
# ============================================================================


class TestCommandArgumentBinding:
    """Tests for Phase 3: binding command arguments."""

    def test_command_args_bound_after_resolution(self) -> None:
        """Test command args bound after command is resolved."""
        spec = _make_spec(
            parameters=[],
            commands=[
                {
                    "name": "deploy",
                    "terminal": True,
                    "arguments": [
                        {"name": "target", "type": "string", "required": True},
                        {"name": "force", "type": "boolean", "default": False},
                    ],
                }
            ],
        )
        cfg = Configuration(spec)

        result = cfg.process(["deploy", "--target", "production", "--force"])

        assert result.command is not None
        assert result.command.arguments["target"] == "production"
        assert result.command.arguments["force"] is True

    def test_inherited_args_available_in_subcommand(self) -> None:
        """Test inherited args bound at subcommand level."""
        spec = _make_spec(
            parameters=[],
            commands=[
                {
                    "name": "deploy",
                    "arguments": [
                        {"name": "region", "type": "string", "scope": "inherited"}
                    ],
                    "subcommands": [
                        {"name": "app", "terminal": True},
                        {"name": "infra", "terminal": True},
                    ],
                }
            ],
        )
        cfg = Configuration(spec)

        result = cfg.process(["deploy", "app", "--region", "us-west-2"])

        assert result.command is not None
        assert result.command.path == ["deploy", "app"]
        assert result.command.arguments["region"] == "us-west-2"

    def test_required_arg_missing_raises_error(self) -> None:
        """Test missing required argument raises error."""
        spec = _make_spec(
            parameters=[],
            commands=[
                {
                    "name": "run",
                    "terminal": True,
                    "arguments": [{"name": "config", "type": "string", "required": True}],
                }
            ],
        )
        cfg = Configuration(spec)

        with pytest.raises(ValueError, match="Required argument"):
            cfg.process(["run"])

    def test_unknown_arg_raises_error(self) -> None:
        """Test unknown argument raises error."""
        spec = _make_spec(
            parameters=[],
            commands=[
                {
                    "name": "build",
                    "terminal": True,
                    "arguments": [{"name": "output", "type": "string"}],
                }
            ],
        )
        cfg = Configuration(spec)

        with pytest.raises(ValueError, match="Unknown argument"):
            cfg.process(["build", "--unknown-flag"])


# ============================================================================
# Full Integration Tests
# ============================================================================


class TestFullIntegration:
    """Tests for complete three-phase parsing flow."""

    def test_complete_flow_all_phases(self) -> None:
        """Test complete parsing with all three phases active."""
        spec = _make_spec(
            parameters=[
                {"namespace": "db", "name": "host", "type": "string", "default": "localhost"},
                {"namespace": "db", "name": "port", "type": "number", "default": 5432},
                {"namespace": "app", "name": "verbose", "type": "boolean", "default": False},
            ],
            commands=[
                {
                    "name": "server",
                    "subcommands": [
                        {
                            "name": "start",
                            "terminal": True,
                            "arguments": [
                                {"name": "workers", "type": "number", "default": 4},
                                {"name": "bind", "type": "string", "default": "0.0.0.0"},
                            ],
                        }
                    ],
                }
            ],
        )
        cfg = Configuration(spec)

        result = cfg.process([
            "--db.host", "mydb.example.com",
            "--app.verbose", "true",
            "server", "start",
            "--workers", "8",
            "--bind", "127.0.0.1",
        ])

        # Phase 1: Global params
        assert result._config["db"]["host"] == "mydb.example.com"
        assert result._config["db"]["port"] == 5432  # default
        assert result._config["app"]["verbose"] is True

        # Phase 2: Command path
        assert result.command is not None
        assert result.command.path == ["server", "start"]

        # Phase 3: Command args
        assert result.command.arguments["workers"] == 8
        assert result.command.arguments["bind"] == "127.0.0.1"

    def test_result_serialization_roundtrip(self) -> None:
        """Test ProcessingResult serializes and deserializes correctly."""
        spec = _make_spec(
            parameters=[{"namespace": "app", "name": "name", "type": "string", "default": "myapp"}],
            commands=[
                {
                    "name": "deploy",
                    "terminal": True,
                    "arguments": [{"name": "env", "type": "string"}],
                }
            ],
        )
        cfg = Configuration(spec)

        result = cfg.process(["deploy", "--env", "staging"])

        # Serialize to dict and back
        data = result.to_dict()
        restored = ProcessingResult.from_dict(data)

        assert restored._config["app"]["name"] == "myapp"
        assert restored.command is not None
        assert restored.command.path == ["deploy"]
        assert restored.command.arguments["env"] == "staging"

    def test_no_commands_returns_none_command(self) -> None:
        """Test spec without commands returns command=None."""
        spec = _make_spec(
            parameters=[{"namespace": "app", "name": "port", "type": "number", "default": 8080}],
            commands=[],
        )
        cfg = Configuration(spec)

        result = cfg.process(["--app.port", "3000"])

        assert result.command is None
        assert result._config["app"]["port"] == 3000

    def test_positional_args_after_double_dash(self) -> None:
        """Test positional args captured after --."""
        spec = _make_spec(
            parameters=[],
            commands=[{"name": "exec", "terminal": True}],
        )
        cfg = Configuration(spec)

        result = cfg.process(["exec", "--", "python", "script.py", "--arg"])

        assert result.command is not None
        assert result.command.positional == ["python", "script.py", "--arg"]

    def test_backward_compat_attribute_access(self) -> None:
        """Test backward-compatible attribute access patterns."""
        spec = _make_spec(
            parameters=[
                {"namespace": "server", "name": "host", "type": "string", "default": "localhost"},
                {"namespace": "server", "name": "port", "type": "number", "default": 8000},
            ],
            commands=[{"name": "run", "terminal": True}],
        )
        cfg = Configuration(spec)

        result = cfg.process(["run"])

        # Old-style namespace.attribute access should work
        assert result.server.host == "localhost"
        assert result.server.port == 8000

        # Dict-style access should work
        assert result._config["server"]["host"] == "localhost"

    def test_env_var_for_command_arg(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test command argument loaded from environment variable."""
        spec = _make_spec(
            parameters=[],
            commands=[
                {
                    "name": "deploy",
                    "terminal": True,
                    "arguments": [
                        {"name": "api-key", "type": "string", "env": True}
                    ],
                }
            ],
        )

        monkeypatch.setenv("TESTAPP_DEPLOY_API_KEY", "secret-key-123")

        cfg = Configuration(spec)
        result = cfg.process(["deploy"])

        assert result.command is not None
        assert result.command.arguments.get("api-key") == "secret-key-123"


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases in three-phase parsing."""

    def test_empty_args_with_defaults(self) -> None:
        """Test empty args uses all defaults."""
        spec = _make_spec(
            parameters=[
                {"namespace": "app", "name": "timeout", "type": "number", "default": 30}
            ],
            commands=[],
        )
        cfg = Configuration(spec)

        result = cfg.process([])

        assert result._config["app"]["timeout"] == 30
        assert result.command is None

    def test_global_param_takes_precedence_over_command_arg(self) -> None:
        """Test global param with same name as command arg are distinct.

        Global params use namespace.name format (--db.host),
        command args use just name format (--host).
        """
        spec = _make_spec(
            parameters=[
                {"namespace": "db", "name": "host", "type": "string", "default": "db-default"}
            ],
            commands=[
                {
                    "name": "connect",
                    "terminal": True,
                    "arguments": [
                        {"name": "host", "type": "string", "default": "cmd-default"}
                    ],
                }
            ],
        )
        cfg = Configuration(spec)

        result = cfg.process(["--db.host", "db-host", "connect", "--host", "cmd-host"])

        # Both should be independently set
        assert result._config["db"]["host"] == "db-host"
        assert result.command is not None
        assert result.command.arguments["host"] == "cmd-host"

    def test_multiple_subcommand_levels(self) -> None:
        """Test parsing through multiple levels of subcommands."""
        spec = _make_spec(
            parameters=[],
            commands=[
                {
                    "name": "cloud",
                    "arguments": [
                        {"name": "project", "type": "string", "scope": "inherited"}
                    ],
                    "subcommands": [
                        {
                            "name": "compute",
                            "subcommands": [
                                {
                                    "name": "instances",
                                    "subcommands": [
                                        {"name": "list", "terminal": True},
                                        {"name": "create", "terminal": True},
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        )
        cfg = Configuration(spec)

        result = cfg.process(["cloud", "compute", "instances", "list", "--project", "my-proj"])

        assert result.command is not None
        assert result.command.path == ["cloud", "compute", "instances", "list"]
        assert result.command.arguments["project"] == "my-proj"

    def test_equals_sign_in_option_value(self) -> None:
        """Test option value containing equals sign."""
        spec = _make_spec(
            parameters=[],
            commands=[
                {
                    "name": "set",
                    "terminal": True,
                    "arguments": [{"name": "value", "type": "string"}],
                }
            ],
        )
        cfg = Configuration(spec)

        result = cfg.process(["set", "--value=key=value"])

        assert result.command is not None
        assert result.command.arguments["value"] == "key=value"
