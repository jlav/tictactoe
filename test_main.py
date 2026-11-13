import pytest
from fastapi.testclient import TestClient
from main import app
from app.storage import games
from app.game import GameState, check_winner, check_draw, validate_move
from app.models import Theme
from app.themes import DEFAULT_THEME_ID, get_theme, get_themes
from pydantic import ValidationError
import json

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_games():
    """Clear the games dictionary before each test."""
    games.clear()
    yield
    games.clear()


# ============================================================================
# Test Game Logic Helpers
# ============================================================================


def test_check_winner_horizontal():
    """Test horizontal win detection."""
    board = ["X", "X", "X", None, None, None, None, None, None]
    assert check_winner(board) == "X"

    board = [None, None, None, "O", "O", "O", None, None, None]
    assert check_winner(board) == "O"


def test_check_winner_vertical():
    """Test vertical win detection."""
    board = ["X", None, None, "X", None, None, "X", None, None]
    assert check_winner(board) == "X"

    board = [None, "O", None, None, "O", None, None, "O", None]
    assert check_winner(board) == "O"


def test_check_winner_diagonal():
    """Test diagonal win detection."""
    board = ["X", None, None, None, "X", None, None, None, "X"]
    assert check_winner(board) == "X"

    board = [None, None, "O", None, "O", None, "O", None, None]
    assert check_winner(board) == "O"


def test_check_winner_no_winner():
    """Test no winner condition."""
    board = ["X", "O", "X", "O", "X", "O", "O", "X", "O"]
    assert check_winner(board) is None


def test_check_draw():
    """Test draw detection."""
    board = ["X", "O", "X", "O", "X", "O", "O", "X", "O"]
    assert check_draw(board) is True

    board = ["X", "O", "X", None, "X", "O", "O", "X", "O"]
    assert check_draw(board) is False


def test_validate_move():
    """Test move validation."""
    board = [None, "X", None, None, None, None, None, None, None]

    assert validate_move(board, 0) is True
    assert validate_move(board, 1) is False  # Already occupied
    assert validate_move(board, 9) is False  # Out of bounds
    assert validate_move(board, -1) is False  # Out of bounds


# ============================================================================
# Test REST Endpoints
# ============================================================================


