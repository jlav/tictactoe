# AGENTS.md - Agent Onboarding Guide

This document helps AI agents understand the codebase structure and work effectively in this repository.

## Project Overview

**Name:** Tic Tac Toe Online Multiplayer
**Tech Stack:** FastAPI, WebSockets, HTML/CSS/JavaScript
**Purpose:** Real-time 2-player tic tac toe game with room-based multiplayer
**Python Version:** 3.14+
**Package Manager:** uv

## Architecture

### Backend (FastAPI)
- **Framework:** FastAPI with async/await
- **Real-time Communication:** WebSockets for bidirectional game updates
- **Storage:** In-memory dictionary (no database)
- **API Style:** REST for room management, WebSocket for gameplay

### Frontend (Static)
- **Vanilla JavaScript** - No frameworks
- **Modern CSS** - Flexbox/Grid layouts
- **WebSocket Client** - Direct browser WebSocket API

### Data Flow
```
Client → POST /rooms → Server creates room → Returns room_id
Client → WS /ws/{room_id}/{player} → Connects to game
Client → Sends move → Server validates → Broadcasts to both players
```

## Project Structure

```
tictactoe/
├── app/                    # Main application package
│   ├── __init__.py        # Package marker
│   ├── models.py          # Pydantic schemas (request/response)
│   ├── game.py            # GameState class + game logic
│   ├── themes.py          # Built-in theme definitions
│   ├── storage.py         # In-memory games dictionary
│   ├── routes.py          # REST API endpoints (APIRouter)
│   └── websocket.py       # WebSocket handler (APIRouter)
├── static/                 # Frontend files
│   ├── index.html         # Main game page
│   ├── style.css          # Modern/minimalist styling
│   └── script.js          # Game logic + WebSocket client
├── main.py                 # FastAPI app + router registration
├── test_main.py            # Pytest test suite
├── pyproject.toml          # Dependencies and config
└── AGENTS.md               # This file
```

## Key Files & Responsibilities

### Backend

**main.py** (~15 lines)
- Creates FastAPI app instance
- Includes API and WebSocket routers
- Mounts static files at `/`

**app/models.py** (~25 lines)
- `CreateRoomResponse` - Room creation response
- `JoinRoomResponse` - Join room response
- `GameStateResponse` - Current game state
- `MoveMessage` - Move request schema

**app/game.py** (~130 lines)
- `GameState` class - Manages board, players, turn, status, winner
- `check_winner()` - Detects winning combinations
- `check_draw()` - Checks for draw condition
- `validate_move()` - Validates move legality
- `broadcast_state()` - Sends game state to all players
- `end_game()` - Handles game termination

**app/themes.py** (~100 lines)
- `THEMES` - List of built-in themes ("classic", "farmyard")
- `DEFAULT_THEME_ID` - Theme used when the player has not chosen one
- `get_themes()` / `get_theme(theme_id)` - Theme lookup

**app/storage.py** (~5 lines)
- `games` - Dict[str, GameState] for active games

**app/routes.py** (~70 lines)
- `POST /rooms` - Create new game room
- `GET /rooms/{room_id}` - Get room status
- `POST /rooms/{room_id}/join` - Join existing room
- `GET /themes` - List themes and the default theme ID
- `GET /themes/{theme_id}` - Get a single theme

**app/websocket.py** (~120 lines)
- `WS /ws/{room_id}/{player}` - WebSocket endpoint
- Handles: connection, moves, restart, disconnection
- Message types: "move", "restart"

### Frontend

**static/index.html**
- Theme dropdown (top right)
- Game board (3x3 grid)
- Room info display
- Player role indicator
- Game over modal with restart/new game buttons

**static/style.css**
- Modern/minimalist design
- Themeable: all colors come from CSS custom properties that themes override
- Responsive grid layout
- Animations for moves and game states
- Color palette: blues/greens/grays

**static/script.js**
- Theme loading, switching and persistence (localStorage)
- Room creation/joining logic
- WebSocket connection management
- Move validation and sending
- Game state updates from server
- UI updates (board, status, modal)

## Running the Project

### Start Development Server
```bash
uv run uvicorn main:app --reload --port 8000
```

### Run Tests
```bash
# All tests
uv run pytest test_main.py -v

# Specific test
uv run pytest test_main.py::test_full_game_round -v
```

### Access Application
- Frontend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Testing

### Test File Structure
- Location: `test_main.py` (root directory)
- Framework: pytest with pytest-asyncio
- Test client: FastAPI TestClient

### Import Pattern
```python
from main import app
from app.storage import games
from app.game import GameState, check_winner, check_draw, validate_move
```

### Test Categories
1. **Game Logic** - Winner detection, draw detection, move validation
2. **REST API** - Room creation, joining, status
3. **WebSocket** - Connections, moves, full game simulations
4. **Edge Cases** - Invalid moves, disconnections, concurrent games

## Important Patterns

### APIRouter Usage
All endpoints use FastAPI's APIRouter for modularity:
```python
router = APIRouter()

@router.post("/rooms")
async def create_room():
    # ...
```

