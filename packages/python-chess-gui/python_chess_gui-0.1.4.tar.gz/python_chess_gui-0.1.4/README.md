# Python Chess GUI

![Demo](chess_demo.gif)

A Python chess application with a graphical user interface built using pygame and python-chess library, featuring player vs Stockfish AI gameplay.

## Features

- Player vs Stockfish AI gameplay
- Color selection (play as White or Black)
- Adjustable AI difficulty (Level 1-5)
- Move takeback (undo)
- Hint system and real-time evaluation bar (computed at chosen difficulty level)
- Visual highlights for legal moves, last move, and check

## Installation

### macOS

```bash
# Install Stockfish and Python 3.12
brew install stockfish python@3.12

# Install pipx and the game
brew install pipx
pipx ensurepath
source ~/.zprofile
pipx install python-chess-gui --python python3.12

# Run the game
chess-gui
```

### Debian/Ubuntu

```bash
# Install Stockfish and Python 3.12
sudo apt install stockfish python3.12

# Install pipx and the game
sudo apt install pipx
pipx ensurepath
source ~/.bashrc
pipx install python-chess-gui --python python3.12

# Run the game
chess-gui
```

## Controls

- **Mouse click**: Select piece / move piece / menu selection
- **H**: Get a hint (Stockfish's suggested move)
- **Z**: Undo last move
- **N**: New game (return to menu)
- **Q / Escape**: Quit

## License

MIT License
