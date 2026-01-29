"""Data package for groundskeeper.

This package contains static data files such as agent configurations.
"""

from pathlib import Path

# Export the data directory path for easy access
DATA_DIR = Path(__file__).parent
AGENTS_DIR = DATA_DIR / "agents"

__all__ = ["AGENTS_DIR", "DATA_DIR"]
