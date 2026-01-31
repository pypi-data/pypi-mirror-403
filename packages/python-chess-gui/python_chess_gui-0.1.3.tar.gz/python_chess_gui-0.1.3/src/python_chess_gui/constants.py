"""Configuration constants for the chess GUI application."""

# Window dimensions (in pixels)
CHESS_BOARD_SIZE_PIXELS = 640
BOARD_SQUARE_SIZE_PIXELS = CHESS_BOARD_SIZE_PIXELS // 8
EVALUATION_BAR_WIDTH_PIXELS = 40
SIDEBAR_WIDTH_PIXELS = 160
STATUS_BAR_HEIGHT_PIXELS = 50
CONTROL_BAR_HEIGHT_PIXELS = 50

MAIN_WINDOW_WIDTH_PIXELS = CHESS_BOARD_SIZE_PIXELS + SIDEBAR_WIDTH_PIXELS
MAIN_WINDOW_HEIGHT_PIXELS = STATUS_BAR_HEIGHT_PIXELS + CHESS_BOARD_SIZE_PIXELS + CONTROL_BAR_HEIGHT_PIXELS

# Board position offset (from top-left of window, in pixels)
BOARD_OFFSET_X_PIXELS = 0
BOARD_OFFSET_Y_PIXELS = STATUS_BAR_HEIGHT_PIXELS

# Colors (RGB/RGBA tuples)
LIGHT_SQUARE_COLOR_RGB = (240, 217, 181)  # Tan
DARK_SQUARE_COLOR_RGB = (181, 136, 99)    # Brown
WINDOW_BACKGROUND_COLOR_RGB = (49, 46, 43)       # Dark gray
WHITE_COLOR_RGB = (255, 255, 255)
BLACK_COLOR_RGB = (0, 0, 0)
SELECTED_SQUARE_HIGHLIGHT_RGBA = (186, 202, 68, 180)  # Yellow-green highlight
LEGAL_MOVE_INDICATOR_COLOR_RGB = (130, 151, 105)    # Green dot for legal moves
LAST_MOVE_HIGHLIGHT_RGBA = (205, 210, 106, 128)  # Yellow highlight for last move
CHECK_HIGHLIGHT_COLOR_RGB = (235, 97, 80)           # Red for check
HINT_MOVE_HIGHLIGHT_RGBA = (72, 150, 220, 200)      # Blue highlight for hint move
BUTTON_BACKGROUND_COLOR_RGB = (70, 70, 70)           # Button background
BUTTON_SELECTED_COLOR_RGB = (76, 154, 42) # Green for selected button
BUTTON_HOVER_COLOR_RGB = (100, 100, 100)  # Button hover
TEXT_COLOR_RGB = (255, 255, 255)          # White text
EVAL_BAR_WHITE_COLOR_RGB = (255, 255, 255)    # White side of eval bar
EVAL_BAR_BLACK_COLOR_RGB = (0, 0, 0)          # Black side of eval bar
MENU_BACKGROUND_COLOR_RGB = (39, 37, 34)          # Menu background

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
STOCKFISH_ANALYSIS_DEPTH = 15  # Analysis depth
STOCKFISH_MOVE_TIME_SECONDS = 1.0  # Seconds to think for AI moves

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
EVALUATION_MAX_CENTIPAWNS = 1000  # +/- 10 pawns = max bar
EVALUATION_MATE_SCORE = 10000  # Score to use for mate positions

# Frame rate
FRAMES_PER_SECOND = 60

# Coordinate labels
FILE_LABELS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
RANK_LABELS = ['1', '2', '3', '4', '5', '6', '7', '8']
