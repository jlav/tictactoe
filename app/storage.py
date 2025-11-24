"""In-memory storage for game state."""

from typing import Dict

# Import will be done lazily to avoid circular dependency
# games: Dict[str, GameState] = {}
games: Dict[str, any] = {}
