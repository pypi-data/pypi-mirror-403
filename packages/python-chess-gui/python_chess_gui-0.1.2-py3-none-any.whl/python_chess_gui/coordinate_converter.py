"""Coordinate conversion utilities for chess board."""

import chess

from python_chess_gui.constants import (
    BOARD_OFFSET_X,
    BOARD_OFFSET_Y,
    SQUARE_SIZE,
)


def convert_screen_position_to_board_square(
    screen_x: int, screen_y: int, player_is_white: bool
) -> chess.Square | None:
    """Convert screen coordinates to a chess square.

    Args:
        screen_x: X coordinate on screen
        screen_y: Y coordinate on screen
        player_is_white: True if player is playing white (white at bottom)

    Returns:
        Chess square index (0-63) or None if outside board
    """
    # Adjust for board offset
    board_x = screen_x - BOARD_OFFSET_X
    board_y = screen_y - BOARD_OFFSET_Y

    # Check if within board bounds
    if board_x < 0 or board_x >= SQUARE_SIZE * 8:
        return None
    if board_y < 0 or board_y >= SQUARE_SIZE * 8:
        return None

    # Convert to file and rank indices (0-7)
    file_idx = board_x // SQUARE_SIZE
    rank_idx = board_y // SQUARE_SIZE

    # If player is white, board is oriented with rank 8 at top (row 0)
    # If player is black, board is flipped
    if player_is_white:
        # White at bottom: rank 8 at top (rank_idx 0 = rank 7)
        file = file_idx
        rank = 7 - rank_idx
    else:
        # Black at bottom: rank 1 at top (rank_idx 0 = rank 0)
        file = 7 - file_idx
        rank = rank_idx

    return chess.square(file, rank)


def convert_board_square_to_screen_position(
    square: chess.Square, player_is_white: bool
) -> tuple[int, int]:
    """Convert a chess square to screen coordinates (top-left of square).

    Args:
        square: Chess square index (0-63)
        player_is_white: True if player is playing white (white at bottom)

    Returns:
        Tuple of (x, y) screen coordinates for top-left corner of square
    """
    file = chess.square_file(square)
    rank = chess.square_rank(square)

    if player_is_white:
        # White at bottom: file a on left, rank 8 at top
        screen_col = file
        screen_row = 7 - rank
    else:
        # Black at bottom: file h on left, rank 1 at top
        screen_col = 7 - file
        screen_row = rank

    x = BOARD_OFFSET_X + screen_col * SQUARE_SIZE
    y = BOARD_OFFSET_Y + screen_row * SQUARE_SIZE

    return (x, y)


def get_square_center(square: chess.Square, player_is_white: bool) -> tuple[int, int]:
    """Get the center coordinates of a chess square on screen.

    Args:
        square: Chess square index (0-63)
        player_is_white: True if player is playing white (white at bottom)

    Returns:
        Tuple of (x, y) screen coordinates for center of square
    """
    x, y = convert_board_square_to_screen_position(square, player_is_white)
    return (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2)
