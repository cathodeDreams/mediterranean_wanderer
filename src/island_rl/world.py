"""World generation and management module."""

import numpy as np
import tcod
from tcod import libtcodpy
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Tuple, cast, Any
from numpy.typing import NDArray

# Add a type alias for the biome array
BiomeArray = NDArray[Any]  # Arrays of enums must use Any


class BiomeType(Enum):
    """Enum representing different biome types."""

    DEEP_WATER = auto()
    SHALLOW_WATER = auto()
    BEACH = auto()
    OLIVE_GROVE = auto()
    PINE_FOREST = auto()
    ROCKY_CLIFF = auto()
    RUINS = auto()


@dataclass
class Location:
    """A special location on the island."""

    x: int
    y: int
    type: str
    description: str
    discovered: bool = False


class Island:
    """Manages the island's terrain and features."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.terrain: Optional[NDArray[np.float64]] = None
        self.moisture: Optional[NDArray[np.float64]] = None
        self.biomes: Optional[BiomeArray] = None
        self.features: List[Location] = []

    def _create_base_noise(self, seed: int) -> tcod.noise.Noise:
        """Create the base noise generator with appropriate dimensions and parameters."""
        dimensions = 2  # 2D noise
        # Create noise with default parameters
        return tcod.noise.Noise(
            dimensions=dimensions,
            algorithm=libtcodpy.NOISE_PERLIN,
            seed=seed,
            octaves=6,
            hurst=0.7,  # Higher value = more variation
            lacunarity=2.5,  # Higher value = more detail
        )

    def _generate_height_map(self, noise: tcod.noise.Noise) -> NDArray[np.float64]:
        """Generate the height map using the noise generator."""
        # Scale factor for noise coordinates (smaller = more variation)
        scale = 2.5

        # Initialize the height map with explicit type
        height_map: NDArray[np.float64] = np.zeros(
            (self.height, self.width), dtype=np.float64
        )

        # Generate noise values
        for y in range(self.height):
            for x in range(self.width):
                nx = x / self.width * scale
                ny = y / self.height * scale
                height_map[y, x] = noise.get_point(nx, ny)

        # Normalize to [0, 1] range and enhance contrast
        height_map = cast(NDArray[np.float64], (height_map + 1.0) / 2.0)

        # Apply exponential transformation to create more extreme heights
        height_map = cast(
            NDArray[np.float64], np.power(height_map, 0.7)
        )  # More high terrain

        # Add some random peaks
        peak_mask = np.random.random(height_map.shape) < 0.02  # 2% chance for peaks
        height_map[peak_mask] = np.minimum(height_map[peak_mask] * 1.5, 1.0)

        return height_map

    def _generate_moisture_map(self, noise: tcod.noise.Noise) -> NDArray[np.float64]:
        """Generate a moisture map using a different noise scale."""
        scale = 4.0  # Larger scale for more distinct moisture zones
        moisture_map: NDArray[np.float64] = np.zeros(
            (self.height, self.width), dtype=np.float64
        )

        # Use different noise coordinates for moisture
        for y in range(self.height):
            for x in range(self.width):
                nx = (x / self.width + 100.0) * scale  # Offset to get different pattern
                ny = (y / self.height + 100.0) * scale
                moisture_map[y, x] = noise.get_point(nx, ny)

        # Normalize and enhance contrast for more distinct zones
        moisture_map = cast(NDArray[np.float64], (moisture_map + 1.0) / 2.0)
        moisture_map = cast(
            NDArray[np.float64], np.power(moisture_map, 1.2)
        )  # Enhance contrast

        # Apply coastal moisture influence
        if self.terrain is not None:
            coastal_influence = np.exp(
                -5.0 * np.abs(self.terrain - 0.3)
            )  # Peak at shoreline
            moisture_map = cast(
                NDArray[np.float64], 0.7 * moisture_map + 0.3 * coastal_influence
            )

        return moisture_map

    def _apply_island_mask(
        self, height_map: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """Apply a circular mask to create an island shape."""
        # Create coordinate grids
        y, x = np.ogrid[: self.height, : self.width]

        # Calculate center points
        center_y, center_x = self.height / 2, self.width / 2

        # Calculate normalized distance from center (0 to 1)
        dist = np.sqrt(
            ((x - center_x) / (self.width / 2)) ** 2
            + ((y - center_y) / (self.height / 2)) ** 2
        )

        # Create a smoother falloff (adjust power for different shapes)
        mask = 1.0 - np.clip(dist**1.5, 0, 1)  # Reduced power for larger island

        # Apply the mask with a bias towards more land
        masked_map = height_map * (mask * 0.8 + 0.2)  # Increased minimum value

        # Enhance contrast to create more distinct shorelines
        masked_map = np.power(masked_map, 0.8)

        return cast(NDArray[np.float64], masked_map)

    def _determine_biomes(self) -> BiomeArray:
        """Determine biome types based on height and moisture."""
        if self.terrain is None or self.moisture is None:
            raise ValueError(
                "Terrain and moisture must be generated before determining biomes"
            )

        biomes = np.empty(self.terrain.shape, dtype=object)

        for y in range(self.height):
            for x in range(self.width):
                height = self.terrain[y, x]
                moisture = self.moisture[y, x]

                # Basic height-based biomes
                if height < 0.2:
                    biomes[y, x] = BiomeType.DEEP_WATER
                elif height < 0.3:
                    biomes[y, x] = BiomeType.SHALLOW_WATER
                elif height < 0.4:
                    biomes[y, x] = BiomeType.BEACH
                else:
                    # Land biomes influenced by moisture and height
                    if height > 0.75:  # Reduced threshold for rocky cliffs
                        biomes[y, x] = BiomeType.ROCKY_CLIFF
                    elif moisture > 0.6:  # High moisture areas
                        if height > 0.5:  # Higher elevation favors pine forests
                            biomes[y, x] = BiomeType.PINE_FOREST
                        else:
                            biomes[y, x] = BiomeType.OLIVE_GROVE
                    elif moisture > 0.4:  # Medium moisture
                        if height > 0.5:  # Higher elevation
                            biomes[y, x] = BiomeType.PINE_FOREST
                        else:
                            biomes[y, x] = BiomeType.OLIVE_GROVE
                    else:  # Low moisture
                        if height > 0.45:  # Most elevated areas are pine forests
                            biomes[y, x] = BiomeType.PINE_FOREST
                        else:
                            biomes[y, x] = BiomeType.OLIVE_GROVE

                    # Small chance for ruins in suitable terrain
                    if 0.4 < height < 0.7 and np.random.random() < 0.02:
                        biomes[y, x] = BiomeType.RUINS

        return cast(BiomeArray, biomes)

    def generate(self, seed: Optional[int] = None) -> None:
        """Generate the island terrain using Perlin noise."""
        if seed is not None:
            np.random.seed(seed)
        else:
            seed = np.random.randint(0, 1000000)

        # Create noise generators
        height_noise = self._create_base_noise(seed)
        moisture_noise = self._create_base_noise(
            seed + 1
        )  # Different seed for moisture

        # Generate base height map
        height_map = self._generate_height_map(height_noise)
        height_map = self._apply_island_mask(height_map)
        self.terrain = cast(NDArray[np.float64], np.clip(height_map, 0.0, 1.0))

        # Generate moisture map
        self.moisture = self._generate_moisture_map(moisture_noise)

        # Determine biomes
        self.biomes = self._determine_biomes()

    def get_tile(self, x: int, y: int) -> np.float64:
        """Get the terrain height at the specified coordinates."""
        if self.terrain is None:
            return np.float64(0.0)
        # Ensure we return a numpy float64
        return np.float64(self.terrain[y, x])

    def get_biome(self, x: int, y: int) -> BiomeType:
        """Get the biome type at the specified coordinates."""
        if self.biomes is None:
            raise ValueError("Biomes have not been generated yet")
        # Cast the numpy array element to BiomeType to ensure correct typing
        return cast(BiomeType, self.biomes[y, x])

    def add_feature(self, location: Location) -> None:
        """Add a new feature to the island."""
        self.features.append(location)
