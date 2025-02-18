"""Weather system module for managing weather conditions and effects."""

from enum import Enum, auto
from dataclasses import dataclass, field
import random
from typing import Dict, Optional, Tuple, cast


class WeatherType(Enum):
    """Available weather types."""

    SUNNY = auto()
    PARTLY_CLOUDY = auto()
    LIGHT_RAIN = auto()


def _get_weather_adjustments() -> Dict[WeatherType, Tuple[float, float, float]]:
    """Factory function for weather adjustments dictionary."""
    return {
        WeatherType.SUNNY: (1.1, 1.1, 1.0),  # Brighter
        WeatherType.PARTLY_CLOUDY: (0.9, 0.9, 0.95),  # Slightly muted
        WeatherType.LIGHT_RAIN: (0.7, 0.7, 0.8),  # Darker and bluer
    }


@dataclass
class WeatherSystem:
    """Manages the game's weather system including transitions and effects."""

    # Optional initialization parameter
    seed: Optional[int] = None

    # Class constants
    MIN_WEATHER_DURATION: int = 180  # Minimum minutes between weather changes (3 hours)
    MAX_WEATHER_DURATION: int = 480  # Maximum minutes between weather changes (8 hours)
    TRANSITION_DURATION: int = 30  # Minutes for weather transition to complete

    # Instance variables with defaults
    current_weather: WeatherType = WeatherType.SUNNY
    next_weather: Optional[WeatherType] = None
    transition_minutes: int = 0
    minutes_until_change: int = field(init=False)
    
    # Color adjustment factors for each weather type
    WEATHER_ADJUSTMENTS: Dict[WeatherType, Tuple[float, float, float]] = field(
        default_factory=_get_weather_adjustments,
        init=False
    )

    def __post_init__(self) -> None:
        """Initialize after dataclass creation."""
        if self.seed is not None:
            random.seed(self.seed)
        self.minutes_until_change = self._get_next_duration()

    def _get_next_duration(self) -> int:
        """Get the duration until the next weather change."""
        return random.randint(self.MIN_WEATHER_DURATION, self.MAX_WEATHER_DURATION)

    def _get_next_weather(self) -> WeatherType:
        """Get the next weather type, ensuring it's different from current."""
        available_weather = [w for w in WeatherType if w != self.current_weather]
        return random.choice(available_weather)

    def update(self) -> None:
        """Update weather state for one minute."""
        if self.is_transitioning():
            self.transition_minutes += 1
            if self.transition_minutes >= self.TRANSITION_DURATION:
                # Complete the transition
                if self.next_weather is not None:  # Type guard for mypy
                    self.current_weather = self.next_weather
                self.next_weather = None
                self.transition_minutes = 0
                self.minutes_until_change = self._get_next_duration()
        else:
            self.minutes_until_change -= 1
            if self.minutes_until_change <= 0:
                # Start a weather transition
                self.next_weather = self._get_next_weather()
                self.transition_minutes = 1  # Start at 1 to ensure transition is active

    def is_transitioning(self) -> bool:
        """Check if weather is currently transitioning."""
        return self.next_weather is not None

    def get_weather_description(self) -> str:
        """Get a text description of the current weather."""
        weather_descriptions = {
            WeatherType.SUNNY: "Sunny",
            WeatherType.PARTLY_CLOUDY: "Partly Cloudy",
            WeatherType.LIGHT_RAIN: "Light Rain",
        }
        return weather_descriptions[self.current_weather]

    def get_weather_symbol(self) -> str:
        """Get the symbol representing the current weather."""
        weather_symbols = {
            WeatherType.SUNNY: "☼",
            WeatherType.PARTLY_CLOUDY: "⛅",
            WeatherType.LIGHT_RAIN: "☂",
        }
        return weather_symbols[self.current_weather]

    def get_color_adjustment(self) -> Tuple[float, float, float]:
        """
        Get the color adjustment factors for the current weather.
        Returns a tuple of (red, green, blue) multipliers.
        """
        if not self.is_transitioning():
            return self.WEATHER_ADJUSTMENTS[self.current_weather]

        # During transition, blend between current and next weather
        current_adj = self.WEATHER_ADJUSTMENTS[self.current_weather]
        next_adj = self.WEATHER_ADJUSTMENTS[cast(WeatherType, self.next_weather)]
        progress = min(1.0, self.transition_minutes / self.TRANSITION_DURATION)

        # Linear interpolation between current and next adjustments
        return cast(
            Tuple[float, float, float],
            tuple(
                current * (1 - progress) + next * progress
                for current, next in zip(current_adj, next_adj)
            ),
        )
