"""Coordinate conversion utilities for chess board."""

import chess

from python_chess_gui.layout_manager import LayoutManager


def convert_screen_position_to_board_square(
    screen_x: int, screen_y: int, player_is_white: bool, layout: LayoutManager
) -> chess.Square | None:
    """Convert screen coordinates to a chess square.

    Args:
        screen_x: X coordinate on screen
        screen_y: Y coordinate on screen
        player_is_white: True if player is playing white (white at bottom)
        layout: Layout manager for dimension calculations

    Returns:
        Chess square index (0-63) or None if outside board
    """
    board_x = screen_x - layout.board_offset_x
    board_y = screen_y - layout.board_offset_y

    if board_x < 0 or board_x >= layout.square_size * 8:
        return None
    if board_y < 0 or board_y >= layout.square_size * 8:
        return None

    file_idx = board_x // layout.square_size
    rank_idx = board_y // layout.square_size

    if player_is_white:
        file = file_idx
        rank = 7 - rank_idx
    else:
        file = 7 - file_idx
        rank = rank_idx

    return chess.square(file, rank)


def convert_board_square_to_screen_position(
    square: chess.Square, player_is_white: bool, layout: LayoutManager
) -> tuple[int, int]:
    """Convert a chess square to screen coordinates (top-left of square).

    Args:
        square: Chess square index (0-63)
        player_is_white: True if player is playing white (white at bottom)
        layout: Layout manager for dimension calculations

    Returns:
        Tuple of (x, y) screen coordinates for top-left corner of square
    """
    file = chess.square_file(square)
    rank = chess.square_rank(square)

    if player_is_white:
        screen_col = file
        screen_row = 7 - rank
    else:
        screen_col = 7 - file
        screen_row = rank

    x = layout.board_offset_x + screen_col * layout.square_size
    y = layout.board_offset_y + screen_row * layout.square_size

    return (x, y)


def get_square_center(
    square: chess.Square, player_is_white: bool, layout: LayoutManager
) -> tuple[int, int]:
    """Get the center coordinates of a chess square on screen.

    Args:
        square: Chess square index (0-63)
        player_is_white: True if player is playing white (white at bottom)
        layout: Layout manager for dimension calculations

    Returns:
        Tuple of (x, y) screen coordinates for center of square
    """
    x, y = convert_board_square_to_screen_position(square, player_is_white, layout)
    return (x + layout.square_size // 2, y + layout.square_size // 2)
