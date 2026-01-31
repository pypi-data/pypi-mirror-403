"""Python Chess GUI - A chess application with pygame interface."""

__version__ = "0.1.4"

from python_chess_gui.main import main, ChessApplication
from python_chess_gui.layout_manager import LayoutManager

__all__ = [
    "main",
    "ChessApplication",
    "LayoutManager",
]
