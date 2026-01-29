#!/usr/bin/env python3
"""Test the builder/suggestion pattern with the pydocker example.

This script demonstrates and tests all builder functionality against
the real pydocker.yaml configuration.
"""

import sys
import os

# Add examples directory to path for loading validators
examples_dir = os.path.dirname(os.path.abspath(__file__))
if examples_dir not in sys.path:
    sys.path.insert(0, examples_dir)

import yaml
from config_loader import Configuration


def test_root_level_suggestions():
    """Test suggestions at root level."""
    print("=" * 60)
    print("TEST: Root level suggestions")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)
    builder = cfg.builder()
    suggestions = builder.check_next()

    print(f"is_valid: {suggestions.is_valid}")
    print(f"Commands available: {[c.name for c in suggestions.commands]}")
    print(f"Arguments available: {len(suggestions.arguments)}")

    assert not suggestions.is_valid, "Root level should not be valid"
    assert len(suggestions.commands) == 4, "Should have 4 commands: run, stop, rm, ps"

    cmd_names = [c.name for c in suggestions.commands]
    assert "run" in cmd_names
    assert "stop" in cmd_names
    assert "rm" in cmd_names
    assert "ps" in cmd_names

    print("✓ PASSED\n")


def test_run_command_suggestions():
    """Test suggestions after selecting 'run' command."""
    print("=" * 60)
    print("TEST: 'run' command suggestions")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)
    builder = cfg.builder().add_command("run")
    suggestions = builder.check_next()

    print(f"is_valid: {suggestions.is_valid}")
    print(f"Subcommands: {[c.name for c in suggestions.commands]}")
    print(f"Arguments ({len(suggestions.arguments)}):")

    for arg in suggestions.arguments:
        flag = f"--{arg.name}"
        if arg.short:
            flag += f" (-{arg.short})"
        extras = []
        if arg.required:
            extras.append("REQUIRED")
        if not arg.expects_value:
            extras.append("flag")
        if arg.value_suggestions:
            extras.append(f"values: {arg.value_suggestions[:3]}...")
        extra_str = f" [{', '.join(extras)}]" if extras else ""
        print(f"  {flag}{extra_str}")

    assert suggestions.is_valid, "'run' is terminal, should be valid"
    assert len(suggestions.commands) == 0, "'run' has no subcommands"
    assert len(suggestions.arguments) > 10, "Should have many arguments"

    # Check specific arguments
    arg_names = [a.name for a in suggestions.arguments]
    assert "detach" in arg_names
    assert "interactive" in arg_names
    assert "network" in arg_names
    assert "restart" in arg_names

    print("✓ PASSED\n")


def test_value_provider_restart():
    """Test value provider for --restart argument."""
    print("=" * 60)
    print("TEST: Value provider for --restart")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)
    builder = cfg.builder().add_command("run")

    # Get value suggestions through ArgumentValueBuilder
    arg_builder = builder.add_argument_builder("restart")
    value_suggestions = arg_builder.check_next()

    print(f"Argument: {value_suggestions.argument_name}")
    print(f"Type: {value_suggestions.arg_type}")
    print(f"Values: {value_suggestions.values}")
    print(f"Accepts any: {value_suggestions.accepts_any}")

    assert value_suggestions.argument_name == "restart"
    assert value_suggestions.arg_type == "string"
    assert "always" in value_suggestions.values
    assert "no" in value_suggestions.values
    assert "unless-stopped" in value_suggestions.values
    assert "on-failure" in value_suggestions.values
    assert not value_suggestions.accepts_any, "Should be restricted to provider values"

    print("✓ PASSED\n")


def test_value_provider_network():
    """Test value provider for --network argument (Docker networks)."""
    print("=" * 60)
    print("TEST: Value provider for --network (Docker networks)")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)
    builder = cfg.builder().add_command("run")

    arg_builder = builder.add_argument_builder("network")
    value_suggestions = arg_builder.check_next()

    print(f"Argument: {value_suggestions.argument_name}")
    print(f"Type: {value_suggestions.arg_type}")
    print(f"Networks found: {value_suggestions.values or '(none - Docker may not be running)'}")
    print(f"Accepts any: {value_suggestions.accepts_any}")

    assert value_suggestions.argument_name == "network"
    # Networks depend on Docker being available - just check it doesn't crash
    print("✓ PASSED (value provider executed without error)\n")


