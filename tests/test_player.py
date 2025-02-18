"""Tests for the player module."""

import pytest
import numpy as np
import tcod.event
from island_rl.player import Player
from island_rl.world import Island
from island_rl.interaction import InteractionSystem
from island_rl.locations import LocationSystem, Location, LocationType
from island_rl.items import ItemFactory, ItemType
from island_rl.inventory import InventoryFullError


@pytest.fixture
def island() -> Island:
    """Create a test island."""
    island = Island(width=50, height=50)
    # Create a simple terrain with walkable land
    island.terrain = np.full((50, 50), 0.6, dtype=np.float64)
    return island


@pytest.fixture
def player() -> Player:
    """Create a test player."""
    return Player(x=25, y=25)


@pytest.fixture
def location_system(island: Island) -> LocationSystem:
    """Create a test location system."""
    if island.terrain is None:
        raise ValueError("Island terrain must be initialized")
    system = LocationSystem(island.terrain)
    # Add a test location near the player's starting position
    test_location = Location(
        x=26,
        y=26,
        type=LocationType.VILLAGE,
        name="Test Village",
        description="A test village",
    )
    system.locations.append(test_location)
    return system


@pytest.fixture
def interaction_system(location_system: LocationSystem) -> InteractionSystem:
    """Create a test interaction system."""
    return InteractionSystem(location_system)


def test_player_initialization(player: Player) -> None:
    """Test that the player initializes with correct values."""
    assert player.x == 25
    assert player.y == 25
    assert player.symbol == "@"
    assert player.color == (255, 255, 255)
    assert player.inventory is not None
    assert len(player.inventory.items) == 0
    assert player.inventory.capacity == 20


def test_valid_movement(player: Player, island: Island) -> None:
    """Test that the player can move in valid directions."""
    # Test movement in all cardinal directions
    assert player.move(1, 0, island)  # Right
    assert player.x == 26 and player.y == 25

    assert player.move(-1, 0, island)  # Left
    assert player.x == 25 and player.y == 25

    assert player.move(0, 1, island)  # Down
    assert player.x == 25 and player.y == 26

    assert player.move(0, -1, island)  # Up
    assert player.x == 25 and player.y == 25


def test_movement_boundaries(player: Player, island: Island) -> None:
    """Test that the player cannot move outside map boundaries."""
    # Move to edge
    player.x = 0
    player.y = 0

    # Try to move outside boundaries
    assert not player.move(-1, 0, island)  # Left
    assert not player.move(0, -1, island)  # Up
    assert player.x == 0 and player.y == 0

    # Move to opposite edge
    player.x = island.width - 1
    player.y = island.height - 1

    # Try to move outside boundaries
    assert not player.move(1, 0, island)  # Right
    assert not player.move(0, 1, island)  # Down
    assert player.x == island.width - 1 and player.y == island.height - 1


def test_movement_water(player: Player, island: Island) -> None:
    """Test that the player cannot move into deep water."""
    if island.terrain is None:
        raise ValueError("Island terrain must be initialized")
    # Create deep water at (26, 25)
    island.terrain[25, 26] = 0.1

    # Try to move into water
    assert not player.move(1, 0, island)
    assert player.x == 25 and player.y == 25


def test_movement_input(player: Player, island: Island) -> None:
    """Test that keyboard input correctly moves the player."""
    # Test arrow keys
    assert player.handle_input(
        tcod.event.KeyDown(
            scancode=tcod.event.Scancode.RIGHT,
            sym=tcod.event.KeySym.RIGHT,
            mod=tcod.event.Modifier.NONE,
        ),
        island,
    )
    assert player.x == 26 and player.y == 25

    assert player.handle_input(
        tcod.event.KeyDown(
            scancode=tcod.event.Scancode.LEFT,
            sym=tcod.event.KeySym.LEFT,
            mod=tcod.event.Modifier.NONE,
        ),
        island,
    )
    assert player.x == 25 and player.y == 25

    # Test vi keys
    assert player.handle_input(
        tcod.event.KeyDown(
            scancode=tcod.event.Scancode.L,
            sym=tcod.event.KeySym.l,
            mod=tcod.event.Modifier.NONE,
        ),
        island,
    )
    assert player.x == 26 and player.y == 25

    assert player.handle_input(
        tcod.event.KeyDown(
            scancode=tcod.event.Scancode.H,
            sym=tcod.event.KeySym.h,
            mod=tcod.event.Modifier.NONE,
        ),
        island,
    )
    assert player.x == 25 and player.y == 25


