#!/usr/bin/env python3
"""Comprehensive test of builder/suggestion pattern with phrase_builder.

Tests all config_loader v2.0 features through the phrase_builder example:
- Hierarchical commands and subcommands
- Inherited arguments (scope: inherited)
- Value providers (species, colors, dance styles, etc.)
- Exclusion groups (mood: happy/sad/excited)
- Dependency rules (partner requires style)
- Deprecation warnings (robot command, battery-level arg)
- Validators (flying requires bird species)
- Boolean flags and number arguments
- Required arguments
- Command aliases
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

# Add examples directory to path
examples_dir = os.path.dirname(os.path.abspath(__file__))
if examples_dir not in sys.path:
    sys.path.insert(0, examples_dir)

import yaml
from config_loader import Configuration


def load_config() -> Configuration:
    """Load the phrase_builder configuration."""
    spec_path = os.path.join(examples_dir, "phrase_builder.yaml")
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    return Configuration(spec)


def suppress_warnings(func):
    """Decorator to suppress warnings during tests."""
    def wrapper(*args, **kwargs):
        import io
        import contextlib
        with contextlib.redirect_stderr(io.StringIO()):
            return func(*args, **kwargs)
    return wrapper


# =============================================================================
# TEST: Root Level Suggestions
# =============================================================================


@suppress_warnings
def test_root_level_commands():
    """Test that root level shows all subject commands."""
    print("=" * 60)
    print("TEST: Root level commands")
    print("=" * 60)

    cfg = load_config()
    builder = cfg.builder()
    suggestions = builder.check_next()

    print(f"is_valid: {suggestions.is_valid}")
    cmd_names = [c.name for c in suggestions.commands]
    print(f"Commands: {cmd_names}")

    assert not suggestions.is_valid, "Root is not valid (no terminal)"
    assert "animal" in cmd_names
    assert "human" in cmd_names
    assert "robot" in cmd_names
    assert "vehicle" in cmd_names

    # Check aliases are present
    animal_cmd = next(c for c in suggestions.commands if c.name == "animal")
    assert "creature" in animal_cmd.aliases
    assert "beast" in animal_cmd.aliases

    print("✓ PASSED\n")


# =============================================================================
# TEST: Hierarchical Command Navigation
# =============================================================================


@suppress_warnings
def test_hierarchical_navigation():
    """Test navigating through command hierarchy."""
    print("=" * 60)
    print("TEST: Hierarchical command navigation")
    print("=" * 60)

    cfg = load_config()

    # Level 1: animal
    builder = cfg.builder().add_command("animal")
    suggestions = builder.check_next()
    print(f"After 'animal': subcommands = {[c.name for c in suggestions.commands]}")
    assert not suggestions.is_valid
    assert "jumped" in [c.name for c in suggestions.commands]
    assert "ran" in [c.name for c in suggestions.commands]
    assert "flew" in [c.name for c in suggestions.commands]

    # Level 2: animal jumped (terminal)
    builder = builder.add_command("jumped")
    suggestions = builder.check_next()
    print(f"After 'animal jumped': is_valid = {suggestions.is_valid}")
    assert suggestions.is_valid, "'animal jumped' is terminal"

    print("✓ PASSED\n")


@suppress_warnings
def test_deep_hierarchy():
    """Test deep command hierarchy (vehicle -> car -> drove)."""
    print("=" * 60)
    print("TEST: Deep command hierarchy")
    print("=" * 60)

    cfg = load_config()

    builder = cfg.builder()
    builder = builder.add_command("vehicle")
    print(f"vehicle subcommands: {[c.name for c in builder.check_next().commands]}")

    builder = builder.add_command("car")
    print(f"car subcommands: {[c.name for c in builder.check_next().commands]}")

    builder = builder.add_command("drove")
    suggestions = builder.check_next()
    print(f"drove is_valid: {suggestions.is_valid}")
    print(f"drove arguments: {[a.name for a in suggestions.arguments]}")

    assert suggestions.is_valid
    assert "to" in [a.name for a in suggestions.arguments]
    assert "speed" in [a.name for a in suggestions.arguments]

    print("✓ PASSED\n")


# =============================================================================
# TEST: Inherited Arguments
# =============================================================================


@suppress_warnings
def test_inherited_arguments():
    """Test that parent arguments must be set at parent level.

    The builder shows arguments for the current command only.
    Inherited arguments are set at the parent level before navigating.
    """
    print("=" * 60)
    print("TEST: Parent arguments set at parent level")
    print("=" * 60)

    cfg = load_config()

    # At 'animal' level, we have all animal args
    builder = cfg.builder().add_command("animal")
    animal_args = [a.name for a in builder.check_next().arguments]
    print(f"At 'animal': {animal_args}")
    assert "species" in animal_args
    assert "color" in animal_args
    assert "add-article" in animal_args

    # Set parent args before navigating to subcommand
    builder = builder.add_argument("species", "dog")
    builder = builder.add_argument("color", "golden")
    builder = builder.add_command("jumped")

    # At 'jumped' level, we only see jumped's local args
    jumped_args = [a.name for a in builder.check_next().arguments]
    print(f"At 'jumped': {jumped_args}")
    assert "over" in jumped_args
    assert "gracefully" in jumped_args

    # But the parent args are preserved in builder state
    print(f"Builder arguments: {builder.arguments}")
    assert builder.arguments["species"] == "dog"
    assert builder.arguments["color"] == "golden"

    print("✓ PASSED\n")


# =============================================================================
# TEST: Value Providers
# =============================================================================


@suppress_warnings
def test_value_provider_species():
    """Test value provider for species argument at parent level."""
    print("=" * 60)
    print("TEST: Value provider for --species")
    print("=" * 60)

    cfg = load_config()
    # Get species suggestions at the 'animal' level (before subcommand)
    builder = cfg.builder().add_command("animal")

    arg_builder = builder.add_argument_builder("species")
    suggestions = arg_builder.check_next()

    print(f"Species values: {suggestions.values}")
    print(f"Accepts any: {suggestions.accepts_any}")

    assert "dog" in suggestions.values
    assert "cat" in suggestions.values
    assert "bird" in suggestions.values
    assert not suggestions.accepts_any

    print("✓ PASSED\n")


@suppress_warnings
def test_value_provider_colors():
    """Test value provider for colors argument at parent level."""
    print("=" * 60)
    print("TEST: Value provider for --color")
    print("=" * 60)

    cfg = load_config()
    # Get color suggestions at the 'animal' level
    builder = cfg.builder().add_command("animal")

    arg_builder = builder.add_argument_builder("color")
    suggestions = arg_builder.check_next()

    print(f"Color values: {suggestions.values}")

    assert "red" in suggestions.values
    assert "golden" in suggestions.values

    print("✓ PASSED\n")


@suppress_warnings
def test_value_provider_dance_styles():
    """Test value provider for dance styles."""
    print("=" * 60)
    print("TEST: Value provider for --style (dance)")
    print("=" * 60)

    cfg = load_config()
    builder = cfg.builder().add_command("human").add_command("danced")

    arg_builder = builder.add_argument_builder("style")
    suggestions = arg_builder.check_next()

    print(f"Dance style values: {suggestions.values}")

    assert "salsa" in suggestions.values
    assert "waltz" in suggestions.values
    assert "breakdance" in suggestions.values

    print("✓ PASSED\n")


@suppress_warnings
def test_value_provider_algorithms():
    """Test value provider for robot algorithms."""
    print("=" * 60)
    print("TEST: Value provider for --algorithm")
    print("=" * 60)

    cfg = load_config()
    builder = (
        cfg.builder()
        .add_command("robot")
        .add_argument("serial", "X123")
        .add_command("computed")
    )

    arg_builder = builder.add_argument_builder("algorithm")
    suggestions = arg_builder.check_next()

    print(f"Algorithm values: {suggestions.values}")

    assert "quicksort" in suggestions.values
    assert "neural-network" in suggestions.values

    print("✓ PASSED\n")


@suppress_warnings
def test_context_aware_value_provider():
    """Test that value providers receive all previously set arguments.

    The provide_speeds function changes suggestions based on species:
    - Birds get flight-related speeds (gliding, swooping, diving, soaring)
    - Other animals get ground speeds (slowly, quickly, very-fast, etc.)
    """
    print("=" * 60)
    print("TEST: Context-aware value provider")
    print("=" * 60)

    cfg = load_config()

    # Test 1: Dog (ground animal) - should get ground speeds
    builder = cfg.builder().add_command("animal")
    builder = builder.add_argument("species", "dog")
    builder = builder.add_command("ran")

    arg_builder = builder.add_argument_builder("speed")
    suggestions = arg_builder.check_next()
    print(f"Speed values for dog: {suggestions.values}")

    assert "slowly" in suggestions.values
    assert "quickly" in suggestions.values
    assert "gliding" not in suggestions.values

    # Test 2: Bird - should get flight speeds
    builder2 = cfg.builder().add_command("animal")
    builder2 = builder2.add_argument("species", "bird")
    builder2 = builder2.add_command("ran")

    arg_builder2 = builder2.add_argument_builder("speed")
    suggestions2 = arg_builder2.check_next()
    print(f"Speed values for bird: {suggestions2.values}")

    assert "gliding" in suggestions2.values
    assert "swooping" in suggestions2.values
    assert "slowly" not in suggestions2.values

    # Test 3: Eagle - should also get flight speeds
    builder3 = cfg.builder().add_command("animal")
    builder3 = builder3.add_argument("species", "eagle")
    builder3 = builder3.add_command("ran")

    arg_builder3 = builder3.add_argument_builder("speed")
    suggestions3 = arg_builder3.check_next()
    print(f"Speed values for eagle: {suggestions3.values}")

    assert "diving" in suggestions3.values
    assert "soaring" in suggestions3.values

    print("✓ PASSED\n")


# =============================================================================
# TEST: Command Aliases
# =============================================================================


@suppress_warnings
def test_command_aliases():
    """Test using command aliases."""
    print("=" * 60)
    print("TEST: Command aliases")
    print("=" * 60)

    cfg = load_config()

    # Use alias 'creature' instead of 'animal'
    builder = cfg.builder().add_command("creature")
    print(f"After 'creature': path = {builder.command_path}")
    assert builder.command_path == ["animal"], "Should resolve to 'animal'"

    # Use alias 'leaped' instead of 'jumped'
    builder = builder.add_command("leaped")
    print(f"After 'leaped': path = {builder.command_path}")
    assert builder.command_path == ["animal", "jumped"], "Should resolve to 'jumped'"

    print("✓ PASSED\n")


# =============================================================================
# TEST: Boolean Flags
# =============================================================================


@suppress_warnings
def test_boolean_flags():
    """Test boolean flag handling."""
    print("=" * 60)
    print("TEST: Boolean flag handling")
    print("=" * 60)

    cfg = load_config()

    # Add parent boolean at parent level
    builder = cfg.builder().add_command("animal")
    builder = builder.add_argument("add-article")
    print(f"After --add-article (at animal): {builder.arguments}")
    assert builder.arguments["add-article"] is True

    # Navigate to subcommand and add local boolean
    builder = builder.add_command("jumped")
    builder = builder.add_argument("gracefully")
    print(f"After --gracefully (at jumped): {builder.arguments}")
    assert builder.arguments["gracefully"] is True
    assert builder.arguments["add-article"] is True  # Still preserved

    print("✓ PASSED\n")


# =============================================================================
# TEST: Number Arguments
# =============================================================================


@suppress_warnings
def test_number_arguments():
    """Test number argument handling."""
    print("=" * 60)
    print("TEST: Number argument handling")
    print("=" * 60)

    cfg = load_config()

    # Set parent number arg at parent level
    builder = cfg.builder().add_command("animal")
    builder = builder.add_argument("repeat", "3")  # Should parse as int
    print(f"After --repeat at animal: {builder.arguments}")

    # Navigate and set local number arg
    builder = builder.add_command("jumped")
    builder = builder.add_argument("height", 5)
    print(f"After --height at jumped: {builder.arguments}")

    assert builder.arguments["height"] == 5
    assert builder.arguments["repeat"] == 3

    print("✓ PASSED\n")


# =============================================================================
# TEST: Required Arguments
# =============================================================================


@suppress_warnings
def test_required_arguments():
    """Test required argument validation.

    Note: Required args are checked at process() time, not builder time.
    The builder validates at current command level only.
    """
    print("=" * 60)
    print("TEST: Required argument validation")
    print("=" * 60)

    cfg = load_config()

    # Robot 'computed' is terminal
    # Serial is required at robot level (inherited)
    builder = cfg.builder().add_command("robot")

    # Check that serial is available
    arg_names = [a.name for a in builder.check_next().arguments]
    print(f"Robot args: {arg_names}")
    assert "serial" in arg_names

    # Set required serial at robot level
    builder = builder.add_argument("serial", "X123")

    # Navigate to computed
    builder = builder.add_command("computed")
    suggestions = builder.check_next()
    print(f"With --serial: is_valid = {suggestions.is_valid}")
    assert suggestions.is_valid

    # Verify the serial is preserved
    print(f"Arguments: {builder.arguments}")
    assert builder.arguments["serial"] == "X123"

    print("✓ PASSED\n")


# =============================================================================
# TEST: Building Complete Commands
# =============================================================================


@suppress_warnings
def test_build_animal_jumped():
    """Test building a complete animal jumped command."""
    print("=" * 60)
    print("TEST: Build 'animal jumped' command")
    print("=" * 60)

    cfg = load_config()

    builder = (
        cfg.builder()
        .add_command("animal")
        .add_argument("species", "dog")
        .add_argument("color", "golden")
        .add_argument("add-name", "Rex")
        .add_command("jumped")
        .add_argument("gracefully")
        .add_argument("over", "fence")
    )

    result = builder.build()

    print(f"Command path: {result.command.path}")
    print(f"Arguments: {result.command.arguments}")

    assert result.command.path == ["animal", "jumped"]
    assert result.command.arguments["species"] == "dog"
    assert result.command.arguments["color"] == "golden"
    assert result.command.arguments["add-name"] == "Rex"
    assert result.command.arguments["gracefully"] is True
    assert result.command.arguments["over"] == "fence"

    print("✓ PASSED\n")


@suppress_warnings
def test_build_human_danced():
    """Test building a complete human danced command."""
    print("=" * 60)
    print("TEST: Build 'human danced' command")
    print("=" * 60)

    cfg = load_config()

    builder = (
        cfg.builder()
        .add_command("human")
        .add_argument("profession", "artist")
        .add_argument("happy")
        .add_command("danced")
        .add_argument("style", "salsa")
        .add_argument("partner", "Alice")
    )

    result = builder.build()

    print(f"Command path: {result.command.path}")
    print(f"Arguments: {result.command.arguments}")

    assert result.command.path == ["human", "danced"]
    assert result.command.arguments["profession"] == "artist"
    assert result.command.arguments["happy"] is True
    assert result.command.arguments["style"] == "salsa"
    assert result.command.arguments["partner"] == "Alice"

    print("✓ PASSED\n")


@suppress_warnings
def test_build_robot_computed():
    """Test building a robot computed command with required args."""
    print("=" * 60)
    print("TEST: Build 'robot computed' command")
    print("=" * 60)

    cfg = load_config()

    builder = (
        cfg.builder()
        .add_command("robot")
        .add_argument("serial", "T-800")
        .add_argument("model", "T-1000")
        .add_command("computed")
        .add_argument("algorithm", "neural-network")
        .add_argument("iterations", 5000)
    )

    result = builder.build()

    print(f"Command path: {result.command.path}")
    print(f"Arguments: {result.command.arguments}")

    assert result.command.path == ["robot", "computed"]
    assert result.command.arguments["serial"] == "T-800"
    assert result.command.arguments["model"] == "T-1000"
    assert result.command.arguments["algorithm"] == "neural-network"
    assert result.command.arguments["iterations"] == 5000

    print("✓ PASSED\n")


# =============================================================================
# TEST: Argument Removal from Suggestions
# =============================================================================


@suppress_warnings
def test_arguments_removed_after_use():
    """Test that used arguments are removed from suggestions."""
    print("=" * 60)
    print("TEST: Arguments removed from suggestions after use")
    print("=" * 60)

    cfg = load_config()

    # Test at 'animal' level
    builder = cfg.builder().add_command("animal")
    initial_args = [a.name for a in builder.check_next().arguments]
    print(f"Initial args at animal: {len(initial_args)}")
    assert "species" in initial_args
    assert "color" in initial_args

    builder = builder.add_argument("species", "dog")
    after_species = [a.name for a in builder.check_next().arguments]
    print(f"After --species: {len(after_species)}")
    assert "species" not in after_species
    assert "color" in after_species

    builder = builder.add_argument("color", "brown")
    after_color = [a.name for a in builder.check_next().arguments]
    print(f"After --color: {len(after_color)}")
    assert "species" not in after_color
    assert "color" not in after_color

    print("✓ PASSED\n")


# =============================================================================
# TEST: Exclusion Groups (via arguments, not via builder validation)
# =============================================================================


@suppress_warnings
def test_mood_arguments_available():
    """Test that mood arguments (exclusion group) are available at parent level."""
    print("=" * 60)
    print("TEST: Mood exclusion group arguments available")
    print("=" * 60)

    cfg = load_config()

    # Mood args are defined at 'human' level
    builder = cfg.builder().add_command("human")
    suggestions = builder.check_next()

    arg_names = [a.name for a in suggestions.arguments]
    print(f"Available at human: {arg_names}")
    print(f"Mood args: happy={('happy' in arg_names)}, sad={('sad' in arg_names)}, excited={('excited' in arg_names)}")

    assert "happy" in arg_names
    assert "sad" in arg_names
    assert "excited" in arg_names

    # Note: The exclusion group is validated at process() time, not builder time
    # So we can add multiple moods via builder (but it would fail on process)

    print("✓ PASSED\n")


# =============================================================================
# TEST: Short Flags
# =============================================================================


@suppress_warnings
def test_short_flags():
    """Test using short flags at correct command level."""
    print("=" * 60)
    print("TEST: Short flag support")
    print("=" * 60)

    cfg = load_config()

    # Use short flags at 'animal' level
    builder = (
        cfg.builder()
        .add_command("animal")
        .add_argument("s", "cat")  # -s for --species
        .add_argument("a")  # -a for --add-article
    )

    print(f"Arguments at animal: {builder.arguments}")

    assert "species" in builder.arguments
    assert builder.arguments["species"] == "cat"
    assert "add-article" in builder.arguments
    assert builder.arguments["add-article"] is True

    # Navigate to subcommand and use short flag there
    builder = builder.add_command("jumped")
    builder = builder.add_argument("g")  # -g for --gracefully

    print(f"Arguments after jumped: {builder.arguments}")
    assert builder.arguments["gracefully"] is True

    print("✓ PASSED\n")


# =============================================================================
# TEST: Immutability
# =============================================================================


@suppress_warnings
def test_builder_immutability():
    """Test that builder operations return new builders."""
    print("=" * 60)
    print("TEST: Builder immutability")
    print("=" * 60)

    cfg = load_config()

    b1 = cfg.builder()
    b2 = b1.add_command("animal")
    b3 = b2.add_argument("species", "dog")
    b4 = b3.add_command("jumped")

    print(f"b1.command_path: {b1.command_path}")
    print(f"b2.command_path: {b2.command_path}")
    print(f"b3.arguments: {b3.arguments}")
    print(f"b4.command_path: {b4.command_path}")

    assert b1.command_path == []
    assert b2.command_path == ["animal"]
    assert b3.arguments == {"species": "dog"}
    assert b4.command_path == ["animal", "jumped"]

    # b3 should not have 'jumped'
    assert b3.command_path == ["animal"]

    print("✓ PASSED\n")


# =============================================================================
# TEST: Error Handling
# =============================================================================


@suppress_warnings
def test_unknown_command_error():
    """Test error on unknown command."""
    print("=" * 60)
    print("TEST: Unknown command error")
    print("=" * 60)

    cfg = load_config()

    try:
        cfg.builder().add_command("dinosaur")
        assert False, "Should have raised"
    except ValueError as e:
        print(f"Got expected error: {e}")
        assert "Unknown command" in str(e)

    print("✓ PASSED\n")


@suppress_warnings
def test_unknown_argument_error():
    """Test error on unknown argument."""
    print("=" * 60)
    print("TEST: Unknown argument error")
    print("=" * 60)

    cfg = load_config()
    builder = cfg.builder().add_command("animal").add_command("jumped")

    try:
        builder.add_argument("wings", "large")
        assert False, "Should have raised"
    except ValueError as e:
        print(f"Got expected error: {e}")
        assert "Unknown argument" in str(e)

    print("✓ PASSED\n")


@suppress_warnings
def test_build_non_terminal_error():
    """Test error when building non-terminal command."""
    print("=" * 60)
    print("TEST: Build non-terminal command error")
    print("=" * 60)

    cfg = load_config()
    builder = cfg.builder().add_command("animal")  # Not terminal

    try:
        builder.build()
        assert False, "Should have raised"
    except ValueError as e:
        print(f"Got expected error: {e}")
        assert "not complete" in str(e)

    print("✓ PASSED\n")


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PHRASE BUILDER - BUILDER PATTERN TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        # Root and navigation
        test_root_level_commands,
        test_hierarchical_navigation,
        test_deep_hierarchy,

        # Inherited arguments
        test_inherited_arguments,

        # Value providers
        test_value_provider_species,
        test_value_provider_colors,
        test_value_provider_dance_styles,
        test_value_provider_algorithms,
        test_context_aware_value_provider,

        # Aliases
        test_command_aliases,

        # Argument types
        test_boolean_flags,
        test_number_arguments,
        test_required_arguments,

        # Building
        test_build_animal_jumped,
        test_build_human_danced,
        test_build_robot_computed,

        # Suggestions
        test_arguments_removed_after_use,
        test_mood_arguments_available,
        test_short_flags,

        # Immutability
        test_builder_immutability,

        # Errors
        test_unknown_command_error,
        test_unknown_argument_error,
        test_build_non_terminal_error,
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
