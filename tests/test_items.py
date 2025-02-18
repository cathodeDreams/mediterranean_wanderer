"""Tests for the item system."""

import pytest
from island_rl.items import ItemType, Item, ItemFactory


def test_item_type_enum() -> None:
    """Test that ItemType enum has all expected values."""
    assert ItemType.SHELL
    assert ItemType.STONE
    assert ItemType.MESSAGE_BOTTLE
    assert ItemType.FLOWER
    assert ItemType.HERB
    assert ItemType.FRUIT


def test_item_creation() -> None:
    """Test basic item creation and properties."""
    item = Item(
        type=ItemType.SHELL,
        name="Test Shell",
        description="A test shell",
        stackable=True,
        stack_size=1,
    )
    assert item.type == ItemType.SHELL
    assert item.name == "Test Shell"
    assert item.description == "A test shell"
    assert item.stackable is True
    assert item.stack_size == 1
    assert item.details is None


def test_item_str_representation() -> None:
    """Test string representation of items."""
    # Non-stackable item
    item1 = Item(
        type=ItemType.MESSAGE_BOTTLE,
        name="Test Bottle",
        description="A test bottle",
        stackable=False,
    )
    assert str(item1) == "Test Bottle"

    # Stackable item with stack_size > 1
    item2 = Item(
        type=ItemType.SHELL,
        name="Test Shell",
        description="A test shell",
        stackable=True,
        stack_size=5,
    )
    assert str(item2) == "Test Shell (x5)"

    # Stackable item with stack_size = 1
    item3 = Item(
        type=ItemType.SHELL,
        name="Test Shell",
        description="A test shell",
        stackable=True,
        stack_size=1,
    )
    assert str(item3) == "Test Shell"


def test_item_factory_creation() -> None:
    """Test ItemFactory creates valid items for each type."""
    for item_type in ItemType:
        item = ItemFactory.create_item(item_type)
        assert isinstance(item, Item)
        assert item.type == item_type
        assert item.name in [name for name in ItemFactory.ITEMS[item_type]["names"]]
        assert item.description in [desc for desc in ItemFactory.ITEMS[item_type]["descriptions"]]
        assert item.stackable == ItemFactory.ITEMS[item_type].get("stackable", False)


def test_message_bottle_details() -> None:
    """Test that message bottles have random messages."""
    item = ItemFactory.create_item(ItemType.MESSAGE_BOTTLE)
    assert item.details is not None
    assert item.details in ItemFactory.ITEMS[ItemType.MESSAGE_BOTTLE]["messages"]


def test_stack_size_parameter() -> None:
    """Test that stack_size parameter works correctly."""
    # Test stackable item
    shell = ItemFactory.create_item(ItemType.SHELL, stack_size=5)
    assert shell.stack_size == 5

    # Test non-stackable item (should always have stack_size=1)
    bottle = ItemFactory.create_item(ItemType.MESSAGE_BOTTLE, stack_size=5)
    assert bottle.stack_size == 1


def test_item_templates() -> None:
    """Test that all item templates have required fields."""
    for item_type, template in ItemFactory.ITEMS.items():
        assert "names" in template
        assert "descriptions" in template
        assert len(template["names"]) == len(template["descriptions"])
        assert "stackable" in template
        if item_type == ItemType.MESSAGE_BOTTLE:
            assert "messages" in template 