def test_boolean_flag_suggestions():
    """Test boolean flag value suggestions."""
    print("=" * 60)
    print("TEST: Boolean flag suggestions")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)
    builder = cfg.builder().add_command("run")

    # Check --detach (boolean flag)
    arg_builder = builder.add_argument_builder("detach")
    value_suggestions = arg_builder.check_next()

    print(f"Argument: {value_suggestions.argument_name}")
    print(f"Type: {value_suggestions.arg_type}")
    print(f"Values: {value_suggestions.values}")
    print(f"Accepts any: {value_suggestions.accepts_any}")

    assert value_suggestions.arg_type == "boolean"
    assert value_suggestions.values == ["true", "false"]
    assert not value_suggestions.accepts_any

    print("✓ PASSED\n")


def test_build_complete_command():
    """Test building a complete command."""
    print("=" * 60)
    print("TEST: Build complete command")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)

    # Build: pydocker run -d --restart=always --name=myapp --network=bridge
    builder = (
        cfg.builder()
        .add_command("run")
        .add_argument("detach")  # Boolean flag
        .add_argument("restart", "always")
        .add_argument("name", "myapp")
    )

    # Check validity before build
    suggestions = builder.check_next()
    print(f"Before build - is_valid: {suggestions.is_valid}")
    print(f"Errors: {suggestions.errors}")

    assert suggestions.is_valid, "Command should be valid"

    # Build the result
    result = builder.build()

    print(f"Command path: {result.command.path}")
    print(f"Arguments: {result.command.arguments}")
    print(f"Terminal: {result.command.terminal}")

    assert result.command.path == ["run"]
    assert result.command.arguments["detach"] is True
    assert result.command.arguments["restart"] == "always"
    assert result.command.arguments["name"] == "myapp"
    assert result.command.terminal is True

    print("✓ PASSED\n")


def test_stop_command_with_time():
    """Test stop command with --time argument."""
    print("=" * 60)
    print("TEST: 'stop' command with --time")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)

    # Build: pydocker stop -t 30
    builder = (
        cfg.builder()
        .add_command("stop")
        .add_argument("time", 30)
    )

    suggestions = builder.check_next()
    print(f"is_valid: {suggestions.is_valid}")

    result = builder.build()

    print(f"Command path: {result.command.path}")
    print(f"Arguments: {result.command.arguments}")

    assert result.command.path == ["stop"]
    assert result.command.arguments["time"] == 30

    print("✓ PASSED\n")


def test_ps_command_with_flags():
    """Test ps command with multiple boolean flags."""
    print("=" * 60)
    print("TEST: 'ps' command with flags")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)

    # Build: pydocker ps -a -q
    builder = (
        cfg.builder()
        .add_command("ps")
        .add_argument("all")
        .add_argument("quiet")
    )

    result = builder.build()

    print(f"Command path: {result.command.path}")
    print(f"Arguments: {result.command.arguments}")

    assert result.command.path == ["ps"]
    assert result.command.arguments["all"] is True
    assert result.command.arguments["quiet"] is True

    print("✓ PASSED\n")


def test_rm_command_with_force():
    """Test rm command with --force flag."""
    print("=" * 60)
    print("TEST: 'rm' command with --force")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)

    # Build: pydocker rm -f -v
    builder = (
        cfg.builder()
        .add_command("rm")
        .add_argument("force")
        .add_argument("volumes")
    )

    result = builder.build()

    print(f"Command path: {result.command.path}")
    print(f"Arguments: {result.command.arguments}")

    assert result.command.path == ["rm"]
    assert result.command.arguments["force"] is True
    assert result.command.arguments["volumes"] is True

    print("✓ PASSED\n")


