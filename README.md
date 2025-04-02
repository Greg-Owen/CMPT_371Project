# Multiplayer Checkbox Game

## Project Overview

This project implements a multiplayer checkbox game using a client-server architecture. Players interact with a 10x10 grid of checkboxes in a Python GUI. The server manages the game state and synchronizes updates across all connected clients using UDP communication.

### Features

1. Player Identification: Each player is assigned a unique color to identify their selections.
2. Synchronization: When a new client joins, the server sends the current board state to ensure synchronization.
3. Selection Timer: Selecting a checkbox takes 3 seconds, during which adjacent checkboxes are temporarily blocked for other players.
4. Ownership Display: The GUI displays the owner of each color, allowing players to identify who selected which checkbox.
5. Immutable Selections: Once a checkbox is selected, it cannot be unselected.

---

## Design Overview

### Architecture

The game uses a client-server architecture:

- Server: Maintains the game state, handles player connections, and broadcasts updates to all clients.
- Clients: Handle user interactions and update their local GUI based on messages from the server.

### Communication Protocol

The server and clients communicate using a simple text-based protocol over UDP. Messages include:

- `register`: Client registers with the server.
- `identity`: Server assigns a name and color to the client.
- `board`: Server sends the current board state to a new client.
- `update`: Server notifies all clients of a completed selection.
- `selecting`: Server notifies clients of an ongoing selection.
- `block_adjacent`: Server blocks adjacent cells during a selection.
- `unblock_adjacent`: Server unblocks adjacent cells after a selection.
- `player_info`: Server broadcasts player information.
- `player_joined`: Server notifies clients of a new player.
- `player_left`: Server notifies clients of a player leaving.

---

## Implementation Details

### 1. Synchronizing the Board for New Clients

When a new client joins, the server sends the current board state and player information to ensure synchronization.

### 2. Coloring Based on Player

Each player is assigned a unique color. The server includes the player's color in update messages, and the client uses this information to update the GUI.

### 3. Selection Timer and Blocking

Selecting a checkbox takes 3 seconds. During this time, adjacent checkboxes are blocked for other players.
