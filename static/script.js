// ============================================================================
// Global State
// ============================================================================

let roomId = null;
let playerId = null;
let websocket = null;
let gameState = {
    board: Array(9).fill(null),
    status: 'waiting',
    current_turn: null,
    winner: null,
    players_connected: 0
};

// ============================================================================
// Themes
// ============================================================================

const THEMES = {
    classic: {
        label: 'Classic',
        playerX: { symbol: 'X', name: 'Player X' },
        playerO: { symbol: 'O', name: 'Player O' },
    },
    farmyard: {
        label: 'Farmyard',
        playerX: { symbol: '🐓', name: 'Rooster' },
        playerO: { symbol: '🐑', name: 'Sheep' },
    },
};

const THEME_STORAGE_KEY = 'tictactoe-theme';

let currentTheme = 'classic';

// ============================================================================
// DOM Elements
// ============================================================================

const roomIdElement = document.getElementById('room-id');
const copyBtn = document.getElementById('copy-btn');
const playerSymbolElement = document.getElementById('player-symbol');
const playerNameElement = document.getElementById('player-name');
const themeSelectElement = document.getElementById('theme-select');
const gameStatusElement = document.getElementById('game-status');
const gameBoardElement = document.getElementById('game-board');
const cells = document.querySelectorAll('.cell');
const gameOverElement = document.getElementById('game-over');
const gameOverTitle = document.getElementById('game-over-title');
const gameOverMessage = document.getElementById('game-over-message');
const newGameBtn = document.getElementById('new-game-btn');

// ============================================================================
// Initialization
// ============================================================================

function loadTheme() {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    if (savedTheme && THEMES[savedTheme]) {
        currentTheme = savedTheme;
    }
    themeSelectElement.value = currentTheme;
    applyTheme(currentTheme);
}

function applyTheme(theme) {
    if (!THEMES[theme]) {
        return;
    }
    currentTheme = theme;
    document.body.classList.toggle('theme-farmyard', theme === 'farmyard');
    localStorage.setItem(THEME_STORAGE_KEY, theme);
    renderPlayerInfo();
    updateBoard();
}

function handleThemeChange(event) {
    applyTheme(event.target.value);
}

function getPlayerSymbol(player) {
    return THEMES[currentTheme][`player${player}`].symbol;
}

function getPlayerName(player) {
    return THEMES[currentTheme][`player${player}`].name;
}

async function init() {
    // Load saved theme before rendering
    loadTheme();

    // Check if room ID is in URL
    const urlParams = new URLSearchParams(window.location.search);
    roomId = urlParams.get('room');

    if (roomId) {
        // Join existing room
        await joinRoom(roomId);
    } else {
        // Create new room
        await createRoom();
    }

    // Set up event listeners
    setupEventListeners();
}

// ============================================================================
// Room Management
// ============================================================================

async function createRoom() {
    try {
        const response = await fetch('/rooms', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to create room');
        }

        const data = await response.json();
        roomId = data.room_id;
        playerId = data.player; // 'X'

        // Update URL with room ID
        const url = new URL(window.location);
        url.searchParams.set('room', roomId);
        window.history.pushState({}, '', url);

        // Update UI
        updateRoomInfo();
        renderPlayerInfo();

        // Connect to WebSocket
        connectWebSocket();
    } catch (error) {
        console.error('Error creating room:', error);
        showStatus('Error creating room. Please refresh.', 'error');
    }
}

async function joinRoom(roomId) {
    try {
        // First check if room exists
        const statusResponse = await fetch(`/rooms/${roomId}`);

        if (!statusResponse.ok) {
            throw new Error('Room not found');
        }

        // Try to join the room
        const joinResponse = await fetch(`/rooms/${roomId}/join`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!joinResponse.ok) {
            // Room might be full or game already started
            // Try connecting as X (room creator might have refreshed)
            playerId = 'X';
        } else {
            const data = await joinResponse.json();
            playerId = data.player; // 'O'
        }

        // Update UI
        updateRoomInfo();
        renderPlayerInfo();

        // Connect to WebSocket
        connectWebSocket();
    } catch (error) {
        console.error('Error joining room:', error);
        showStatus('Room not found. Creating new room...', 'warning');
        // Create new room if join fails
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    }
}

