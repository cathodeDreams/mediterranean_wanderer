"""Interaction system for Mediterranean Wanderer."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from .locations import Location, LocationSystem


@dataclass
class InteractionResult:
    """Result of an interaction attempt."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class InteractionSystem:
    """System for handling interactions with game objects."""

    def __init__(self, location_system: LocationSystem):
        """Initialize the interaction system."""
        self.location_system = location_system
        self.interaction_radius = 1  # How close player needs to be to interact

    def try_interact(self, player_x: int, player_y: int) -> InteractionResult:
        """Attempt to interact with something at the player's location, preferring exact matches."""
        nearby = self.location_system.get_nearby_locations(player_x, player_y, self.interaction_radius)

        if not nearby:
            return InteractionResult(
                success=False,
                message="Nothing interesting to interact with here.",
            )

        # First check for exact location matches
        exact_matches = [loc for loc in nearby if loc.x == player_x and loc.y == player_y]
        if exact_matches:
            location = exact_matches[0]
            if not location.discovered:
                location.discover()
                return InteractionResult(
                    success=True,
                    message=f"Discovered {location.name}!",
                    details={
                        "name": location.name,
                        "type": location.type.name,
                        "description": location.description,
                    },
                )
            else:
                return InteractionResult(
                    success=True,
                    message=f"Examining {location.name}...",
                    details={
                        "name": location.name,
                        "type": location.type.name,
                        "description": location.description,
                    },
                )

        # If no exact matches, prioritize undiscovered locations
        undiscovered = [loc for loc in nearby if not loc.discovered]
        if undiscovered:
            location = undiscovered[0]
            location.discover()
            return InteractionResult(
                success=True,
                message=f"Discovered {location.name}!",
                details={
                    "name": location.name,
                    "type": location.type.name,
                    "description": location.description,
                },
            )
        else:
            location = nearby[0]
            return InteractionResult(
                success=True,
                message=f"Examining {location.name}...",
                details={
                    "name": location.name,
                    "type": location.type.name,
                    "description": location.description,
                },
            )

    def _interact_with_location(self, location: Location) -> InteractionResult:
        """Handle interaction with a location."""
        if not location.discovered:
            location.discover()
            return InteractionResult(
                success=True,
                message=f"Discovered {location.name}!",
                details={
                    "name": location.name,
                    "type": location.type.name,
                    "description": location.description,
                },
            )
        
        return InteractionResult(
            success=True,
            message=f"Examining {location.name}...",
            details={
                "name": location.name,
                "type": location.type.name,
                "description": location.description,
            },
        ) 