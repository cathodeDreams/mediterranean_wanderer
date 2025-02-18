# Mediterranean Wanderer

A cozy procedurally generated Greek island exploration game built with Python and libtcod.

## Description

Mediterranean Wanderer is a relaxing roguelike-inspired game where players explore a procedurally generated Greek island at their own pace. Unlike traditional roguelikes, there is no combat, no death, and no pressure - just peaceful exploration and discovery. The island terrain is generated using Perlin noise, creating realistic and varied landscapes.

## Features

- Procedurally generated Greek island environments
- Realistic terrain generation with:
  - Perlin noise-based heightmaps
  - Circular island mask
  - Biome-specific color mappings
- Dynamic time system with:
  - 24-minute day cycle
  - Color adjustments based on time
  - Progressive lighting changes
- Weather system with:
  - 3 weather states
  - Smooth transitions
  - Weather-based color filters
- Inventory system with:
  - 10 item capacity
  - Stackable items
  - Categorization and sorting
- 12 types of discoverable locations
- 124 comprehensive unit tests
- Responsive input system with:
  - Non-blocking event handling
  - Arrow key and vi-key movement
  - Inventory toggle (i key)
- Properly aligned UI frames:
  - Top status bar with time/weather
  - Main game area (80x40)
  - Bottom message log with word wrapping
- Message log displays last 3 messages with details

## Development Setup

### Prerequisites

- Python 3.11
- Poetry (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/cathodeDreams/mediterranean_wanderer.git
cd mediterranean_wanderer
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Run the game:
```bash
poetry run python -m island_rl
```

### Development Tools

- **Testing**: `poetry run pytest`
- **Code formatting**: `poetry run black .`
- **Type checking**: `poetry run mypy .`
- **Import sorting**: `poetry run isort .`

## Project Structure

```
island_rl/
├── src/
│   └── island_rl/
│       ├── __init__.py
│       ├── __main__.py
│       ├── engine.py
│       ├── world.py
│       ├── player.py
│       ├── time_system.py
│       ├── weather_system.py
│       ├── locations.py
│       ├── interaction.py
│       ├── message_log.py
│       ├── inventory.py
│       ├── items.py
│       └── assets/
│           └── dejavu10x10_gs_tc.png
├── tests/
│   ├── test_biomes.py
│   ├── test_engine.py
│   ├── test_interaction.py
│   ├── test_inventory.py
│   ├── test_items.py
│   ├── test_locations.py
│   ├── test_main.py
│   ├── test_message_log.py
│   ├── test_player.py
│   ├── test_time_system.py
│   ├── test_weather_system.py
│   └── test_world.py
├── docs/
│   ├── game-design.md
│   └── technical_report.md
├── pyproject.toml
└── README.md
```

## Controls

- **Movement:** Arrow keys or vi keys (h, j, k, l)
- **Interact:** Spacebar or Enter
- **Inventory:** i
- **Quit:** q

## Development Status

- Core game engine and rendering system: ✅
- Terrain generation with Perlin noise: ✅
- Biome system with multiple terrain types: ✅
- Player movement and controls: ✅
- Day/night cycle: ✅
- Weather system: ✅
- Discoverable Locations: ✅
- Interaction System: ✅
- Message Log: ✅
- Inventory System: ✅
- Test coverage: 95%
- Type checking: Passed (no issues)
- Code formatting: ✅
- Deprecation warnings: ✅
- NPC interactions: 🚧
- Village content: 🚧
- UI alignment and input handling: ✅
- Message log with word wrapping: ✅

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Note

- Brainstorming currently for NPC + Village implementation using llama-cpp-python
- Planning to integrate local LLM for dynamic NPC interactions and village life simulation

## Contributing

[Your contribution guidelines]
