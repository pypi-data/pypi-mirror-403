"""Evaluation bar visualization."""

import pygame

from python_chess_gui.constants import (
    EVAL_BAR_BLACK_COLOR_RGB,
    EVAL_BAR_WHITE_COLOR_RGB,
    EVALUATION_MAX_CENTIPAWNS,
    TEXT_COLOR_RGB,
)
from python_chess_gui.layout_manager import LayoutManager


class EvaluationBarRenderer:
    """Renders the position evaluation bar."""

    def __init__(self, screen: pygame.Surface, layout: LayoutManager):
        """Initialize the evaluation bar renderer.

        Args:
            screen: Pygame surface to render on
            layout: Layout manager for dynamic sizing
        """
        self.screen = screen
        self.layout = layout
        self._create_fonts()

    def _create_fonts(self) -> None:
        """Create fonts based on current layout dimensions."""
        self.font = pygame.font.SysFont(
            "Arial, Helvetica",
            self.layout.font_size_coordinates
        )

    def update_layout(self, layout: LayoutManager) -> None:
        """Update the layout manager and recreate fonts.

        Args:
            layout: New layout manager instance
        """
        self.layout = layout
        self._create_fonts()

    def render(self, evaluation: float | None, player_is_white: bool) -> None:
        """Render the evaluation bar.

        Args:
            evaluation: Position evaluation in pawns (positive = white advantage)
            player_is_white: True if player is white (affects bar orientation)
        """
        bar_x = self.layout.evaluation_bar_x
        bar_y = self.layout.evaluation_bar_y
        bar_width = self.layout.evaluation_bar_width
        bar_height = self.layout.evaluation_bar_height

        # Draw background (black side)
        pygame.draw.rect(
            self.screen,
            EVAL_BAR_BLACK_COLOR_RGB,
            (bar_x, bar_y, bar_width, bar_height),
        )

        if evaluation is None:
            white_height = bar_height // 2
        else:
            max_pawns = EVALUATION_MAX_CENTIPAWNS / 100.0
            clamped_eval = max(-max_pawns, min(max_pawns, evaluation))
            proportion = (clamped_eval + max_pawns) / (2 * max_pawns)
            white_height = int(bar_height * proportion)

        # Draw white portion
        if player_is_white:
            white_y = bar_y + bar_height - white_height
        else:
            white_y = bar_y

        pygame.draw.rect(
            self.screen,
            EVAL_BAR_WHITE_COLOR_RGB,
            (bar_x, white_y, bar_width, white_height),
        )

        # Draw border
        pygame.draw.rect(
            self.screen,
            TEXT_COLOR_RGB,
            (bar_x, bar_y, bar_width, bar_height),
            1,
        )

        # Draw evaluation text
        self._draw_eval_text(evaluation, bar_x, bar_y, bar_width, bar_height)

    def _draw_eval_text(self, evaluation: float | None, bar_x: int, bar_y: int,
                        bar_width: int, bar_height: int) -> None:
        """Draw the evaluation number below the bar.

        Args:
            evaluation: Position evaluation in pawns
            bar_x: X position of the bar
            bar_y: Y position of the bar
            bar_width: Width of the bar
            bar_height: Height of the bar
        """
        if evaluation is None:
            text = "N/A"
        elif abs(evaluation) >= 100:
            if evaluation > 0:
                text = "M+"
            else:
                text = "M-"
        else:
            if evaluation >= 0:
                text = f"+{evaluation:.1f}"
            else:
                text = f"{evaluation:.1f}"

        text_surface = self.font.render(text, True, TEXT_COLOR_RGB)
        text_rect = text_surface.get_rect(
            centerx=bar_x + bar_width // 2,
            top=bar_y + bar_height + 5,
        )
        self.screen.blit(text_surface, text_rect)
