"""Built-in theme definitions.

A theme customizes the symbols, text, icons and colors of the frontend.
The board is always stored server-side as "X"/"O"; a theme only changes how
those values are presented.
"""

from typing import List, Optional

from .models import Theme, ThemeIcons, ThemeSymbols, ThemeText

DEFAULT_THEME_ID = "classic"

THEMES: List[Theme] = [
    Theme(
        id="classic",
        name="Classic",
        symbols=ThemeSymbols(X="X", O="O"),
        icons=ThemeIcons(copy_link="📋", copy_success="✓", celebrate="🎉"),
        text=ThemeText(
            title="Tic Tac Toe",
            subtitle="Online Multiplayer",
            waiting="Waiting for opponent...",
            your_turn="Your turn!",
            opponent_turn="Opponent's turn",
            win_title="You Win!",
            win_message="Congratulations!",
            lose_title="You Lose",
            lose_message="Better luck next time!",
            draw_title="It's a Draw!",
            draw_message="Good game!",
        ),
        colors={
            "--primary-color": "#4A90E2",
            "--primary-dark": "#357ABD",
            "--secondary-color": "#50E3C2",
            "--background": "#F5F7FA",
            "--surface": "#FFFFFF",
            "--text-primary": "#2C3E50",
            "--text-secondary": "#7F8C8D",
            "--border-color": "#E1E8ED",
            "--success": "#2ECC71",
            "--warning": "#F39C12",
            "--danger": "#E74C3C",
            "--player-x": "#4A90E2",
            "--player-o": "#E74C3C",
            "--body-background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        },
    ),
    Theme(
        id="farmyard",
        name="Farmyard",
        symbols=ThemeSymbols(X="🐄", O="🐓"),
        icons=ThemeIcons(copy_link="🚜", copy_success="✓", celebrate="🌻"),
        text=ThemeText(
            title="Barnyard Tic Tac Toe",
            subtitle="Cows vs. Roosters",
            waiting="Waiting for a farmhand...",
            your_turn="Your turn, farmer!",
            opponent_turn="The other farmer is thinking",
            win_title="You Win!",
            win_message="The whole barn is cheering!",
            lose_title="You Lose",
            lose_message="Better luck at the next harvest!",
            draw_title="It's a Draw!",
            draw_message="Everyone back to the barn.",
        ),
        colors={
            "--primary-color": "#B5451B",
            "--primary-dark": "#8A3414",
            "--secondary-color": "#E8B931",
            "--background": "#FBF3DE",
            "--surface": "#FFFBF0",
            "--text-primary": "#4A3220",
            "--text-secondary": "#8C7355",
            "--border-color": "#D8C49A",
            "--success": "#6B9B37",
            "--warning": "#E8A33D",
            "--danger": "#B5451B",
            "--player-x": "#8C5A2B",
            "--player-o": "#B5451B",
            "--body-background": "linear-gradient(135deg, #8FC045 0%, #4F8A3D 100%)",
        },
    ),
]


def get_themes() -> List[Theme]:
    """Return every available theme."""
    return THEMES


def get_theme(theme_id: str) -> Optional[Theme]:
    """Return a theme by ID, or None if it does not exist."""
    for theme in THEMES:
        if theme.id == theme_id:
            return theme
    return None
