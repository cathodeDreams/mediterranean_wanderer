"""Message log system for Mediterranean Wanderer."""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum, auto
from datetime import datetime


class MessageCategory(Enum):
    """Categories for different types of messages."""
    DISCOVERY = auto()
    INTERACTION = auto()
    SYSTEM = auto()
    WEATHER = auto()
    TIME = auto()


@dataclass
class Message:
    """A message in the message log."""
    text: str
    category: MessageCategory
    timestamp: datetime
    details: Optional[str] = None
    

class MessageLog:
    """System for managing and displaying game messages."""
    
    def __init__(self, max_messages: int = 50):
        """Initialize the message log."""
        self.messages: List[Message] = []
        self.max_messages = max_messages
    
    def add_message(
        self,
        text: str,
        category: MessageCategory,
        details: Optional[str] = None,
    ) -> None:
        """Add a message to the log."""
        message = Message(
            text=text,
            category=category,
            timestamp=datetime.now(),
            details=details,
        )
        self.messages.append(message)
        
        # Keep only the most recent messages
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
    
    def get_recent_messages(self, count: int = 5) -> List[Message]:
        """Get the most recent messages."""
        return self.messages[-count:]
    
    def get_messages_by_category(
        self,
        category: MessageCategory,
        count: Optional[int] = None
    ) -> List[Message]:
        """Get messages of a specific category."""
        filtered = [msg for msg in self.messages if msg.category == category]
        if count is not None:
            return filtered[-count:]
        return filtered
    
    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear() 