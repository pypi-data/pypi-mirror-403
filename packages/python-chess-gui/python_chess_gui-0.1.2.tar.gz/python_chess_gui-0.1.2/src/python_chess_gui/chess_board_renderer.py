"""Chess board and piece rendering."""

import chess
import pygame

from python_chess_gui.constants import (
    BOARD_OFFSET_X,
    BOARD_OFFSET_Y,
    BOARD_SIZE,
    COLOR_CHECK,
    COLOR_DARK_SQUARE,
    COLOR_HINT,
    COLOR_LAST_MOVE,
    COLOR_LEGAL_MOVE,
    COLOR_LIGHT_SQUARE,
    COLOR_SELECTED,
    FILE_LABELS,
    FONT_NAME,
    FONT_SIZE_COORD,
    FONT_SIZE_PIECE,
    PIECE_UNICODE,
    RANK_LABELS,
    SQUARE_SIZE,
)
from python_chess_gui.coordinate_converter import convert_board_square_to_screen_position


class ChessBoardRenderer:
    """Renders the chess board, pieces, and visual highlights."""

    def __init__(self, screen: pygame.Surface):
        """Initialize the renderer.

        Args:
            screen: Pygame surface to render on
        """
        self.screen = screen
        # Use a system font that supports Unicode chess symbols
        self.piece_font = pygame.font.SysFont("Apple Symbols, Segoe UI Symbol, DejaVu Sans", FONT_SIZE_PIECE)
        self.coord_font = pygame.font.SysFont("Arial, Helvetica", FONT_SIZE_COORD)

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

    def _draw_squares(self, player_is_white: bool) -> None:
        """Draw the 8x8 chess board squares."""
        for row in range(8):
            for col in range(8):
                x = BOARD_OFFSET_X + col * SQUARE_SIZE
                y = BOARD_OFFSET_Y + row * SQUARE_SIZE

                # Determine square color based on position
                # (row + col) even = light, odd = dark
                is_light = (row + col) % 2 == 0
                color = COLOR_LIGHT_SQUARE if is_light else COLOR_DARK_SQUARE

                pygame.draw.rect(
                    self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE)
                )

    def _draw_selected_highlight(
        self, selected_square: chess.Square | None, player_is_white: bool
    ) -> None:
        """Draw highlight on the selected square."""
        if selected_square is None:
            return

        x, y = convert_board_square_to_screen_position(selected_square, player_is_white)

        # Create semi-transparent surface for highlight
        highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        highlight.fill(COLOR_SELECTED)
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
            x, y = convert_board_square_to_screen_position(target_square, player_is_white)

            center_x = x + SQUARE_SIZE // 2
            center_y = y + SQUARE_SIZE // 2

            # Check if target square has a piece (capture)
            if board.piece_at(target_square) is not None:
                # Draw ring for captures
                pygame.draw.circle(
                    self.screen,
                    COLOR_LEGAL_MOVE,
                    (center_x, center_y),
                    SQUARE_SIZE // 2 - 4,
                    4,
                )
            else:
                # Draw small dot for empty squares
                pygame.draw.circle(
                    self.screen,
                    COLOR_LEGAL_MOVE,
                    (center_x, center_y),
                    SQUARE_SIZE // 6,
                )

    def _draw_last_move_highlight(
        self, last_move: chess.Move | None, player_is_white: bool
    ) -> None:
        """Highlight the squares involved in the last move."""
        if last_move is None:
            return

        for square in [last_move.from_square, last_move.to_square]:
            x, y = convert_board_square_to_screen_position(square, player_is_white)

            highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight.fill(COLOR_LAST_MOVE)
            self.screen.blit(highlight, (x, y))

    def _draw_hint_highlight(
        self, hint_move: chess.Move | None, player_is_white: bool
    ) -> None:
        """Highlight the suggested hint move with an arrow."""
        if hint_move is None:
            return

        # Highlight both from and to squares
        for square in [hint_move.from_square, hint_move.to_square]:
            x, y = convert_board_square_to_screen_position(square, player_is_white)

            highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight.fill(COLOR_HINT)
            self.screen.blit(highlight, (x, y))

        # Draw an arrow from source to destination
        from_x, from_y = convert_board_square_to_screen_position(hint_move.from_square, player_is_white)
        to_x, to_y = convert_board_square_to_screen_position(hint_move.to_square, player_is_white)

        # Calculate centers
        from_center = (from_x + SQUARE_SIZE // 2, from_y + SQUARE_SIZE // 2)
        to_center = (to_x + SQUARE_SIZE // 2, to_y + SQUARE_SIZE // 2)

        # Draw arrow line
        pygame.draw.line(
            self.screen,
            (72, 150, 220),  # Blue color for arrow
            from_center,
            to_center,
            4,
        )

        # Draw arrowhead
        import math
        angle = math.atan2(to_center[1] - from_center[1], to_center[0] - from_center[0])
        arrow_size = 15
        arrow_angle = math.pi / 6  # 30 degrees

        # Calculate arrowhead points
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
            (72, 150, 220),
            [to_center, point1, point2],
        )

    def _draw_check_highlight(
        self, board: chess.Board, player_is_white: bool
    ) -> None:
        """Highlight the king if in check."""
        if not board.is_check():
            return

        # Find the king of the side to move (they're in check)
        king_square = board.king(board.turn)
        if king_square is None:
            return

        x, y = convert_board_square_to_screen_position(king_square, player_is_white)

        # Draw radial gradient effect for check
        center_x = x + SQUARE_SIZE // 2
        center_y = y + SQUARE_SIZE // 2

        # Draw concentric circles for gradient effect
        for radius in range(SQUARE_SIZE // 2, 0, -2):
            alpha = int(180 * (1 - radius / (SQUARE_SIZE // 2)))
            color = (*COLOR_CHECK[:3], alpha)
            surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(
                surface, color, (SQUARE_SIZE // 2, SQUARE_SIZE // 2), radius
            )
            self.screen.blit(surface, (x, y))

    def _draw_pieces(self, board: chess.Board, player_is_white: bool) -> None:
        """Draw all pieces on the board."""
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                continue

            x, y = convert_board_square_to_screen_position(square, player_is_white)

            # Get Unicode symbol for the piece
            symbol = piece.symbol()
            unicode_char = PIECE_UNICODE.get(symbol, '?')

            # Render the piece
            piece_surface = self.piece_font.render(unicode_char, True, (0, 0, 0))
            piece_rect = piece_surface.get_rect(
                center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2)
            )
            self.screen.blit(piece_surface, piece_rect)

    def _draw_coordinates(self, player_is_white: bool) -> None:
        """Draw file and rank labels on the board edges."""
        coord_color_light = COLOR_DARK_SQUARE
        coord_color_dark = COLOR_LIGHT_SQUARE

        # Draw file labels (a-h) at bottom of board
        for col in range(8):
            if player_is_white:
                file_label = FILE_LABELS[col]
            else:
                file_label = FILE_LABELS[7 - col]

            x = BOARD_OFFSET_X + col * SQUARE_SIZE + SQUARE_SIZE - 10
            y = BOARD_OFFSET_Y + BOARD_SIZE - 14

            # Use contrasting color based on square
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

            x = BOARD_OFFSET_X + 3
            y = BOARD_OFFSET_Y + row * SQUARE_SIZE + 3

            # Use contrasting color based on square
            is_light_square = (row) % 2 == 0
            color = coord_color_light if is_light_square else coord_color_dark

            label = self.coord_font.render(rank_label, True, color)
            self.screen.blit(label, (x, y))
