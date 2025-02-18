import pytest
import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass
from numpy.typing import NDArray

from island_rl.locations import Location, LocationType, LocationSystem


def test_location_creation() -> None:
    """Test that locations can be created with proper attributes"""
    loc = Location(
        x=10,
        y=20,
        type=LocationType.VILLAGE,
        name="Olive Grove Village",
        description="A peaceful village nestled among olive trees.",
    )

    assert loc.x == 10
    assert loc.y == 20
    assert loc.type == LocationType.VILLAGE
    assert loc.name == "Olive Grove Village"
    assert loc.description == "A peaceful village nestled among olive trees."
    assert not loc.discovered


def test_location_discovery() -> None:
    """Test that locations can be discovered"""
    loc = Location(
        x=10,
        y=20,
        type=LocationType.RUINS,
        name="Ancient Temple",
        description="Weathered marble columns reach skyward.",
    )

    assert not loc.discovered
    loc.discover()
    assert loc.discovered


class TestLocationSystem:
    @pytest.fixture
    def terrain(self) -> NDArray[np.float64]:
        """Create a simple test terrain"""
        # Create a 50x50 terrain with some variation
        terrain = np.zeros((50, 50), dtype=np.float64)
        # Add several elevated areas for potential locations
        terrain[10:15, 10:15] = 0.7  # Potential village area
        terrain[30:35, 30:35] = 0.9  # Potential ruins area
        terrain[20:25, 40:45] = 0.6  # Potential viewpoint area
        terrain[5:10, 25:30] = 0.55  # Potential beach area
        terrain[35:40, 15:20] = 0.65  # Potential grove area
        return terrain

    @pytest.fixture
    def location_system(self, terrain: NDArray[np.float64]) -> LocationSystem:
        """Create a location system with test terrain"""
        return LocationSystem(terrain)

    def test_initialization(
        self, location_system: LocationSystem, terrain: NDArray[np.float64]
    ) -> None:
        """Test that the location system initializes properly"""
        assert location_system.terrain.shape == terrain.shape
        assert len(location_system.locations) == 0

    def test_generate_locations(self, location_system: LocationSystem) -> None:
        """Test that locations are generated appropriately"""
        location_system.generate_locations(min_locations=3, max_locations=5)

        # Check we have the right number of locations
        assert 3 <= len(location_system.locations) <= 5

        # Check locations are valid
        for loc in location_system.locations:
            # Location should be on valid terrain (not in water)
            assert location_system.terrain[loc.y, loc.x] >= 0.5

            # Locations should be properly spaced
            for other_loc in location_system.locations:
                if other_loc != loc:
                    distance = np.sqrt(
                        (loc.x - other_loc.x) ** 2 + (loc.y - other_loc.y) ** 2
                    )
                    assert distance >= location_system.MIN_SPACING

    def test_generate_locations_with_limited_space(
        self, location_system: LocationSystem
    ) -> None:
        """Test location generation with very limited valid terrain"""
        # Create terrain with only a small valid area
        location_system.terrain = np.zeros((50, 50), dtype=np.float64)
        location_system.terrain[25:27, 25:27] = 0.7  # Small valid area

        # Try to generate more locations than can fit
        location_system.generate_locations(min_locations=3, max_locations=5)

        # Should still generate at least one location
        assert len(location_system.locations) >= 1
        # Location should be in the valid area
        loc = location_system.locations[0]
        assert 25 <= loc.y <= 26
        assert 25 <= loc.x <= 26

    def test_generate_locations_all_water(
        self, location_system: LocationSystem
    ) -> None:
        """Test location generation with no valid terrain"""
        # Create terrain that's all water
        location_system.terrain = np.zeros((50, 50), dtype=np.float64)
        location_system.terrain.fill(0.4)  # All below WATER_THRESHOLD

        # Try to generate locations
        location_system.generate_locations(min_locations=3, max_locations=5)

        # Should not generate any locations
        assert len(location_system.locations) == 0

    def test_location_type_selection(self, location_system: LocationSystem) -> None:
        """Test location type selection based on terrain height"""
        # Test each location type's height range
        test_cases = [
            (0.55, {LocationType.BEACH}),  # Beach only
            (
                0.65,
                {LocationType.VILLAGE, LocationType.GROVE, LocationType.RUINS},
            ),  # Multiple possible
            (0.80, {LocationType.VIEWPOINT, LocationType.RUINS}),  # High elevation
            (0.45, set()),  # Too low (water)
            (0.95, set()),  # Too high
        ]

        for height, expected_types in test_cases:
            valid_types = set()
            for _ in range(100):  # Test multiple times due to randomness
                loc_type = location_system._choose_location_type(height)
                if loc_type:
                    valid_types.add(loc_type)
            assert (
                valid_types == expected_types
            ), f"For height {height}, got {valid_types}, expected {expected_types}"

    def test_name_generation(self, location_system: LocationSystem) -> None:
        """Test name generation for all location types"""
        for loc_type in LocationType:
            # Generate multiple names to ensure variety
            names = {location_system._generate_name(loc_type) for _ in range(10)}
            # Should get at least 2 different names
            assert len(names) >= 2
            # Names should be non-empty strings
            assert all(isinstance(name, str) and name for name in names)

    def test_description_generation(self, location_system: LocationSystem) -> None:
        """Test description generation for all location types"""
        for loc_type in LocationType:
            name = location_system._generate_name(loc_type)
            # Generate multiple descriptions to ensure variety
            descriptions = {
                location_system._generate_description(loc_type, name) for _ in range(10)
            }
            # Should get at least 2 different descriptions
            assert len(descriptions) >= 2
            # Descriptions should be non-empty strings
            assert all(isinstance(desc, str) and desc for desc in descriptions)

    def test_get_nearby_locations(self, location_system: LocationSystem) -> None:
        """Test finding locations near a given point using Manhattan distance"""
        # Add some test locations
        test_locations = [
            Location(
                x=10,
                y=10,
                type=LocationType.VILLAGE,
                name="Test Village 1",
                description="A test village",
            ),
            Location(
                x=20,
                y=20,
                type=LocationType.RUINS,
                name="Test Ruins 1",
                description="Some test ruins",
            ),
            Location(
                x=40,
                y=40,
                type=LocationType.VIEWPOINT,
                name="Test Viewpoint 1",
                description="A test viewpoint",
            ),
        ]
        location_system.locations.extend(test_locations)

        # Test finding locations within range using Manhattan distance
        # From (15, 15), Manhattan distance to (10, 10) is |15-10| + |15-10| = 10
        # and to (20, 20) is |15-20| + |15-20| = 10
        nearby = location_system.get_nearby_locations(x=15, y=15, radius=9)
        assert len(nearby) == 0  # No locations within radius 9

        nearby = location_system.get_nearby_locations(x=15, y=15, radius=10)
        assert len(nearby) == 2  # Both locations exactly at distance 10

        nearby = location_system.get_nearby_locations(x=15, y=15, radius=11)
        assert len(nearby) == 2  # Still just the two closest locations

        # Test with point closer to one location
        nearby = location_system.get_nearby_locations(x=12, y=12, radius=5)
        assert len(nearby) == 1
        assert nearby[0].name == "Test Village 1"

        # Test with invalid coordinates (should return empty list)
        nearby = location_system.get_nearby_locations(x=-1, y=-1, radius=5)
        assert len(nearby) == 0

        # Test with zero radius (should return empty list)
        nearby = location_system.get_nearby_locations(x=10, y=10, radius=0)
        assert len(nearby) == 0

    def test_discover_location(self, location_system: LocationSystem) -> None:
        """Test discovering locations when player is nearby"""
        # Add a test location
        test_location = Location(
            x=25,
            y=25,
            type=LocationType.VILLAGE,
            name="Test Village",
            description="A test village",
        )
        location_system.locations.append(test_location)

        # Test discovery when player is nearby
        discovered = location_system.check_discoveries(x=24, y=24)
        assert len(discovered) == 1
        assert discovered[0].name == "Test Village"
        assert discovered[0].discovered

        # Test no discovery when player is far
        discovered = location_system.check_discoveries(x=0, y=0)
        assert len(discovered) == 0

        # Test rediscovery of already discovered location (should not be included)
        discovered = location_system.check_discoveries(x=24, y=24)
        assert len(discovered) == 0

    def test_get_discovered_locations(self, location_system: LocationSystem) -> None:
        """Test getting only discovered locations"""
        # Add some test locations
        test_locations = [
            Location(
                x=10,
                y=10,
                type=LocationType.VILLAGE,
                name="Village 1",
                description="First village",
            ),
            Location(
                x=20,
                y=20,
                type=LocationType.RUINS,
                name="Ruins 1",
                description="First ruins",
            ),
            Location(
                x=30,
                y=30,
                type=LocationType.VIEWPOINT,
                name="Viewpoint 1",
                description="First viewpoint",
            ),
        ]
        location_system.locations.extend(test_locations)

        # Initially no locations should be discovered
        assert len(location_system.get_discovered_locations()) == 0

        # Discover some locations
        location_system.check_discoveries(x=11, y=11)  # Should discover Village 1
        location_system.check_discoveries(x=21, y=21)  # Should discover Ruins 1

        discovered = location_system.get_discovered_locations()
        assert len(discovered) == 2
        assert "Village 1" in [loc.name for loc in discovered]
        assert "Ruins 1" in [loc.name for loc in discovered]
        assert "Viewpoint 1" not in [loc.name for loc in discovered]

        # Discover all locations
        location_system.check_discoveries(x=31, y=31)  # Should discover Viewpoint 1

        discovered = location_system.get_discovered_locations()
        assert len(discovered) == 3
        assert all(loc.discovered for loc in discovered)
