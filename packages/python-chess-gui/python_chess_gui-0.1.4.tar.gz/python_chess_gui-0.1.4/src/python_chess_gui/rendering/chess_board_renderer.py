"""Chess board and piece rendering."""

import math

import chess
import pygame

from python_chess_gui.constants import (
    CHECK_HIGHLIGHT_COLOR_RGB,
    DARK_SQUARE_COLOR_RGB,
    FILE_LABELS,
    HINT_MOVE_HIGHLIGHT_RGBA,
    LAST_MOVE_HIGHLIGHT_RGBA,
    LEGAL_MOVE_INDICATOR_COLOR_RGB,
    LIGHT_SQUARE_COLOR_RGB,
    PIECE_UNICODE,
    RANK_LABELS,
    SELECTED_SQUARE_HIGHLIGHT_RGBA,
)
from python_chess_gui.layout_manager import LayoutManager


class ChessBoardRenderer:
    """Renders the chess board, pieces, and visual highlights."""

    def __init__(self, screen: pygame.Surface, layout: LayoutManager):
        """Initialize the renderer.

        Args:
            screen: Pygame surface to render on
            layout: Layout manager for dynamic sizing
        """
        self.screen = screen
        self.layout = layout
        self._create_fonts()

    def _create_fonts(self) -> None:
        """Create fonts based on current layout dimensions."""
        self.piece_font = pygame.font.SysFont(
            "Apple Symbols, Segoe UI Symbol, DejaVu Sans",
            self.layout.font_size_piece
        )
        self.coord_font = pygame.font.SysFont(
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

    def render(
        self,
        board: chess.Board,
        player_is_white: bool,
        selected_square: chess.Square | None = None,
        legal_moves: list[chess.Move] | None = None,
        last_move: chess.Move | None = None,
        hint_move: chess.Move | None = None,
    ) -> None:
        """Render the complete chess board with all highlights.

        Args:
            board: Current chess board state
            player_is_white: True if player is white (white at bottom)
            selected_square: Currently selected square, if any
            legal_moves: List of legal moves from selected square
            last_move: The last move made, for highlighting
            hint_move: Suggested move from Stockfish (for hint feature)
        """
        self._draw_squares(player_is_white)
        self._draw_last_move_highlight(last_move, player_is_white)
        self._draw_hint_highlight(hint_move, player_is_white)
        self._draw_check_highlight(board, player_is_white)
        self._draw_selected_highlight(selected_square, player_is_white)
        self._draw_legal_move_indicators(legal_moves, player_is_white, board)
        self._draw_pieces(board, player_is_white)
        self._draw_coordinates(player_is_white)

    def _convert_square_to_screen(self, square: chess.Square, player_is_white: bool) -> tuple[int, int]:
        """Convert a chess square to screen coordinates.

        Args:
            square: Chess square index (0-63)
            player_is_white: True if player is playing white

        Returns:
            Tuple of (x, y) screen coordinates
        """
        file = chess.square_file(square)
        rank = chess.square_rank(square)

        if player_is_white:
            screen_col = file
            screen_row = 7 - rank
        else:
            screen_col = 7 - file
            screen_row = rank

        x = self.layout.board_offset_x + screen_col * self.layout.square_size
        y = self.layout.board_offset_y + screen_row * self.layout.square_size

        return (x, y)

    def _draw_squares(self, player_is_white: bool) -> None:
        """Draw the 8x8 chess board squares."""
        for row in range(8):
            for col in range(8):
                x = self.layout.board_offset_x + col * self.layout.square_size
                y = self.layout.board_offset_y + row * self.layout.square_size

                is_light = (row + col) % 2 == 0
                color = LIGHT_SQUARE_COLOR_RGB if is_light else DARK_SQUARE_COLOR_RGB

                pygame.draw.rect(
                    self.screen, color,
                    (x, y, self.layout.square_size, self.layout.square_size)
                )

    def _draw_selected_highlight(
        self, selected_square: chess.Square | None, player_is_white: bool
    ) -> None:
        """Draw highlight on the selected square."""
        if selected_square is None:
            return

        x, y = self._convert_square_to_screen(selected_square, player_is_white)

        highlight = pygame.Surface(
            (self.layout.square_size, self.layout.square_size),
            pygame.SRCALPHA
        )
        highlight.fill(SELECTED_SQUARE_HIGHLIGHT_RGBA)
        self.screen.blit(highlight, (x, y))

    def _draw_legal_move_indicators(
        self,
        legal_moves: list[chess.Move] | None,
        player_is_white: bool,
        board: chess.Board,
    ) -> None:
        """Draw indicators for legal move destinations."""
        if legal_moves is None:
            return

        for move in legal_moves:
            target_square = move.to_square
            x, y = self._convert_square_to_screen(target_square, player_is_white)

            center_x = x + self.layout.square_size // 2
            center_y = y + self.layout.square_size // 2

            if board.piece_at(target_square) is not None:
                # Draw ring for captures
                pygame.draw.circle(
                    self.screen,
                    LEGAL_MOVE_INDICATOR_COLOR_RGB,
                    (center_x, center_y),
                    self.layout.square_size // 2 - 4,
                    4,
                )
            else:
                # Draw small dot for empty squares
                pygame.draw.circle(
                    self.screen,
                    LEGAL_MOVE_INDICATOR_COLOR_RGB,
                    (center_x, center_y),
                    self.layout.square_size // 6,
                )

    def _draw_last_move_highlight(
        self, last_move: chess.Move | None, player_is_white: bool
    ) -> None:
        """Highlight the squares involved in the last move."""
        if last_move is None:
            return

        for square in [last_move.from_square, last_move.to_square]:
            x, y = self._convert_square_to_screen(square, player_is_white)

            highlight = pygame.Surface(
                (self.layout.square_size, self.layout.square_size),
                pygame.SRCALPHA
            )
            highlight.fill(LAST_MOVE_HIGHLIGHT_RGBA)
            self.screen.blit(highlight, (x, y))

    def _draw_hint_highlight(
        self, hint_move: chess.Move | None, player_is_white: bool
    ) -> None:
        """Highlight the suggested hint move with an arrow."""
        if hint_move is None:
            return

        # Highlight both from and to squares
        for square in [hint_move.from_square, hint_move.to_square]:
            x, y = self._convert_square_to_screen(square, player_is_white)

            highlight = pygame.Surface(
                (self.layout.square_size, self.layout.square_size),
                pygame.SRCALPHA
            )
            highlight.fill(HINT_MOVE_HIGHLIGHT_RGBA)
            self.screen.blit(highlight, (x, y))

        # Draw an arrow from source to destination
        from_x, from_y = self._convert_square_to_screen(hint_move.from_square, player_is_white)
        to_x, to_y = self._convert_square_to_screen(hint_move.to_square, player_is_white)

        # Calculate centers
        from_center = (from_x + self.layout.square_size // 2, from_y + self.layout.square_size // 2)
        to_center = (to_x + self.layout.square_size // 2, to_y + self.layout.square_size // 2)

        # Draw arrow line
        arrow_color = (72, 150, 220)
        pygame.draw.line(
            self.screen,
            arrow_color,
            from_center,
            to_center,
            4,
        )

        # Draw arrowhead
        angle = math.atan2(to_center[1] - from_center[1], to_center[0] - from_center[0])
        arrow_size = 15
        arrow_angle = math.pi / 6  # 30 degrees

        point1 = (
            to_center[0] - arrow_size * math.cos(angle - arrow_angle),
            to_center[1] - arrow_size * math.sin(angle - arrow_angle),
        )
        point2 = (
            to_center[0] - arrow_size * math.cos(angle + arrow_angle),
            to_center[1] - arrow_size * math.sin(angle + arrow_angle),
        )

        pygame.draw.polygon(
            self.screen,
            arrow_color,
            [to_center, point1, point2],
        )

    def _draw_check_highlight(
        self, board: chess.Board, player_is_white: bool
    ) -> None:
        """Highlight the king if in check."""
        if not board.is_check():
            return

        king_square = board.king(board.turn)
        if king_square is None:
            return

        x, y = self._convert_square_to_screen(king_square, player_is_white)

        # Draw radial gradient effect for check
        for radius in range(self.layout.square_size // 2, 0, -2):
            alpha = int(180 * (1 - radius / (self.layout.square_size // 2)))
            color = (*CHECK_HIGHLIGHT_COLOR_RGB[:3], alpha)
            surface = pygame.Surface(
                (self.layout.square_size, self.layout.square_size),
                pygame.SRCALPHA
            )
            pygame.draw.circle(
                surface, color,
                (self.layout.square_size // 2, self.layout.square_size // 2),
                radius
            )
            self.screen.blit(surface, (x, y))

    def _draw_pieces(self, board: chess.Board, player_is_white: bool) -> None:
        """Draw all pieces on the board."""
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                continue

            x, y = self._convert_square_to_screen(square, player_is_white)

            symbol = piece.symbol()
            unicode_char = PIECE_UNICODE.get(symbol, '?')

            piece_surface = self.piece_font.render(unicode_char, True, (0, 0, 0))
            piece_rect = piece_surface.get_rect(
                center=(x + self.layout.square_size // 2, y + self.layout.square_size // 2)
            )
            self.screen.blit(piece_surface, piece_rect)

    def _draw_coordinates(self, player_is_white: bool) -> None:
        """Draw file and rank labels on the board edges."""
        coord_color_light = DARK_SQUARE_COLOR_RGB
        coord_color_dark = LIGHT_SQUARE_COLOR_RGB

        # Draw file labels (a-h) at bottom of board
        for col in range(8):
            if player_is_white:
                file_label = FILE_LABELS[col]
            else:
                file_label = FILE_LABELS[7 - col]

            x = self.layout.board_offset_x + col * self.layout.square_size + self.layout.square_size - 10
            y = self.layout.board_offset_y + self.layout.board_size - 14

            is_light_square = (7 + col) % 2 == 0
            color = coord_color_light if is_light_square else coord_color_dark

            label = self.coord_font.render(file_label, True, color)
            self.screen.blit(label, (x, y))

        # Draw rank labels (1-8) on left of board
        for row in range(8):
            if player_is_white:
                rank_label = RANK_LABELS[7 - row]
            else:
                rank_label = RANK_LABELS[row]

            x = self.layout.board_offset_x + 3
            y = self.layout.board_offset_y + row * self.layout.square_size + 3

            is_light_square = (row) % 2 == 0
            color = coord_color_light if is_light_square else coord_color_dark

            label = self.coord_font.render(rank_label, True, color)
            self.screen.blit(label, (x, y))
