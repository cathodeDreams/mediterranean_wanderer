from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
import random
from numpy.typing import NDArray


class LocationType(Enum):
    """Types of discoverable locations in the game"""

    VILLAGE = auto()
    RUINS = auto()
    VIEWPOINT = auto()
    BEACH = auto()
    GROVE = auto()


@dataclass
class Location:
    """A discoverable location in the game world"""

    x: int
    y: int
    type: LocationType
    name: str
    description: str
    discovered: bool = False

    def discover(self) -> None:
        """Mark this location as discovered"""
        self.discovered = True


class LocationSystem:
    """System for managing discoverable locations in the game world"""

    # Location generation parameters
    MIN_SPACING = 10  # Minimum distance between locations
    DISCOVERY_RADIUS = 3  # How close player needs to be to discover a location
    WATER_THRESHOLD = 0.5  # Height below this is considered water

    # Location type placement preferences (height ranges)
    LOCATION_PREFERENCES = {
        LocationType.BEACH: (0.5, 0.6),
        LocationType.VILLAGE: (0.6, 0.7),
        LocationType.GROVE: (0.65, 0.75),
        LocationType.VIEWPOINT: (0.7, 0.85),
        LocationType.RUINS: (0.6, 0.8),
    }

    # Name generators for different location types
    VILLAGE_NAMES = [
        "Olive Grove Village",
        "Fisher's Rest",
        "Goat Path Town",
        "Harbor View",
        "Vineyard Settlement",
        "Shepherd's Haven",
    ]

    RUINS_NAMES = [
        "Temple of Poseidon",
        "Ancient Agora",
        "Forgotten Shrine",
        "Old Amphitheater",
        "Lost Library",
        "Marble Columns",
    ]

    VIEWPOINT_NAMES = [
        "Eagle's Perch",
        "Sunset Point",
        "Azure Overlook",
        "Cloud Watch",
        "Sea Vista",
        "Island Peak",
    ]

    BEACH_NAMES = [
        "Golden Sands",
        "Shell Cove",
        "Crystal Bay",
        "Pebble Beach",
        "Hidden Lagoon",
        "Dolphin Shore",
    ]

    GROVE_NAMES = [
        "Ancient Olive Grove",
        "Citrus Garden",
        "Pine Haven",
        "Fig Tree Grove",
        "Cypress Walk",
        "Laurel Woods",
    ]

    def __init__(self, terrain: NDArray[np.float64]):
        """Initialize the location system with the game's terrain"""
        self.terrain = terrain
        self.locations: List[Location] = []

    def generate_locations(
        self, min_locations: int = 5, max_locations: int = 8
    ) -> None:
        """Generate a set of locations on the terrain"""
        # First, count valid terrain tiles
        valid_tiles = int(np.sum(self.terrain >= self.WATER_THRESHOLD))
        if valid_tiles == 0:
            self.locations = []
            return

        # For very small valid areas, use a more lenient approach
        if valid_tiles < 10:  # If we have very few valid tiles
            # Try to place at least one location
            valid_y, valid_x = np.where(self.terrain >= self.WATER_THRESHOLD)  # Note: returns row (y), col (x)
            if len(valid_y) > 0:
                idx = random.randint(0, len(valid_y) - 1)
                height = float(self.terrain[valid_y[idx], valid_x[idx]])  # Convert to float
                loc_type = self._choose_location_type(height)
                if loc_type:
                    location = Location(
                        x=int(valid_x[idx]),  # Convert to int
                        y=int(valid_y[idx]),  # Convert to int
                        type=loc_type,
                        name=self._generate_name(loc_type),
                        description=self._generate_description(loc_type, ""),
                    )
                    self.locations = [location]
                    return

        # For normal cases, estimate max possible locations
        # Use a more optimistic estimate - square packing instead of circular
        area_per_location = (self.MIN_SPACING/2)**2  # Square area
        max_possible = int(valid_tiles / area_per_location)
        
        # Ensure we try to generate at least one location if we have valid terrain
        max_possible = max(1, max_possible)
        
        # Adjust requested locations based on available space
        adjusted_max = min(max_locations, max_possible)
        adjusted_min = min(min_locations, adjusted_max)
        num_locations = random.randint(adjusted_min, adjusted_max)

        original_spacing = self.MIN_SPACING
        best_locations: List[Location] = []
        current_spacing = original_spacing

        while current_spacing >= 2:
            attempts = 0
            max_attempts = 1000  # Prevent infinite loops
            candidate_locations: List[Location] = []

            while len(candidate_locations) < num_locations and attempts < max_attempts:
                attempts += 1

                # Pick a random position
                x = random.randint(0, self.terrain.shape[1] - 1)
                y = random.randint(0, self.terrain.shape[0] - 1)

                # Skip if in water
                if self.terrain[y, x] < self.WATER_THRESHOLD:
                    continue

                # Skip if too close to other candidate locations
                too_close = False
                for loc in candidate_locations:
                    distance = np.sqrt((x - loc.x) ** 2 + (y - loc.y) ** 2)
                    if distance < current_spacing:
                        too_close = True
                        break
                
                if too_close:
                    continue

                # Choose appropriate location type for the terrain height
                loc_type = self._choose_location_type(float(self.terrain[y, x]))  # Convert to float
                if not loc_type:
                    continue

                # Generate name and description
                name = self._generate_name(loc_type)
                description = self._generate_description(loc_type, name)

                # Create and add the location to candidates
                location = Location(
                    x=x, y=y, type=loc_type, name=name, description=description
                )
                candidate_locations.append(location)

            # If we found more locations than our previous best, use these
            if len(candidate_locations) > len(best_locations):
                best_locations = candidate_locations

            # If we found enough locations, we're done
            if len(best_locations) >= adjusted_min:
                break

            # Otherwise, reduce spacing and try again
            current_spacing = max(2, current_spacing // 2)

        # Use the best set of locations we found
        self.locations = best_locations
        # Restore original spacing
        self.MIN_SPACING = original_spacing

    def _is_valid_location(self, x: int, y: int) -> bool:
        """Check if a location is valid (not too close to others)"""
        for loc in self.locations:
            distance = np.sqrt((x - loc.x) ** 2 + (y - loc.y) ** 2)
            if distance < self.MIN_SPACING:
                return False
        return True

    def _choose_location_type(self, height: float) -> Optional[LocationType]:
        """Choose an appropriate location type for the given terrain height"""
        valid_types = []
        for loc_type, (min_height, max_height) in self.LOCATION_PREFERENCES.items():
            if min_height <= height <= max_height:
                valid_types.append(loc_type)
        return random.choice(valid_types) if valid_types else None

    def _generate_name(self, loc_type: LocationType) -> str:
        """Generate a name for a location based on its type"""
        name_lists = {
            LocationType.VILLAGE: self.VILLAGE_NAMES,
            LocationType.RUINS: self.RUINS_NAMES,
            LocationType.VIEWPOINT: self.VIEWPOINT_NAMES,
            LocationType.BEACH: self.BEACH_NAMES,
            LocationType.GROVE: self.GROVE_NAMES,
        }
        return random.choice(name_lists[loc_type])

    def _generate_description(self, loc_type: LocationType, name: str) -> str:
        """Generate a description for a location based on its type and name"""
        descriptions = {
            LocationType.VILLAGE: [
                "A peaceful village nestled among olive trees.",
                "A small settlement with white-washed houses.",
                "A quiet fishing village by the coast.",
            ],
            LocationType.RUINS: [
                "Ancient marble columns reach skyward.",
                "Weathered stone walls tell tales of the past.",
                "Moss-covered ruins of an ancient civilization.",
            ],
            LocationType.VIEWPOINT: [
                "A breathtaking view of the island and sea.",
                "The perfect spot to watch the sunset.",
                "A panoramic vista of the surrounding waters.",
            ],
            LocationType.BEACH: [
                "Crystal clear waters lap at golden sand.",
                "A secluded cove with gentle waves.",
                "A pristine beach with scattered seashells.",
            ],
            LocationType.GROVE: [
                "Ancient olive trees provide cool shade.",
                "A peaceful grove filled with birdsong.",
                "Fragrant citrus trees line winding paths.",
            ],
        }
        return random.choice(descriptions[loc_type])

    def get_nearby_locations(self, x: int, y: int, radius: float) -> List[Location]:
        """Get all locations within a given radius of a point using Manhattan distance"""
        if radius <= 0:
            return []

        nearby = []
        for loc in self.locations:
            # Use Manhattan distance for more natural gameplay feel
            distance = abs(x - loc.x) + abs(y - loc.y)
            if distance <= radius:
                nearby.append(loc)
        return nearby

    def check_discoveries(self, x: int, y: int) -> List[Location]:
        """Check for and return any newly discovered locations near a point"""
        discovered = []
        for loc in self.locations:
            if abs(loc.x - x) <= self.DISCOVERY_RADIUS and abs(loc.y - y) <= self.DISCOVERY_RADIUS:
                if not loc.discovered:
                    loc.discover()
                    discovered.append(loc)  # Append only if newly discovered
        return discovered

    def get_discovered_locations(self) -> List[Location]:
        """Get a list of all discovered locations"""
        return [loc for loc in self.locations if loc.discovered]
