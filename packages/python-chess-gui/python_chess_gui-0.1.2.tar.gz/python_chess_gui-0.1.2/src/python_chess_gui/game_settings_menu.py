"""Game settings menu for color and difficulty selection."""

import pygame

from python_chess_gui.constants import (
    COLOR_BACKGROUND,
    COLOR_BUTTON,
    COLOR_BUTTON_HOVER,
    COLOR_BUTTON_SELECTED,
    COLOR_MENU_BG,
    COLOR_TEXT,
    COLOR_WHITE,
    DEFAULT_DIFFICULTY,
    DIFFICULTY_PRESETS,
    FONT_NAME,
    FONT_SIZE_BUTTON,
    FONT_SIZE_MENU_OPTION,
    FONT_SIZE_MENU_TITLE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


class GameSettingsMenu:
    """Renders and handles the game settings menu."""

    def __init__(self, screen: pygame.Surface):
        """Initialize the settings menu.

        Args:
            screen: Pygame surface to render on
        """
        self.screen = screen
        self.title_font = pygame.font.SysFont("Arial, Helvetica", FONT_SIZE_MENU_TITLE)
        self.option_font = pygame.font.SysFont("Arial, Helvetica", FONT_SIZE_MENU_OPTION)
        self.button_font = pygame.font.SysFont("Arial, Helvetica", FONT_SIZE_BUTTON)

        # Menu state
        self.selected_color: bool | None = None  # True = white, False = black
        self.selected_difficulty: str = DEFAULT_DIFFICULTY
        self.error_message: str | None = None

        # Path input state
        self.path_input_mode: bool = False
        self.path_input_text: str = ""
        self.path_input_prompt: str = ""

        # Button rectangles (calculated in render)
        self.white_button_rect: pygame.Rect | None = None
        self.black_button_rect: pygame.Rect | None = None
        self.difficulty_button_rects: dict[str, pygame.Rect] = {}
        self.start_button_rect: pygame.Rect | None = None
        self.path_input_rect: pygame.Rect | None = None
        self.path_confirm_rect: pygame.Rect | None = None

    def render(self) -> None:
        """Render the complete settings menu."""
        # Fill background
        self.screen.fill(COLOR_MENU_BG)

        # Title
        title = self.title_font.render("Play Chess", True, COLOR_TEXT)
        title_rect = title.get_rect(centerx=WINDOW_WIDTH // 2, top=40)
        self.screen.blit(title, title_rect)

        # Subtitle
        subtitle = self.option_font.render("vs Stockfish AI", True, COLOR_TEXT)
        subtitle_rect = subtitle.get_rect(centerx=WINDOW_WIDTH // 2, top=90)
        self.screen.blit(subtitle, subtitle_rect)

        if self.path_input_mode:
            # Show path input screen
            self._render_path_input()
        else:
            # Normal menu
            # Color selection
            self._render_color_selection()

            # Difficulty selection
            self._render_difficulty_selection()

            # Start button
            self._render_start_button()

            # Error message if any
            self._render_error_message()

    def _render_color_selection(self) -> None:
        """Render the color selection buttons."""
        y_pos = 160

        # Label
        label = self.option_font.render("Play as:", True, COLOR_TEXT)
        label_rect = label.get_rect(centerx=WINDOW_WIDTH // 2, top=y_pos)
        self.screen.blit(label, label_rect)

        # Buttons
        button_width = 150
        button_height = 50
        button_spacing = 30
        buttons_total_width = 2 * button_width + button_spacing
        start_x = (WINDOW_WIDTH - buttons_total_width) // 2
        button_y = y_pos + 50

        # White button
        self.white_button_rect = pygame.Rect(start_x, button_y, button_width, button_height)
        white_color = COLOR_BUTTON_SELECTED if self.selected_color is True else COLOR_BUTTON
        pygame.draw.rect(self.screen, white_color, self.white_button_rect, border_radius=5)
        border_color = COLOR_WHITE if self.selected_color is True else COLOR_TEXT
        pygame.draw.rect(self.screen, border_color, self.white_button_rect, 3, border_radius=5)

        white_text = self.button_font.render("White", True, COLOR_TEXT)
        white_text_rect = white_text.get_rect(center=self.white_button_rect.center)
        self.screen.blit(white_text, white_text_rect)

        # Black button
        self.black_button_rect = pygame.Rect(
            start_x + button_width + button_spacing, button_y, button_width, button_height
        )
        black_color = COLOR_BUTTON_SELECTED if self.selected_color is False else COLOR_BUTTON
        pygame.draw.rect(self.screen, black_color, self.black_button_rect, border_radius=5)
        border_color = COLOR_WHITE if self.selected_color is False else COLOR_TEXT
        pygame.draw.rect(self.screen, border_color, self.black_button_rect, 3, border_radius=5)

        black_text = self.button_font.render("Black", True, COLOR_TEXT)
        black_text_rect = black_text.get_rect(center=self.black_button_rect.center)
        self.screen.blit(black_text, black_text_rect)

    def _render_difficulty_selection(self) -> None:
        """Render the difficulty selection buttons."""
        y_pos = 300

        # Label
        label = self.option_font.render("Difficulty:", True, COLOR_TEXT)
        label_rect = label.get_rect(centerx=WINDOW_WIDTH // 2, top=y_pos)
        self.screen.blit(label, label_rect)

        # Difficulty buttons
        difficulties = list(DIFFICULTY_PRESETS.keys())
        button_width = 120
        button_height = 40
        button_spacing = 10
        buttons_total_width = len(difficulties) * button_width + (len(difficulties) - 1) * button_spacing
        start_x = (WINDOW_WIDTH - buttons_total_width) // 2
        button_y = y_pos + 45

        self.difficulty_button_rects = {}

        for i, diff_name in enumerate(difficulties):
            rect = pygame.Rect(
                start_x + i * (button_width + button_spacing),
                button_y,
                button_width,
                button_height,
            )
            self.difficulty_button_rects[diff_name] = rect

            # Highlight selected
            is_selected = diff_name == self.selected_difficulty
            color = COLOR_BUTTON_SELECTED if is_selected else COLOR_BUTTON
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            border_color = COLOR_WHITE if is_selected else COLOR_TEXT
            pygame.draw.rect(self.screen, border_color, rect, 3, border_radius=5)

            # Difficulty name
            text = self.button_font.render(diff_name, True, COLOR_TEXT)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

    def _render_start_button(self) -> None:
        """Render the start game button."""
        button_width = 200
        button_height = 60
        button_x = (WINDOW_WIDTH - button_width) // 2
        button_y = 450

        self.start_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        # Only enable if color is selected
        if self.selected_color is not None:
            color = COLOR_BUTTON_SELECTED
            border_color = COLOR_WHITE
        else:
            color = COLOR_BUTTON
            border_color = COLOR_TEXT

        pygame.draw.rect(self.screen, color, self.start_button_rect, border_radius=8)
        pygame.draw.rect(self.screen, border_color, self.start_button_rect, 3, border_radius=8)

        text = self.option_font.render("Start Game", True, COLOR_TEXT)
        text_rect = text.get_rect(center=self.start_button_rect.center)
        self.screen.blit(text, text_rect)

        # Hint text if no color selected
        if self.selected_color is None:
            hint = self.button_font.render("Select a color to start", True, COLOR_TEXT)
            hint_rect = hint.get_rect(centerx=WINDOW_WIDTH // 2, top=button_y + button_height + 20)
            self.screen.blit(hint, hint_rect)

    def handle_click(self, pos: tuple[int, int]) -> bool:
        """Handle a mouse click on the menu.

        Args:
            pos: (x, y) position of the click

        Returns:
            True if game should start, False otherwise
        """
        # Check color buttons
        if self.white_button_rect and self.white_button_rect.collidepoint(pos):
            self.selected_color = True
            return False

        if self.black_button_rect and self.black_button_rect.collidepoint(pos):
            self.selected_color = False
            return False

        # Check difficulty buttons
        for diff_name, rect in self.difficulty_button_rects.items():
            if rect.collidepoint(pos):
                self.selected_difficulty = diff_name
                return False

        # Check start button
        if self.start_button_rect and self.start_button_rect.collidepoint(pos):
            if self.selected_color is not None:
                return True

        return False

    def get_settings(self) -> tuple[bool, str]:
        """Get the selected settings.

        Returns:
            Tuple of (player_is_white, difficulty_name)
        """
        player_is_white = self.selected_color if self.selected_color is not None else True
        return (player_is_white, self.selected_difficulty)

    def reset(self) -> None:
        """Reset menu selections."""
        self.selected_color = None
        self.selected_difficulty = DEFAULT_DIFFICULTY
        self.error_message = None
        self.path_input_mode = False
        self.path_input_text = ""
        self.path_input_prompt = ""

    def set_error(self, message: str) -> None:
        """Set an error message to display.

        Args:
            message: Error message to show
        """
        self.error_message = message

    def _render_error_message(self) -> None:
        """Render error message if present."""
        if self.error_message is None:
            return

        # Red color for error
        error_color = (255, 100, 100)

        # Word wrap the error message
        max_width = WINDOW_WIDTH - 40
        words = self.error_message.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            test_surface = self.button_font.render(test_line, True, error_color)
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # Render each line
        y_pos = 540
        for line in lines:
            error_surface = self.button_font.render(line, True, error_color)
            error_rect = error_surface.get_rect(centerx=WINDOW_WIDTH // 2, top=y_pos)
            self.screen.blit(error_surface, error_rect)
            y_pos += 22

    def show_path_input(self, prompt: str) -> None:
        """Show the path input screen.

        Args:
            prompt: Prompt message to show
        """
        self.path_input_mode = True
        self.path_input_prompt = prompt
        self.path_input_text = ""
        self.error_message = None

    def get_stockfish_path(self) -> str | None:
        """Get the user-entered Stockfish path.

        Returns:
            Path string if entered, None otherwise
        """
        if self.path_input_text:
            return self.path_input_text
        return None

    def handle_key_event(self, event: pygame.event.Event) -> bool:
        """Handle keyboard events for path input.

        Args:
            event: Pygame key event

        Returns:
            True if event was handled
        """
        if not self.path_input_mode:
            return False

        if event.key == pygame.K_RETURN:
            # Confirm path and try to start game
            self.path_input_mode = False
            return True
        elif event.key == pygame.K_ESCAPE:
            # Cancel path input
            self.path_input_mode = False
            self.path_input_text = ""
            return True
        elif event.key == pygame.K_BACKSPACE:
            self.path_input_text = self.path_input_text[:-1]
            return True
        elif event.unicode and event.unicode.isprintable():
            self.path_input_text += event.unicode
            return True

        return False

    def _render_path_input(self) -> None:
        """Render the path input screen."""
        # Prompt text
        prompt_color = (255, 200, 100)
        prompt_surface = self.button_font.render(self.path_input_prompt, True, prompt_color)
        prompt_rect = prompt_surface.get_rect(centerx=WINDOW_WIDTH // 2, top=160)
        self.screen.blit(prompt_surface, prompt_rect)

        # Input field background
        input_width = WINDOW_WIDTH - 80
        input_height = 40
        input_x = 40
        input_y = 220
        self.path_input_rect = pygame.Rect(input_x, input_y, input_width, input_height)

        pygame.draw.rect(self.screen, (60, 60, 60), self.path_input_rect, border_radius=5)
        pygame.draw.rect(self.screen, COLOR_WHITE, self.path_input_rect, 2, border_radius=5)

        # Input text (with cursor)
        display_text = self.path_input_text + "|"
        text_surface = self.button_font.render(display_text, True, COLOR_TEXT)
        text_rect = text_surface.get_rect(midleft=(input_x + 10, input_y + input_height // 2))

        # Clip text if too long
        if text_rect.width > input_width - 20:
            # Show the end of the text
            visible_text = display_text
            while self.button_font.size(visible_text)[0] > input_width - 20 and len(visible_text) > 1:
                visible_text = visible_text[1:]
            text_surface = self.button_font.render(visible_text, True, COLOR_TEXT)
            text_rect = text_surface.get_rect(midleft=(input_x + 10, input_y + input_height // 2))

        self.screen.blit(text_surface, text_rect)

        # Confirm button
        button_width = 150
        button_height = 50
        button_x = (WINDOW_WIDTH - button_width) // 2
        button_y = 300
        self.path_confirm_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        pygame.draw.rect(self.screen, COLOR_BUTTON_SELECTED, self.path_confirm_rect, border_radius=5)
        pygame.draw.rect(self.screen, COLOR_WHITE, self.path_confirm_rect, 2, border_radius=5)

        confirm_text = self.button_font.render("Confirm", True, COLOR_TEXT)
        confirm_rect = confirm_text.get_rect(center=self.path_confirm_rect.center)
        self.screen.blit(confirm_text, confirm_rect)

        # Help text
        help_texts = [
            "Enter the full path to stockfish executable",
            "Press Enter to confirm, Escape to cancel",
            "Example: /usr/local/bin/stockfish",
        ]
        y_pos = 380
        for help_text in help_texts:
            help_surface = self.button_font.render(help_text, True, (150, 150, 150))
            help_rect = help_surface.get_rect(centerx=WINDOW_WIDTH // 2, top=y_pos)
            self.screen.blit(help_surface, help_rect)
            y_pos += 25