def test_root():
    """Test root endpoint serves static HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Tic Tac Toe" in response.text


def test_create_room():
    """Test room creation."""
    response = client.post("/rooms")
    assert response.status_code == 200

    data = response.json()
    assert "room_id" in data
    assert data["player"] == "X"

    # Verify room exists in storage
    room_id = data["room_id"]
    assert room_id in games


def test_get_room_status():
    """Test getting room status."""
    # Create a room first
    create_response = client.post("/rooms")
    room_id = create_response.json()["room_id"]

    # Get room status
    response = client.get(f"/rooms/{room_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "waiting"
    assert data["current_turn"] == "X"
    assert data["winner"] is None
    assert data["players_connected"] == 0
    assert len(data["board"]) == 9


def test_get_room_status_not_found():
    """Test getting status of non-existent room."""
    response = client.get("/rooms/invalid-room-id")
    assert response.status_code == 404


def test_join_room():
    """Test joining a room."""
    # Create a room first
    create_response = client.post("/rooms")
    room_id = create_response.json()["room_id"]

    # Join the room
    response = client.post(f"/rooms/{room_id}/join")
    assert response.status_code == 200
    assert response.json()["player"] == "O"


def test_join_room_not_found():
    """Test joining a non-existent room."""
    response = client.post("/rooms/invalid-room-id/join")
    assert response.status_code == 404


# ============================================================================
# Test WebSocket Connection
# ============================================================================


def test_websocket_connection():
    """Test basic WebSocket connection."""
    # Create a room
    create_response = client.post("/rooms")
    room_id = create_response.json()["room_id"]

    # Connect as player X
    with client.websocket_connect(f"/ws/{room_id}/X") as websocket:
        # Should receive initial game state
        data = websocket.receive_text()
        message = json.loads(data)

        assert message["type"] == "game_state"
        assert message["data"]["status"] == "waiting"
        assert message["data"]["current_turn"] == "X"


def test_websocket_invalid_room():
    """Test WebSocket connection to invalid room."""
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/invalid-room/X") as websocket:
            pass


def test_websocket_invalid_player():
    """Test WebSocket connection with invalid player symbol."""
    create_response = client.post("/rooms")
    room_id = create_response.json()["room_id"]

    with pytest.raises(Exception):
        with client.websocket_connect(f"/ws/{room_id}/Z") as websocket:
            pass


# ============================================================================
# Test Full Game Simulation
# ============================================================================


def test_full_game_round():
    """
    Simulate a complete game from start to finish.

    Game board positions:
    0 | 1 | 2
    ---------
    3 | 4 | 5
    ---------
    6 | 7 | 8

    Moves:
    X plays: 0, 1, 2 (wins horizontally)
    O plays: 3, 4
    """
    # Create a room
    create_response = client.post("/rooms")
    room_id = create_response.json()["room_id"]

    # Connect both players
    with (
        client.websocket_connect(f"/ws/{room_id}/X") as ws_x,
        client.websocket_connect(f"/ws/{room_id}/O") as ws_o,
    ):
        # Player X receives initial state (waiting)
        msg_x = json.loads(ws_x.receive_text())
        assert msg_x["data"]["status"] == "waiting"

        # Player O receives initial state (active, since both players now connected)
        msg_o = json.loads(ws_o.receive_text())
        assert msg_o["data"]["status"] == "active"

        # Player X also receives the broadcast when O joins (game becomes active)
        msg_x_active = json.loads(ws_x.receive_text())
        assert msg_x_active["data"]["status"] == "active"

        # Move 1: X plays position 0
        ws_x.send_text(json.dumps({"type": "move", "position": 0}))

        # Both players receive updated state
        state_x = json.loads(ws_x.receive_text())
        state_o = json.loads(ws_o.receive_text())

        assert state_x["data"]["board"][0] == "X"
        assert state_x["data"]["current_turn"] == "O"
        assert state_o["data"]["board"][0] == "X"

        # Move 2: O plays position 3
        ws_o.send_text(json.dumps({"type": "move", "position": 3}))

        state_x = json.loads(ws_x.receive_text())
        state_o = json.loads(ws_o.receive_text())

        assert state_x["data"]["board"][3] == "O"
        assert state_x["data"]["current_turn"] == "X"

        # Move 3: X plays position 1
        ws_x.send_text(json.dumps({"type": "move", "position": 1}))

        state_x = json.loads(ws_x.receive_text())
        state_o = json.loads(ws_o.receive_text())

        assert state_x["data"]["board"][1] == "X"
        assert state_x["data"]["current_turn"] == "O"

        # Move 4: O plays position 4
        ws_o.send_text(json.dumps({"type": "move", "position": 4}))

        state_x = json.loads(ws_x.receive_text())
        state_o = json.loads(ws_o.receive_text())

        assert state_x["data"]["board"][4] == "O"
        assert state_x["data"]["current_turn"] == "X"

        # Move 5: X plays position 2 (winning move)
        ws_x.send_text(json.dumps({"type": "move", "position": 2}))

        # Both players receive final state
        state_x = json.loads(ws_x.receive_text())
        state_o = json.loads(ws_o.receive_text())

        assert state_x["data"]["board"][2] == "X"
        assert state_x["data"]["status"] == "finished"
        assert state_x["data"]["winner"] == "X"

        # Both players receive game ended message
        end_x = json.loads(ws_x.receive_text())
        end_o = json.loads(ws_o.receive_text())

        assert end_x["type"] == "game_ended"
        assert end_x["reason"] == "win"
        assert end_o["type"] == "game_ended"


def test_invalid_move_not_your_turn():
    """Test that players can't move when it's not their turn."""
    create_response = client.post("/rooms")
    room_id = create_response.json()["room_id"]

    with (
        client.websocket_connect(f"/ws/{room_id}/X") as ws_x,
        client.websocket_connect(f"/ws/{room_id}/O") as ws_o,
    ):
        # Clear initial messages
        ws_x.receive_text()  # X's initial state (waiting)
        ws_o.receive_text()  # O's initial state (active)
        ws_x.receive_text()  # X's broadcast when O joins (active)

        # O tries to move (but it's X's turn)
        ws_o.send_text(json.dumps({"type": "move", "position": 0}))

        error_msg = json.loads(ws_o.receive_text())
        assert error_msg["type"] == "error"
        assert "Not your turn" in error_msg["message"]


def test_invalid_move_position_occupied():
    """Test that players can't play on an occupied position."""
    create_response = client.post("/rooms")
    room_id = create_response.json()["room_id"]

    with (
        client.websocket_connect(f"/ws/{room_id}/X") as ws_x,
        client.websocket_connect(f"/ws/{room_id}/O") as ws_o,
    ):
        # Clear initial messages
        ws_x.receive_text()  # X's initial state (waiting)
        ws_o.receive_text()  # O's initial state (active)
        ws_x.receive_text()  # X's broadcast when O joins (active)

        # X plays position 0
        ws_x.send_text(json.dumps({"type": "move", "position": 0}))
        ws_x.receive_text()
        ws_o.receive_text()

        # O tries to play the same position
        ws_o.send_text(json.dumps({"type": "move", "position": 0}))

        error_msg = json.loads(ws_o.receive_text())
        assert error_msg["type"] == "error"
        assert "Invalid move" in error_msg["message"]


