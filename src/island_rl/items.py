"""Item system for Mediterranean Wanderer."""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, TypedDict


class ItemType(Enum):
    """Types of items that can be found in the game."""
    SHELL = auto()
    STONE = auto()
    MESSAGE_BOTTLE = auto()
    FLOWER = auto()
    HERB = auto()
    FRUIT = auto()


class ItemTemplate(TypedDict, total=False):
    """Type definition for item templates."""
    names: List[str]
    descriptions: List[str]
    stackable: bool
    messages: List[str]  # Optional, only for MESSAGE_BOTTLE


@dataclass
class Item:
    """An item that can be collected by the player."""
    type: ItemType
    name: str
    description: str
    stackable: bool = False
    stack_size: int = 1  # Only relevant if stackable is True
    details: Optional[str] = None  # Additional details (e.g., message content for bottles)

    def __str__(self) -> str:
        """String representation of the item."""
        if self.stackable and self.stack_size > 1:
            return f"{self.name} (x{self.stack_size})"
        return self.name


class ItemFactory:
    """Factory class for creating items."""

    # Item templates
    ITEMS: Dict[ItemType, ItemTemplate] = {
        ItemType.SHELL: {
            "names": [
                "Spiral Shell",
                "Conch Shell",
                "Scallop Shell",
                "Pearl Oyster",
                "Nautilus Shell",
            ],
            "descriptions": [
                "A beautiful spiral shell with iridescent colors.",
                "A large conch shell that echoes the sea.",
                "A delicate scallop shell with perfect ridges.",
                "A smooth oyster shell with a pearly interior.",
                "An ancient nautilus shell with intricate chambers.",
            ],
            "stackable": True,
        },
        ItemType.STONE: {
            "names": [
                "Smooth Pebble",
                "Sea Glass",
                "Marble Fragment",
                "Quartz Crystal",
                "Beach Stone",
            ],
            "descriptions": [
                "A perfectly smooth pebble worn by the waves.",
                "A piece of frosted sea glass in a beautiful color.",
                "A fragment of ancient marble with faint patterns.",
                "A small crystal that catches the light.",
                "A uniquely shaped stone from the beach.",
            ],
            "stackable": True,
        },
        ItemType.MESSAGE_BOTTLE: {
            "names": [
                "Sealed Message Bottle",
                "Ancient Message Bottle",
                "Weathered Message Bottle",
                "Crystal Clear Bottle",
                "Green Glass Bottle",
            ],
            "descriptions": [
                "A corked bottle containing a rolled message.",
                "An old bottle with a faded message inside.",
                "A weathered bottle protecting a mysterious note.",
                "A pristine bottle with a message waiting to be read.",
                "An emerald green bottle with a secret message.",
            ],
            "stackable": False,
            "messages": [
                "May the winds guide you to treasures untold...",
                "In the olive groves, ancient secrets rest...",
                "Follow the path of the setting sun...",
                "When the moon is full, the ruins whisper...",
                "The old fisherman knows more than he tells...",
            ],
        },
        ItemType.FLOWER: {
            "names": [
                "Mediterranean Daisy",
                "Wild Cyclamen",
                "Sea Lavender",
                "Rock Rose",
                "Wild Orchid",
            ],
            "descriptions": [
                "A cheerful daisy with white petals.",
                "A delicate cyclamen with swept-back petals.",
                "A cluster of tiny purple flowers.",
                "A bright pink flower that grows among rocks.",
                "A rare wild orchid with spotted petals.",
            ],
            "stackable": True,
        },
        ItemType.HERB: {
            "names": [
                "Wild Thyme",
                "Bay Leaf",
                "Rosemary Sprig",
                "Sage Leaf",
                "Wild Oregano",
            ],
            "descriptions": [
                "Fragrant wild thyme that grows between rocks.",
                "A glossy bay leaf from an ancient tree.",
                "A sprig of aromatic rosemary.",
                "A soft, silvery sage leaf.",
                "Wild oregano with a strong, spicy scent.",
            ],
            "stackable": True,
        },
        ItemType.FRUIT: {
            "names": [
                "Wild Fig",
                "Olive",
                "Lemon",
                "Orange",
                "Pomegranate",
            ],
            "descriptions": [
                "A ripe fig, sweet and fresh from the tree.",
                "A perfectly ripe olive, ready for curing.",
                "A fragrant lemon from a garden tree.",
                "A sweet orange warmed by the sun.",
                "A heavy pomegranate, full of jewel-like seeds.",
            ],
            "stackable": True,
        },
    }

    @classmethod
    def create_item(cls, item_type: ItemType, stack_size: int = 1) -> Item:
        """Create a new item of the specified type."""
        import random

        template = cls.ITEMS[item_type]
        name_idx = random.randint(0, len(template["names"]) - 1)
        
        details = None
        if item_type == ItemType.MESSAGE_BOTTLE:
            details = random.choice(template["messages"])

        return Item(
            type=item_type,
            name=template["names"][name_idx],
            description=template["descriptions"][name_idx],
            stackable=template.get("stackable", False),
            stack_size=stack_size if template.get("stackable", False) else 1,
            details=details,
        ) 