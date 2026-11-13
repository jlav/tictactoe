"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel, field_validator
from typing import Dict, Optional, List


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


class ThemeSymbols(BaseModel):
    X: str
    O: str  # noqa: E741 - keyed by the board values "X" and "O"


class ThemeIcons(BaseModel):
    copy_link: str
    copy_success: str
    celebrate: str


class ThemeText(BaseModel):
    title: str
    subtitle: str
    waiting: str
    your_turn: str
    opponent_turn: str
    win_title: str
    win_message: str
    lose_title: str
    lose_message: str
    draw_title: str
    draw_message: str


class Theme(BaseModel):
    id: str
    name: str
    symbols: ThemeSymbols
    icons: ThemeIcons
    text: ThemeText
    colors: Dict[str, str]

    @field_validator("colors")
    @classmethod
    def validate_css_variables(cls, colors: Dict[str, str]) -> Dict[str, str]:
        """Colors are applied verbatim as CSS custom properties."""
        for name in colors:
            if not name.startswith("--"):
                raise ValueError(
                    f"Color key '{name}' must be a CSS custom property "
                    "starting with '--'"
                )
        return colors


class ThemesResponse(BaseModel):
    default: str
    themes: List[Theme]
