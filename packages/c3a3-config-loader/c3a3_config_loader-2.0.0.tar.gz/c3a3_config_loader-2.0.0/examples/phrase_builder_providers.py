# SPDX-License-Identifier: Prosperity-3.0.0
# © 2025 ã — see LICENSE.md for terms.

"""Value providers and validators for phrase_builder example.

This module provides dynamic value suggestions and validation for the
phrase_builder CLI, demonstrating config_loader's extensibility features.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from config_loader import ValidatorContext


# =============================================================================
# ANIMAL VALUE PROVIDERS
# =============================================================================


def provide_animal_species(ctx: Any) -> List[str]:
    """Provide animal species options."""
    return [
        "dog",
        "cat",
        "bird",
        "fish",
        "rabbit",
        "horse",
        "elephant",
        "butterfly",
        "eagle",
        "dolphin",
    ]


def provide_colors(ctx: Any) -> List[str]:
    """Provide color options."""
    return [
        "red",
        "blue",
        "green",
        "yellow",
        "orange",
        "purple",
        "black",
        "white",
        "golden",
        "silver",
    ]


def provide_speeds(ctx: Any) -> List[str]:
    """Provide speed adverbs based on species.

    Demonstrates context-aware value provider:
    - Birds get flight-related speeds
    - Other animals get ground speeds
    """
    species = ctx.parsed_args.get("species") if ctx else None

    if species in ("bird", "eagle", "butterfly"):
        return ["gliding", "swooping", "diving", "soaring"]

    return [
        "slowly",
        "quickly",
        "very-fast",
        "leisurely",
        "frantically",
    ]


def provide_directions(ctx: Any) -> List[str]:
    """Provide direction options."""
    return ["north", "south", "east", "west", "uphill", "downhill", "in-circles"]


# Flying species for validation
FLYING_SPECIES = {"bird", "butterfly", "eagle", "bat", "flying-fish"}


def validate_can_fly(args: Dict[str, Any], ctx: "ValidatorContext") -> Optional[str]:
    """Validate that the animal species can fly.

    Returns None if valid, error message if invalid.
    """
    species = args.get("species")

    # If no species specified, allow it (could be a flying creature)
    if not species:
        return None

    if species.lower() not in FLYING_SPECIES:
        return f"A {species} cannot fly! Flying species: {', '.join(sorted(FLYING_SPECIES))}"

    return None


# =============================================================================
# HUMAN VALUE PROVIDERS
# =============================================================================


def provide_professions(ctx: Any) -> List[str]:
    """Provide profession options."""
    return [
        "doctor",
        "engineer",
        "artist",
        "teacher",
        "chef",
        "pilot",
        "scientist",
        "musician",
        "athlete",
        "writer",
    ]


def provide_dance_styles(ctx: Any) -> List[str]:
    """Provide dance style options."""
    return [
        "salsa",
        "waltz",
        "tango",
        "breakdance",
        "ballet",
        "hip-hop",
        "swing",
        "flamenco",
    ]


# =============================================================================
# ROBOT VALUE PROVIDERS
# =============================================================================


def provide_robot_models(ctx: Any) -> List[str]:
    """Provide robot model options."""
    return [
        "T-1000",
        "R2-D2",
        "C-3PO",
        "WALL-E",
        "Optimus",
        "Bender",
        "Data",
        "HAL-9000",
    ]


def provide_algorithms(ctx: Any) -> List[str]:
    """Provide algorithm options."""
    return [
        "quicksort",
        "neural-network",
        "genetic",
        "dijkstra",
        "a-star",
        "monte-carlo",
        "gradient-descent",
    ]


# =============================================================================
# VEHICLE VALUE PROVIDERS
# =============================================================================


def provide_vehicle_brands(ctx: Any) -> List[str]:
    """Provide vehicle brand options."""
    return [
        "Toyota",
        "Ford",
        "Tesla",
        "BMW",
        "Honda",
        "Ferrari",
        "Harley",
        "Trek",
    ]
