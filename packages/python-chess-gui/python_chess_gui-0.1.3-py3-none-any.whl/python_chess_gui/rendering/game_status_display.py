"""Game status text rendering."""

import pygame

from python_chess_gui.constants import (
    TEXT_COLOR_RGB,
    WINDOW_BACKGROUND_COLOR_RGB,
)
from python_chess_gui.layout_manager import LayoutManager


class GameStatusDisplay:
    """Renders game status text and control hints."""

    def __init__(self, screen: pygame.Surface, layout: LayoutManager):
        """Initialize the status display.

        Args:
            screen: Pygame surface to render on
            layout: Layout manager for dynamic sizing
        """
        self.screen = screen
        self.layout = layout
        self._create_fonts()

    def _create_fonts(self) -> None:
        """Create fonts based on current layout dimensions."""
        self.status_font = pygame.font.SysFont(
            "Arial, Helvetica",
            self.layout.font_size_status
        )
        self.button_font = pygame.font.SysFont(
            "Arial, Helvetica",
            self.layout.font_size_button
        )

    def update_layout(self, layout: LayoutManager) -> None:
        """Update the layout manager and recreate fonts.

        Args:
            layout: New layout manager instance
        """
        self.layout = layout
        self._create_fonts()

    def render(
        self,
        turn_text: str,
        eval_text: str,
        difficulty_name: str,
    ) -> None:
        """Render all status elements.

        Args:
            turn_text: Text showing whose turn it is
            eval_text: Text showing position evaluation
            difficulty_name: Current difficulty setting name
        """
        self._draw_status_bar(turn_text, eval_text)
        self._draw_control_bar(difficulty_name)

    def _draw_status_bar(self, turn_text: str, eval_text: str) -> None:
        """Draw the top status bar."""
        # Clear the status bar area
        pygame.draw.rect(
            self.screen,
            WINDOW_BACKGROUND_COLOR_RGB,
            (0, 0, self.layout.window_width, self.layout.board_offset_y),
        )

        # Draw turn text on left
        turn_surface = self.status_font.render(turn_text, True, TEXT_COLOR_RGB)
        self.screen.blit(turn_surface, (15, 15))

        # Draw evaluation on right
        eval_surface = self.status_font.render(eval_text, True, TEXT_COLOR_RGB)
        eval_rect = eval_surface.get_rect(right=self.layout.window_width - 15, top=15)
        self.screen.blit(eval_surface, eval_rect)

    def _draw_control_bar(self, difficulty_name: str) -> None:
        """Draw the bottom control bar with hints."""
        control_bar_y = self.layout.window_height - self.layout.control_bar_height
        pygame.draw.rect(
            self.screen,
            WINDOW_BACKGROUND_COLOR_RGB,
            (0, control_bar_y, self.layout.window_width, self.layout.control_bar_height),
        )

        hints = [
            "[Z] Undo",
            "[H] Hint*",
            "[N] New Game",
            f"{difficulty_name}",
        ]

        x_offset = 15
        for hint in hints:
            hint_surface = self.button_font.render(hint, True, TEXT_COLOR_RGB)
            self.screen.blit(hint_surface, (x_offset, control_bar_y + 8))
            x_offset += hint_surface.get_width() + 30

        # Draw disclaimer about hints and eval being at chosen level
        disclaimer_color = (150, 150, 150)
        disclaimer = f"* Hints & Eval are computed at {difficulty_name} strength"
        disclaimer_surface = self.button_font.render(disclaimer, True, disclaimer_color)
        self.screen.blit(disclaimer_surface, (15, control_bar_y + 30))
