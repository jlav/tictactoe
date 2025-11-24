"""Game state management and logic."""

from fastapi import WebSocket
from typing import Optional, Dict, List
import json

from .storage import games


class GameState:
    """Represents the state of a tic tac toe game."""

    def __init__(self):
        self.board: List[Optional[str]] = [None] * 9
        self.players: Dict[str, Optional[WebSocket]] = {"X": None, "O": None}
        self.current_turn: str = "X"
        self.status: str = "waiting"  # waiting, active, finished
        self.winner: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert game state to dictionary for JSON serialization."""
        return {
            "board": self.board,
            "status": self.status,
            "current_turn": self.current_turn,
            "winner": self.winner,
            "players_connected": sum(
                1 for p in self.players.values() if p is not None
            ),
        }

    def reset(self):
        """Reset the game state for a new game, keeping the same players."""
        self.board = [None] * 9
        self.current_turn = "X"
        self.winner = None
        # Only set to active if both players are still connected
        if self.players["X"] and self.players["O"]:
            self.status = "active"
        else:
            self.status = "waiting"


# ============================================================================
# Game Logic Functions
# ============================================================================


def check_winner(board: List[Optional[str]]) -> Optional[str]:
    """Check if there's a winner. Returns 'X', 'O', or None."""
    # Define winning combinations (rows, columns, diagonals)
    winning_combos = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],  # rows
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],  # columns
        [0, 4, 8],
        [2, 4, 6],  # diagonals
    ]

    for combo in winning_combos:
        if (
            board[combo[0]]
            and board[combo[0]] == board[combo[1]] == board[combo[2]]
        ):
            return board[combo[0]]

    return None


def check_draw(board: List[Optional[str]]) -> bool:
    """Check if the board is full (draw condition)."""
    return all(cell is not None for cell in board)


def validate_move(board: List[Optional[str]], position: int) -> bool:
    """Validate if a move is legal."""
    if position < 0 or position > 8:
        return False
    return board[position] is None


async def broadcast_state(game: GameState):
    """Send current game state to all connected players."""
    state_message = json.dumps({"type": "game_state", "data": game.to_dict()})

    for player_ws in game.players.values():
        if player_ws:
            try:
                await player_ws.send_text(state_message)
            except:
                pass  # Connection might be closed


async def end_game(room_id: str, reason: str = "disconnection"):
    """End a game and notify players.

    For win/draw: Keep connections alive and room in memory for potential restart.
    For disconnection/error: Close connections and clean up room.
    """
    if room_id in games:
        game = games[room_id]
        game.status = "finished"

        end_message = json.dumps(
            {"type": "game_ended", "reason": reason, "data": game.to_dict()}
        )

        # Determine if we should keep the game alive (for restart)
        keep_alive = reason in ["win", "draw"]

        for player_ws in game.players.values():
            if player_ws:
                try:
                    await player_ws.send_text(end_message)
                    # Only close connections for disconnection/error
                    if not keep_alive:
                        await player_ws.close()
                except:
                    pass

        # Only clean up room if not keeping alive for restart
        if not keep_alive:
            del games[room_id]
