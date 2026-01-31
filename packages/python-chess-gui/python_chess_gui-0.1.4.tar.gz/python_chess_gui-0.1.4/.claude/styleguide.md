# Python Style Guide

This document defines the coding standards for the python-chess-gui project.

## Language

- All code, comments, docstrings, and documentation must be written in **English**.

## Imports

### Absolute Imports Only

**Always use absolute imports. Never use relative imports.**

```python
# CORRECT - Absolute imports
from python_chess_gui.board import ChessBoardRenderer
from python_chess_gui.pieces import PieceSprite
from python_chess_gui.engine import StockfishEngineWrapper

# INCORRECT - Relative imports (NEVER use these)
from .board import ChessBoardRenderer
from ..pieces import PieceSprite
```

### Import Organization

Organize imports in the following order, separated by blank lines:

1. Standard library imports
2. Third-party library imports
3. Local application imports

```python
import sys
from pathlib import Path

import chess
import pygame

from python_chess_gui.board import ChessBoardRenderer
from python_chess_gui.constants import BOARD_SIZE
```

## Naming Conventions

### Be Explicit and Meaningful

Names should be **self-documenting**. A reader should understand the purpose without additional context.

### Classes

Use PascalCase. Names should clearly describe what the class represents.

```python
# CORRECT - Clear and descriptive
class ChessBoardRenderer:
class PieceMovementValidator:
class StockfishEngineWrapper:
class PlayerTurnManager:
class GameStateSerializer:

# INCORRECT - Vague or abbreviated
class Board:      # Too generic
class Renderer:   # What does it render?
class CBR:        # Cryptic abbreviation
class Helper:     # Meaningless
class Manager:    # Too generic without context
```

### Functions and Methods

Use snake_case. Names should describe the action and, when relevant, what is being acted upon.

```python
# CORRECT - Verb + subject, clearly describes the action
def render_chess_board_to_surface(board_state, target_surface):
def calculate_legal_moves_for_piece(piece_position):
def validate_castling_rights(current_board_state):
def load_piece_images_from_directory(assets_directory_path):
def convert_algebraic_notation_to_coordinates(algebraic_square):

# INCORRECT - Vague, abbreviated, or missing context
def render():           # Render what?
def calc():             # Calculate what?
def process():          # Process what? How?
def do_stuff():         # Meaningless
def hlpr():             # Cryptic
def handle(x):          # Handle what? What is x?
```

### Variables

Use snake_case. Names should clearly indicate what the variable contains.

```python
# CORRECT - Clearly describes the content
selected_piece_position = None
current_player_color = chess.WHITE
legal_moves_for_selected_piece = []
board_square_size_in_pixels = 80
time_remaining_for_white_player_seconds = 300
captured_pieces_by_black = []

# INCORRECT - Vague, single letters, or abbreviated
pos = None          # Position of what?
c = chess.WHITE     # What is c?
moves = []          # Moves of what? All moves? Legal moves?
sz = 80             # Size of what?
t = 300             # Time? What time?
lst = []            # A list of what?
tmp = None          # Temporary what?
x, y = 0, 0         # Acceptable only in very limited mathematical contexts
```

### Constants

Use UPPER_SNAKE_CASE. Names should describe the constant's purpose.

```python
# CORRECT
CHESS_BOARD_SIZE_SQUARES = 8
DEFAULT_SQUARE_SIZE_PIXELS = 80
LIGHT_SQUARE_COLOR_RGB = (240, 217, 181)
DARK_SQUARE_COLOR_RGB = (181, 136, 99)
STOCKFISH_DEFAULT_DEPTH = 15
MINIMUM_MOVE_TIME_MILLISECONDS = 100

# INCORRECT
SIZE = 8            # Size of what?
SQ = 80             # Cryptic
COLOR1 = (240, 217, 181)  # What color?
DEPTH = 15          # Depth of what?
```

### Boolean Variables and Functions

Boolean names should read as questions or statements that are clearly true/false.

```python
# CORRECT - Clear yes/no semantics
is_king_in_check = False
has_player_castled = True
can_piece_move_to_square = False
should_highlight_legal_moves = True

def is_move_legal(move):
def has_game_ended():
def can_castle_kingside(board_state):

# INCORRECT
check = False       # Is this a check? A checking action?
castle = True       # Is this about castling? A castle piece?
flag = False        # What flag?
```

## Code Style

### Line Length

Maximum line length is **88 characters** (Black formatter default).

### String Quotes

Use double quotes for strings consistently.

```python
message = "Game over"
piece_type = "knight"
```

### Type Hints

Use type hints for function signatures and class attributes.

```python
def calculate_legal_moves_for_piece(
    piece_position: chess.Square,
    current_board: chess.Board
) -> list[chess.Move]:
    pass

class ChessBoardRenderer:
    board_surface: pygame.Surface
    square_size_pixels: int
    highlighted_squares: list[chess.Square]
```

### Docstrings

Use docstrings for all public modules, classes, and functions.

```python
def convert_screen_coordinates_to_board_square(
    screen_x_position: int,
    screen_y_position: int,
    board_offset_x: int,
    board_offset_y: int,
    square_size_pixels: int
) -> chess.Square | None:
    """Convert screen pixel coordinates to a chess board square.

    Args:
        screen_x_position: The x coordinate in screen pixels.
        screen_y_position: The y coordinate in screen pixels.
        board_offset_x: The x offset of the board from screen origin.
        board_offset_y: The y offset of the board from screen origin.
        square_size_pixels: The size of each square in pixels.

    Returns:
        The chess.Square at the given coordinates, or None if the
        coordinates are outside the board boundaries.
    """
    pass
```

## General Principles

1. **Clarity over brevity**: A longer, clearer name is always better than a short, cryptic one.
2. **Self-documenting code**: The code should explain itself through good naming.
3. **Consistency**: Follow these conventions throughout the entire codebase.
4. **No abbreviations**: Avoid abbreviations unless they are universally understood (e.g., `id`, `url`).
5. **Context in names**: Include enough context in names so they make sense outside their immediate scope.
