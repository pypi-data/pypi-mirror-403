"""User input handling for mouse clicks and keyboard events."""

from dataclasses import dataclass
from enum import Enum, auto

import chess
import pygame

from python_chess_gui.core.coordinate_converter import convert_screen_position_to_board_square
from python_chess_gui.layout_manager import LayoutManager


class InputAction(Enum):
    """Types of user input actions."""

    NONE = auto()
    SELECT_SQUARE = auto()
    UNDO = auto()
    NEW_GAME = auto()
    HINT = auto()
    QUIT = auto()


@dataclass
class InputResult:
    """Result of processing user input."""

    action: InputAction
    square: chess.Square | None = None


class UserInputHandler:
    """Handles mouse clicks and keyboard input."""

    def __init__(self, layout: LayoutManager, player_is_white: bool = True):
        """Initialize the input handler.

        Args:
            layout: Layout manager for coordinate conversion
            player_is_white: True if player is white (affects coordinate conversion)
        """
        self.layout = layout
        self.player_is_white = player_is_white

    def update_layout(self, layout: LayoutManager) -> None:
        """Update the layout manager.

        Args:
            layout: New layout manager instance
        """
        self.layout = layout

    def set_player_color(self, player_is_white: bool) -> None:
        """Update the player's color for coordinate conversion.

        Args:
            player_is_white: True if player is playing white
        """
        self.player_is_white = player_is_white

    def process_event(self, event: pygame.event.Event) -> InputResult:
        """Process a pygame event and return the action.

        Args:
            event: Pygame event to process

        Returns:
            InputResult describing the action to take
        """
        if event.type == pygame.QUIT:
            return InputResult(InputAction.QUIT)

        if event.type == pygame.KEYDOWN:
            return self._handle_key(event.key)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                return self._handle_click(event.pos)

        return InputResult(InputAction.NONE)

    def _handle_key(self, key: int) -> InputResult:
        """Handle keyboard input.

        Args:
            key: Pygame key constant

        Returns:
            InputResult for the key action
        """
        if key == pygame.K_z:
            return InputResult(InputAction.UNDO)
        elif key == pygame.K_n:
            return InputResult(InputAction.NEW_GAME)
        elif key == pygame.K_h:
            return InputResult(InputAction.HINT)
        elif key in (pygame.K_ESCAPE, pygame.K_q):
            return InputResult(InputAction.QUIT)

        return InputResult(InputAction.NONE)

    def _handle_click(self, pos: tuple[int, int]) -> InputResult:
        """Handle mouse click.

        Args:
            pos: (x, y) position of the click

        Returns:
            InputResult with the clicked square, if on board
        """
        square = convert_screen_position_to_board_square(
            pos[0], pos[1], self.player_is_white, self.layout
        )

        if square is not None:
            return InputResult(InputAction.SELECT_SQUARE, square)

        return InputResult(InputAction.NONE)
