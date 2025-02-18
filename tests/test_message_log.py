"""Tests for the message log system."""

import pytest
from datetime import datetime, timedelta
from island_rl.message_log import MessageLog, Message, MessageCategory


@pytest.fixture
def message_log() -> MessageLog:
    """Create a MessageLog fixture."""
    return MessageLog(max_messages=5)


def test_message_log_initialization(message_log: MessageLog) -> None:
    """Test that the message log initializes properly."""
    assert message_log.messages == []
    assert message_log.max_messages == 5


def test_add_message(message_log: MessageLog) -> None:
    """Test adding a message to the log."""
    message_log.add_message("Test message", MessageCategory.SYSTEM)
    assert len(message_log.messages) == 1
    assert message_log.messages[0].text == "Test message"
    assert message_log.messages[0].category == MessageCategory.SYSTEM
    assert isinstance(message_log.messages[0].timestamp, datetime)


def test_add_message_with_details(message_log: MessageLog) -> None:
    """Test adding a message with details."""
    message_log.add_message(
        "Test message",
        MessageCategory.DISCOVERY,
        details="Additional details"
    )
    assert message_log.messages[0].details == "Additional details"


def test_max_messages(message_log: MessageLog) -> None:
    """Test that the log respects the maximum message limit."""
    # Add more messages than the maximum
    for i in range(10):
        message_log.add_message(f"Message {i}", MessageCategory.SYSTEM)
    
    # Should only keep the 5 most recent messages
    assert len(message_log.messages) == 5
    assert message_log.messages[0].text == "Message 5"
    assert message_log.messages[-1].text == "Message 9"


def test_get_recent_messages(message_log: MessageLog) -> None:
    """Test retrieving recent messages."""
    # Add some messages
    for i in range(4):
        message_log.add_message(f"Message {i}", MessageCategory.SYSTEM)
    
    # Get the 2 most recent messages
    recent = message_log.get_recent_messages(2)
    assert len(recent) == 2
    assert recent[0].text == "Message 2"
    assert recent[1].text == "Message 3"


def test_get_messages_by_category(message_log: MessageLog) -> None:
    """Test filtering messages by category."""
    # Add messages of different categories
    message_log.add_message("Discovery 1", MessageCategory.DISCOVERY)
    message_log.add_message("System 1", MessageCategory.SYSTEM)
    message_log.add_message("Discovery 2", MessageCategory.DISCOVERY)
    
    # Get all discovery messages
    discovery_messages = message_log.get_messages_by_category(MessageCategory.DISCOVERY)
    assert len(discovery_messages) == 2
    assert all(msg.category == MessageCategory.DISCOVERY for msg in discovery_messages)
    
    # Get limited number of discovery messages
    limited = message_log.get_messages_by_category(MessageCategory.DISCOVERY, count=1)
    assert len(limited) == 1
    assert limited[0].text == "Discovery 2"


def test_clear_messages(message_log: MessageLog) -> None:
    """Test clearing all messages."""
    # Add some messages
    message_log.add_message("Test 1", MessageCategory.SYSTEM)
    message_log.add_message("Test 2", MessageCategory.DISCOVERY)
    
    # Clear the log
    message_log.clear()
    assert len(message_log.messages) == 0


def test_message_categories() -> None:
    """Test that all expected message categories exist."""
    assert MessageCategory.DISCOVERY
    assert MessageCategory.INTERACTION
    assert MessageCategory.SYSTEM
    assert MessageCategory.WEATHER
    assert MessageCategory.TIME 