def test_non_movement_input(player: Player, island: Island) -> None:
    """Test that non-movement keys are ignored."""
    result = player.handle_input(
        tcod.event.KeyDown(
            scancode=tcod.event.Scancode.A,
            sym=tcod.event.KeySym.a,
            mod=tcod.event.Modifier.NONE,
        ),
        island,
    )
    assert result is None
    assert player.x == 25 and player.y == 25


def test_interaction_input(
    player: Player, 
    island: Island, 
    interaction_system: InteractionSystem
) -> None:
    """Test interaction input handling."""
    # Move player next to the test location
    player.x = 25
    player.y = 26

    # Test space key
    result = player.handle_input(
        tcod.event.KeyDown(
            scancode=tcod.event.Scancode.SPACE,
            sym=tcod.event.KeySym.SPACE,
            mod=tcod.event.Modifier.NONE,
        ),
        island,
        interaction_system,
    )
    assert result == ("interact", True)

    # Test enter key
    result = player.handle_input(
        tcod.event.KeyDown(
            scancode=tcod.event.Scancode.RETURN,
            sym=tcod.event.KeySym.RETURN,
            mod=tcod.event.Modifier.NONE,
        ),
        island,
        interaction_system,
    )
    assert result == ("interact", True)

    # Test interaction without interaction system
    result = player.handle_input(
        tcod.event.KeyDown(
            scancode=tcod.event.Scancode.SPACE,
            sym=tcod.event.KeySym.SPACE,
            mod=tcod.event.Modifier.NONE,
        ),
        island,
    )
    assert result == ("interact", False)


def test_interaction_range(
    player: Player,
    island: Island,
    interaction_system: InteractionSystem,
) -> None:
    """Test that interactions only work within range."""
    # Move player away from the test location
    player.x = 0
    player.y = 0

    # Try to interact (should fail due to distance)
    result = player.handle_input(
        tcod.event.KeyDown(
            scancode=tcod.event.Scancode.SPACE,
            sym=tcod.event.KeySym.SPACE,
            mod=tcod.event.Modifier.NONE,
        ),
        island,
        interaction_system,
    )
    assert result == ("interact", False)


def test_inventory_input(player: Player, island: Island) -> None:
    """Test inventory key handling."""
    result = player.handle_input(
        tcod.event.KeyDown(
            scancode=tcod.event.Scancode.I,
            sym=tcod.event.KeySym.i,
            mod=tcod.event.Modifier.NONE,
        ),
        island,
    )
    assert result == ("inventory", None)


def test_add_to_inventory(player: Player) -> None:
    """Test adding items to inventory."""
    shell = ItemFactory.create_item(ItemType.SHELL)
    assert player.add_to_inventory(shell)
    assert len(player.inventory.items) == 1
    assert player.inventory.items[0] == shell


def test_add_to_full_inventory(player: Player) -> None:
    """Test adding items to a full inventory."""
    # Fill inventory
    for _ in range(player.inventory.capacity):
        player.add_to_inventory(ItemFactory.create_item(ItemType.MESSAGE_BOTTLE))

    # Try to add one more
    shell = ItemFactory.create_item(ItemType.SHELL)
    assert not player.add_to_inventory(shell)
    assert len(player.inventory.items) == player.inventory.capacity


def test_add_stackable_items(player: Player) -> None:
    """Test adding stackable items to inventory."""
    shell1 = ItemFactory.create_item(ItemType.SHELL)
    shell2 = ItemFactory.create_item(ItemType.SHELL)
    shell2.name = shell1.name  # Ensure same name for stacking
    shell2.stack_size = 2

    assert player.add_to_inventory(shell1)
    assert player.add_to_inventory(shell2)
    assert len(player.inventory.items) == 1
    assert player.inventory.items[0].stack_size == 3
