"""Tests for the game engine module."""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock, call
import tcod
import numpy as np
from pathlib import Path
from typing import Generator, Tuple, cast, Any
from island_rl.engine import Engine, COLORS
from island_rl.world import Island, BiomeType
from island_rl.player import Player
from island_rl.weather_system import WeatherType
from island_rl.locations import LocationType, Location
from island_rl.message_log import MessageCategory
from island_rl.items import ItemType, Item, ItemFactory


@pytest.fixture
def engine() -> Engine:
    """Create a test engine instance."""
    return Engine(80, 50)


@pytest.fixture
def mock_console() -> MagicMock:
    """Create a mock console for testing rendering."""
    console = MagicMock()
    console.print = MagicMock()
    console.draw_frame = MagicMock()
    return console


@pytest.fixture
def initialized_engine(engine: Engine) -> Engine:
    """Create an initialized engine with mocked console and context."""
    with patch("tcod.tileset.load_tilesheet"), \
         patch("tcod.console.Console"), \
         patch("tcod.context.new"):
        engine.initialize()
    return engine


class TestEngine:
    """Test suite for the Engine class."""

    def test_initialization(self, engine: Engine) -> None:
        """Test that the engine initializes all systems properly."""
        assert engine.screen_width == 80
        assert engine.screen_height == 50
        assert engine.console is None
        assert engine.context is None
        assert engine.island is not None
        assert engine.player is not None
        assert engine.time is not None
        assert engine.weather is not None
        assert engine.locations is not None
        assert engine.interaction is not None
        assert engine.message_log is not None
        assert len(engine.message_log.messages) == 1  # Welcome message
        assert engine.message_log.messages[0].category == MessageCategory.SYSTEM
        assert (
            len(engine.locations.locations) > 0
        )  # Should have generated some locations
        assert engine._last_weather_desc == engine.weather.get_weather_description()
        assert not engine.show_inventory  # Inventory should start hidden

    def test_initialize_player_normal(self, engine: Engine) -> None:
        """Test player initialization on normal terrain."""
        # Set up a simple terrain with a valid starting position
        engine.island.terrain = np.full((50, 80), 0.5, dtype=np.float64)
        player = engine._initialize_player()

        assert isinstance(player, Player)
        assert 0 <= player.x < 80
        assert 0 <= player.y < 50
        assert engine.island.get_tile(player.x, player.y) >= 0.3

    def test_initialize_player_fallback(self, engine: Engine) -> None:
        """Test player initialization fallback when no valid position exists."""
        # Set up terrain with only water
        engine.island.terrain = np.full((50, 80), 0.1, dtype=np.float64)
        player = engine._initialize_player()

        assert isinstance(player, Player)
        assert player.x == 40  # screen_width // 2
        assert player.y == 25  # screen_height // 2

    def test_update_movement(self, engine: Engine) -> None:
        """Test handling of movement input."""
        key_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.RIGHT,
            sym=tcod.event.KeySym.RIGHT,
            mod=tcod.event.Modifier.NONE,
        )

        with patch("tcod.event.get", return_value=[key_event]):
            with patch.object(
                engine.player, "handle_input", return_value=True
            ) as mock_handle_input:
                initial_minutes = engine.time.minutes
                engine.update()
                mock_handle_input.assert_called_once_with(
                    key_event, engine.island, engine.interaction
                )
                # Time should advance after movement
                assert engine.time.minutes == initial_minutes + 1

    def test_inventory_toggle(self, engine: Engine) -> None:
        """Test toggling inventory display."""
        # Test opening inventory
        key_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.I,
            sym=tcod.event.KeySym.i,
            mod=tcod.event.Modifier.NONE,
        )
        with patch("tcod.event.get", return_value=[key_event]):
            with patch.object(
                engine.player, "handle_input", return_value=("inventory", None)
            ):
                engine.update()
                assert engine.show_inventory

        # Test closing inventory
        with patch("tcod.event.get", return_value=[key_event]):
            engine.update()
            assert not engine.show_inventory

    def test_item_generation(self, engine: Engine) -> None:
        """Test item generation for different location types."""
        # Test each location type
        for loc_type in LocationType:
            item = engine._generate_item_for_location(loc_type.name)
            if item:
                assert isinstance(item, Item)
                # Verify item type matches location
                if loc_type == LocationType.BEACH:
                    assert item.type in (ItemType.SHELL, ItemType.STONE)
                elif loc_type == LocationType.GROVE:
                    assert item.type in (ItemType.HERB, ItemType.FRUIT)
                elif loc_type == LocationType.RUINS:
                    assert item.type in (ItemType.STONE, ItemType.MESSAGE_BOTTLE)
                elif loc_type == LocationType.VIEWPOINT:
                    assert item.type == ItemType.FLOWER
                elif loc_type == LocationType.VILLAGE:
                    assert item.type in (ItemType.FRUIT, ItemType.HERB)

    def test_item_collection(self, engine: Engine) -> None:
        """Test item collection during interaction."""
        # Create a test location
        test_location = Location(
            x=engine.player.x + 1,
            y=engine.player.y,
            type=LocationType.BEACH,
            name="Test Beach",
            description="A test beach",
        )
        engine.locations.locations = [test_location]

        # Simulate interaction
        key_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.SPACE,
            sym=tcod.event.KeySym.SPACE,
            mod=tcod.event.Modifier.NONE,
        )

        with patch("tcod.event.get", return_value=[key_event]):
            with patch.object(
                engine.player, "handle_input", return_value=("interact", True)
            ):
                initial_items = len(engine.player.inventory.items)
                engine.update()
                # Should have found an item
                assert len(engine.player.inventory.items) > initial_items

    def test_render_inventory(self, engine: Engine, mock_console: MagicMock) -> None:
        """Test inventory rendering."""
        engine.console = mock_console
        engine.show_inventory = True

        # Add some test items
        shell = ItemFactory.create_item(ItemType.SHELL)
        bottle = ItemFactory.create_item(ItemType.MESSAGE_BOTTLE)
        engine.player.add_to_inventory(shell)
        engine.player.add_to_inventory(bottle)

        # Test rendering
        engine._render_inventory()

        # Verify frame was drawn
        mock_console.draw_frame.assert_called_with(
            0,
            0,
            engine.screen_width,
            engine.screen_height,
            title="Inventory (press 'i' to close)",
            fg=COLORS["white"],
            bg=(0, 0, 0),
        )

        # Verify items were printed
        assert mock_console.print.call_count >= 4  # Frame + 2 categories + items

    def test_render_empty_inventory(self, engine: Engine, mock_console: MagicMock) -> None:
        """Test rendering empty inventory."""
        engine.console = mock_console
        engine.show_inventory = True

        # Clear inventory
        engine.player.inventory.clear()

        # Test rendering
        engine._render_inventory()

        # Verify empty message was printed
        mock_console.print.assert_any_call(
            2, 2, "Your inventory is empty.", fg=COLORS["text"]
        )

    def test_initialization_error_handling(self, engine: Engine) -> None:
        """Test error handling during engine initialization."""
        with patch("tcod.tileset.load_tilesheet", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                engine.initialize()
            assert len([m for m in engine.message_log.messages if m.category == MessageCategory.SYSTEM]) == 2

    def test_weather_and_time_changes(self, engine: Engine) -> None:
        """Test weather and time change messages."""
        # Simulate movement that triggers time and weather changes
        key_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.RIGHT,
            sym=tcod.event.KeySym.RIGHT,
            mod=tcod.event.Modifier.NONE,
        )

        # Set up initial state
        engine._last_weather_desc = "Sunny"

        with patch("tcod.event.get", return_value=[key_event]):
            with patch.object(engine.player, "handle_input", return_value=True):
                with patch.object(engine.time, "get_time_description", side_effect=["Day", "Dusk"]):
                    with patch.object(engine.weather, "get_weather_description", return_value="Partly Cloudy"):
                        engine.update()
                        time_messages = [m for m in engine.message_log.messages if m.category == MessageCategory.TIME]
                        weather_messages = [m for m in engine.message_log.messages if m.category == MessageCategory.WEATHER]
                        assert len(time_messages) >= 1
                        assert len(weather_messages) >= 1
                        assert "Time changes to Dusk" in time_messages[-1].text
                        assert "Weather changes to Partly Cloudy" in weather_messages[-1].text

    def test_color_adjustment(self, engine: Engine) -> None:
        """Test color adjustment for time and weather."""
        # Test color adjustment at different times and weather conditions
        test_color = COLORS["water"]
        
        # Test different times
        with patch.object(engine.time, "get_light_level", return_value=0.5):
            with patch.object(engine.weather, "get_color_adjustment", return_value=(1.0, 1.0, 1.0)):
                adjusted = engine._adjust_color(test_color)
                assert all(0 <= c <= 255 for c in adjusted)
                assert adjusted != test_color  # Should be adjusted for time

    def test_terrain_and_biome_symbols(self, engine: Engine) -> None:
        """Test terrain and biome symbol generation."""
        # Test terrain symbols
        for height in [0.1, 0.3, 0.5, 0.7, 0.9]:
            symbol, color = engine.get_terrain_symbol(height)
            assert isinstance(symbol, str)
            assert len(symbol) == 1
            assert isinstance(color, tuple)
            assert len(color) == 3

        # Test biome symbols
        for biome in BiomeType:
            symbol, color = engine.get_biome_symbol(biome)
            assert isinstance(symbol, str)
            assert len(symbol) == 1
            assert isinstance(color, tuple)
            assert len(color) == 3

    def test_location_symbols(self, engine: Engine) -> None:
        """Test location symbol generation."""
        for loc_type in LocationType:
            symbol = engine._get_location_symbol(loc_type)
            assert isinstance(symbol, str)
            assert len(symbol) == 1

    def test_game_rendering(self, engine: Engine, mock_console: MagicMock) -> None:
        """Test game world rendering."""
        engine.console = mock_console
        engine.show_inventory = False

        # Test main game rendering
        engine._render_game()

        # Verify terrain was rendered
        assert mock_console.print.call_count > 0

        # Verify UI elements were rendered
        mock_console.draw_frame.assert_called()

    def test_system_exit(self, engine: Engine) -> None:
        """Test system exit handling."""
        # Test escape key
        key_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )
        with patch("tcod.event.get", return_value=[key_event]):
            with pytest.raises(SystemExit):
                engine.update()

        # Test quit event
        quit_event = tcod.event.Quit()
        with patch("tcod.event.get", return_value=[quit_event]):
            with pytest.raises(SystemExit):
                engine.update()

    def test_error_handling_during_update(self, engine: Engine) -> None:
        """Test error handling during update."""
        # Test RuntimeWarning handling
        with patch("tcod.event.get", side_effect=RuntimeWarning):
            engine.update()  # Should not raise an exception

    def test_player_movement_initialization(self, engine: Engine) -> None:
        """Test player movement initialization with different terrain configurations."""
        # Test with a mix of land and water
        mixed_terrain = np.zeros((50, 80), dtype=np.float64)
        mixed_terrain[25:30, 25:30] = 0.5  # Small land area
        engine.island.terrain = mixed_terrain
        player = engine._initialize_player()
        assert 25 <= player.x < 30
        assert 25 <= player.y < 30
        assert engine.island.get_tile(player.x, player.y) >= 0.3

        # Test with spiral search pattern
        sparse_terrain = np.zeros((50, 80), dtype=np.float64)
        sparse_terrain[10, 10] = 0.5  # Single valid spot
        engine.island.terrain = sparse_terrain
        player = engine._initialize_player()
        assert engine.island.get_tile(player.x, player.y) >= 0.3

    def test_ui_alignment(self, engine: Engine, mock_console: MagicMock) -> None:
        """Test UI element alignment and rendering."""
        engine.console = mock_console
        engine.show_inventory = False

        # Test frame alignment
        engine._render_game()
        
        # Verify status line position (top of screen)
        calls = mock_console.print.call_args_list
        status_calls = [call for call in calls if "Time:" in str(call) or "Weather:" in str(call)]
        for call in status_calls:
            args = call[0]
            assert args[0] >= 0  # x position
            assert args[0] < engine.screen_width  # within screen width
            assert args[1] >= 0  # y position
            assert args[1] < 5  # near top of screen

    def test_message_display_alignment(self, engine: Engine, mock_console: MagicMock) -> None:
        """Test message log display alignment."""
        engine.console = mock_console
        engine.show_inventory = False

        # Add test messages
        engine.message_log.add_message("Test message 1", MessageCategory.SYSTEM)
        engine.message_log.add_message("Test message 2", MessageCategory.INTERACTION)
        engine.message_log.add_message("Test message 3", MessageCategory.DISCOVERY)

        # Test message rendering
        engine._render_game()

        # Verify message positions
        message_calls = [
            call for call in mock_console.print.call_args_list 
            if any(msg in str(call) for msg in ["Test message 1", "Test message 2", "Test message 3"])
        ]
        
        for call in message_calls:
            args = call[0]
            assert args[0] >= 2  # x position (with padding)
            assert args[0] < engine.screen_width - 2  # within frame
            assert args[1] >= engine.screen_height - 5  # near bottom of screen

    def test_render_game_with_locations(self, engine: Engine, mock_console: MagicMock) -> None:
        """Test game rendering with discovered and undiscovered locations."""
        engine.console = mock_console
        
        # Create test locations
        discovered_location = Location(
            x=10, y=10,
            type=LocationType.VILLAGE,
            name="Test Village",
            description="A test village"
        )
        discovered_location.discovered = True

        undiscovered_location = Location(
            x=20, y=20,
            type=LocationType.RUINS,
            name="Hidden Ruins",
            description="Hidden ruins"
        )

        engine.locations.locations = [discovered_location, undiscovered_location]

        # Test rendering
        engine._render_game()

        # Get all print calls
        print_calls = mock_console.print.call_args_list

        # Check that discovered location was rendered with highlight color
        village_symbol = engine._get_location_symbol(LocationType.VILLAGE)
        discovered_calls = [
            call for call in print_calls 
            if call[0][:2] == (10, 10) and village_symbol in str(call)
        ]
        assert len(discovered_calls) > 0

        # Check that undiscovered location was not rendered with highlight color
        ruins_symbol = engine._get_location_symbol(LocationType.RUINS)
        highlight_color_str = str(COLORS["highlight"])
        undiscovered_highlight_calls = [
            call for call in print_calls 
            if call[0][:2] == (20, 20) and ruins_symbol in str(call) and highlight_color_str in str(call)
        ]
        assert len(undiscovered_highlight_calls) == 0

    @pytest.mark.integration
    def test_game_loop_integration(self, initialized_engine: Engine) -> None:
        """Integration test for the main game loop."""
        # Simulate a sequence of game actions
        actions = [
            # Movement
            tcod.event.KeyDown(
                scancode=tcod.event.Scancode.RIGHT,
                sym=tcod.event.KeySym.RIGHT,
                mod=tcod.event.Modifier.NONE,
            ),
            # Interaction
            tcod.event.KeyDown(
                scancode=tcod.event.Scancode.SPACE,
                sym=tcod.event.KeySym.SPACE,
                mod=tcod.event.Modifier.NONE,
            ),
            # Open inventory
            tcod.event.KeyDown(
                scancode=tcod.event.Scancode.I,
                sym=tcod.event.KeySym.i,
                mod=tcod.event.Modifier.NONE,
            ),
            # Close inventory
            tcod.event.KeyDown(
                scancode=tcod.event.Scancode.I,
                sym=tcod.event.KeySym.i,
                mod=tcod.event.Modifier.NONE,
            ),
        ]

        initial_position = (initialized_engine.player.x, initialized_engine.player.y)
        initial_time = initialized_engine.time.minutes

        # Process each action
        for action in actions:
            with patch("tcod.event.get", return_value=[action]):
                initialized_engine.update()

        # Verify game state changes
        final_position = (initialized_engine.player.x, initialized_engine.player.y)
        assert final_position != initial_position  # Player moved
        assert initialized_engine.time.minutes > initial_time  # Time advanced
        assert not initialized_engine.show_inventory  # Inventory closed

    @pytest.mark.integration
    def test_game_loop_with_discoveries(self, initialized_engine: Engine) -> None:
        """Integration test for discoveries during gameplay."""
        # Create a test location near the player
        test_location = Location(
            x=initialized_engine.player.x + 1,
            y=initialized_engine.player.y,
            type=LocationType.BEACH,
            name="Test Beach",
            description="A beautiful test beach",
        )
        initialized_engine.locations.locations = [test_location]

        # Move towards the location
        move_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.RIGHT,
            sym=tcod.event.KeySym.RIGHT,
            mod=tcod.event.Modifier.NONE,
        )

        # Simulate movement and interaction
        with patch("tcod.event.get", return_value=[move_event]):
            initialized_engine.update()

        interact_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.SPACE,
            sym=tcod.event.KeySym.SPACE,
            mod=tcod.event.Modifier.NONE,
        )

        with patch("tcod.event.get", return_value=[interact_event]):
            initialized_engine.update()

        # Verify discovery and interaction
        discovery_messages = [
            m for m in initialized_engine.message_log.messages 
            if m.category == MessageCategory.DISCOVERY
        ]
        interaction_messages = [
            m for m in initialized_engine.message_log.messages 
            if m.category == MessageCategory.INTERACTION
        ]

        assert len(discovery_messages) >= 1
        assert len(interaction_messages) >= 1
        assert test_location.discovered
        assert len(initialized_engine.player.inventory.items) > 0  # Should have found an item
