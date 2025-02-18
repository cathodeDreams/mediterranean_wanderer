"""Tests for the interaction system."""

import pytest
from unittest.mock import MagicMock
import numpy as np
from numpy.typing import NDArray
from island_rl.interaction import InteractionSystem, InteractionResult
from island_rl.locations import Location, LocationSystem, LocationType
from typing import Any


@pytest.fixture
def terrain() -> NDArray[np.float64]:
    """Create a test terrain."""
    return np.full((50, 80), 0.5, dtype=np.float64)


@pytest.fixture
def location_system(terrain: NDArray[np.float64]) -> LocationSystem:
    """Create a test location system."""
    system = LocationSystem(terrain)
    system.generate_locations()
    return system


@pytest.fixture
def interaction_system(location_system: LocationSystem) -> InteractionSystem:
    """Create a test interaction system."""
    return InteractionSystem(location_system)


class TestInteractionSystem:
    """Test suite for the InteractionSystem class."""

    def test_interaction_system_initialization(self, interaction_system: InteractionSystem) -> None:
        """Test interaction system initialization."""
        assert interaction_system.location_system is not None
        assert interaction_system.interaction_radius > 0

    def test_interaction_with_nothing_nearby(self, interaction_system: InteractionSystem) -> None:
        """Test interaction when nothing is nearby."""
        result = interaction_system.try_interact(0, 0)
        assert not result.success
        assert "nothing interesting" in result.message.lower()
        assert result.details is None

    def test_interaction_with_undiscovered_location(
        self, interaction_system: InteractionSystem
    ) -> None:
        """Test interaction with an undiscovered location."""
        # Create a test location
        test_location = Location(
            x=1,
            y=1,
            type=LocationType.BEACH,
            name="Test Beach",
            description="A test beach",
        )
        interaction_system.location_system.locations = [test_location]

        result = interaction_system.try_interact(1, 1)
        assert result.success
        assert test_location.name in result.message
        assert result.details is not None
        assert result.details["type"] == LocationType.BEACH.name
        assert result.details["description"] == test_location.description

    def test_interaction_with_discovered_location(
        self, interaction_system: InteractionSystem
    ) -> None:
        """Test interaction with a discovered location."""
        # Create a discovered test location
        test_location = Location(
            x=1,
            y=1,
            type=LocationType.BEACH,
            name="Test Beach",
            description="A test beach",
        )
        test_location.discovered = True
        interaction_system.location_system.locations = [test_location]

        result = interaction_system.try_interact(1, 1)
        assert result.success
        assert test_location.name in result.message
        assert result.details is not None
        assert result.details["type"] == LocationType.BEACH.name
        assert result.details["description"] == test_location.description

    def test_interaction_radius(self, interaction_system: InteractionSystem) -> None:
        """Test interaction radius limits."""
        # Create a test location just outside interaction radius
        test_location = Location(
            x=interaction_system.interaction_radius + 1,
            y=0,
            type=LocationType.BEACH,
            name="Test Beach",
            description="A test beach",
        )
        interaction_system.location_system.locations = [test_location]

        result = interaction_system.try_interact(0, 0)
        assert not result.success
        assert "nothing interesting" in result.message.lower()

    def test_interaction_with_multiple_locations(self, interaction_system: InteractionSystem) -> None:
        """Test interaction when multiple locations are within range."""
        # Create two test locations at the same distance
        location1 = Location(
            x=1, y=0,
            type=LocationType.BEACH,
            name="Test Beach",
            description="A test beach"
        )
        location2 = Location(
            x=0, y=1,
            type=LocationType.VILLAGE,
            name="Test Village",
            description="A test village"
        )
        interaction_system.location_system.locations = [location1, location2]

        # Test interaction at a point equidistant from both
        result = interaction_system.try_interact(0, 0)
        assert result.success
        # Should interact with the first undiscovered location found
        assert result.details is not None
        assert not location1.discovered or not location2.discovered

    def test_interaction_priority(self, interaction_system: InteractionSystem) -> None:
        """Test interaction priority between discovered and undiscovered locations."""
        # Create a discovered and an undiscovered location
        discovered = Location(
            x=1, y=0,
            type=LocationType.BEACH,
            name="Discovered Beach",
            description="A discovered beach"
        )
        discovered.discovered = True

        undiscovered = Location(
            x=0, y=1,
            type=LocationType.VILLAGE,
            name="Hidden Village",
            description="A hidden village"
        )

        interaction_system.location_system.locations = [discovered, undiscovered]

        # Test interaction - should prioritize undiscovered location
        result = interaction_system.try_interact(0, 0)
        assert result.success
        assert result.details is not None
        assert result.details["name"] == "Hidden Village"

    def test_interaction_distance_priority(self, interaction_system: InteractionSystem) -> None:
        """Test that closer locations are prioritized for interaction."""
        # Create locations at different distances
        close_location = Location(
            x=1, y=0,
            type=LocationType.BEACH,
            name="Close Beach",
            description="A nearby beach"
        )
        far_location = Location(
            x=2, y=0,
            type=LocationType.VILLAGE,
            name="Far Village",
            description="A distant village"
        )

        interaction_system.location_system.locations = [far_location, close_location]

        # Test interaction - should prioritize closer location
        result = interaction_system.try_interact(0, 0)
        assert result.success
        assert result.details is not None
        assert result.details["name"] == "Close Beach"

    def test_interaction_result_creation(self) -> None:
        """Test creation and properties of InteractionResult."""
        # Test successful interaction
        success_result = InteractionResult(
            success=True,
            message="Test success",
            details={"type": "TEST", "description": "Test details"}
        )
        assert success_result.success
        assert success_result.message == "Test success"
        assert success_result.details is not None  # Type guard
        assert success_result.details["type"] == "TEST"

        # Test failed interaction
        fail_result = InteractionResult(
            success=False,
            message="Test failure",
            details=None
        )
        assert not fail_result.success
        assert fail_result.message == "Test failure"
        assert fail_result.details is None

    @pytest.mark.integration
    def test_interaction_integration(self, interaction_system: InteractionSystem) -> None:
        """Integration test for interaction system with multiple locations and states."""
        # Create a mix of locations
        locations = [
            Location(x=1, y=0, type=LocationType.BEACH, name="Near Beach", description="A nearby beach"),
            Location(x=2, y=0, type=LocationType.VILLAGE, name="Far Village", description="A distant village"),
            Location(x=0, y=2, type=LocationType.RUINS, name="Hidden Ruins", description="Ancient ruins"),
        ]
        
        # Set first location as discovered
        locations[0].discovered = True
        interaction_system.location_system.locations = locations

        # Test sequence of interactions
        # 1. Try interacting with nothing nearby
        result1 = interaction_system.try_interact(10, 10)
        assert not result1.success
        assert "nothing interesting" in result1.message.lower()

        # 2. Interact with the discovered beach
        result2 = interaction_system.try_interact(1, 0)
        assert result2.success
        assert "Near Beach" in result2.message
        assert result2.details is not None  # Type guard
        assert "nearby beach" in result2.details["description"]
        assert "examining" in result2.message.lower()

        # 3. Interact with the undiscovered village
        result3 = interaction_system.try_interact(2, 0)
        assert result3.success
        assert "discovered" in result3.message.lower()
        assert "Far Village" in result3.message
        assert locations[1].discovered

        # 4. Interact with the hidden ruins
        result4 = interaction_system.try_interact(0, 2)
        assert result4.success
        assert "discovered" in result4.message.lower()
        assert "Hidden Ruins" in result4.message
        assert locations[2].discovered 