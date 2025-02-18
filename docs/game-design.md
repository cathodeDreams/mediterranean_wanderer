# Mediterranean Wanderer
## A Cozy Procedurally Generated Island Exploration Experience

### Core Concept
Mediterranean Wanderer is a relaxing roguelike-inspired game where players explore a procedurally generated Greek island at their own pace. Unlike traditional roguelikes, there is no combat, no death, and no pressure - just peaceful exploration and discovery.

### Technical Implementation

#### Development Environment
- Operating System: Arch Linux
- Terminal: XFCE4 Terminal
- Programming Language: Python 3.11.11
- Engine/Library: libtcod (The Doryen Library)

#### Core Systems

##### Procedural Island Generation
- Heightmap-based terrain generation using Perlin noise
- Biome zones including:
  - Sandy beaches
  - Olive groves
  - Rocky cliffs
  - Small villages
  - Ancient ruins
  - Mediterranean pine forests
- Natural paths and trails connecting points of interest

##### Time System
- Day/night cycle affecting lighting and ambient events
- Gentle weather patterns (sunny, partly cloudy, light rain)
- No negative effects from weather - purely atmospheric

##### Movement and Interaction
- Simple cardinal direction movement (arrow keys/vi keys)
- No diagonal movement to keep navigation relaxing
- Interaction key for examining objects and talking to NPCs
- Auto-walk to visible destinations

#### Visual Design

##### Color Palette
- Warm Mediterranean colors:
  - Sandy beige (#F5DEB3)
  - Sea blue (#4169E1)
  - Olive green (#556B2F)
  - Terracotta (#E27D60)
  - White limestone (#FFFFFF)
- Time-of-day color shifts using libtcod's color manipulation

##### ASCII Art Style
- Simple but recognizable symbols:
  - ~ for water
  - . for paths
  - T for trees
  - ⌂ for houses
  - ☼ for the sun
  - @ for the player
- Color combinations to create depth and atmosphere

#### Features and Content

##### Discoverable Elements
- Hidden viewpoints revealing beautiful vistas
- Small villages with friendly NPCs
- Ancient ruins with historical snippets
- Local flora and fauna to observe
- Bottles with messages from other wanderers
- Secluded beaches and coves

##### Activities
- Collecting shells and stones
- Speaking with local villagers
- Writing in a travel journal
- Sketching landscapes (simple ASCII art minigame)
- Planting flowers and trees
- Swimming in the sea

##### NPCs and Stories
- Friendly villagers sharing local legends
- Traveling merchants with small trades
- Philosophers contemplating by the sea
- Shepherds tending their flocks
- Each with simple dialogue trees focusing on atmosphere

### Technical Considerations

#### Data Structures
```python
class Island:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.terrain = None  # HeightMap
        self.features = []   # List of special locations
        self.npcs = []      # List of NPCs
        self.weather = None  # Current weather state
        self.time = None    # Time of day

class Location:
    def __init__(self, x, y, type, description):
        self.x = x
        self.y = y
        self.type = type  # Village, Ruin, Viewpoint, etc.
        self.description = description
        self.discovered = False
```

#### Save System
- Simple JSON-based save system
- Stores:
  - Current island seed
  - Player position
  - Discovered locations
  - Journal entries
  - Collected items
  - NPC relationships

#### Performance Considerations
- Chunk-based map generation and rendering
- Simple line-of-sight calculations
- Minimal pathfinding requirements
- Efficient terrain generation using libtcod's noise functions

### User Interface

#### Main Screen Layout
```
+------------------------------------------+
|                Time: 14:30               |
|          Weather: Partly Cloudy          |
+------------------------------------------+
|                                          |
|                                          |
|              Game World                  |
|                                          |
|                                          |
+------------------------------------------+
|              Status Line                 |
|           Current Location               |
+------------------------------------------+
```

#### Commands
- Movement: Arrow keys or vi keys (h,j,k,l)
- Interact: Space or Enter
- Inventory: i
- Journal: j
- Help: ?
- Quit: q

### Future Expansion Possibilities
- Multiple islands with boat travel
- Seasonal changes
- Photography mechanic
- Bird watching with a collection book
- Local cuisine discovery
- Simple fishing minigame
- Musical instruments to play
- Constellation viewing at night

### Development Roadmap

#### Phase 1: Core Systems
1. Basic terrain generation
2. Player movement
3. Simple rendering system
4. Time cycle

#### Phase 2: Content
1. NPC implementation
2. Location generation
3. Basic interactions
4. Save/load system

#### Phase 3: Polish
1. Weather effects
2. Sound design
3. UI improvements
4. Content expansion

### Conclusion
Mediterranean Wanderer aims to provide a peaceful, contemplative gaming experience that captures the essence of exploring a Greek island. By focusing on atmosphere and discovery rather than challenge, it creates a unique space in the roguelike genre for relaxation and peaceful exploration.