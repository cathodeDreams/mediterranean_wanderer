"""Tests for the world generation module."""

import pytest
import numpy as np
from island_rl.world import Island, Location
from island_rl.engine import Engine, COLORS


def test_island_initialization() -> None:
    """Test that an island is properly initialized."""
    island = Island(width=100, height=80)
    assert island.width == 100
    assert island.height == 80
    assert island.terrain is None
    assert len(island.features) == 0


def test_island_generation() -> None:
    """Test basic island generation."""
    island = Island(width=100, height=80)
    island.generate(seed=42)  # Use fixed seed for reproducibility

    assert island.terrain is not None
    assert island.terrain.shape == (80, 100)
    assert isinstance(island.terrain, np.ndarray)


def test_location_creation() -> None:
    """Test creation of a location on the island."""
    location = Location(
        x=10, y=20, type="village", description="A small fishing village"
    )

    assert location.x == 10
    assert location.y == 20
    assert location.type == "village"
    assert location.description == "A small fishing village"
    assert location.discovered is False


def test_adding_feature_to_island() -> None:
    """Test adding a feature to the island."""
    island = Island(width=100, height=80)
    location = Location(x=10, y=20, type="ruins", description="Ancient temple ruins")

    island.add_feature(location)
    assert len(island.features) == 1
    assert island.features[0] == location


def test_terrain_generation_properties() -> None:
    """Test that generated terrain has expected properties."""
    island = Island(width=100, height=80)
    island.generate(seed=42)

    # Check terrain bounds
    assert np.all(island.terrain >= 0.0)  # type: ignore
    assert np.all(island.terrain <= 1.0)  # type: ignore

    # Check that we have some water (values < 0.3)
    assert np.any(island.terrain < 0.3)  # type: ignore

    # Check that we have some land (values >= 0.4)
    assert np.any(island.terrain >= 0.4)  # type: ignore

    # Check that terrain is not uniform (has variation)
    assert np.std(island.terrain) > 0.1  # type: ignore


def test_terrain_reproducibility() -> None:
    """Test that terrain generation is reproducible with the same seed."""
    island1 = Island(width=100, height=80)
    island2 = Island(width=100, height=80)

    island1.generate(seed=42)
    island2.generate(seed=42)

    np.testing.assert_array_almost_equal(island1.terrain, island2.terrain)  # type: ignore


def test_terrain_different_seeds() -> None:
    """Test that different seeds produce different terrain."""
    island1 = Island(width=100, height=80)
    island2 = Island(width=100, height=80)

    island1.generate(seed=42)
    island2.generate(seed=43)

    # Terrains should be different
    with pytest.raises(AssertionError):
        np.testing.assert_array_almost_equal(island1.terrain, island2.terrain)  # type: ignore


def test_get_tile() -> None:
    """Test getting terrain height at specific coordinates."""
    island = Island(width=100, height=80)
    island.generate(seed=42)

    # Test a few random coordinates
    for x, y in [(0, 0), (50, 40), (99, 79)]:
        height = island.get_tile(x, y)
        assert isinstance(height, np.float64)
        assert 0.0 <= height <= 1.0


def test_terrain_visualization() -> None:
    """Test terrain visualization symbols."""
    from island_rl.engine import Engine

    engine = Engine(80, 50)

    # Force time to noon for consistent lighting
    engine.time.minutes = 720  # 12:00 PM

    # Test deep water
    symbol, color = engine.get_terrain_symbol(0.1)
    assert symbol == "≈"
    # Don't test exact color values as they change with time of day
    assert len(color) == 3
    assert all(isinstance(c, int) for c in color)
    assert all(0 <= c <= 255 for c in color)

    # Test shallow water
    symbol, color = engine.get_terrain_symbol(0.25)
    assert symbol == "~"
    assert len(color) == 3
    assert all(0 <= c <= 255 for c in color)

    # Test beach
    symbol, color = engine.get_terrain_symbol(0.35)
    assert symbol == "."
    assert len(color) == 3
    assert all(0 <= c <= 255 for c in color)

    # Test grass/plains
    symbol, color = engine.get_terrain_symbol(0.5)
    assert symbol == '"'
    assert len(color) == 3
    assert all(0 <= c <= 255 for c in color)

    # Test cliffs/hills
    symbol, color = engine.get_terrain_symbol(0.8)
    assert symbol == "^"
    assert len(color) == 3
    assert all(0 <= c <= 255 for c in color)


def test_engine_initialization() -> None:
    """Test that the engine properly initializes with an island."""
    engine = Engine(80, 50)

    # Check that island was created and terrain generated
    assert engine.island is not None
    assert engine.island.terrain is not None
    assert engine.island.width == 80
    assert engine.island.height == 50
