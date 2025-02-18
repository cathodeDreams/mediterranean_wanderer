"""Inventory system for Mediterranean Wanderer."""

from typing import Dict, List, Optional, Tuple
from .items import Item, ItemType


class InventoryFullError(Exception):
    """Raised when trying to add an item to a full inventory."""
    pass


class Inventory:
    """Player's inventory for storing collected items."""

    def __init__(self, capacity: int = 20):
        """Initialize an empty inventory with the given capacity."""
        self.capacity = capacity
        self.items: List[Item] = []

    def add_item(self, item: Item) -> None:
        """
        Add an item to the inventory.
        
        If the item is stackable and we already have one of the same type,
        increase the stack size instead of adding a new item.
        
        Raises:
            InventoryFullError: If the inventory is full and the item can't be stacked.
        """
        if item.stackable:
            # Try to find an existing stack of this item
            for existing_item in self.items:
                if (existing_item.type == item.type and 
                    existing_item.name == item.name and 
                    existing_item.stackable):
                    existing_item.stack_size += item.stack_size
                    return

        # If we get here, either the item isn't stackable or we don't have one yet
        if len(self.items) >= self.capacity:
            raise InventoryFullError("Inventory is full!")
        
        self.items.append(item)

    def remove_item(self, index: int, count: int = 1) -> Optional[Item]:
        """
        Remove an item from the inventory.
        
        Args:
            index: Index of the item to remove
            count: Number of items to remove from the stack (default: 1)
            
        Returns:
            The removed item, or None if the index is invalid
        """
        if 0 <= index < len(self.items):
            item = self.items[index]
            if item.stackable and item.stack_size > count:
                # Remove part of a stack
                item.stack_size -= count
                # Create a new item with the removed count
                return Item(
                    type=item.type,
                    name=item.name,
                    description=item.description,
                    stackable=True,
                    stack_size=count,
                    details=item.details
                )
            else:
                # Remove the entire item/stack
                return self.items.pop(index)
        return None

    def get_item(self, index: int) -> Optional[Item]:
        """Get an item from the inventory without removing it."""
        if 0 <= index < len(self.items):
            return self.items[index]
        return None

    def get_items_by_type(self, item_type: ItemType) -> List[Item]:
        """Get all items of a specific type."""
        return [item for item in self.items if item.type == item_type]

    def get_total_count(self, item_type: ItemType) -> int:
        """Get the total count of items of a specific type, including stacks."""
        return sum(
            item.stack_size if item.stackable else 1
            for item in self.items
            if item.type == item_type
        )

    def is_full(self) -> bool:
        """Check if the inventory is full."""
        return len(self.items) >= self.capacity

    def get_free_space(self) -> int:
        """Get the number of free slots in the inventory."""
        return self.capacity - len(self.items)

    def clear(self) -> None:
        """Remove all items from the inventory."""
        self.items.clear()

    def sort_items(self) -> None:
        """Sort items by type and name."""
        self.items.sort(key=lambda x: (x.type.name, x.name))

    def get_item_categories(self) -> Dict[ItemType, List[Item]]:
        """Get items organized by category."""
        categories: Dict[ItemType, List[Item]] = {}
        for item in self.items:
            if item.type not in categories:
                categories[item.type] = []
            categories[item.type].append(item)
        return categories 