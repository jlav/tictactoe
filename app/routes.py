"""REST API endpoints for room management."""

from fastapi import APIRouter, HTTPException
from uuid import uuid4

from .models import CreateRoomResponse, JoinRoomResponse, GameStateResponse
from .game import GameState
from .storage import games

router = APIRouter()


@router.post("/rooms", response_model=CreateRoomResponse)
async def create_room():
    """Create a new game room and return the room ID."""
    room_id = str(uuid4())
    games[room_id] = GameState()

    return CreateRoomResponse(room_id=room_id, player="X")


@router.get("/rooms/{room_id}", response_model=GameStateResponse)
async def get_room_status(room_id: str):
    """Get the current status of a game room."""
    if room_id not in games:
        raise HTTPException(status_code=404, detail="Room not found")

    game = games[room_id]
    return GameStateResponse(**game.to_dict())


@router.post("/rooms/{room_id}/join", response_model=JoinRoomResponse)
async def join_room(room_id: str):
    """Join an existing game room as player O."""
    if room_id not in games:
        raise HTTPException(status_code=404, detail="Room not found")

    game = games[room_id]

    if game.status != "waiting":
        raise HTTPException(
            status_code=400, detail="Game is not accepting new players"
        )

    if game.players["O"] is not None:
        raise HTTPException(status_code=400, detail="Room is full")

    return JoinRoomResponse(player="O")
