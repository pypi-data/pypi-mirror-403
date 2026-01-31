"""Dynamic layout management for resizable window support."""

from python_chess_gui.constants import (
    MAIN_WINDOW_WIDTH_PIXELS,
    MAIN_WINDOW_HEIGHT_PIXELS,
)


class LayoutManager:
    """Manages dynamic layout calculations based on window size."""

    # Proportions (ratios relative to window dimensions)
    SIDEBAR_WIDTH_RATIO = 0.20          # 20% of width for sidebar
    STATUS_BAR_HEIGHT_RATIO = 0.07      # 7% of height for status bar
    CONTROL_BAR_HEIGHT_RATIO = 0.07     # 7% of height for control bar

    # Minimum window dimensions (in pixels)
    MINIMUM_WINDOW_WIDTH_PIXELS = 600
    MINIMUM_WINDOW_HEIGHT_PIXELS = 500

    def __init__(self, window_width: int = MAIN_WINDOW_WIDTH_PIXELS,
                 window_height: int = MAIN_WINDOW_HEIGHT_PIXELS):
        """Initialize the layout manager.

        Args:
            window_width: Initial window width in pixels
            window_height: Initial window height in pixels
        """
        # Initialize all dimension attributes
        self.window_width = 0
        self.window_height = 0
        self.status_bar_height = 0
        self.control_bar_height = 0
        self.sidebar_width = 0
        self.board_size = 0
        self.square_size = 0
        self.board_offset_x = 0
        self.board_offset_y = 0
        self.evaluation_bar_width = 0
        self.evaluation_bar_x = 0
        self.evaluation_bar_y = 0
        self.evaluation_bar_height = 0
        self.font_size_piece = 0
        self.font_size_coordinates = 0
        self.font_size_status = 0
        self.font_size_button = 0
        self.font_size_menu_title = 0
        self.font_size_menu_option = 0

        # Calculate initial dimensions
        self.update_dimensions(window_width, window_height)

    def update_dimensions(self, window_width: int, window_height: int) -> None:
        """Recalculate all dimensions based on new window size.

        Args:
            window_width: New window width in pixels
            window_height: New window height in pixels
        """
        # Constrain to minimum dimensions
        self.window_width = max(window_width, self.MINIMUM_WINDOW_WIDTH_PIXELS)
        self.window_height = max(window_height, self.MINIMUM_WINDOW_HEIGHT_PIXELS)

        # Calculate bar dimensions
        self.status_bar_height = int(self.window_height * self.STATUS_BAR_HEIGHT_RATIO)
        self.control_bar_height = int(self.window_height * self.CONTROL_BAR_HEIGHT_RATIO)
        self.sidebar_width = int(self.window_width * self.SIDEBAR_WIDTH_RATIO)

        # Calculate board size (must be square and divisible by 8)
        available_height = self.window_height - self.status_bar_height - self.control_bar_height
        available_width = self.window_width - self.sidebar_width
        board_size = min(available_height, available_width)
        self.board_size = (board_size // 8) * 8  # Round down to multiple of 8

        self.square_size = self.board_size // 8
        self.board_offset_x = 0
        self.board_offset_y = self.status_bar_height

        # Evaluation bar dimensions
        self.evaluation_bar_width = max(30, self.sidebar_width // 4)
        self.evaluation_bar_x = self.board_size + (self.sidebar_width - self.evaluation_bar_width) // 2
        self.evaluation_bar_y = self.board_offset_y
        self.evaluation_bar_height = self.board_size

        # Proportional font sizes
        self.font_size_piece = max(20, self.square_size * 3 // 4)
        self.font_size_coordinates = max(10, self.square_size // 6)
        self.font_size_status = max(14, self.window_height // 40)
        self.font_size_button = max(12, self.window_height // 50)
        self.font_size_menu_title = max(24, self.window_height // 20)
        self.font_size_menu_option = max(18, self.window_height // 30)

    def get_minimum_size(self) -> tuple[int, int]:
        """Get the minimum window size.

        Returns:
            Tuple of (min_width, min_height) in pixels
        """
        return (self.MINIMUM_WINDOW_WIDTH_PIXELS, self.MINIMUM_WINDOW_HEIGHT_PIXELS)
