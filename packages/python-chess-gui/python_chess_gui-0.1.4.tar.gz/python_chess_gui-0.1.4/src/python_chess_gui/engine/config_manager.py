"""Configuration file management for user settings."""

import json
import os
import platform
import shutil
from pathlib import Path


def _get_config_dir() -> Path:
    """Get the configuration directory path.

    Returns:
        Path to config directory
    """
    if platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"

    config_dir = base / "python-chess-gui"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def _get_config_path() -> Path:
    """Get the configuration file path.

    Returns:
        Path to config.json
    """
    return _get_config_dir() / "config.json"


def load_config() -> dict:
    """Load configuration from file.

    Returns:
        Configuration dictionary
    """
    config_path = _get_config_path()
    if config_path.exists():
        try:
            with open(config_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_config(config: dict) -> None:
    """Save configuration to file.

    Args:
        config: Configuration dictionary to save
    """
    config_path = _get_config_path()
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def get_stockfish_path() -> str | None:
    """Get Stockfish path from config.

    Returns:
        Stockfish path if configured, None otherwise
    """
    config = load_config()
    path = config.get("stockfish_path")
    if path and Path(path).exists():
        return path
    return None


def set_stockfish_path(path: str) -> None:
    """Save Stockfish path to config.

    Args:
        path: Path to Stockfish executable
    """
    config = load_config()
    config["stockfish_path"] = path
    save_config(config)


def find_stockfish() -> str | None:
    """Find Stockfish executable on the system.

    Checks in order:
    1. Saved config file
    2. STOCKFISH_PATH environment variable
    3. System PATH
    4. Common installation locations per platform

    Returns:
        Path to Stockfish executable, or None if not found
    """
    config_path = get_stockfish_path()
    if config_path:
        return config_path

    env_path = os.environ.get("STOCKFISH_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    stockfish_in_path = shutil.which("stockfish")
    if stockfish_in_path:
        return stockfish_in_path

    system = platform.system()

    if system == "Darwin":
        common_paths = [
            "/opt/homebrew/bin/stockfish",
            "/usr/local/bin/stockfish",
        ]
    elif system == "Linux":
        common_paths = [
            "/usr/bin/stockfish",
            "/usr/games/stockfish",
            "/usr/local/bin/stockfish",
        ]
    elif system == "Windows":
        common_paths = [
            Path.home() / "stockfish" / "stockfish.exe",
            Path.home() / "stockfish" / "stockfish-windows-x86-64-avx2.exe",
            "C:/Program Files/Stockfish/stockfish.exe",
            "C:/stockfish/stockfish.exe",
        ]
    else:
        common_paths = []

    for path in common_paths:
        if Path(path).exists():
            return str(path)

    return None
