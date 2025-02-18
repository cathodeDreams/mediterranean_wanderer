"""Main entry point for the Mediterranean Wanderer game."""

import sys
from island_rl.engine import Engine


def main() -> None:
    """Initialize and run the game."""
    screen_width = 80
    screen_height = 50

    engine = Engine(screen_width, screen_height)

    try:
        engine.run()
    except KeyboardInterrupt:
        print("\nGame terminated by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
