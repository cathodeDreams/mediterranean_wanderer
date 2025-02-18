"""Tests for the time system module."""

import pytest
from island_rl.time_system import TimeSystem


def test_time_initialization() -> None:
    """Test that TimeSystem initializes with correct default values."""
    time_system = TimeSystem()
    assert time_system.minutes == 360  # 6:00 AM
    assert time_system.day == 1
    assert time_system.minutes_per_turn == 1
    assert time_system.minutes_per_day == 1440


def test_time_advance() -> None:
    """Test that time advances correctly."""
    time_system = TimeSystem()
    initial_minutes = time_system.minutes

    # Advance one turn
    time_system.advance()
    assert time_system.minutes == initial_minutes + 1

    # Test day rollover
    time_system.minutes = 1439  # One minute before midnight
    time_system.advance()
    assert time_system.minutes == 0
    assert time_system.day == 2


def test_get_time_of_day() -> None:
    """Test time string formatting."""
    time_system = TimeSystem()

    # Test 6:00 (default)
    assert time_system.get_time_of_day() == "06:00"

    # Test midnight
    time_system.minutes = 0
    assert time_system.get_time_of_day() == "00:00"

    # Test 23:59
    time_system.minutes = 1439
    assert time_system.get_time_of_day() == "23:59"


def test_get_day_progress() -> None:
    """Test day progress calculation."""
    time_system = TimeSystem()

    # Test midnight
    time_system.minutes = 0
    assert time_system.get_day_progress() == 0.0

    # Test noon
    time_system.minutes = 720
    assert time_system.get_day_progress() == 0.5

    # Test end of day
    time_system.minutes = 1439
    assert pytest.approx(time_system.get_day_progress(), 0.001) == 0.999


def test_get_light_level() -> None:
    """Test light level calculation."""
    time_system = TimeSystem()

    # Test midnight (darkest)
    time_system.minutes = 0
    assert time_system.get_light_level() < 0.1

    # Test noon (brightest)
    time_system.minutes = 720
    assert time_system.get_light_level() > 0.9

    # Test 6 AM (dawn)
    time_system.minutes = 360
    assert 0.3 < time_system.get_light_level() < 0.7


def test_get_time_description() -> None:
    """Test time of day descriptions."""
    time_system = TimeSystem()

    # Test night (midnight)
    time_system.minutes = 0
    assert time_system.get_time_description() == "Night"

    # Test dawn (6 AM)
    time_system.minutes = 360
    assert time_system.get_time_description() == "Dawn"

    # Test day (noon)
    time_system.minutes = 720
    assert time_system.get_time_description() == "Day"

    # Test dusk (6 PM)
    time_system.minutes = 1080
    assert time_system.get_time_description() == "Dusk"


@pytest.mark.parametrize(
    "time,color,expected",
    [
        # Noon - full brightness
        (720, (100, 100, 100), (100, 100, 100)),
        # Midnight - darkened with blue tint
        (0, (100, 100, 100), (35, 40, 50)),
        # Dawn - orange tint
        (360, (100, 100, 100), (90, 67, 52)),
        # Dusk - orange tint
        (1080, (100, 100, 100), (90, 67, 52)),
    ],
)
def test_adjust_color(
    time: int, color: tuple[int, int, int], expected: tuple[int, int, int]
) -> None:
    """Test color adjustment based on time of day."""
    time_system = TimeSystem()
    time_system.minutes = time
    adjusted = time_system.adjust_color(color)
    assert all(abs(a - b) <= 5 for a, b in zip(adjusted, expected))
