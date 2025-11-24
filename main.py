from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, List
from uuid import uuid4, UUID
import json

app = FastAPI(title="Tic Tac Toe API")

# ============================================================================
# Pydantic Models
# ============================================================================


class CreateRoomResponse(BaseModel):
    room_id: str
    player: str


class JoinRoomResponse(BaseModel):
    player: str


class GameStateResponse(BaseModel):
    board: List[Optional[str]]
    status: str
    current_turn: Optional[str]
    winner: Optional[str]
    players_connected: int


class MoveMessage(BaseModel):
    position: int


# ============================================================================
# Game State Data Structure
# ============================================================================


class GameState:
    def __init__(self):
        self.board: List[Optional[str]] = [None] * 9
        self.players: Dict[str, Optional[WebSocket]] = {"X": None, "O": None}
        self.current_turn: str = "X"
        self.status: str = "waiting"  # waiting, active, finished
        self.winner: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "board": self.board,
            "status": self.status,
            "current_turn": self.current_turn,
            "winner": self.winner,
            "players_connected": sum(1 for p in self.players.values() if p is not None),
        }


# ============================================================================
# In-Memory Storage
# ============================================================================

games: Dict[str, GameState] = {}

# ============================================================================
# Game Logic Helpers
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
        if board[combo[0]] and board[combo[0]] == board[combo[1]] == board[combo[2]]:
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
    """End a game and notify players."""
    if room_id in games:
        game = games[room_id]
        game.status = "finished"

        end_message = json.dumps(
            {"type": "game_ended", "reason": reason, "data": game.to_dict()}
        )

        for player_ws in game.players.values():
            if player_ws:
                try:
                    await player_ws.send_text(end_message)
                    await player_ws.close()
                except:
                    pass

        # Clean up the game from memory
        del games[room_id]


# ============================================================================
# REST API Endpoints
# ============================================================================


@app.post("/rooms", response_model=CreateRoomResponse)
async def create_room():
    """Create a new game room and return the room ID."""
    room_id = str(uuid4())
    games[room_id] = GameState()

    return CreateRoomResponse(room_id=room_id, player="X")


@app.get("/rooms/{room_id}", response_model=GameStateResponse)
async def get_room_status(room_id: str):
    """Get the current status of a game room."""
    if room_id not in games:
        raise HTTPException(status_code=404, detail="Room not found")

    game = games[room_id]
    return GameStateResponse(**game.to_dict())


@app.post("/rooms/{room_id}/join", response_model=JoinRoomResponse)
async def join_room(room_id: str):
    """Join an existing game room as player O."""
    if room_id not in games:
        raise HTTPException(status_code=404, detail="Room not found")

    game = games[room_id]

    if game.status != "waiting":
        raise HTTPException(status_code=400, detail="Game is not accepting new players")

    if game.players["O"] is not None:
        raise HTTPException(status_code=400, detail="Room is full")

    return JoinRoomResponse(player="O")


# ============================================================================
# WebSocket Endpoint
# ============================================================================


@app.websocket("/ws/{room_id}/{player}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player: str):
    """WebSocket endpoint for real-time game communication."""

    # Validate room exists
    if room_id not in games:
        await websocket.close(code=1008, reason="Room not found")
        return

    # Validate player symbol
    if player not in ["X", "O"]:
        await websocket.close(code=1008, reason="Invalid player symbol")
        return

    game = games[room_id]

    # Check if player slot is available
    if game.players[player] is not None:
        await websocket.close(code=1008, reason="Player slot already taken")
        return

    # Accept connection
    await websocket.accept()
    game.players[player] = websocket

    # If both players are connected, start the game
    if game.players["X"] and game.players["O"]:
        game.status = "active"

    # Send initial game state
    await broadcast_state(game)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle move message
            if message.get("type") == "move":
                position = message.get("position")

                # Validate it's the player's turn
                if game.current_turn != player:
                    await websocket.send_text(
                        json.dumps({"type": "error", "message": "Not your turn"})
                    )
                    continue

                # Validate game is active
                if game.status != "active":
                    await websocket.send_text(
                        json.dumps({"type": "error", "message": "Game is not active"})
                    )
                    continue

                # Validate move
                if not validate_move(game.board, position):
                    await websocket.send_text(
                        json.dumps({"type": "error", "message": "Invalid move"})
                    )
                    continue

                # Make the move
                game.board[position] = player

                # Check for winner
                winner = check_winner(game.board)
                if winner:
                    game.status = "finished"
                    game.winner = winner
                    await broadcast_state(game)
                    await end_game(room_id, reason="win")
                    break

                # Check for draw
                if check_draw(game.board):
                    game.status = "finished"
                    game.winner = "draw"
                    await broadcast_state(game)
                    await end_game(room_id, reason="draw")
                    break

                # Switch turn
                game.current_turn = "O" if player == "X" else "X"

                # Broadcast updated state
                await broadcast_state(game)

    except WebSocketDisconnect:
        # Handle disconnection - end the game immediately
        game.players[player] = None
        await end_game(room_id, reason="player_disconnected")

    except Exception as e:
        # Handle any other errors
        game.players[player] = None
        await end_game(room_id, reason="error")


# ============================================================================
# Static Files - Mount after all API routes
# ============================================================================

app.mount("/", StaticFiles(directory="static", html=True), name="static")
