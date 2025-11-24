"""WebSocket endpoint for real-time game communication."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

from .storage import games
from .game import (
    check_winner,
    check_draw,
    validate_move,
    broadcast_state,
    end_game,
)

router = APIRouter()


@router.websocket("/ws/{room_id}/{player}")
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

            # Handle restart message
            elif message.get("type") == "restart":
                # Only allow restart if game is finished
                if game.status != "finished":
                    await websocket.send_text(
                        json.dumps(
                            {"type": "error", "message": "Game is not finished"}
                        )
                    )
                    continue

                # Reset the game state
                game.reset()

                # Broadcast the new game state to both players
                await broadcast_state(game)

    except WebSocketDisconnect:
        # Handle disconnection - end the game immediately
        game.players[player] = None
        await end_game(room_id, reason="player_disconnected")

    except Exception as e:
        # Handle any other errors
        game.players[player] = None
        await end_game(room_id, reason="error")
