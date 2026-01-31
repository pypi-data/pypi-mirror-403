"""Main entry point for the Python Chess GUI application."""

import chess
import pygame

from python_chess_gui.chess_board_renderer import ChessBoardRenderer
from python_chess_gui.config_manager import find_stockfish, set_stockfish_path
from python_chess_gui.constants import (
    COLOR_BACKGROUND,
    DIFFICULTY_PRESETS,
    FPS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from python_chess_gui.evaluation_bar_renderer import EvaluationBarRenderer
from python_chess_gui.game_settings_menu import GameSettingsMenu
from python_chess_gui.game_state_manager import GameStateManager
from python_chess_gui.game_status_display import GameStatusDisplay
from python_chess_gui.stockfish_engine_controller import StockfishEngineController
from python_chess_gui.user_input_handler import InputAction, UserInputHandler


class ChessApplication:
    """Main chess application that coordinates all components."""

    def __init__(self):
        """Initialize the chess application."""
        pygame.init()
        pygame.display.set_caption("Play Chess - vs Stockfish")

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        # Components
        self.board_renderer = ChessBoardRenderer(self.screen)
        self.status_display = GameStatusDisplay(self.screen)
        self.eval_bar_renderer = EvaluationBarRenderer(self.screen)
        self.settings_menu = GameSettingsMenu(self.screen)
        self.game_state = GameStateManager()
        self.input_handler = UserInputHandler()
        self.engine: StockfishEngineController | None = None

        # Game state
        self.running = True
        self.in_menu = True
        self.player_is_white = True
        self.difficulty_name = "Medium"
        self.current_evaluation: float | None = None
        self.legal_moves_from_selection: list[chess.Move] = []
        self.ai_thinking = False
        self.hint_move: chess.Move | None = None

    def run(self) -> None:
        """Run the main game loop."""
        while self.running:
            self._process_events()

            if self.in_menu:
                self._render_menu()
            else:
                self._update_game()
                self._render_game()

            pygame.display.flip()
            self.clock.tick(FPS)

        self._cleanup()

    def _process_events(self) -> None:
        """Process all pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if self.in_menu:
                self._handle_menu_event(event)
            else:
                self._handle_game_event(event)

    def _handle_menu_event(self, event: pygame.event.Event) -> None:
        """Handle events while in menu.

        Args:
            event: Pygame event to process
        """
        # Handle path input mode keyboard events
        if event.type == pygame.KEYDOWN:
            if self.settings_menu.path_input_mode:
                if self.settings_menu.handle_key_event(event):
                    # If Enter was pressed and path input mode ended, try to start game
                    if not self.settings_menu.path_input_mode and self.settings_menu.path_input_text:
                        self._start_game()
                    return
            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.running = False
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if clicking confirm button in path input mode
            if self.settings_menu.path_input_mode:
                if (self.settings_menu.path_confirm_rect and
                    self.settings_menu.path_confirm_rect.collidepoint(event.pos)):
                    self.settings_menu.path_input_mode = False
                    if self.settings_menu.path_input_text:
                        self._start_game()
                return

            if self.settings_menu.handle_click(event.pos):
                self._start_game()

    def _handle_game_event(self, event: pygame.event.Event) -> None:
        """Handle events during gameplay.

        Args:
            event: Pygame event to process
        """
        result = self.input_handler.process_event(event)

        if result.action == InputAction.QUIT:
            self.running = False

        elif result.action == InputAction.NEW_GAME:
            self._return_to_menu()

        elif result.action == InputAction.UNDO:
            self._handle_undo()

        elif result.action == InputAction.HINT:
            self._handle_hint()

        elif result.action == InputAction.SELECT_SQUARE:
            if not self.ai_thinking and result.square is not None:
                self._handle_square_click(result.square)

    def _handle_square_click(self, square: chess.Square) -> None:
        """Handle a click on a board square.

        Args:
            square: The clicked square
        """
        # Don't allow moves if it's the AI's turn
        is_player_turn = self.game_state.board.turn == chess.WHITE if self.player_is_white else self.game_state.board.turn == chess.BLACK

        if not is_player_turn:
            return

        if self.game_state.is_game_over():
            return

        # If a piece is already selected
        if self.game_state.selected_square is not None:
            # Try to move to the clicked square
            move = self.game_state.try_move(self.game_state.selected_square, square)

            if move is not None:
                # Move successful
                self.legal_moves_from_selection = []
                self.hint_move = None
                self._update_evaluation()
                self._trigger_ai_move()
            else:
                # Try selecting a new piece
                self.legal_moves_from_selection = self.game_state.select_square(square)
        else:
            # Select a piece
            self.legal_moves_from_selection = self.game_state.select_square(square)

    def _trigger_ai_move(self) -> None:
        """Trigger the AI to make a move if it's the AI's turn."""
        if self.game_state.is_game_over():
            return

        is_player_turn = self.game_state.board.turn == chess.WHITE if self.player_is_white else self.game_state.board.turn == chess.BLACK

        if is_player_turn:
            return

        if self.engine is None or not self.engine.is_available():
            return

        self.ai_thinking = True

        # Get AI move
        ai_move = self.engine.get_best_move(self.game_state.board)
        if ai_move is not None:
            self.game_state.make_move(ai_move)
            self._update_evaluation()

        self.ai_thinking = False

    def _handle_hint(self) -> None:
        """Handle hint request - ask Stockfish for the best move."""
        if self.ai_thinking:
            return

        if self.game_state.is_game_over():
            return

        # Only show hint on player's turn
        is_player_turn = (
            self.game_state.board.turn == chess.WHITE
            if self.player_is_white
            else self.game_state.board.turn == chess.BLACK
        )
        if not is_player_turn:
            return

        if self.engine is not None and self.engine.is_available():
            self.hint_move = self.engine.get_best_move(self.game_state.board)

    def _handle_undo(self) -> None:
        """Handle undo request."""
        if self.ai_thinking:
            return

        # Undo both AI and player moves (one full round)
        self.game_state.undo_move_pair()
        self.legal_moves_from_selection = []
        self.hint_move = None
        self._update_evaluation()

        # If it's now AI's turn (can happen with odd move counts), trigger AI
        is_player_turn = (
            self.game_state.board.turn == chess.WHITE
            if self.player_is_white
            else self.game_state.board.turn == chess.BLACK
        )
        if not is_player_turn and not self.game_state.is_game_over():
            self._trigger_ai_move()

    def _update_evaluation(self) -> None:
        """Update the position evaluation."""
        # Handle game over positions directly
        if self.game_state.board.is_checkmate():
            # The side to move is checkmated, so the other side won
            if self.game_state.board.turn == chess.WHITE:
                self.current_evaluation = -100.0  # Black won
            else:
                self.current_evaluation = 100.0  # White won
            return

        if self.game_state.board.is_game_over():
            # Stalemate or draw
            self.current_evaluation = 0.0
            return

        if self.engine is not None and self.engine.is_available():
            self.current_evaluation = self.engine.evaluate_position(self.game_state.board)

    def _start_game(self) -> None:
        """Start a new game with the selected settings."""
        self.player_is_white, self.difficulty_name = self.settings_menu.get_settings()

        # Check if user provided a custom Stockfish path
        custom_path = self.settings_menu.get_stockfish_path()
        if custom_path:
            # Save to config for future use
            set_stockfish_path(custom_path)

        # Initialize engine with selected difficulty
        elo = DIFFICULTY_PRESETS[self.difficulty_name]
        stockfish_path = custom_path or find_stockfish()

        if self.engine is not None:
            self.engine.quit()
        self.engine = StockfishEngineController(elo, stockfish_path)

        # Check if Stockfish is available
        if not self.engine.is_available():
            self.settings_menu.show_path_input(
                "Stockfish not found! Enter the path to the Stockfish executable:"
            )
            return

        # Reset game state
        self.game_state.reset()
        self.legal_moves_from_selection = []
        self.hint_move = None
        self.current_evaluation = 0.0

        # Update input handler with player color
        self.input_handler.set_player_color(self.player_is_white)

        # Get initial evaluation
        self._update_evaluation()

        self.in_menu = False

        # If player is black, AI moves first
        if not self.player_is_white:
            self._trigger_ai_move()

    def _return_to_menu(self) -> None:
        """Return to the settings menu."""
        self.in_menu = True
        self.settings_menu.reset()
        self.game_state.reset()
        self.legal_moves_from_selection = []

    def _update_game(self) -> None:
        """Update game state."""
        pass

    def _render_menu(self) -> None:
        """Render the settings menu."""
        self.settings_menu.render()

    def _render_game(self) -> None:
        """Render the game screen."""
        # Clear background
        self.screen.fill(COLOR_BACKGROUND)

        # Render board
        self.board_renderer.render(
            board=self.game_state.board,
            player_is_white=self.player_is_white,
            selected_square=self.game_state.selected_square,
            legal_moves=self.legal_moves_from_selection if self.legal_moves_from_selection else None,
            last_move=self.game_state.get_last_move(),
            hint_move=self.hint_move,
        )

        # Render evaluation bar
        self.eval_bar_renderer.render(self.current_evaluation, self.player_is_white)

        # Render status
        turn_text = self.game_state.get_turn_text()
        if self.ai_thinking:
            turn_text = "AI thinking..."

        eval_text = self._format_evaluation()

        self.status_display.render(turn_text, eval_text, self.difficulty_name)

    def _format_evaluation(self) -> str:
        """Format the evaluation for display.

        Returns:
            Formatted evaluation string
        """
        if self.current_evaluation is None:
            return "Eval: N/A"

        if abs(self.current_evaluation) >= 100:
            if self.current_evaluation > 0:
                return "Eval: White wins"
            else:
                return "Eval: Black wins"

        if self.current_evaluation >= 0:
            return f"Eval: +{self.current_evaluation:.1f}"
        else:
            return f"Eval: {self.current_evaluation:.1f}"

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self.engine is not None:
            self.engine.quit()
        pygame.quit()


def main() -> None:
    """Initialize and run the chess GUI application."""
    app = ChessApplication()
    app.run()


if __name__ == "__main__":
    main()
