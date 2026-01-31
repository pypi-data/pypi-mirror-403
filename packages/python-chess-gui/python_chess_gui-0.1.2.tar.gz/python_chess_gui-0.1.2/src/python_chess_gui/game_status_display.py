"""Game status text rendering."""

import pygame

from python_chess_gui.constants import (
    BOARD_OFFSET_Y,
    COLOR_BACKGROUND,
    COLOR_TEXT,
    CONTROL_BAR_HEIGHT,
    FONT_NAME,
    FONT_SIZE_BUTTON,
    FONT_SIZE_STATUS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


class GameStatusDisplay:
    """Renders game status text and control hints."""

    def __init__(self, screen: pygame.Surface):
        """Initialize the status display.

        Args:
            screen: Pygame surface to render on
        """
        self.screen = screen
        self.status_font = pygame.font.SysFont("Arial, Helvetica", FONT_SIZE_STATUS)
        self.button_font = pygame.font.SysFont("Arial, Helvetica", FONT_SIZE_BUTTON)

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
            COLOR_BACKGROUND,
            (0, 0, WINDOW_WIDTH, BOARD_OFFSET_Y),
        )

        # Draw turn text on left
        turn_surface = self.status_font.render(turn_text, True, COLOR_TEXT)
        self.screen.blit(turn_surface, (15, 15))

        # Draw evaluation on right
        eval_surface = self.status_font.render(eval_text, True, COLOR_TEXT)
        eval_rect = eval_surface.get_rect(right=WINDOW_WIDTH - 15, top=15)
        self.screen.blit(eval_surface, eval_rect)

    def _draw_control_bar(self, difficulty_name: str) -> None:
        """Draw the bottom control bar with hints."""
        # Clear the control bar area
        control_bar_y = WINDOW_HEIGHT - CONTROL_BAR_HEIGHT
        pygame.draw.rect(
            self.screen,
            COLOR_BACKGROUND,
            (0, control_bar_y, WINDOW_WIDTH, CONTROL_BAR_HEIGHT),
        )

        # Draw control hints
        hints = [
            "[Z] Undo",
            "[H] Hint*",
            "[N] New Game",
            f"{difficulty_name}",
        ]

        x_offset = 15
        for hint in hints:
            hint_surface = self.button_font.render(hint, True, COLOR_TEXT)
            self.screen.blit(hint_surface, (x_offset, control_bar_y + 8))
            x_offset += hint_surface.get_width() + 30

        # Draw disclaimer about hints and eval being at chosen level
        disclaimer_color = (150, 150, 150)  # Gray
        disclaimer = f"* Hints & Eval are computed at {difficulty_name} strength"
        disclaimer_surface = self.button_font.render(disclaimer, True, disclaimer_color)
        self.screen.blit(disclaimer_surface, (15, control_bar_y + 30))