// ============================================================================
// WebSocket Connection
// ============================================================================

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${roomId}/${playerId}`;

    websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
        console.log('WebSocket connected');
        showStatus('Connected! Waiting for opponent...', 'waiting');
    };

    websocket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };

    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        showStatus('Connection error', 'error');
    };

    websocket.onclose = () => {
        console.log('WebSocket closed');
        showStatus('Disconnected', 'error');
    };
}

function handleWebSocketMessage(message) {
    console.log('Received message:', message);

    switch (message.type) {
        case 'game_state':
            updateGameState(message.data);
            break;

        case 'game_ended':
            handleGameEnd(message);
            break;

        case 'error':
            showError(message.message);
            break;

        default:
            console.log('Unknown message type:', message.type);
    }
}

// ============================================================================
// Game State Management
// ============================================================================

function updateGameState(data) {
    gameState = data;

    // Update board
    updateBoard();

    // Update status
    updateStatus();
}

function updateBoard() {
    cells.forEach((cell, index) => {
        const value = gameState.board[index];

        // Clear previous classes
        cell.classList.remove('X', 'O', 'occupied', 'disabled');
        cell.textContent = '';

        if (value) {
            // Cell is occupied
            cell.classList.add(value, 'occupied');
            cell.textContent = getPlayerSymbol(value);
        } else if (gameState.status !== 'active' || gameState.current_turn !== playerId) {
            // Disable cell if game not active or not player's turn
            cell.classList.add('disabled');
        }
    });
}

function updateStatus() {
    let statusText = '';
    let statusClass = '';

    switch (gameState.status) {
        case 'waiting':
            statusText = 'Waiting for opponent...';
            statusClass = 'waiting';
            break;

        case 'active':
            if (gameState.current_turn === playerId) {
                statusText = 'Your turn!';
                statusClass = 'your-turn';
            } else {
                statusText = "Opponent's turn";
                statusClass = 'opponent-turn';
            }
            break;

        case 'finished':
            if (gameState.winner === 'draw') {
                statusText = "It's a draw!";
            } else if (gameState.winner === playerId) {
                statusText = 'You won!';
            } else {
                statusText = 'You lost!';
            }
            statusClass = 'finished';
            break;

        default:
            statusText = 'Unknown status';
            statusClass = '';
    }

    gameStatusElement.textContent = statusText;
    gameStatusElement.className = `game-status ${statusClass}`;
}

function handleGameEnd(message) {
    console.log('Game ended:', message);

    // Show game over modal
    let title = 'Game Over';
    let messageText = '';

    if (message.reason === 'win') {
        if (gameState.winner === playerId) {
            title = 'You Win! 🎉';
            messageText = 'Congratulations!';
        } else {
            title = 'You Lose';
            messageText = 'Better luck next time!';
        }
    } else if (message.reason === 'draw') {
        title = "It's a Draw!";
        messageText = 'Good game!';
    } else if (message.reason === 'player_disconnected') {
        title = 'Game Ended';
        messageText = 'Opponent disconnected';
    } else {
        title = 'Game Ended';
        messageText = message.reason;
    }

    gameOverTitle.textContent = title;
    gameOverMessage.textContent = messageText;
    gameOverElement.classList.remove('hidden');
}

// ============================================================================
// User Actions
// ============================================================================

function handleCellClick(event) {
    const cell = event.target;
    const index = parseInt(cell.dataset.index);

    // Check if move is valid
    if (gameState.board[index] !== null) {
        return; // Cell already occupied
    }

    if (gameState.status !== 'active') {
        return; // Game not active
    }

    if (gameState.current_turn !== playerId) {
        return; // Not player's turn
    }

    // Send move to server
    sendMove(index);
}

function sendMove(position) {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        console.error('WebSocket not connected');
        return;
    }

    const message = {
        type: 'move',
        position: position
    };

    websocket.send(JSON.stringify(message));
}

function handleCopyLink() {
    const url = window.location.href;

    navigator.clipboard.writeText(url).then(() => {
        // Show success feedback
        copyBtn.textContent = '✓';
        copyBtn.classList.add('copied');

        setTimeout(() => {
            copyBtn.textContent = '📋';
            copyBtn.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy link. Please copy manually: ' + url);
    });
}

function handleNewGame() {
    // Redirect to home to create a new room
    window.location.href = '/';
}

// ============================================================================
// UI Updates
// ============================================================================

function updateRoomInfo() {
    if (roomId) {
        // Display shortened room ID
        const shortId = roomId.substring(0, 8);
        roomIdElement.textContent = shortId;
        roomIdElement.title = roomId;
    }
}

function renderPlayerInfo() {
    if (playerId) {
        playerSymbolElement.textContent = getPlayerSymbol(playerId);
        playerSymbolElement.classList.remove('X', 'O');
        playerSymbolElement.classList.add(playerId);
        playerNameElement.textContent = getPlayerName(playerId);
    }
}

function showStatus(message, type) {
    gameStatusElement.textContent = message;
    gameStatusElement.className = `game-status ${type}`;
}

function showError(message) {
    console.error('Game error:', message);
    showStatus(message, 'error');
}

// ============================================================================
// Event Listeners
// ============================================================================

function setupEventListeners() {
    // Cell clicks
    cells.forEach(cell => {
        cell.addEventListener('click', handleCellClick);
    });

    // Copy button
    copyBtn.addEventListener('click', handleCopyLink);

    // New game button
    newGameBtn.addEventListener('click', handleNewGame);

    // Theme selector
    themeSelectElement.addEventListener('change', handleThemeChange);

    // Handle page unload
    window.addEventListener('beforeunload', () => {
        if (websocket) {
            websocket.close();
        }
    });
}

// ============================================================================
// Start the application
// ============================================================================

document.addEventListener('DOMContentLoaded', init);
