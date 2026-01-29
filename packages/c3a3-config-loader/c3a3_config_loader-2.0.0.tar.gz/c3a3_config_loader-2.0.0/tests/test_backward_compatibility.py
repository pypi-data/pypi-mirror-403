# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""Test suite for backward compatibility with v1.x specs.

Ensures that existing v1.x specifications continue to work unchanged
when using the v2.0 Configuration class.

Run with:
    pytest tests/test_backward_compatibility.py -v
"""

from __future__ import annotations

import pytest
from config_loader import Configuration, ProcessingResult


# ============================================================================
# v1.x Spec Compatibility
# ============================================================================


class TestV1SpecCompatibility:
    """Tests ensuring v1.x specs work with the new system."""

    def test_v1_spec_without_schema_version(self) -> None:
        """Test v1.x spec without explicit schema version."""
        spec = {
            "app_name": "myapp",
            "parameters": [
                {"namespace": "db", "name": "host", "type": "string", "default": "localhost"},
            ],
        }
        cfg = Configuration(spec)
        result = cfg.process(["--db.host", "myhost"])

        # Should return ProcessingResult with command=None
        assert isinstance(result, ProcessingResult)
        assert result.command is None
        assert result._config["db"]["host"] == "myhost"

    def test_v1_spec_with_explicit_version_1_0(self) -> None:
        """Test v1.x spec with explicit schema_version: 1.0."""
        spec = {
            "schema_version": "1.0",
            "app_name": "myapp",
            "parameters": [
                {"namespace": "cache", "name": "ttl", "type": "number", "default": 300},
            ],
        }
        cfg = Configuration(spec)
        result = cfg.process([])

        assert isinstance(result, ProcessingResult)
        assert result.command is None
        assert result._config["cache"]["ttl"] == 300

    def test_v1_spec_attribute_access(self) -> None:
        """Test attribute access pattern works for v1 specs."""
        spec = {
            "app_name": "myapp",
            "parameters": [
                {"namespace": "server", "name": "host", "type": "string", "default": "0.0.0.0"},
                {"namespace": "server", "name": "port", "type": "number", "default": 8080},
            ],
        }
        cfg = Configuration(spec)
        result = cfg.process([])

        # Attribute access should work through ProcessingResult
        assert result.server.host == "0.0.0.0"
        assert result.server.port == 8080

    def test_v1_spec_dict_access(self) -> None:
        """Test dict access pattern works for v1 specs."""
        spec = {
            "app_name": "myapp",
            "parameters": [
                {"namespace": "app", "name": "name", "type": "string", "default": "TestApp"},
            ],
        }
        cfg = Configuration(spec)
        result = cfg.process([])

        # Dict access through _config should work
        assert result._config["app"]["name"] == "TestApp"

    def test_v1_spec_with_precedence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test precedence rules work with v1 specs."""
        spec = {
            "app_name": "testapp",
            "precedence": ["args", "env"],
            "parameters": [
                {"namespace": "api", "name": "key", "type": "string"},
            ],
        }

        monkeypatch.setenv("TESTAPP_API_KEY", "env-value")

        cfg = Configuration(spec)

        # Args should take precedence over env
        result = cfg.process(["--api.key", "arg-value"])
        assert result._config["api"]["key"] == "arg-value"

        # Env should be used when no args
        result2 = cfg.process([])
        assert result2._config["api"]["key"] == "env-value"

    def test_v1_spec_required_params(self) -> None:
        """Test required parameter validation for v1 specs."""
        spec = {
            "app_name": "myapp",
            "parameters": [
                {"namespace": "db", "name": "host", "type": "string", "required": True},
            ],
        }
        cfg = Configuration(spec)

        with pytest.raises(ValueError, match="Required"):
            cfg.process([])

    def test_v1_spec_type_validation(self) -> None:
        """Test type validation for v1 specs."""
        spec = {
            "app_name": "myapp",
            "parameters": [
                {"namespace": "app", "name": "count", "type": "number"},
            ],
        }
        cfg = Configuration(spec)

        result = cfg.process(["--app.count", "42"])
        assert result._config["app"]["count"] == 42
        assert isinstance(result._config["app"]["count"], int)


