"""Application configuration and paths."""
from __future__ import annotations

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# When frozen (PyInstaller), resources are extracted to sys._MEIPASS.
RESOURCE_DIR = sys._MEIPASS if getattr(sys, "frozen", False) else BASE_DIR

# Bundled read-only resources
EXERCISES_JSON = os.path.join(RESOURCE_DIR, "data", "exercises.json")
PUZZLES_CSV = os.path.join(RESOURCE_DIR, "lichess_db_puzzle.csv")

# Repetition-method parameters
CYCLES = 7
DEFAULT_SESSION_SIZE = 60
MAX_REPEAT_ROUNDS = 3
PROBLEM_THRESHOLD = 2  # misses before an exercise becomes a "problem"

# Difficulty bands (Lichess puzzle rating)
EASY_RATING_MAX = 1000
INTERMEDIATE_RATING_MAX = 1500


def _user_data_dir() -> str:
    """Writable directory for progress, sounds and generated assets.

    Packaged apps must not write next to their own files (an AppImage mount is
    read-only), so user data lives in the platform data directory instead.
    """
    if getattr(sys, "frozen", False):
        if sys.platform == "win32":
            base = os.environ.get("LOCALAPPDATA") \
                or os.path.join(os.path.expanduser("~"), "AppData", "Local")
        else:
            base = os.environ.get("XDG_DATA_HOME") \
                or os.path.join(os.path.expanduser("~"), ".local", "share")
        return os.path.join(base, "ChessPractice")
    return os.path.join(BASE_DIR, "data")


DATA_DIR = _user_data_dir()
DB_PATH = os.path.join(DATA_DIR, "chess_practice.db")


def total_exercises() -> int:
    """Number of exercises in the data file (loaded lazily to avoid cycles)."""
    import json

    with open(EXERCISES_JSON) as fh:
        return len(json.load(fh))
