"""Tests for the weather system module."""

import pytest
from typing import Tuple
from island_rl.weather_system import WeatherSystem, WeatherType


def test_weather_initialization() -> None:
    """Test that WeatherSystem initializes with correct default values."""
    weather = WeatherSystem()
    assert isinstance(weather.current_weather, WeatherType)
    assert weather.transition_minutes == 0
    assert weather.minutes_until_change > 0


def test_weather_types() -> None:
    """Test that all weather types are properly defined."""
    assert WeatherType.SUNNY in WeatherType
    assert WeatherType.PARTLY_CLOUDY in WeatherType
    assert WeatherType.LIGHT_RAIN in WeatherType


@pytest.mark.parametrize(
    "weather_type,expected_color_adjustment",
    [
        (WeatherType.SUNNY, (1.1, 1.1, 1.0)),  # Brighter in sunny weather
        (WeatherType.PARTLY_CLOUDY, (0.9, 0.9, 0.95)),  # Slightly muted
        (WeatherType.LIGHT_RAIN, (0.7, 0.7, 0.8)),  # Darker and bluer in rain
    ],
)
def test_get_color_adjustment(
    weather_type: WeatherType, expected_color_adjustment: Tuple[float, float, float]
) -> None:
    """Test color adjustments for different weather types."""
    weather = WeatherSystem()
    weather.current_weather = weather_type
    adjustment = weather.get_color_adjustment()
    assert len(adjustment) == 3
    assert all(isinstance(x, float) for x in adjustment)
    assert all(abs(a - b) < 0.01 for a, b in zip(adjustment, expected_color_adjustment))


def test_weather_transition() -> None:
    """Test weather transition mechanics."""
    weather = WeatherSystem()
    initial_weather = weather.current_weather

    # Force a weather change
    weather.minutes_until_change = 1
    weather.update()

    # Weather should be changing
    assert weather.transition_minutes > 0
    assert weather.is_transitioning()

    # Complete the transition
    for _ in range(weather.TRANSITION_DURATION + 1):
        weather.update()

    # Weather should have changed
    assert not weather.is_transitioning()
    assert weather.transition_minutes == 0
    assert weather.current_weather != initial_weather


def test_get_weather_description() -> None:
    """Test weather descriptions."""
    weather = WeatherSystem()

    weather.current_weather = WeatherType.SUNNY
    assert weather.get_weather_description() == "Sunny"

    weather.current_weather = WeatherType.PARTLY_CLOUDY
    assert weather.get_weather_description() == "Partly Cloudy"

    weather.current_weather = WeatherType.LIGHT_RAIN
    assert weather.get_weather_description() == "Light Rain"


def test_get_weather_symbol() -> None:
    """Test weather symbols."""
    weather = WeatherSystem()

    weather.current_weather = WeatherType.SUNNY
    assert weather.get_weather_symbol() == "☼"

    weather.current_weather = WeatherType.PARTLY_CLOUDY
    assert weather.get_weather_symbol() == "⛅"

    weather.current_weather = WeatherType.LIGHT_RAIN
    assert weather.get_weather_symbol() == "☂"


def test_color_blending_during_transition() -> None:
    """Test color adjustment blending during weather transitions."""
    weather = WeatherSystem()

    # Force a transition from sunny to rainy
    weather.current_weather = WeatherType.SUNNY
    weather.next_weather = WeatherType.LIGHT_RAIN
    weather.transition_minutes = weather.TRANSITION_DURATION // 2

    # Get color adjustment at 50% transition
    adjustment = weather.get_color_adjustment()

    # Should be halfway between sunny and rainy adjustments
    sunny_adjustment = (1.1, 1.1, 1.0)
    rainy_adjustment = (0.7, 0.7, 0.8)
    expected = tuple((a + b) / 2 for a, b in zip(sunny_adjustment, rainy_adjustment))

    assert all(abs(a - b) < 0.01 for a, b in zip(adjustment, expected))


def test_weather_change_probability() -> None:
    """Test that weather changes occur with appropriate frequency."""
    weather = WeatherSystem(seed=42)  # Fixed seed for reproducibility
    changes = 0
    initial_weather = weather.current_weather

    # Simulate 24 hours of updates
    for _ in range(1440):  # minutes in a day
        weather.update()
        if weather.current_weather != initial_weather:
            changes += 1
            initial_weather = weather.current_weather

    # Should have 2-6 weather changes per day
    assert 2 <= changes <= 6