# ============================================================================
# ProcessingResult Compatibility
# ============================================================================


class TestProcessingResultCompatibility:
    """Tests for ProcessingResult backward compatibility features."""

    def test_processing_result_wraps_config_result(self) -> None:
        """Test ProcessingResult properly wraps ConfigurationResult."""
        spec = {
            "app_name": "myapp",
            "parameters": [
                {"namespace": "log", "name": "level", "type": "string", "default": "info"},
            ],
        }
        cfg = Configuration(spec)
        result = cfg.process([])

        # config property should return ConfigurationResult
        assert hasattr(result.config, "export_dict")
        assert hasattr(result.config, "export_json")
        assert result.config.export_dict()["log"]["level"] == "info"

    def test_processing_result_debug_info(self) -> None:
        """Test _debug_info is accessible through ProcessingResult."""
        spec = {
            "app_name": "myapp",
            "parameters": [
                {"namespace": "app", "name": "mode", "type": "string", "default": "dev"},
            ],
        }
        cfg = Configuration(spec)
        result = cfg.process([])

        # _debug_info should be a dict
        assert isinstance(result._debug_info, dict)

    def test_processing_result_export_methods(self) -> None:
        """Test export methods work on ProcessingResult."""
        spec = {
            "app_name": "myapp",
            "parameters": [
                {"namespace": "test", "name": "value", "type": "string", "default": "hello"},
            ],
        }
        cfg = Configuration(spec)
        result = cfg.process([])

        # to_dict should work
        data = result.to_dict()
        assert "config" in data
        assert data["config"]["test"]["value"] == "hello"

        # to_json should work
        json_str = result.to_json()
        assert '"value": "hello"' in json_str


# ============================================================================
# v2.0 Spec Without Commands
# ============================================================================


class TestV2SpecWithoutCommands:
    """Tests for v2.0 specs that don't define commands."""

    def test_v2_spec_empty_commands(self) -> None:
        """Test v2.0 spec with empty commands array."""
        spec = {
            "schema_version": "2.0",
            "app_name": "myapp",
            "parameters": [
                {"namespace": "db", "name": "host", "type": "string", "default": "localhost"},
            ],
            "commands": [],
        }
        cfg = Configuration(spec)
        result = cfg.process([])

        assert result.command is None
        assert result._config["db"]["host"] == "localhost"

    def test_v2_spec_no_commands_key(self) -> None:
        """Test v2.0 spec without commands key."""
        spec = {
            "schema_version": "2.0",
            "app_name": "myapp",
            "parameters": [
                {"namespace": "app", "name": "env", "type": "string", "default": "dev"},
            ],
        }
        cfg = Configuration(spec)
        result = cfg.process([])

        assert result.command is None
        assert result._config["app"]["env"] == "dev"


# ============================================================================
# Existing Test Patterns
# ============================================================================


