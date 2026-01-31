"""Chess game state management with move history."""

import chess


class GameStateManager:
    """Manages the chess game state, selection, and move history."""

    def __init__(self):
        """Initialize a new game state."""
        self.board = chess.Board()
        self.selected_square: chess.Square | None = None
        self.move_history: list[chess.Move] = []
        self.position_history: list[str] = [self.board.fen()]

    def reset(self) -> None:
        """Reset the game to initial position."""
        self.board = chess.Board()
        self.selected_square = None
        self.move_history = []
        self.position_history = [self.board.fen()]

    def select_square(self, square: chess.Square) -> list[chess.Move]:
        """Select a square on the board.

        Args:
            square: The square to select

        Returns:
            List of legal moves from this square (empty if no piece or not player's turn)
        """
        piece = self.board.piece_at(square)

        if piece is not None and piece.color == self.board.turn:
            self.selected_square = square
            return self.get_legal_moves_from_square(square)

        return []

    def get_legal_moves_from_square(self, square: chess.Square) -> list[chess.Move]:
        """Get all legal moves from a specific square.

        Args:
            square: The source square

        Returns:
            List of legal moves from this square
        """
        return [move for move in self.board.legal_moves if move.from_square == square]

    def try_move(self, from_square: chess.Square, to_square: chess.Square) -> chess.Move | None:
        """Attempt to make a move.

        Args:
            from_square: Source square
            to_square: Destination square

        Returns:
            The move if successful, None if illegal
        """
        piece = self.board.piece_at(from_square)
        promotion = None

        if piece is not None and piece.piece_type == chess.PAWN:
            if piece.color == chess.WHITE and chess.square_rank(to_square) == 7:
                promotion = chess.QUEEN
            elif piece.color == chess.BLACK and chess.square_rank(to_square) == 0:
                promotion = chess.QUEEN

        move = chess.Move(from_square, to_square, promotion=promotion)

        if move in self.board.legal_moves:
            self.board.push(move)
            self.move_history.append(move)
            self.position_history.append(self.board.fen())
            self.selected_square = None
            return move

        move_no_promo = chess.Move(from_square, to_square)
        if move_no_promo in self.board.legal_moves:
            self.board.push(move_no_promo)
            self.move_history.append(move_no_promo)
            self.position_history.append(self.board.fen())
            self.selected_square = None
            return move_no_promo

        return None

    def make_move(self, move: chess.Move) -> bool:
        """Make a specific move (used for AI moves).

        Args:
            move: The move to make

        Returns:
            True if move was made, False if illegal
        """
        if move in self.board.legal_moves:
            self.board.push(move)
            self.move_history.append(move)
            self.position_history.append(self.board.fen())
            self.selected_square = None
            return True
        return False

    def undo_move(self) -> bool:
        """Undo the last move.

        Returns:
            True if a move was undone, False if no moves to undo
        """
        if len(self.move_history) == 0:
            return False

        self.board.pop()
        self.move_history.pop()
        self.position_history.pop()
        self.selected_square = None
        return True

    def undo_move_pair(self) -> bool:
        """Undo both the AI's and player's last moves.

        Returns:
            True if moves were undone, False if not enough moves
        """
        if len(self.move_history) < 2:
            return self.undo_move()

        self.undo_move()
        self.undo_move()
        return True

    def clear_selection(self) -> None:
        """Clear the current selection."""
        self.selected_square = None

    def get_last_move(self) -> chess.Move | None:
        """Get the last move made.

        Returns:
            The last move, or None if no moves made
        """
        if self.move_history:
            return self.move_history[-1]
        return None

    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.board.is_game_over()

    def get_game_result(self) -> str:
        """Get the game result string.

        Returns:
            Result description (checkmate, stalemate, etc.)
        """
        if self.board.is_checkmate():
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            return f"Checkmate! {winner} wins"
        elif self.board.is_stalemate():
            return "Stalemate - Draw"
        elif self.board.is_insufficient_material():
            return "Insufficient material - Draw"
        elif self.board.is_fifty_moves():
            return "50-move rule - Draw"
        elif self.board.is_repetition():
            return "Threefold repetition - Draw"
        return ""

    def get_turn_text(self) -> str:
        """Get text describing whose turn it is.

        Returns:
            Turn description string
        """
        if self.is_game_over():
            return self.get_game_result()

        turn = "White" if self.board.turn == chess.WHITE else "Black"
        check_text = " (Check!)" if self.board.is_check() else ""
        return f"{turn} to move{check_text}"
