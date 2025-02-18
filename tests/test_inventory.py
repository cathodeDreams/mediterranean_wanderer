"""Tests for the inventory system."""

import pytest
from island_rl.inventory import Inventory, InventoryFullError
from island_rl.items import Item, ItemType, ItemFactory


@pytest.fixture
def empty_inventory() -> Inventory:
    """Create an empty inventory for testing."""
    return Inventory(capacity=5)


@pytest.fixture
def shell_item() -> Item:
    """Create a test shell item."""
    return ItemFactory.create_item(ItemType.SHELL)


@pytest.fixture
def bottle_item() -> Item:
    """Create a test message bottle item."""
    return ItemFactory.create_item(ItemType.MESSAGE_BOTTLE)


def test_inventory_initialization(empty_inventory: Inventory) -> None:
    """Test inventory initialization."""
    assert empty_inventory.capacity == 5
    assert len(empty_inventory.items) == 0
    assert empty_inventory.get_free_space() == 5
    assert not empty_inventory.is_full()


def test_add_item(empty_inventory: Inventory, shell_item: Item) -> None:
    """Test adding items to inventory."""
    empty_inventory.add_item(shell_item)
    assert len(empty_inventory.items) == 1
    assert empty_inventory.items[0] == shell_item


def test_add_stackable_items(empty_inventory: Inventory) -> None:
    """Test adding stackable items."""
    shell1 = ItemFactory.create_item(ItemType.SHELL)
    shell2 = Item(
        type=ItemType.SHELL,
        name=shell1.name,  # Same name to ensure stacking
        description=shell1.description,
        stackable=True,
        stack_size=2,
    )

    empty_inventory.add_item(shell1)
    empty_inventory.add_item(shell2)

    # Should only be one item with stack_size = 3
    assert len(empty_inventory.items) == 1
    assert empty_inventory.items[0].stack_size == 3


def test_add_different_stackable_items(empty_inventory: Inventory) -> None:
    """Test adding different stackable items."""
    shell1 = Item(
        type=ItemType.SHELL,
        name="Spiral Shell",
        description="A beautiful spiral shell with iridescent colors.",
        stackable=True,
        stack_size=1
    )
    shell2 = Item(
        type=ItemType.SHELL,
        name="Conch Shell",  # Different name
        description="A large conch shell that makes a sound when blown.",  # Different description
        stackable=True,
        stack_size=1
    )
    
    empty_inventory.add_item(shell1)
    empty_inventory.add_item(shell2)

    # Should be two separate items since they have different names/descriptions
    assert len(empty_inventory.items) == 2
    assert empty_inventory.items[0].name != empty_inventory.items[1].name
    assert empty_inventory.items[0].description != empty_inventory.items[1].description


def test_inventory_full(empty_inventory: Inventory, shell_item: Item) -> None:
    """Test inventory capacity limit."""
    # Fill inventory
    for _ in range(empty_inventory.capacity):
        empty_inventory.add_item(ItemFactory.create_item(ItemType.MESSAGE_BOTTLE))

    # Try to add one more
    with pytest.raises(InventoryFullError):
        empty_inventory.add_item(shell_item)


def test_remove_item(empty_inventory: Inventory, shell_item: Item, bottle_item: Item) -> None:
    """Test removing items from inventory."""
    empty_inventory.add_item(shell_item)
    empty_inventory.add_item(bottle_item)

    removed = empty_inventory.remove_item(0)
    assert removed == shell_item
    assert len(empty_inventory.items) == 1
    assert empty_inventory.items[0] == bottle_item


def test_remove_from_stack() -> None:
    """Test removing items from a stack."""
    inventory = Inventory()
    shell = ItemFactory.create_item(ItemType.SHELL)
    shell.stack_size = 5
    inventory.add_item(shell)

    # Remove 2 from the stack
    removed = inventory.remove_item(0, 2)
    assert removed is not None
    assert removed.stack_size == 2
    assert inventory.items[0].stack_size == 3


def test_get_item(empty_inventory: Inventory, shell_item: Item) -> None:
    """Test getting item without removing it."""
    empty_inventory.add_item(shell_item)
    
    item = empty_inventory.get_item(0)
    assert item == shell_item
    assert len(empty_inventory.items) == 1  # Item should still be in inventory


def test_get_items_by_type(empty_inventory: Inventory) -> None:
    """Test getting items by type."""
    shell = ItemFactory.create_item(ItemType.SHELL)
    bottle = ItemFactory.create_item(ItemType.MESSAGE_BOTTLE)
    empty_inventory.add_item(shell)
    empty_inventory.add_item(bottle)

    shells = empty_inventory.get_items_by_type(ItemType.SHELL)
    assert len(shells) == 1
    assert shells[0] == shell

    bottles = empty_inventory.get_items_by_type(ItemType.MESSAGE_BOTTLE)
    assert len(bottles) == 1
    assert bottles[0] == bottle


def test_get_total_count(empty_inventory: Inventory) -> None:
    """Test counting total items of a type."""
    # Add two shells, one with stack_size 2
    shell1 = ItemFactory.create_item(ItemType.SHELL)
    shell2 = ItemFactory.create_item(ItemType.SHELL)
    shell2.stack_size = 2
    empty_inventory.add_item(shell1)
    empty_inventory.add_item(shell2)

    # Add one bottle (non-stackable)
    bottle = ItemFactory.create_item(ItemType.MESSAGE_BOTTLE)
    empty_inventory.add_item(bottle)

    assert empty_inventory.get_total_count(ItemType.SHELL) == 3
    assert empty_inventory.get_total_count(ItemType.MESSAGE_BOTTLE) == 1
    assert empty_inventory.get_total_count(ItemType.FLOWER) == 0


def test_clear_inventory(empty_inventory: Inventory, shell_item: Item, bottle_item: Item) -> None:
    """Test clearing the inventory."""
    empty_inventory.add_item(shell_item)
    empty_inventory.add_item(bottle_item)
    
    empty_inventory.clear()
    assert len(empty_inventory.items) == 0


def test_sort_items(empty_inventory: Inventory) -> None:
    """Test sorting items by type and name."""
    bottle = ItemFactory.create_item(ItemType.MESSAGE_BOTTLE)
    shell = ItemFactory.create_item(ItemType.SHELL)
    herb = ItemFactory.create_item(ItemType.HERB)
    
    empty_inventory.add_item(bottle)
    empty_inventory.add_item(shell)
    empty_inventory.add_item(herb)
    
    empty_inventory.sort_items()
    
    assert empty_inventory.items[0].type == ItemType.HERB  # H comes first
    assert empty_inventory.items[1].type == ItemType.MESSAGE_BOTTLE  # M comes second
    assert empty_inventory.items[2].type == ItemType.SHELL  # S comes last


def test_get_item_categories(empty_inventory: Inventory) -> None:
    """Test organizing items by category."""
    shell1 = ItemFactory.create_item(ItemType.SHELL)
    shell2 = ItemFactory.create_item(ItemType.SHELL)
    bottle = ItemFactory.create_item(ItemType.MESSAGE_BOTTLE)

    empty_inventory.add_item(shell1)
    empty_inventory.add_item(shell2)
    empty_inventory.add_item(bottle)

    categories = empty_inventory.get_item_categories()

    assert len(categories) == 2  # SHELL and MESSAGE_BOTTLE
    assert ItemType.SHELL in categories
    assert ItemType.MESSAGE_BOTTLE in categories
    
    # Get total count of shells (including stacks)
    shell_count = sum(item.stack_size for item in categories[ItemType.SHELL])
    assert shell_count == 2  # Two shells total, might be stacked 