def test_game_draw():
    """Test a game that ends in a draw."""
    create_response = client.post("/rooms")
    room_id = create_response.json()["room_id"]

    with (
        client.websocket_connect(f"/ws/{room_id}/X") as ws_x,
        client.websocket_connect(f"/ws/{room_id}/O") as ws_o,
    ):
        # Clear initial messages
        ws_x.receive_text()  # X's initial state (waiting)
        ws_o.receive_text()  # O's initial state (active)
        ws_x.receive_text()  # X's broadcast when O joins (active)

        # Play a sequence that leads to a draw:
        # X O X
        # X O O
        # O X X
        moves = [
            (ws_x, 0),
            (ws_o, 1),
            (ws_x, 2),  # Row 1: X O X
            (ws_o, 5),
            (ws_x, 3),
            (ws_o, 4),  # Row 2: X O O
            (ws_x, 7),
            (ws_o, 6),
            (ws_x, 8),  # Row 3: O X X (draw)
        ]

        for websocket, position in moves[:-1]:
            websocket.send_text(json.dumps({"type": "move", "position": position}))
            ws_x.receive_text()
            ws_o.receive_text()

        # Final move that causes draw
        ws_x.send_text(json.dumps({"type": "move", "position": 8}))

        # Both players receive final state
        state_x = json.loads(ws_x.receive_text())
        state_o = json.loads(ws_o.receive_text())

        assert state_x["data"]["status"] == "finished"
        assert state_x["data"]["winner"] == "draw"

        # Both players receive game ended message
        end_x = json.loads(ws_x.receive_text())
        end_o = json.loads(ws_o.receive_text())

        assert end_x["type"] == "game_ended"
        assert end_x["reason"] == "draw"


# ============================================================================
# Test Multiple Concurrent Games
# ============================================================================


def test_multiple_concurrent_games():
    """Test that multiple games can run concurrently."""
    # Create two rooms
    room1_response = client.post("/rooms")
    room2_response = client.post("/rooms")

    room1_id = room1_response.json()["room_id"]
    room2_id = room2_response.json()["room_id"]

    assert room1_id != room2_id
    assert room1_id in games
    assert room2_id in games

    # Connect to both rooms
    with (
        client.websocket_connect(f"/ws/{room1_id}/X") as ws1_x,
        client.websocket_connect(f"/ws/{room2_id}/X") as ws2_x,
    ):
        msg1 = json.loads(ws1_x.receive_text())
        msg2 = json.loads(ws2_x.receive_text())

        assert msg1["type"] == "game_state"
        assert msg2["type"] == "game_state"

        # Verify they are separate games
        assert games[room1_id] != games[room2_id]


# ============================================================================
# Test Themes
# ============================================================================


def test_list_themes():
    """Test listing available themes."""
    response = client.get("/themes")
    assert response.status_code == 200

    data = response.json()
    assert data["default"] == DEFAULT_THEME_ID

    theme_ids = [theme["id"] for theme in data["themes"]]
    assert DEFAULT_THEME_ID in theme_ids
    assert "farmyard" in theme_ids
    assert len(theme_ids) == len(set(theme_ids))


def test_get_classic_theme():
    """Test that the default theme keeps the original X/O symbols."""
    response = client.get(f"/themes/{DEFAULT_THEME_ID}")
    assert response.status_code == 200

    theme = response.json()
    assert theme["symbols"] == {"X": "X", "O": "O"}
    assert theme["text"]["title"] == "Tic Tac Toe"


def test_get_farmyard_theme():
    """Test the farmyard theme replaces X/O with farm animals."""
    response = client.get("/themes/farmyard")
    assert response.status_code == 200

    theme = response.json()
    assert theme["name"] == "Farmyard"
    assert theme["symbols"]["X"] == "🐄"
    assert theme["symbols"]["O"] == "🐓"
    assert theme["colors"]["--primary-color"] == "#B5451B"


def test_get_theme_not_found():
    """Test getting a theme that does not exist."""
    response = client.get("/themes/not-a-theme")
    assert response.status_code == 404


def test_theme_colors_are_css_variables():
    """Test every theme color is a CSS custom property name."""
    for theme in get_themes():
        assert theme.colors
        for name in theme.colors:
            assert name.startswith("--")


def test_theme_rejects_non_css_variable_color():
    """Test theme validation rejects colors that are not CSS variables."""
    classic = get_theme(DEFAULT_THEME_ID)

    with pytest.raises(ValidationError):
        Theme(
            id="broken",
            name="Broken",
            symbols=classic.symbols,
            icons=classic.icons,
            text=classic.text,
            colors={"primary-color": "#000000"},
        )


def test_themes_define_the_same_colors():
    """Test all themes override the same set of CSS variables."""
    color_keys = [set(theme.colors) for theme in get_themes()]
    assert all(keys == color_keys[0] for keys in color_keys)


def test_index_includes_theme_picker():
    """Test the frontend exposes the theme dropdown."""
    response = client.get("/")
    assert response.status_code == 200
    assert 'id="theme-select"' in response.text
