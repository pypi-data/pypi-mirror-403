# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""Test suite for serialization functionality.

Tests to_dict, from_dict, to_yaml, sensitive value filtering,
and round-trip serialization.

Run with:
    pytest tests/test_serialization.py -v
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from config_loader import (
    Configuration,
    ProcessingResult,
    SerializationContext,
    filter_sensitive_values,
    to_json_safe,
    to_yaml,
)
from config_loader.serialization import (
    create_replay_file,
    from_yaml,
    load_replay_file,
    replay_from_dict,
)


# ============================================================================
# Sensitive Value Filtering Tests
# ============================================================================


class TestSensitiveValueFiltering:
    """Tests for sensitive value filtering."""

    def test_filter_password_key(self) -> None:
        """Test filtering keys containing 'password'."""
        data = {"db": {"host": "localhost", "password": "secret123"}}
        result = filter_sensitive_values(data)

        assert result["db"]["host"] == "localhost"
        assert result["db"]["password"] == "[REDACTED]"

    def test_filter_token_key(self) -> None:
        """Test filtering keys containing 'token'."""
        data = {"api_token": "abc123", "name": "myapp"}
        result = filter_sensitive_values(data)

        assert result["api_token"] == "[REDACTED]"
        assert result["name"] == "myapp"

    def test_filter_obfuscated_value(self) -> None:
        """Test filtering obfuscated values."""
        data = {"setting": "obfuscated:a1b2c3d4e5f6"}
        result = filter_sensitive_values(data)

        assert result["setting"] == "[REDACTED]"

    def test_custom_replacement(self) -> None:
        """Test custom replacement string."""
        data = {"password": "secret"}
        result = filter_sensitive_values(data, replacement="***")

        assert result["password"] == "***"

    def test_custom_sensitive_keys(self) -> None:
        """Test custom sensitive key set."""
        data = {"my_secret_field": "value", "normal": "value"}
        result = filter_sensitive_values(
            data, sensitive_keys={"my_secret_field"}
        )

        assert result["my_secret_field"] == "[REDACTED]"
        assert result["normal"] == "value"

    def test_nested_filtering(self) -> None:
        """Test filtering works on nested structures."""
        data = {
            "level1": {
                "level2": {
                    "password": "deep_secret",
                    "normal": "ok",
                }
            }
        }
        result = filter_sensitive_values(data)

        assert result["level1"]["level2"]["password"] == "[REDACTED]"
        assert result["level1"]["level2"]["normal"] == "ok"

    def test_list_filtering(self) -> None:
        """Test filtering works on lists."""
        data = {
            "users": [  # "users" is not a sensitive key
                {"password": "secret1"},
                {"password": "secret2"},
            ]
        }
        result = filter_sensitive_values(data)

        assert result["users"][0]["password"] == "[REDACTED]"
        assert result["users"][1]["password"] == "[REDACTED]"


# ============================================================================
# ProcessingResult Serialization Tests
# ============================================================================


class TestProcessingResultSerialization:
    """Tests for ProcessingResult serialization methods."""

    def test_to_dict_basic(self) -> None:
        """Test basic to_dict serialization."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "parameters": [
                {"namespace": "db", "name": "host", "type": "string", "default": "localhost"}
            ],
            "commands": [{"name": "run", "terminal": True}],
        }
        cfg = Configuration(spec)
        result = cfg.process(["run"])

        data = result.to_dict()

        assert data["schema_version"] == "2.0"
        assert "config" in data
        assert data["config"]["db"]["host"] == "localhost"
        assert "command" in data
        assert data["command"]["path"] == ["run"]

    def test_to_json(self) -> None:
        """Test to_json serialization."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [{"name": "test", "terminal": True}],
        }
        cfg = Configuration(spec)
        result = cfg.process(["test"])

        json_str = result.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["command"]["path"] == ["test"]

    def test_from_dict_roundtrip(self) -> None:
        """Test from_dict correctly restores result."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "parameters": [
                {"namespace": "app", "name": "name", "type": "string", "default": "test"}
            ],
            "commands": [
                {
                    "name": "deploy",
                    "terminal": True,
                    "arguments": [{"name": "env", "type": "string"}],
                }
            ],
        }
        cfg = Configuration(spec)
        original = cfg.process(["deploy", "--env", "prod"])

        # Round-trip through dict
        data = original.to_dict()
        restored = ProcessingResult.from_dict(data)

        assert restored.command is not None
        assert restored.command.path == original.command.path
        assert restored.command.arguments["env"] == "prod"
        assert restored._config["app"]["name"] == "test"


# ============================================================================
# YAML Serialization Tests
# ============================================================================


class TestYamlSerialization:
    """Tests for YAML serialization."""

    def test_to_yaml(self) -> None:
        """Test to_yaml serialization."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [{"name": "run", "terminal": True}],
        }
        cfg = Configuration(spec)
        result = cfg.process(["run"])

        yaml_str = to_yaml(result)

        assert "schema_version" in yaml_str
        assert "command:" in yaml_str
        assert "path:" in yaml_str

    def test_to_yaml_filtered(self) -> None:
        """Test to_yaml with sensitive filtering."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "parameters": [
                {"namespace": "db", "name": "password", "type": "string", "default": "secret"}
            ],
            "commands": [{"name": "run", "terminal": True}],
        }
        cfg = Configuration(spec)
        result = cfg.process(["run"])

        yaml_str = to_yaml(result, filter_sensitive=True)

        assert "[REDACTED]" in yaml_str
        assert "secret" not in yaml_str

    def test_from_yaml(self) -> None:
        """Test from_yaml parsing."""
        yaml_str = """
