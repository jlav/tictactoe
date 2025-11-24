"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel
from typing import Optional, List


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