def test_argument_value_builder_flow():
    """Test the ArgumentValueBuilder workflow."""
    print("=" * 60)
    print("TEST: ArgumentValueBuilder flow")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)
    builder = cfg.builder().add_command("run")

    # Use ArgumentValueBuilder to set restart policy
    arg_builder = builder.add_argument_builder("restart")

    # Check suggestions
    suggestions = arg_builder.check_next()
    print(f"Available values: {suggestions.values}")

    # Set value and return to parent builder
    new_builder = arg_builder.set_value("unless-stopped").build()

    print(f"Arguments after set_value: {new_builder.arguments}")

    assert new_builder.arguments["restart"] == "unless-stopped"

    # Build final result
    result = new_builder.build()
    assert result.command.arguments["restart"] == "unless-stopped"

    print("✓ PASSED\n")


def test_used_arguments_not_suggested():
    """Test that used arguments are removed from suggestions."""
    print("=" * 60)
    print("TEST: Used arguments removed from suggestions")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)

    # Start with run command
    builder = cfg.builder().add_command("run")
    initial_suggestions = builder.check_next()
    initial_args = [a.name for a in initial_suggestions.arguments]
    print(f"Initial arguments: {len(initial_args)}")
    assert "restart" in initial_args
    assert "name" in initial_args

    # Add restart argument
    builder = builder.add_argument("restart", "always")
    after_restart = builder.check_next()
    args_after_restart = [a.name for a in after_restart.arguments]
    print(f"After --restart: {len(args_after_restart)}")
    assert "restart" not in args_after_restart, "restart should be removed"
    assert "name" in args_after_restart, "name should still be available"

    # Add name argument
    builder = builder.add_argument("name", "myapp")
    after_name = builder.check_next()
    args_after_name = [a.name for a in after_name.arguments]
    print(f"After --name: {len(args_after_name)}")
    assert "restart" not in args_after_name
    assert "name" not in args_after_name

    print("✓ PASSED\n")


def test_immutability():
    """Test that builder operations are immutable."""
    print("=" * 60)
    print("TEST: Builder immutability")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)

    # Create builder chain
    b1 = cfg.builder()
    b2 = b1.add_command("run")
    b3 = b2.add_argument("detach")
    b4 = b3.add_argument("restart", "always")

    # Check each builder has its own state
    print(f"b1 command_path: {b1.command_path}")
    print(f"b2 command_path: {b2.command_path}")
    print(f"b3 arguments: {b3.arguments}")
    print(f"b4 arguments: {b4.arguments}")

    assert b1.command_path == []
    assert b2.command_path == ["run"]
    assert b3.arguments == {"detach": True}
    assert b4.arguments == {"detach": True, "restart": "always"}

    # Verify b3 wasn't modified by b4
    assert "restart" not in b3.arguments

    print("✓ PASSED\n")


def test_short_flag_support():
    """Test using short flags in the builder."""
    print("=" * 60)
    print("TEST: Short flag support")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)

    # Use short flags: -d for detach, -e for env
    builder = (
        cfg.builder()
        .add_command("run")
        .add_argument("d")  # Short for --detach
    )

    print(f"Arguments (using -d): {builder.arguments}")

    # Should be stored under canonical name
    assert "detach" in builder.arguments
    assert builder.arguments["detach"] is True

    print("✓ PASSED\n")


def test_error_on_unknown_command():
    """Test error handling for unknown command."""
    print("=" * 60)
    print("TEST: Error on unknown command")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)
    builder = cfg.builder()

    try:
        builder.add_command("unknown")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"Got expected error: {e}")
        assert "Unknown command" in str(e)

    print("✓ PASSED\n")


def test_error_on_unknown_argument():
    """Test error handling for unknown argument."""
    print("=" * 60)
    print("TEST: Error on unknown argument")
    print("=" * 60)

    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)
    builder = cfg.builder().add_command("run")

    try:
        builder.add_argument("unknown_arg", "value")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"Got expected error: {e}")
        assert "Unknown argument" in str(e)

    print("✓ PASSED\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PYDOCKER BUILDER PATTERN TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        test_root_level_suggestions,
        test_run_command_suggestions,
        test_value_provider_restart,
        test_value_provider_network,
        test_boolean_flag_suggestions,
        test_build_complete_command,
        test_stop_command_with_time,
        test_ps_command_with_flags,
        test_rm_command_with_force,
        test_argument_value_builder_flow,
        test_used_arguments_not_suggested,
        test_immutability,
        test_short_flag_support,
        test_error_on_unknown_command,
        test_error_on_unknown_argument,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            print()

    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
