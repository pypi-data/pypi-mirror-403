"""Stockfish engine controller for AI moves and position evaluation."""

import chess
import chess.engine

from python_chess_gui.engine.config_manager import find_stockfish
from python_chess_gui.constants import (
    DIFFICULTY_PRESETS,
    EVALUATION_MATE_SCORE,
    STOCKFISH_ANALYSIS_DEPTH,
    STOCKFISH_MOVE_TIME_SECONDS,
)


class StockfishEngineController:
    """Controls Stockfish engine for AI moves and evaluation."""

    def __init__(self, elo: int = 1600, stockfish_path: str | None = None):
        """Initialize the Stockfish engine.

        Args:
            elo: Elo rating to limit Stockfish strength (800-3000)
            stockfish_path: Optional custom path to Stockfish executable
        """
        self.engine: chess.engine.SimpleEngine | None = None
        self.elo = elo
        self.stockfish_path = stockfish_path or find_stockfish()
        self._start_engine()

    def _start_engine(self) -> None:
        """Start the Stockfish engine process."""
        if self.stockfish_path is None:
            self.engine = None
            return

        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            self._configure_elo(self.elo)
        except FileNotFoundError:
            print(f"Error: Stockfish not found at {self.stockfish_path}")
            self.engine = None
        except Exception as e:
            print(f"Error starting Stockfish: {e}")
            self.engine = None

    def _configure_elo(self, elo: int) -> None:
        """Configure the engine to play at a specific Elo rating.

        Args:
            elo: Target Elo rating (1320-3000 for Stockfish 17+)
        """
        if self.engine is None:
            return

        elo = max(1320, min(3000, elo))
        self.elo = elo

        self.engine.configure({
            "UCI_LimitStrength": True,
            "UCI_Elo": elo,
        })

    def set_difficulty(self, difficulty_name: str) -> None:
        """Set engine difficulty by preset name.

        Args:
            difficulty_name: One of the DIFFICULTY_PRESETS keys
        """
        if difficulty_name in DIFFICULTY_PRESETS:
            self._configure_elo(DIFFICULTY_PRESETS[difficulty_name])

    def set_elo(self, elo: int) -> None:
        """Set engine Elo rating directly.

        Args:
            elo: Target Elo rating (800-3000)
        """
        self._configure_elo(elo)

    def get_best_move(self, board: chess.Board) -> chess.Move | None:
        """Get the best move for the current position.

        Args:
            board: Current chess board state

        Returns:
            Best move, or None if engine unavailable
        """
        if self.engine is None:
            return None

        try:
            result = self.engine.play(
                board,
                chess.engine.Limit(time=STOCKFISH_MOVE_TIME_SECONDS),
            )
            return result.move
        except Exception as e:
            print(f"Error getting move from Stockfish: {e}")
            return None

    def evaluate_position(self, board: chess.Board) -> float | None:
        """Evaluate the current position.

        Args:
            board: Current chess board state

        Returns:
            Evaluation in pawns (positive = white advantage), or None if unavailable
        """
        if self.engine is None:
            return None

        try:
            info = self.engine.analyse(
                board,
                chess.engine.Limit(depth=STOCKFISH_ANALYSIS_DEPTH),
            )

            score = info["score"].white()

            if score.is_mate():
                mate_in = score.mate()
                if mate_in is not None:
                    if mate_in >= 0:
                        return EVALUATION_MATE_SCORE / 100
                    else:
                        return -EVALUATION_MATE_SCORE / 100
                return 0.0

            cp = score.score()
            if cp is not None:
                return cp / 100.0
            return 0.0

        except Exception as e:
            print(f"Error evaluating position: {e}")
            return None

    def is_available(self) -> bool:
        """Check if the engine is available.

        Returns:
            True if engine is ready to use
        """
        return self.engine is not None

    def quit(self) -> None:
        """Shutdown the engine gracefully."""
        if self.engine is not None:
            try:
                self.engine.quit()
            except Exception:
                pass
            self.engine = None

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.quit()
