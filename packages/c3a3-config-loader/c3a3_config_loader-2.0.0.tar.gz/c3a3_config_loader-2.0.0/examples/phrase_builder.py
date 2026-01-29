#!/usr/bin/env python3
# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""Phrase Builder - Synthetic example demonstrating config_loader v2.0 features.

This CLI builds phrases based on commands and arguments, demonstrating:
- Hierarchical commands (subject -> action)
- Inherited arguments (add-article, uppercase, repeat)
- Value providers (species, colors, dance styles, etc.)
- Exclusion groups (mood: happy/sad/excited)
- Dependency rules (partner requires style)
- Deprecation warnings (robot command, battery-level arg)
- Validators (flying requires bird species)
- Variadic arguments (multiple music genres)

Usage:
    phrase_builder animal jumped fence
    phrase_builder animal jumped fence --add-article
    phrase_builder animal --species dog --color golden jumped fence --gracefully
    phrase_builder human --happy danced --style salsa --partner Alice
    phrase_builder robot --serial X123 computed --algorithm quicksort
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional

# Add examples directory to path for value providers
examples_dir = os.path.dirname(os.path.abspath(__file__))
if examples_dir not in sys.path:
    sys.path.insert(0, examples_dir)

import yaml
from config_loader import Configuration, ProcessingResult


def load_config() -> Configuration:
    """Load the phrase_builder configuration."""
    spec_path = os.path.join(examples_dir, "phrase_builder.yaml")
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    return Configuration(spec)


def build_phrase(result: ProcessingResult) -> str:
    """Build a phrase from the processing result.

    Args:
        result: The parsed command result.

    Returns:
        The constructed phrase.
    """
    path = result.command.path
    args = result.command.arguments
    positional = result.command.positional

    # Extract common options
    add_article = args.get("add-article", False)
    add_name = args.get("add-name")
    uppercase = args.get("uppercase", False)
    repeat = args.get("repeat", 1)

    # Build subject
    subject = path[0]  # animal, human, robot, vehicle

    # Add adjectives before subject
    adjectives: List[str] = []
    if args.get("color"):
        adjectives.append(args["color"])
    if args.get("happy"):
        adjectives.append("happy")
    if args.get("sad"):
        adjectives.append("sad")
    if args.get("excited"):
        adjectives.append("excited")

    # Build subject with species/profession
    if args.get("species"):
        subject = args["species"]
    elif args.get("profession"):
        subject = args["profession"]
    elif args.get("model"):
        subject = f"{args['model']} robot"

    # Add adjectives
    if adjectives:
        subject = f"{' '.join(adjectives)} {subject}"

    # Add article
    if add_article:
        subject = f"the {subject}"

    # Add name
    if add_name:
        subject = f"{subject} named {add_name}"

    # Build action
    action = path[-1] if len(path) > 1 else "exists"

    # Get the object (from positional or arguments)
    obj = ""
    if positional:
        obj = " ".join(str(p) for p in positional)

    # Build action modifiers based on command
    action_parts = [action]

    # Handle different actions
    if action in ["jumped", "leaped", "hopped"]:
        if args.get("gracefully"):
            action_parts.insert(0, "gracefully")
        if args.get("with-style"):
            action_parts.append("with style")
        if args.get("over"):
            obj = args["over"]
        if args.get("height"):
            action_parts.append(f"({args['height']}m high)")
        if args.get("shouting"):
            action_parts.append(f'shouting "{args["shouting"]}"')

    elif action in ["ran", "sprinted", "dashed"]:
        if args.get("speed"):
            action_parts.insert(0, args["speed"])
        if args.get("direction"):
            action_parts.append(f"heading {args['direction']}")
        if args.get("chasing"):
            obj = args["chasing"]
            action_parts.append("chasing")

    elif action in ["flew", "soared"]:
        if args.get("altitude"):
            action_parts.append(f"at {args['altitude']}m altitude")
        if args.get("destination"):
            action_parts.append(f"towards {args['destination']}")

    elif action in ["danced", "grooved", "boogied"]:
        if args.get("style"):
            action_parts.append(f"the {args['style']}")
        if args.get("partner"):
            action_parts.append(f"with {args['partner']}")
        if args.get("music"):
            genres = args["music"]
            if isinstance(genres, list):
                action_parts.append(f"to {' and '.join(genres)} music")
            else:
                action_parts.append(f"to {genres} music")

    elif action == "worked":
        if args.get("task"):
            action_parts.append(f"on {args['task']}")
        if args.get("hours"):
            action_parts.append(f"for {args['hours']} hours")
        if args.get("diligently"):
            action_parts.insert(0, "diligently")

    elif action in ["computed", "calculated", "processed"]:
        if args.get("algorithm"):
            action_parts.append(f"using {args['algorithm']}")
        if args.get("iterations"):
            action_parts.append(f"({args['iterations']} iterations)")
        if args.get("result"):
            action_parts.append(f"= {args['result']}")

    elif action == "beeped":
        if args.get("loudly"):
            action_parts.insert(0, "loudly")
        if args.get("frequency"):
            action_parts.append(f"at {args['frequency']}Hz")
        if args.get("times"):
            action_parts.append(f"{args['times']} times")

    elif action == "transformed":
        if args.get("dramatically"):
            action_parts.insert(0, "dramatically")
        if args.get("into"):
            action_parts.append(f"into {args['into']}")

    elif action == "drove":
        if args.get("speed"):
            action_parts.append(f"at {args['speed']}km/h")
        if args.get("to"):
            action_parts.append(f"to {args['to']}")

    elif action == "parked":
        if args.get("at"):
            action_parts.append(f"at {args['at']}")

    elif action == "rode":
        if args.get("uphill"):
            action_parts.insert(0, "uphill")
        if args.get("through"):
            action_parts.append(f"through {args['through']}")

    elif action == "crashed":
        if args.get("spectacularly"):
            action_parts.insert(0, "spectacularly")
        if args.get("into"):
            action_parts.append(f"into {args['into']}")

    # Build the action string
    action_str = " ".join(action_parts)

    # Build final phrase
    if obj:
        if add_article and not obj.startswith("the "):
            obj = f"the {obj}"
        phrase = f"{subject} {action_str} {obj}"
    else:
        phrase = f"{subject} {action_str}"

    # Apply transformations
    if uppercase:
        phrase = phrase.upper()

    # Repeat if requested
    if repeat > 1:
        phrase = "\n".join([phrase] * repeat)

    return phrase


def main() -> int:
    """Main entry point."""
    try:
        cfg = load_config()
        result = cfg.process(sys.argv[1:])

        # Check if we have a valid command
        if not result.command or not result.command.terminal:
            print("Error: Incomplete command. Use --help for usage.", file=sys.stderr)
            return 1

        # Build and print the phrase
        phrase = build_phrase(result)
        print(phrase)
        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
