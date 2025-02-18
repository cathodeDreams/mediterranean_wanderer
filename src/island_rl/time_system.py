"""Time system module for managing day/night cycle."""

from dataclasses import dataclass
from typing import Tuple
import math


@dataclass
class TimeSystem:
    """Manages the game's time system including day/night cycle."""

    minutes: int = 360  # Start at 6:00 AM (360 minutes)
    day: int = 1
    minutes_per_turn: int = 1  # How many minutes pass per game turn
    minutes_per_day: int = 1440  # 24 hours * 60 minutes

    def advance(self) -> None:
        """Advance time by one turn."""
        self.minutes += self.minutes_per_turn
        if self.minutes >= self.minutes_per_day:
            self.minutes = 0
            self.day += 1

    def get_time_of_day(self) -> str:
        """Get the current time as a string in 24-hour format."""
        hours = self.minutes // 60
        mins = self.minutes % 60
        return f"{hours:02d}:{mins:02d}"

    def get_day_progress(self) -> float:
        """Get the progress through the current day as a float from 0 to 1."""
        return self.minutes / self.minutes_per_day

    def get_light_level(self) -> float:
        """
        Get the current light level as a float from 0 to 1.
        0 = darkest (midnight), 1 = brightest (noon)
        Uses a sinusoidal curve for smooth transitions.
        """
        # Convert day progress to radians (2π = full day)
        # Offset by -π/2 so noon (0.5) is the peak
        angle = 2 * math.pi * self.get_day_progress() - math.pi / 2
        # Convert from -1,1 to 0,1 range and smooth the curve
        return float(pow((math.sin(angle) + 1) / 2, 0.8))

    def get_time_description(self) -> str:
        """Get a text description of the current time of day."""
        progress = self.get_day_progress()
        if 0.0 <= progress < 0.25:  # 00:00-06:00
            return "Night"
        elif 0.25 <= progress < 0.35:  # 06:00-08:24
            return "Dawn"
        elif 0.35 <= progress < 0.708:  # 08:24-17:00
            return "Day"
        elif 0.708 <= progress < 0.792:  # 17:00-19:00
            return "Dusk"
        else:  # 19:00-24:00
            return "Night"

    def adjust_color(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Adjust a color based on the current light level.

        Args:
            color: Original RGB color tuple

        Returns:
            Adjusted RGB color tuple
        """
        progress = self.get_day_progress()

        # Determine the time of day and apply appropriate adjustments
        if progress < 0.25 or progress >= 0.792:  # Night
            # Night colors are darkened and shifted towards blue
            light_level = 0.35  # Fixed darkness level for night
            tint = (1.0, 1.15, 1.43)  # Blue tint
        elif 0.25 <= progress < 0.35 or 0.708 <= progress < 0.792:  # Dawn/Dusk
            # Dawn/Dusk colors are shifted towards orange
            light_level = 0.67  # Reduced brightness for dawn/dusk
            tint = (1.34, 1.0, 0.78)  # Orange tint
        else:  # Day
            # Full brightness during the day
            light_level = 1.0
            tint = (1.0, 1.0, 1.0)

        # Apply the adjustments
        r = int(min(255, color[0] * light_level * tint[0]))
        g = int(min(255, color[1] * light_level * tint[1]))
        b = int(min(255, color[2] * light_level * tint[2]))

        return (r, g, b)
