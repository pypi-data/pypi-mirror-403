"""Configuration constants for the chess GUI application."""

# Window dimensions
BOARD_SIZE = 640
SQUARE_SIZE = BOARD_SIZE // 8
EVAL_BAR_WIDTH = 40
SIDEBAR_WIDTH = 160
STATUS_BAR_HEIGHT = 50
CONTROL_BAR_HEIGHT = 50

WINDOW_WIDTH = BOARD_SIZE + SIDEBAR_WIDTH
WINDOW_HEIGHT = STATUS_BAR_HEIGHT + BOARD_SIZE + CONTROL_BAR_HEIGHT

# Board position offset (from top-left of window)
BOARD_OFFSET_X = 0
BOARD_OFFSET_Y = STATUS_BAR_HEIGHT

# Colors (RGB)
COLOR_LIGHT_SQUARE = (240, 217, 181)  # Tan
COLOR_DARK_SQUARE = (181, 136, 99)    # Brown
COLOR_BACKGROUND = (49, 46, 43)       # Dark gray
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_SELECTED = (186, 202, 68, 180)  # Yellow-green highlight
COLOR_LEGAL_MOVE = (130, 151, 105)    # Green dot for legal moves
COLOR_LAST_MOVE = (205, 210, 106, 128)  # Yellow highlight for last move
COLOR_CHECK = (235, 97, 80)           # Red for check
COLOR_HINT = (72, 150, 220, 200)      # Blue highlight for hint move
COLOR_BUTTON = (70, 70, 70)           # Button background
COLOR_BUTTON_SELECTED = (76, 154, 42) # Green for selected button
COLOR_BUTTON_HOVER = (100, 100, 100)  # Button hover
COLOR_TEXT = (255, 255, 255)          # White text
COLOR_EVAL_WHITE = (255, 255, 255)    # White side of eval bar
COLOR_EVAL_BLACK = (0, 0, 0)          # Black side of eval bar
COLOR_MENU_BG = (39, 37, 34)          # Menu background

# Fonts
FONT_NAME = None  # Use default system font
FONT_SIZE_PIECE = 60
FONT_SIZE_COORD = 14
FONT_SIZE_STATUS = 20
FONT_SIZE_BUTTON = 16
FONT_SIZE_MENU_TITLE = 36
FONT_SIZE_MENU_OPTION = 24

# Unicode chess pieces
PIECE_UNICODE = {
    'K': '\u2654',  # White King
    'Q': '\u2655',  # White Queen
    'R': '\u2656',  # White Rook
    'B': '\u2657',  # White Bishop
    'N': '\u2658',  # White Knight
    'P': '\u2659',  # White Pawn
    'k': '\u265A',  # Black King
    'q': '\u265B',  # Black Queen
    'r': '\u265C',  # Black Rook
    'b': '\u265D',  # Black Bishop
    'n': '\u265E',  # Black Knight
    'p': '\u265F',  # Black Pawn
}

# Stockfish configuration
STOCKFISH_DEPTH = 15  # Analysis depth
STOCKFISH_MOVE_TIME = 1.0  # Seconds to think for AI moves

# AI difficulty presets (Elo ratings)
# Note: Stockfish 17+ requires minimum Elo of 1320
# Stockfish UCI_Elo tends to play weaker than the rating suggests
DIFFICULTY_PRESETS = {
    "Level 1": 1350,
    "Level 2": 1800,
    "Level 3": 2200,
    "Level 4": 2600,
    "Level 5": 3000,
}
DEFAULT_DIFFICULTY = "Level 3"

# Evaluation bar scaling
EVAL_MAX_CENTIPAWNS = 1000  # +/- 10 pawns = max bar
EVAL_MATE_SCORE = 10000  # Score to use for mate positions

# Frame rate
FPS = 60

# Coordinate labels
FILE_LABELS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
RANK_LABELS = ['1', '2', '3', '4', '5', '6', '7', '8']
