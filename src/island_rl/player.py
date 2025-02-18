"""Player character module for Mediterranean Wanderer."""

from dataclasses import dataclass, field
from typing import Tuple, Optional, Union, Literal
import tcod.event
from .world import Island
from .interaction import InteractionSystem
from .inventory import Inventory, InventoryFullError
from .items import Item


@dataclass
class Player:
    """Player character class managing position and movement."""

    x: int  # Current x position
    y: int  # Current y position
    symbol: str = "@"  # Player character symbol
    color: Tuple[int, int, int] = (255, 255, 255)  # White
    inventory: Inventory = field(default_factory=Inventory)

    def __post_init__(self) -> None:
        """Initialize after dataclass creation."""
        if not isinstance(self.inventory, Inventory):
            self.inventory = Inventory()

    def move(self, dx: int, dy: int, island: Island) -> bool:
        """
        Attempt to move the player by the given delta.
        Returns True if movement was successful, False otherwise.
        """
        new_x = self.x + dx
        new_y = self.y + dy

        # Check map boundaries
        if not (0 <= new_x < island.width and 0 <= new_y < island.height):
            return False

        # Check if terrain is walkable (not deep water)
        terrain_height = island.get_tile(new_x, new_y)
        if terrain_height < 0.2:  # Deep water is not walkable
            return False

        # Update position if movement is valid
        self.x = new_x
        self.y = new_y
        return True

    def handle_input(
        self, 
        event: tcod.event.KeyDown, 
        island: Island,
        interaction_system: Optional[InteractionSystem] = None,
    ) -> Union[bool, Tuple[Literal["interact"], bool], Tuple[Literal["inventory"], None], None]:
        """
        Handle keyboard input for player movement, interaction, and inventory.
        Returns:
            - For movement: True if successful, False if blocked
            - For interaction: Tuple["interact", success]
            - For inventory: Tuple["inventory", None]
            - None if the event wasn't a valid action key
        """
        # Movement keys mapping (arrow keys and vi keys)
        movement_keys = {
            # Arrow keys
            tcod.event.KeySym.UP: (0, -1),
            tcod.event.KeySym.DOWN: (0, 1),
            tcod.event.KeySym.LEFT: (-1, 0),
            tcod.event.KeySym.RIGHT: (1, 0),
            # Vi keys
            tcod.event.KeySym.k: (0, -1),  # Up
            tcod.event.KeySym.j: (0, 1),  # Down
            tcod.event.KeySym.h: (-1, 0),  # Left
            tcod.event.KeySym.l: (1, 0),  # Right
        }

        # Check if the pressed key is a movement key
        if event.sym in movement_keys:
            dx, dy = movement_keys[event.sym]
            return self.move(dx, dy, island)

        # Check for interaction keys (space or enter)
        if event.sym in (tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN):
            if interaction_system:
                nearby = interaction_system.location_system.get_nearby_locations(
                    self.x, 
                    self.y, 
                    interaction_system.interaction_radius
                )
                # Allow interaction if there are any nearby locations
                return ("interact", len(nearby) > 0)
            return ("interact", False)

        # Check for inventory key (i)
        if event.sym == tcod.event.KeySym.i:
            return ("inventory", None)

        return None  # Not a valid action key

    def add_to_inventory(self, item: Item) -> bool:
        """
        Add an item to the player's inventory.
        Returns True if successful, False if inventory is full.
        """
        try:
            self.inventory.add_item(item)
            return True
        except InventoryFullError:
            return False