schema_version: "2.0"
config:
  db:
    host: localhost
command:
  path:
    - run
  arguments: {}
  positional: []
  terminal: true
"""
        data = from_yaml(yaml_str)

        assert data["schema_version"] == "2.0"
        assert data["config"]["db"]["host"] == "localhost"


# ============================================================================
# Safe JSON Tests
# ============================================================================


class TestSafeJson:
    """Tests for to_json_safe function."""

    def test_to_json_safe_filters_sensitive(self) -> None:
        """Test to_json_safe filters sensitive values by default."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "parameters": [
                {"namespace": "api", "name": "key", "type": "string", "default": "secret-key"}
            ],
            "commands": [{"name": "run", "terminal": True}],
        }
        cfg = Configuration(spec)
        result = cfg.process(["run"])

        json_str = to_json_safe(result)

        assert "[REDACTED]" in json_str
        assert "secret-key" not in json_str

    def test_to_json_safe_no_filter(self) -> None:
        """Test to_json_safe without filtering."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "parameters": [
                {"namespace": "api", "name": "key", "type": "string", "default": "secret-key"}
            ],
            "commands": [{"name": "run", "terminal": True}],
        }
        cfg = Configuration(spec)
        result = cfg.process(["run"])

        json_str = to_json_safe(result, filter_sensitive=False)

        assert "secret-key" in json_str


# ============================================================================
# Replay File Tests
# ============================================================================


class TestReplayFiles:
    """Tests for replay file creation and loading."""

    def test_create_and_load_json_replay(self) -> None:
        """Test creating and loading JSON replay file."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [{"name": "deploy", "terminal": True}],
        }
        cfg = Configuration(spec)
        result = cfg.process(["deploy"])

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            create_replay_file(result, filepath)
            restored = load_replay_file(filepath)

            assert restored.command is not None
            assert restored.command.path == ["deploy"]
        finally:
            Path(filepath).unlink()

    def test_create_and_load_yaml_replay(self) -> None:
        """Test creating and loading YAML replay file."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [{"name": "run", "terminal": True}],
        }
        cfg = Configuration(spec)
        result = cfg.process(["run"])

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            filepath = f.name

        try:
            create_replay_file(result, filepath, format="yaml")
            restored = load_replay_file(filepath)

            assert restored.command is not None
            assert restored.command.path == ["run"]
        finally:
            Path(filepath).unlink()

    def test_replay_from_dict_validates_version(self) -> None:
        """Test replay_from_dict validates schema version."""
        data = {"schema_version": "3.0", "config": {}}

        with pytest.raises(ValueError, match="Unsupported schema version"):
            replay_from_dict(data)


# ============================================================================
# Serialization Context Tests
# ============================================================================


class TestSerializationContext:
    """Tests for SerializationContext class."""

    def test_context_filters_sensitive(self) -> None:
        """Test context filters sensitive values."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "parameters": [
                {"namespace": "db", "name": "password", "type": "string", "default": "secret"}
            ],
            "commands": [{"name": "run", "terminal": True}],
        }
        cfg = Configuration(spec)
        result = cfg.process(["run"])

        ctx = SerializationContext(filter_sensitive=True)
        data = ctx.to_dict(result)

        assert data["config"]["db"]["password"] == "[REDACTED]"

    def test_context_custom_sensitive_keys(self) -> None:
        """Test context with custom sensitive keys."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "parameters": [
                {"namespace": "my", "name": "secret", "type": "string", "default": "value"}
            ],
            "commands": [{"name": "run", "terminal": True}],
        }
        cfg = Configuration(spec)
        result = cfg.process(["run"])

        ctx = SerializationContext(
            filter_sensitive=True,
            additional_sensitive={"secret"},
        )
        data = ctx.to_dict(result)

        assert data["config"]["my"]["secret"] == "[REDACTED]"

    def test_context_custom_replacement(self) -> None:
        """Test context with custom replacement string."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "parameters": [
                {"namespace": "api", "name": "key", "type": "string", "default": "secret"}
            ],
            "commands": [{"name": "run", "terminal": True}],
        }
        cfg = Configuration(spec)
        result = cfg.process(["run"])

        ctx = SerializationContext(
            filter_sensitive=True,
            replacement="<hidden>",
        )
        json_str = ctx.to_json(result)

        assert "<hidden>" in json_str

    def test_context_save_to_file(self) -> None:
        """Test context save method."""
        spec = {
            "schema_version": "2.0",
            "app_name": "testapp",
            "commands": [{"name": "run", "terminal": True}],
        }
        cfg = Configuration(spec)
        result = cfg.process(["run"])

        ctx = SerializationContext()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            ctx.save(result, filepath)

            with open(filepath) as f:
                content = f.read()
            assert "run" in content
        finally:
            Path(filepath).unlink()
