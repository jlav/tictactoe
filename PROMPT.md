Create a simple FastAPI backend for a 2-player online tic tac toe game.
The game should support real-time updates using WebSockets.
Support multiple rooms so that multiple games can be played concurrently.
Use in-memory storage for game state to keep it simple.
Implement basic game logic to handle player moves, check for wins, and manage game state.
Represent the game board as a list with 9 elements, where each element can be 'X', 'O', or None.
Define endpoints for creating a game room, joining a game room, and making moves.
Implement WebSocket endpoints for real-time communication between players.
Ensure that the server can handle multiple WebSocket connections for different game rooms.


FE:
Create a simple frontend using HTML, CSS, and JavaScript.
The frontend should create a new game room when the user visits the page.
Just use a query parameter to store the current room id, and allow users to share the link to invite another player.
Display the tic tac toe board and allow players to click on cells to make moves.
Use WebSockets to receive real-time updates from the server and update the game board accordingly.
Show the current player's turn and display messages for game status (win, draw, etc.).
Style the game board and interface for a better user experience.
Serve the frontend files using FastAPI's StaticFiles.