Routers are included in main.py:
```python
app.include_router(api_router)
app.include_router(ws_router)
```

### WebSocket Message Format
**From Client:**
```json
{"type": "move", "position": 0-8}
{"type": "restart"}
```

**From Server:**
```json
{"type": "game_state", "data": {board, status, current_turn, winner, players_connected}}
{"type": "game_ended", "reason": "win|draw|player_disconnected", "data": {...}}
{"type": "error", "message": "error description"}
```

### Game State Lifecycle
1. `waiting` - Room created, waiting for 2nd player
2. `active` - Both players connected, game in progress
3. `finished` - Game ended (win/draw/disconnect)

### Room Management
- Room IDs: UUID v4
- Player X: Room creator
- Player O: Room joiner
- Cleanup: Rooms deleted on disconnection, kept on win/draw for restart

## Common Tasks

### Adding a New REST Endpoint
1. Define Pydantic models in `app/models.py` if needed
2. Add endpoint to `app/routes.py` using `@router` decorator
3. Import from `app.storage` and `app.game` as needed
4. No changes needed to `main.py` (router auto-includes)

### Modifying Game Logic
1. Update logic in `app/game.py`
2. Update tests in `test_main.py`
3. No changes needed to routes/websocket (unless API changes)

### Adding a New Theme
1. Append a `Theme` to `THEMES` in `app/themes.py`
2. Define the same CSS custom properties as the other themes (keys must start with `--`)
3. No frontend changes needed - the dropdown is built from `GET /themes`

### Adding New WebSocket Message Type
1. Add handler in `app/websocket.py` under message type checks
2. Define message structure in docstring/comments
3. Update frontend `script.js` to send/receive new type
4. Add test case in `test_main.py`

### Frontend Changes
- HTML: `static/index.html`
- CSS: `static/style.css`
- JavaScript: `static/script.js`
- No build step required - changes are instant

## Code Conventions

### Import Style
```python
# Absolute imports from app package
from app.models import CreateRoomResponse
from app.game import GameState, check_winner
from app.storage import games

# NOT relative imports
# from .models import ...  # Don't use in main.py or tests
```

### Module Organization
- Each file has a single, clear responsibility
- Game logic separate from API endpoints
- Models separate from business logic
- Storage is a simple shared module

### Async/Await
- All route handlers are `async def`
- WebSocket handlers use `async/await` for I/O
- Game logic functions can be sync (check_winner) or async (broadcast_state)

### Error Handling
- REST: Raise `HTTPException` with appropriate status codes
- WebSocket: Send JSON error messages, don't raise
- Game logic: Return None or False for invalid operations

## Game Rules Implementation

### Board Representation
- List of 9 elements (indices 0-8)
- Values: None (empty), "X", "O"
- Position mapping:
  ```
  0 | 1 | 2
  ---------
  3 | 4 | 5
  ---------
  6 | 7 | 8
  ```

### Win Conditions
- 8 winning combinations checked (3 rows, 3 columns, 2 diagonals)
- First player to get 3 in a row wins
- Implemented in `check_winner()` function

### Turn Management
- X always goes first
- Alternates after each valid move
- Enforced server-side in WebSocket handler

### Game Restart
- Available after win or draw (not disconnection)
- Resets board and turn, keeps same players
- Both players receive updated state automatically

## Dependencies

### Production
- `fastapi[standard]` - Web framework + WebSocket support
- `uvicorn` - ASGI server
- `pydantic` - Data validation (included with FastAPI)

### Development
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `httpx` - HTTP client for tests (included with FastAPI TestClient)

## Notes for Agents

1. **No Database:** All state is in-memory. Server restart = all games lost.
2. **No Authentication:** Players are identified only by room_id and symbol (X/O).
3. **Static Files Last:** The static files mount must come after API routes in `main.py`.
4. **Test Imports:** Always import from `app.*` modules, not from `main` (except `app` object).
5. **WebSocket Lifecycle:** Games are cleaned up on disconnection but kept on win/draw for restart.
6. **UUID Room IDs:** Auto-generated, cannot be custom. Prevents collision, enables sharing.
7. **Query Parameter Rooms:** Frontend uses `?room=uuid` for shareable links.
8. **Themes Are Presentation Only:** The board is always stored as "X"/"O" server-side; themes only change how those values are displayed.

## Troubleshooting

### Tests Failing
- Check imports are from `app.*` modules
- Ensure `games` dict is cleared between tests (autouse fixture)
- Verify WebSocket message consumption (broadcast creates multiple messages)

### WebSocket Not Connecting
- Verify room exists before connecting
- Check player symbol is "X" or "O"
- Ensure slot not already taken

### Static Files Not Serving
- Confirm mount is last in `main.py`
- Check `static/` directory exists
- Verify files have correct names (index.html, style.css, script.js)

## Future Enhancements Ideas

1. Persistent storage (database)
2. Player authentication
3. Game history/statistics
4. Spectator mode
5. Private rooms with passwords
6. AI opponent
7. Multiple board sizes
8. Game replays

---

**Last Updated:** After code refactoring into modular structure
**Maintained By:** AI Agents working on this project
