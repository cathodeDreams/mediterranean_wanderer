"""Main game engine module handling the core game loop and state management."""

import tcod
from tcod import libtcodpy
import numpy as np
from typing import Optional, Dict, Tuple, cast, List, Any
from pathlib import Path
from .world import Island, BiomeType
from .player import Player
from .time_system import TimeSystem
from .weather_system import WeatherSystem
from .locations import LocationSystem, Location, LocationType
from .interaction import InteractionSystem, InteractionResult
from .message_log import MessageLog, MessageCategory
from .items import ItemFactory, ItemType

# Color palette based on game design document
COLORS: Dict[str, Tuple[int, int, int]] = {
    "water": (65, 105, 225),  # Royal blue
    "deep_water": (25, 25, 112),  # Midnight blue
    "beach": (245, 222, 179),  # Sandy beige
    "grass": (85, 107, 47),  # Olive green
    "cliff": (139, 69, 19),  # Saddle brown
    "white": (255, 255, 255),  # White
    "olive": (128, 128, 0),  # Olive green
    "pine": (34, 139, 34),  # Forest green
    "ruins": (169, 169, 169),  # Gray
    "text": (200, 200, 200),  # Light gray for text
    "highlight": (255, 255, 0),  # Yellow for highlights
}


class Engine:
    """Main game engine class coordinating all game systems."""

    def __init__(self, screen_width: int, screen_height: int) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.console: Optional[tcod.console.Console] = None
        self.context: Optional[tcod.context.Context] = None
        # Get the directory where this file is located
        self.package_dir = Path(__file__).parent.resolve()

        # Initialize the island
        self.island = Island(screen_width, screen_height)
        self.island.generate()  # Generate initial terrain

        # Initialize location system with properly typed terrain
        if self.island.terrain is None:
            raise ValueError(
                "Island terrain must be generated before initializing LocationSystem"
            )
        self.locations = LocationSystem(self.island.terrain)
        self.locations.generate_locations()
        self.recent_discoveries: List[Location] = []

        # Initialize player at a valid starting position
        self.player = self._initialize_player()

        # Initialize time system
        self.time = TimeSystem()

        # Initialize weather system
        self.weather = WeatherSystem()
        self._last_weather_desc = self.weather.get_weather_description()

        # Initialize interaction system
        self.interaction = InteractionSystem(self.locations)

        # Initialize message log
        self.message_log = MessageLog()

        # State for inventory display
        self.show_inventory = False

        # Add initial system message
        self.message_log.add_message(
            "Welcome to Mediterranean Wanderer!",
            MessageCategory.SYSTEM,
            "Use arrow keys or vi keys (h,j,k,l) to move. Space or Enter to interact. 'i' for inventory.",
        )

    def _initialize_player(self) -> Player:
        """Initialize the player at a valid starting position on the island."""
        # Try to find a suitable starting position near the center first
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        radius = 0
        max_radius = max(self.screen_width, self.screen_height) // 2

        while radius <= max_radius:
            # Check positions in expanding circles around center
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    x = center_x + dx
                    y = center_y + dy
                    # Check if position is within bounds and suitable
                    if (0 <= x < self.screen_width and 
                        0 <= y < self.screen_height and 
                        self.island.get_tile(x, y) >= 0.3):  # Beach or higher
                        return Player(x=x, y=y)
            radius += 1

        # If no suitable position found, try any position on the map
        for y in range(self.screen_height):
            for x in range(self.screen_width):
                if self.island.get_tile(x, y) >= 0.3:  # Beach or higher
                    return Player(x=x, y=y)

        # Ultimate fallback to center if no suitable position found
        self.message_log.add_message(
            "Warning: No suitable starting position found.",
            MessageCategory.SYSTEM,
            "Starting at map center. You may be in water."
        )
        return Player(x=center_x, y=center_y)

    def initialize(self) -> None:
        """Initialize the game engine and all subsystems."""
        try:
            # Load tileset
            tileset = tcod.tileset.load_tilesheet(
                str(self.package_dir / "assets" / "dejavu10x10_gs_tc.png"),
                32,
                8,
                tcod.tileset.CHARMAP_TCOD,
            )

            # Create console first
            self.console = tcod.console.Console(
                width=self.screen_width,
                height=self.screen_height,
                order="F"
            )

            # Create context with proper parameters
            self.context = tcod.context.new(
                columns=self.screen_width,
                rows=self.screen_height,
                tileset=tileset,
                title="Mediterranean Wanderer",
                vsync=True,
                sdl_window_flags=tcod.context.SDL_WINDOW_RESIZABLE
            )

            # Clear console and present initial frame
            self.console.clear()
            self.render()
            self.context.present(self.console)

        except Exception as e:
            self.message_log.add_message(
                "Error initializing game engine.",
                MessageCategory.SYSTEM,
                str(e)
            )
            raise

    def update(self) -> None:
        """Update game state for the current frame."""
        try:
            # Get all pending events
            events = tcod.event.get()
            if events is None:
                events = []

            for event in events:
                if isinstance(event, tcod.event.Quit) or (
                    isinstance(event, tcod.event.KeyDown)
                    and event.sym == tcod.event.KeySym.ESCAPE
                ):
                    raise SystemExit()
                elif isinstance(event, tcod.event.KeyDown):
                    # If inventory is shown, handle inventory keys
                    if self.show_inventory:
                        if event.sym == tcod.event.KeySym.i:
                            self.show_inventory = False
                        continue

                    # Handle player input
                    result = self.player.handle_input(event, self.island, self.interaction)
                    
                    if isinstance(result, tuple):
                        action_type = result[0]
                        if action_type == "interact":
                            # For interaction, attempt to interact at player's position
                            inter_result = self.interaction.try_interact(self.player.x, self.player.y)
                            if inter_result.success:
                                self.message_log.add_message(
                                    inter_result.message,
                                    MessageCategory.INTERACTION,
                                    inter_result.details.get("description") if inter_result.details else None
                                )
                                # Try to generate an item based on location type
                                if inter_result.details and "type" in inter_result.details:
                                    item = self._generate_item_for_location(inter_result.details["type"])
                                    if item and self.player.add_to_inventory(item):
                                        self.message_log.add_message(
                                            f"Found {item.name}!",
                                            MessageCategory.INTERACTION,
                                            item.description
                                        )
                            else:
                                self.message_log.add_message(
                                    inter_result.message,
                                    MessageCategory.SYSTEM
                                )
                        elif action_type == "inventory":
                            self.show_inventory = True
                    elif result:
                        # Check for new discoveries
                        discoveries = self.locations.check_discoveries(
                            self.player.x, self.player.y
                        )
                        for discovery in discoveries:
                            self.message_log.add_message(
                                f"Discovered {discovery.name}!",
                                MessageCategory.DISCOVERY,
                                discovery.description
                            )
                        
                        # Time and weather advance when player moves
                        old_time_desc = self.time.get_time_description()
                        
                        self.time.advance()
                        self.weather.update()
                        
                        # Log time changes
                        new_time_desc = self.time.get_time_description()
                        if new_time_desc != old_time_desc:
                            self.message_log.add_message(
                                f"Time changes to {new_time_desc}",
                                MessageCategory.TIME
                            )
                        
                        # Log weather changes
                        new_weather_desc = self.weather.get_weather_description()
                        if new_weather_desc != self._last_weather_desc:
                            self.message_log.add_message(
                                f"Weather changes to {new_weather_desc}",
                                MessageCategory.WEATHER
                            )
                            self._last_weather_desc = new_weather_desc
        except RuntimeWarning:
            # Handle RuntimeWarning from event polling before SDL init
            pass

    def _generate_item_for_location(self, location_type: str) -> Optional[Any]:
        """Generate an appropriate item based on location type."""
        # Define item probabilities for each location type
        location_items = {
            "BEACH": [(ItemType.SHELL, 0.7), (ItemType.STONE, 0.3)],
            "GROVE": [(ItemType.HERB, 0.4), (ItemType.FRUIT, 0.6)],
            "RUINS": [(ItemType.STONE, 0.8), (ItemType.MESSAGE_BOTTLE, 0.2)],
            "VIEWPOINT": [(ItemType.FLOWER, 1.0)],
            "VILLAGE": [(ItemType.FRUIT, 0.5), (ItemType.HERB, 0.5)],
        }

        if location_type not in location_items:
            return None

        # Roll for item type
        roll = np.random.random()
        cumulative_prob = 0.0
        selected_type = None

        for item_type, prob in location_items[location_type]:
            cumulative_prob += prob
            if roll <= cumulative_prob:
                selected_type = item_type
                break

        if selected_type:
            return ItemFactory.create_item(selected_type)
        return None

    def get_biome_symbol(self, biome: BiomeType) -> Tuple[str, Tuple[int, int, int]]:
        """Get the appropriate symbol and color for a given biome type."""
        biome_visuals = {
            BiomeType.DEEP_WATER: ("≈", COLORS["deep_water"]),
            BiomeType.SHALLOW_WATER: ("~", COLORS["water"]),
            BiomeType.BEACH: (".", COLORS["beach"]),
            BiomeType.OLIVE_GROVE: ("τ", COLORS["olive"]),
            BiomeType.PINE_FOREST: ("♠", COLORS["pine"]),
            BiomeType.ROCKY_CLIFF: ("^", COLORS["cliff"]),
            BiomeType.RUINS: ("Π", COLORS["ruins"]),
        }
        symbol, color = biome_visuals[biome]
        # Apply time-of-day and weather lighting
        adjusted_color = self.time.adjust_color(color)
        weather_adjustment = self.weather.get_color_adjustment()
        final_color = cast(
            Tuple[int, int, int],
            tuple(
                int(min(255, c * w)) for c, w in zip(adjusted_color, weather_adjustment)
            ),
        )
        return symbol, final_color

    def get_terrain_symbol(self, height: float) -> Tuple[str, Tuple[int, int, int]]:
        """Get the appropriate symbol and color for a given terrain height."""
        if height < 0.2:
            return ("≈", self._adjust_color(COLORS["deep_water"]))
        elif height < 0.3:
            return ("~", self._adjust_color(COLORS["water"]))
        elif height < 0.4:
            return (".", self._adjust_color(COLORS["beach"]))
        elif height < 0.7:
            return ('"', self._adjust_color(COLORS["grass"]))
        else:
            return ("^", self._adjust_color(COLORS["cliff"]))

    def _adjust_color(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Apply both time and weather adjustments to a color."""
        time_adjusted = self.time.adjust_color(color)
        weather_adjustment = self.weather.get_color_adjustment()
        return cast(
            Tuple[int, int, int],
            tuple(
                int(min(255, c * w)) for c, w in zip(time_adjusted, weather_adjustment)
            ),
        )

    def render(self) -> None:
        """Render the current game state to the screen."""
        if self.console and self.context and self.island.terrain is not None:
            # Clear the console
            self.console.clear()

            if self.show_inventory:
                self._render_inventory()
            else:
                self._render_game()

            # Present the console
            self.context.present(self.console)

    def _render_game(self) -> None:
        """Render the main game view."""
        if not self.console or not self.island.terrain is not None:
            return

        # Render terrain with biomes
        for y in range(self.screen_height):
            for x in range(self.screen_width):
                biome = self.island.get_biome(x, y)
                symbol, color = self.get_biome_symbol(biome)
                self.console.print(x, y, symbol, fg=color)

        # Render discovered locations
        for loc in self.locations.get_discovered_locations():
            symbol = self._get_location_symbol(loc.type)
            self.console.print(
                loc.x, loc.y, symbol, fg=self._adjust_color(COLORS["white"])
            )

        # Render player
        self.console.print(
            self.player.x,
            self.player.y,
            self.player.symbol,
            fg=self._adjust_color(self.player.color),
        )

        # Calculate UI layout
        ui_frame_height = 3  # Height of top frame
        message_frame_height = 5  # Height of bottom frame for messages
        game_area_height = self.screen_height - ui_frame_height - message_frame_height

        # Draw top frame
        self.console.draw_frame(
            0,
            0,
            self.screen_width,
            ui_frame_height,
            fg=COLORS["white"],
            bg=(0, 0, 0),
        )
        
        # Draw title
        title = "Mediterranean Wanderer"
        title_x = (self.screen_width - len(title)) // 2
        self.console.print(title_x, 0, title, fg=COLORS["white"])

        # Add time and weather information
        time_text = f"Time: {self.time.get_time_of_day()} - {self.time.get_time_description()}"
        weather_text = f"Weather: {self.weather.get_weather_description()} {self.weather.get_weather_symbol()}"
        self.console.print(2, 1, time_text, fg=COLORS["white"])
        self.console.print(2, 2, weather_text, fg=COLORS["white"])

        # Draw message frame
        self.console.draw_frame(
            0,
            self.screen_height - message_frame_height,
            self.screen_width,
            message_frame_height,
            title="Messages",
            fg=COLORS["white"],
            bg=(0, 0, 0),
        )

        # Calculate message area dimensions
        message_area_width = self.screen_width - 4  # 2 padding on each side
        message_area_height = message_frame_height - 2  # Account for frame borders

        # Draw message log (show last 3 messages)
        messages = self.message_log.get_recent_messages(3)
        y_offset = 0
        for message in messages:
            if y_offset >= message_area_height:
                break

            # Combine message text and details
            text = message.text
            if message.details:
                text += f" - {message.details}"

            # Word wrap the text
            wrapped_lines = self._wrap_text(text, message_area_width)
            for line in wrapped_lines:
                if y_offset >= message_area_height:
                    break
                self.console.print(
                    2,
                    self.screen_height - message_frame_height + 1 + y_offset,
                    line,
                    fg=COLORS["white"],
                    bg=(0, 0, 0),
                    alignment=libtcodpy.LEFT,
                )
                y_offset += 1

    def _wrap_text(self, text: str, width: int) -> list[str]:
        """Word wrap text to fit within a given width."""
        if not text:
            return []

        words = text.split()
        lines = []
        current_line: list[str] = []
        current_length = 0

        for word in words:
            word_length = len(word)
            if current_length + word_length + 1 <= width:
                # Add word to current line
                if current_line:
                    current_line.append(" ")
                    current_length += 1
                current_line.append(word)
                current_length += word_length
            else:
                # Start a new line
                if current_line:
                    lines.append("".join(current_line))
                current_line = [word]
                current_length = word_length

        if current_line:
            lines.append("".join(current_line))

        return lines

    def _render_inventory(self) -> None:
        """Render the inventory screen."""
        if not self.console:
            return

        # Draw frame
        self.console.draw_frame(
            0,
            0,
            self.screen_width,
            self.screen_height,
            title="Inventory (press 'i' to close)",
            fg=COLORS["white"],
            bg=(0, 0, 0),
        )

        # Get items by category
        categories = self.player.inventory.get_item_categories()
        
        # Display inventory contents
        y = 2
        if not categories:
            self.console.print(2, y, "Your inventory is empty.", fg=COLORS["text"])
        else:
            for category, items in categories.items():
                # Print category header
                self.console.print(2, y, f"=== {category.name} ===", fg=COLORS["highlight"])
                y += 1
                
                # Print items in category
                for item in items:
                    text = str(item)
                    if item.details:
                        text += f" - {item.details}"
                    self.console.print(4, y, text, fg=COLORS["text"])
                    y += 1
                y += 1  # Add space between categories

        # Show capacity
        capacity_text = f"Capacity: {len(self.player.inventory.items)}/{self.player.inventory.capacity}"
        self.console.print(
            2,
            self.screen_height - 2,
            capacity_text,
            fg=COLORS["text"],
        )

    def _get_location_symbol(self, loc_type: LocationType) -> str:
        """Get the appropriate symbol for a location type."""
        symbols = {
            LocationType.VILLAGE: "⌂",
            LocationType.RUINS: "Π",
            LocationType.VIEWPOINT: "▲",
            LocationType.BEACH: "≈",
            LocationType.GROVE: "♣",
        }
        return symbols[loc_type]

    def run(self) -> None:
        """Main game loop."""
        self.initialize()

        try:
            while True:
                self.update()
                self.render()
        except SystemExit:
            # Clean up when exiting
            if self.context:
                self.context.close()
