"""Tests for the biome generation system."""

import pytest
import numpy as np
from island_rl.world import Island, BiomeType
from island_rl.engine import COLORS


def test_biome_type_enum() -> None:
    """Test that BiomeType enum contains all expected biome types."""
    assert hasattr(BiomeType, "DEEP_WATER")
    assert hasattr(BiomeType, "SHALLOW_WATER")
    assert hasattr(BiomeType, "BEACH")
    assert hasattr(BiomeType, "OLIVE_GROVE")
    assert hasattr(BiomeType, "PINE_FOREST")
    assert hasattr(BiomeType, "ROCKY_CLIFF")
    assert hasattr(BiomeType, "RUINS")


def test_biome_generation() -> None:
    """Test that biomes are generated correctly based on height and moisture."""
    island = Island(width=100, height=80)
    island.generate(seed=42)

    assert island.biomes is not None
    assert island.biomes.shape == (80, 100)
    assert isinstance(island.biomes, np.ndarray)


def test_biome_distribution() -> None:
    """Test that biome distribution follows expected patterns."""
    island = Island(width=100, height=80)
    island.generate(seed=42)

    # Convert biomes to a list for counting
    biome_list = island.biomes.flatten().tolist()  # type: ignore

    # Check that we have all major biome types
    assert BiomeType.DEEP_WATER in biome_list
    assert BiomeType.SHALLOW_WATER in biome_list
    assert BiomeType.BEACH in biome_list
    assert BiomeType.OLIVE_GROVE in biome_list
    assert BiomeType.PINE_FOREST in biome_list
    assert BiomeType.ROCKY_CLIFF in biome_list

    # Check relative distributions
    water_count = sum(
        1 for b in biome_list if b in [BiomeType.DEEP_WATER, BiomeType.SHALLOW_WATER]
    )
    land_count = sum(
        1
        for b in biome_list
        if b not in [BiomeType.DEEP_WATER, BiomeType.SHALLOW_WATER]
    )

    # Expect roughly 40-60% water
    water_percentage = water_count / len(biome_list)
    assert 0.4 <= water_percentage <= 0.6


def test_biome_moisture_influence() -> None:
    """Test that moisture levels influence biome generation."""
    island = Island(width=100, height=80)
    island.generate(seed=42)

    # Get counts of moisture-dependent biomes
    biome_list = island.biomes.flatten().tolist()  # type: ignore
    pine_count = sum(1 for b in biome_list if b == BiomeType.PINE_FOREST)
    olive_count = sum(1 for b in biome_list if b == BiomeType.OLIVE_GROVE)

    # Both biomes should exist, but not in equal numbers
    assert pine_count > 0
    assert olive_count > 0
    assert (
        abs(pine_count - olive_count) > len(biome_list) * 0.1
    )  # At least 10% difference


def test_biome_height_influence() -> None:
    """Test that terrain height properly influences biome placement."""
    island = Island(width=100, height=80)
    island.generate(seed=42)

    # Check correlation between height and biomes
    for y in range(island.height):
        for x in range(island.width):
            height = island.get_tile(x, y)
            biome = island.get_biome(x, y)

            if height < 0.2:
                assert biome == BiomeType.DEEP_WATER
            elif height < 0.3:
                assert biome == BiomeType.SHALLOW_WATER
            elif height < 0.4:
                assert biome == BiomeType.BEACH


def test_get_biome() -> None:
    """Test the get_biome method returns correct biome types."""
    island = Island(width=100, height=80)
    island.generate(seed=42)

    # Test getting biomes at various coordinates
    for x, y in [(0, 0), (50, 40), (99, 79)]:
        biome = island.get_biome(x, y)
        assert isinstance(biome, BiomeType)


def test_biome_visualization() -> None:
    """Test that each biome type has appropriate visualization characters."""
    from island_rl.engine import Engine

    engine = Engine(80, 50)

    # Force time to noon for consistent lighting
    engine.time.minutes = 720  # 12:00 PM

    test_cases = [
        (BiomeType.DEEP_WATER, "≈"),
        (BiomeType.SHALLOW_WATER, "~"),
        (BiomeType.BEACH, "."),
        (BiomeType.OLIVE_GROVE, "τ"),
        (BiomeType.PINE_FOREST, "♠"),
        (BiomeType.ROCKY_CLIFF, "^"),
        (BiomeType.RUINS, "Π"),
    ]

    for biome_type, expected_symbol in test_cases:
        symbol, color = engine.get_biome_symbol(biome_type)
        assert symbol == expected_symbol
        # Don't test exact color values as they change with time of day
        assert len(color) == 3
        assert all(isinstance(c, int) for c in color)
        assert all(0 <= c <= 255 for c in color)
