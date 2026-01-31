"""Evaluation bar visualization."""

import pygame

from python_chess_gui.constants import (
    BOARD_OFFSET_Y,
    BOARD_SIZE,
    COLOR_EVAL_BLACK,
    COLOR_EVAL_WHITE,
    COLOR_TEXT,
    EVAL_BAR_WIDTH,
    EVAL_MAX_CENTIPAWNS,
    FONT_NAME,
    FONT_SIZE_COORD,
    SIDEBAR_WIDTH,
)


class EvaluationBarRenderer:
    """Renders the position evaluation bar."""

    def __init__(self, screen: pygame.Surface):
        """Initialize the evaluation bar renderer.

        Args:
            screen: Pygame surface to render on
        """
        self.screen = screen
        self.font = pygame.font.SysFont("Arial, Helvetica", FONT_SIZE_COORD)

        # Bar position (right side of board)
        self.bar_x = BOARD_SIZE + (SIDEBAR_WIDTH - EVAL_BAR_WIDTH) // 2
        self.bar_y = BOARD_OFFSET_Y
        self.bar_height = BOARD_SIZE

    def render(self, evaluation: float | None, player_is_white: bool) -> None:
        """Render the evaluation bar.

        Args:
            evaluation: Position evaluation in pawns (positive = white advantage)
            player_is_white: True if player is white (affects bar orientation)
        """
        # Draw background (black side)
        pygame.draw.rect(
            self.screen,
            COLOR_EVAL_BLACK,
            (self.bar_x, self.bar_y, EVAL_BAR_WIDTH, self.bar_height),
        )

        if evaluation is None:
            # No evaluation available - draw half-half
            white_height = self.bar_height // 2
        else:
            # Convert evaluation to bar proportion
            # Clamp to +/- max pawns
            max_pawns = EVAL_MAX_CENTIPAWNS / 100.0
            clamped_eval = max(-max_pawns, min(max_pawns, evaluation))

            # Convert to 0-1 range (0 = black winning, 1 = white winning)
            proportion = (clamped_eval + max_pawns) / (2 * max_pawns)

            white_height = int(self.bar_height * proportion)

        # Draw white portion
        # If player is white, white advantage is at top (bar fills from bottom)
        # If player is black, board is flipped, so white advantage at bottom
        if player_is_white:
            # White at bottom of board, so white advantage = bar grows from bottom
            white_y = self.bar_y + self.bar_height - white_height
        else:
            # Black at bottom of board, so white advantage = bar grows from top
            white_y = self.bar_y

        pygame.draw.rect(
            self.screen,
            COLOR_EVAL_WHITE,
            (self.bar_x, white_y, EVAL_BAR_WIDTH, white_height),
        )

        # Draw border
        pygame.draw.rect(
            self.screen,
            COLOR_TEXT,
            (self.bar_x, self.bar_y, EVAL_BAR_WIDTH, self.bar_height),
            1,
        )

        # Draw evaluation text
        self._draw_eval_text(evaluation)

    def _draw_eval_text(self, evaluation: float | None) -> None:
        """Draw the evaluation number below the bar.

        Args:
            evaluation: Position evaluation in pawns
        """
        if evaluation is None:
            text = "N/A"
        elif abs(evaluation) >= 100:
            # Mate score
            if evaluation > 0:
                text = "M+"
            else:
                text = "M-"
        else:
            # Format with sign
            if evaluation >= 0:
                text = f"+{evaluation:.1f}"
            else:
                text = f"{evaluation:.1f}"

        text_surface = self.font.render(text, True, COLOR_TEXT)
        text_rect = text_surface.get_rect(
            centerx=self.bar_x + EVAL_BAR_WIDTH // 2,
            top=self.bar_y + self.bar_height + 5,
        )
        self.screen.blit(text_surface, text_rect)
