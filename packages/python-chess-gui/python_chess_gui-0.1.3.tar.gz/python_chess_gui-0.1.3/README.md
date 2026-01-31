# Python Chess GUI

![Demo](chess_demo.gif)

A Python chess application with a graphical user interface built using pygame and python-chess library, featuring player vs Stockfish AI gameplay.

## Features

- Player vs Stockfish AI gameplay
- Color selection (play as White or Black)
- Adjustable AI difficulty (Level 1-5)
- Move takeback (undo)
- Hint system (get Stockfish's suggested move)
- Real-time evaluation bar
- Visual highlights for legal moves, last move, and check

## Installation

### macOS

```bash
# Install Stockfish
brew install stockfish

# Install pipx and the game
brew install pipx
pipx ensurepath
source ~/.zprofile
pipx install python-chess-gui

# Run the game
chess-gui
```

### Debian/Ubuntu

```bash
# Install Stockfish
sudo apt install stockfish

# Install pipx and the game
sudo apt install pipx
pipx ensurepath
source ~/.bashrc
pipx install python-chess-gui

# Run the game
chess-gui
```

## Controls

- **Mouse click**: Select piece / move piece / menu selection
- **H**: Get a hint (Stockfish's suggested move)
- **Z**: Undo last move
- **N**: New game (return to menu)
- **Q / Escape**: Quit

## Development

Clone and run from source:

```bash
git clone git@github.com:Bobain/python-chess-gui.git
cd python-chess-gui
pip install -e .
chess-gui
```

## License

MIT License