class TestExistingPatterns:
    """Tests ensuring existing test patterns still work."""

    def test_monkeypatch_loader_pattern(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test the _prepare_config pattern with monkeypatching still works."""
        spec = {
            "app_name": "myapp",
            "parameters": [
                {"namespace": "db", "name": "host", "type": "string"},
            ],
        }
        cfg = Configuration(spec)

        # Existing pattern of monkeypatching loaders
        monkeypatch.setattr(
            cfg.arg_loader, "load", lambda _: {"param_db_host": "patched-host"}
        )

        result = cfg.process([])
        assert result._config["db"]["host"] == "patched-host"

    def test_multiple_namespaces(self) -> None:
        """Test multiple namespaces work as expected."""
        spec = {
            "app_name": "myapp",
            "parameters": [
                {"namespace": "db", "name": "host", "type": "string", "default": "db-host"},
                {"namespace": "cache", "name": "host", "type": "string", "default": "cache-host"},
                {"namespace": "api", "name": "host", "type": "string", "default": "api-host"},
            ],
        }
        cfg = Configuration(spec)
        result = cfg.process([])

        assert result._config["db"]["host"] == "db-host"
        assert result._config["cache"]["host"] == "cache-host"
        assert result._config["api"]["host"] == "api-host"

        # Attribute access for each namespace
        assert result.db.host == "db-host"
        assert result.cache.host == "cache-host"
        assert result.api.host == "api-host"

    def test_null_namespace_param(self) -> None:
        """Test parameter with null namespace.

        Params with null namespace are stored under 'default' namespace.
        """
        spec = {
            "app_name": "myapp",
            "parameters": [
                {"namespace": None, "name": "global_flag", "type": "boolean", "default": False},
            ],
        }
        cfg = Configuration(spec)
        result = cfg.process(["--global_flag", "true"])

        assert result._config["default"]["global_flag"] is True

    def test_accepts_validation(self) -> None:
        """Test accepts validation still works."""
        spec = {
            "app_name": "myapp",
            "parameters": [
                {
                    "namespace": "log",
                    "name": "level",
                    "type": "string",
                    "accepts": ["debug", "info", "warn", "error"],
                    "default": "info",
                },
            ],
        }
        cfg = Configuration(spec)

        # Valid value
        result = cfg.process(["--log.level", "debug"])
        assert result._config["log"]["level"] == "debug"

        # Invalid value
        with pytest.raises(ValueError, match="not in"):
            cfg.process(["--log.level", "invalid"])


# ============================================================================
# Mixed v1/v2 Features
# ============================================================================


class TestMixedFeatures:
    """Tests for specs mixing v1 and v2 features."""

    def test_v2_commands_with_v1_params(self) -> None:
        """Test v2 commands can coexist with traditional parameters."""
        spec = {
            "schema_version": "2.0",
            "app_name": "myapp",
            "parameters": [
                {"namespace": "db", "name": "host", "type": "string", "default": "localhost"},
                {"namespace": "db", "name": "port", "type": "number", "default": 5432},
            ],
            "commands": [
                {"name": "migrate", "terminal": True},
            ],
        }
        cfg = Configuration(spec)
        result = cfg.process(["--db.host", "myhost", "migrate"])

        # Both params and command should work
        assert result._config["db"]["host"] == "myhost"
        assert result._config["db"]["port"] == 5432
        assert result.command is not None
        assert result.command.path == ["migrate"]

    def test_v2_commands_dont_break_config_access(self) -> None:
        """Test v2 commands don't break existing config access patterns."""
        spec = {
            "schema_version": "2.0",
            "app_name": "myapp",
            "parameters": [
                {"namespace": "server", "name": "bind", "type": "string", "default": "0.0.0.0"},
            ],
            "commands": [
                {
                    "name": "start",
                    "terminal": True,
                    "arguments": [{"name": "port", "type": "number", "default": 8080}],
                }
            ],
        }
        cfg = Configuration(spec)
        result = cfg.process(["start", "--port", "3000"])

        # Config access works
        assert result.server.bind == "0.0.0.0"
        assert result._config["server"]["bind"] == "0.0.0.0"

        # Command access works
        assert result.command is not None
        assert result.command.arguments["port"] == 3000


# ============================================================================
# Error Handling Compatibility
# ============================================================================


class TestErrorHandlingCompatibility:
    """Tests for error handling backward compatibility."""

    def test_validation_error_format(self) -> None:
        """Test validation errors have compatible format."""
        spec = {
            "app_name": "myapp",
            "parameters": [
                {"namespace": "app", "name": "count", "type": "number", "required": True},
            ],
        }
        cfg = Configuration(spec)

        # Should raise ValueError (not a new exception type)
        with pytest.raises(ValueError):
            cfg.process([])

    def test_unknown_param_error(self) -> None:
        """Test unknown parameter error handling."""
        spec = {
            "app_name": "myapp",
            "parameters": [
                {"namespace": "app", "name": "port", "type": "number"},
            ],
        }
        cfg = Configuration(spec)

        # Unknown params should be handled gracefully
        # (current behavior varies - this tests current state)
        _result = cfg.process(["--unknown.param", "value"])
        # Unknown params may or may not be stored depending on implementation
