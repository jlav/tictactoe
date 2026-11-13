// ============================================================================
// Global State
// ============================================================================

const THEME_STORAGE_KEY = 'tictactoe-theme';

let roomId = null;
let playerId = null;
let websocket = null;
let currentTheme = null;
let gameEndReason = null;
let gameState = {
    board: Array(9).fill(null),
    status: 'waiting',
    current_turn: null,
    winner: null,
    players_connected: 0
};

// ============================================================================
// DOM Elements
// ============================================================================

const themeSelect = document.getElementById('theme-select');
const gameTitleElement = document.getElementById('game-title');
const gameSubtitleElement = document.getElementById('game-subtitle');
const roomIdElement = document.getElementById('room-id');
const copyBtn = document.getElementById('copy-btn');
const playerSymbolElement = document.getElementById('player-symbol');
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

async function init() {
    // Load themes before the board is rendered
    await loadThemes();

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
// Themes
// ============================================================================

async function loadThemes() {
    try {
        const response = await fetch('/themes');

        if (!response.ok) {
            throw new Error('Failed to load themes');
        }

        const data = await response.json();

        themeSelect.innerHTML = '';
        data.themes.forEach(theme => {
            const option = document.createElement('option');
            option.value = theme.id;
            option.textContent = theme.name;
            themeSelect.appendChild(option);
        });

        const storedId = localStorage.getItem(THEME_STORAGE_KEY);
        const selected =
            data.themes.find(theme => theme.id === storedId) ||
            data.themes.find(theme => theme.id === data.default) ||
            data.themes[0];

        if (selected) {
            themeSelect.value = selected.id;
            applyTheme(selected);
        }
    } catch (error) {
        console.error('Error loading themes:', error);
    }
}

function applyTheme(theme) {
    currentTheme = theme;

    Object.entries(theme.colors).forEach(([property, value]) => {
        document.documentElement.style.setProperty(property, value);
    });

    document.title = `${theme.text.title} - ${theme.text.subtitle}`;
    gameTitleElement.textContent = theme.text.title;
    gameSubtitleElement.textContent = theme.text.subtitle;
    copyBtn.textContent = theme.icons.copy_link;

    // Re-render anything that already shows themed symbols or text
    updateBoard();
    updateStatus();
    updatePlayerInfo();
    updateGameOverContent();
}

async function handleThemeChange(event) {
    const themeId = event.target.value;

    try {
        const response = await fetch(`/themes/${themeId}`);

        if (!response.ok) {
            throw new Error('Theme not found');
        }

        const theme = await response.json();
        localStorage.setItem(THEME_STORAGE_KEY, theme.id);
        applyTheme(theme);
    } catch (error) {
        console.error('Error applying theme:', error);
    }
}

function symbolFor(player) {
    return currentTheme ? currentTheme.symbols[player] : player;
}

function themeText(key, fallback) {
    return currentTheme ? currentTheme.text[key] : fallback;
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
        updatePlayerInfo();

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
        updatePlayerInfo();

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
        showStatus(themeText('waiting', 'Waiting for opponent...'), 'waiting');
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
            cell.textContent = symbolFor(value);
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
            statusText = themeText('waiting', 'Waiting for opponent...');
            statusClass = 'waiting';
            break;

        case 'active':
            if (gameState.current_turn === playerId) {
                statusText = themeText('your_turn', 'Your turn!');
                statusClass = 'your-turn';
            } else {
                statusText = themeText('opponent_turn', "Opponent's turn");
                statusClass = 'opponent-turn';
            }
            break;

        case 'finished':
            if (gameState.winner === 'draw') {
                statusText = themeText('draw_title', "It's a draw!");
            } else if (gameState.winner === playerId) {
                statusText = themeText('win_title', 'You won!');
            } else {
                statusText = themeText('lose_title', 'You lost!');
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

    gameEndReason = message.reason;

    updateGameOverContent();
    gameOverElement.classList.remove('hidden');
}

function updateGameOverContent() {
    if (!gameEndReason) {
        return;
    }

    let title = 'Game Over';
    let messageText = '';

    if (gameEndReason === 'win') {
        const celebrate = currentTheme ? ` ${currentTheme.icons.celebrate}` : '';

        if (gameState.winner === playerId) {
            title = `${themeText('win_title', 'You Win!')}${celebrate}`;
            messageText = themeText('win_message', 'Congratulations!');
        } else {
            title = themeText('lose_title', 'You Lose');
            messageText = themeText('lose_message', 'Better luck next time!');
        }
    } else if (gameEndReason === 'draw') {
        title = themeText('draw_title', "It's a Draw!");
        messageText = themeText('draw_message', 'Good game!');
    } else if (gameEndReason === 'player_disconnected') {
        title = 'Game Ended';
        messageText = 'Opponent disconnected';
    } else {
        title = 'Game Ended';
        messageText = gameEndReason;
    }

    gameOverTitle.textContent = title;
    gameOverMessage.textContent = messageText;
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
        copyBtn.textContent = currentTheme ? currentTheme.icons.copy_success : '✓';
        copyBtn.classList.add('copied');

        setTimeout(() => {
            copyBtn.textContent = currentTheme ? currentTheme.icons.copy_link : '📋';
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

function updatePlayerInfo() {
    if (playerId) {
        playerSymbolElement.textContent = symbolFor(playerId);
        playerSymbolElement.classList.add(playerId);
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

    // Theme picker
    themeSelect.addEventListener('change', handleThemeChange);

    // Copy button
    copyBtn.addEventListener('click', handleCopyLink);

    // New game button
    newGameBtn.addEventListener('click', handleNewGame);

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
