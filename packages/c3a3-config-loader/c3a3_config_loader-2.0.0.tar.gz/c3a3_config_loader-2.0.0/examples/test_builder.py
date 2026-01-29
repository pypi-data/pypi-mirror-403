#!/usr/bin/env python3
"""Test and demonstrate the CommandBuilder API for pydocker.

This example shows how to use the builder pattern for incremental
command construction with suggestions at each step.
"""

import sys
import os

# Add examples directory to path for loading validators
examples_dir = os.path.dirname(os.path.abspath(__file__))
if examples_dir not in sys.path:
    sys.path.insert(0, examples_dir)

import yaml
from config_loader import Configuration


def main() -> None:
    # Load spec
    with open(os.path.join(examples_dir, "pydocker.yaml")) as f:
        spec = yaml.safe_load(f)

    cfg = Configuration(spec)
    builder = cfg.builder()

    # =========================================================================
    # Step 1: At root level - what commands are available?
    # =========================================================================
    print("=== At root level ===")
    suggestions = builder.check_next()
    print(f"is_valid: {suggestions.is_valid}")
    print(f"Commands: {', '.join(c.name for c in suggestions.commands)}")
    print()

    # =========================================================================
    # Step 2: Add the "run" command
    # =========================================================================
    print("=== After adding 'run' ===")
    builder = builder.add_command("run")
    suggestions = builder.check_next()
    print(f"is_valid: {suggestions.is_valid}")
    print(f"Subcommands: {', '.join(c.name for c in suggestions.commands) or 'none'}")
    print("Arguments:")
    for arg in suggestions.arguments:
        flag = f"--{arg.name}"
        if arg.short:
            flag += f" (-{arg.short})"
        req = " [REQUIRED]" if arg.required else ""
        val = " (flag)" if not arg.expects_value else ""
        print(f"  {flag}{req}{val}")
    print()

    # =========================================================================
    # Step 3: Get suggestions for restart policy
    # =========================================================================
    print("=== Value suggestions for --restart ===")
    arg_builder = builder.add_argument_builder("restart")
    value_suggestions = arg_builder.check_next()
    print(f"Valid values: {value_suggestions.values}")
    print(f"Accepts any value: {value_suggestions.accepts_any}")
    print()

    # =========================================================================
    # Step 4: Get suggestions for network (from Docker API)
    # =========================================================================
    print("=== Value suggestions for --network ===")
    arg_builder = builder.add_argument_builder("network")
    value_suggestions = arg_builder.check_next()
    print(f"Available networks: {value_suggestions.values or '(none or Docker not running)'}")
    print()

    # =========================================================================
    # Step 5: Build a complete command
    # =========================================================================
    print("=== Building: pydocker run -d --restart=always --name=myapp ===")
    final_builder = (
        builder
        .add_argument("detach")  # Boolean flag, no value needed
        .add_argument("restart", "always")
        .add_argument("name", "myapp")
    )

    # Check if valid
    suggestions = final_builder.check_next()
    print(f"is_valid: {suggestions.is_valid}")
    if suggestions.errors:
        print(f"Errors: {suggestions.errors}")

    # Build the result
    if suggestions.is_valid:
        result = final_builder.build()
        print(f"Command path: {result.command.path}")
        print(f"Arguments: {result.command.arguments}")
        print(f"Terminal: {result.command.terminal}")
    print()

    # =========================================================================
    # Step 6: Try to build invalid command (missing required args)
    # =========================================================================
    print("=== Demonstrating validation ===")
    # Navigate to 'ps' command and check its state
    ps_builder = cfg.builder().add_command("ps")
    ps_suggestions = ps_builder.check_next()
    print(f"'pydocker ps' is_valid: {ps_suggestions.is_valid}")

    # Try to get --format argument suggestions
    print("\nBuilder API provides incremental construction with validation!")


if __name__ == "__main__":
    main()
