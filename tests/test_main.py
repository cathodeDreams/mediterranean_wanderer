"""Tests for the main module."""

import pytest
from unittest.mock import patch, MagicMock
from island_rl.__main__ import main


def test_main_normal_exit() -> None:
    """Test main function with normal exit."""
    mock_engine = MagicMock()

    with patch(
        "island_rl.__main__.Engine", return_value=mock_engine
    ) as mock_engine_class:
        with patch("sys.exit") as mock_exit:
            # Simulate normal exit
            mock_engine.run.side_effect = SystemExit()

            # SystemExit should be raised and not caught
            with pytest.raises(SystemExit):
                main()

            # Verify engine was created with correct dimensions
            mock_engine_class.assert_called_once_with(80, 50)
            # Verify run was called
            mock_engine.run.assert_called_once()
            # Verify sys.exit wasn't called (SystemExit was raised directly)
            mock_exit.assert_not_called()


def test_main_keyboard_interrupt() -> None:
    """Test main function with keyboard interrupt."""
    mock_engine = MagicMock()

    with patch(
        "island_rl.__main__.Engine", return_value=mock_engine
    ) as mock_engine_class:
        with patch("sys.exit") as mock_exit:
            with patch("builtins.print") as mock_print:
                # Simulate keyboard interrupt
                mock_engine.run.side_effect = KeyboardInterrupt()
                main()

                # Verify engine was created with correct dimensions
                mock_engine_class.assert_called_once_with(80, 50)
                # Verify run was called
                mock_engine.run.assert_called_once()
                # Verify exit message was printed
                mock_print.assert_called_once_with("\nGame terminated by user.")
                # Verify sys.exit was called with 0
                mock_exit.assert_called_once_with(0)
