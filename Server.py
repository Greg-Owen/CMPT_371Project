import socket
import threading
import json
import time
import random
import math

# Server settings
HOST = 'localhost'
PORT = 8765

# Game settings
WIDTH = 800
HEIGHT = 600
PLAYER_SPEED = 5
BALL_SPEED = 3
PLAYER_RADIUS = 15
BALL_RADIUS = 10

# Game state
players = []
ball_pos = [WIDTH // 2, HEIGHT // 2]
ball_vel = [0, 0]
game_started = False
lock = threading.Lock()

# Create server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(4)  # Listen for up to 4 connections
print(f"Server started on {HOST}:{PORT}")

# List to keep track of all client sockets
clients = []

# Function to handle each client connection
def handle_client(client_socket, player_id):
    global game_started, players, ball_pos
    
    print(f"Player {player_id} connected")
    
    # Assign team based on player_id
    team = 0 if player_id < 2 else 1
    
    # Initialize player position based on team and position
    positions = {
        0: [WIDTH // 4, HEIGHT // 3],
        1: [WIDTH // 4, 2 * HEIGHT // 3],
        2: [3 * WIDTH // 4, HEIGHT // 3],
        3: [3 * WIDTH // 4, 2 * HEIGHT // 3]
    }
    
    # Create player object
    player = {
        "x": positions[player_id][0], 
        "y": positions[player_id][1], 
        "keys": {
            "up": False, 
            "down": False, 
            "left": False, 
            "right": False
        }
    }
    
    with lock:
        # Add player to list
        if player_id >= len(players):
            players.append(player)
        else:
            players[player_id] = player
    
    # Send player ID
    client_socket.send(json.dumps({"type": "id", "id": player_id}).encode('utf-8'))
    
    # Send lobby info to all clients
    broadcast_lobby_state()
    
    # Check if game can start
    check_game_start()
    
    # Main client handling loop
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
                
            message = json.loads(data)
            
            if message["type"] == "input" and game_started:
                # Update player's input state
                with lock:
                    if player_id < len(players):
                        players[player_id]["keys"] = message["keys"]
    except Exception as e:
        print(f"Error handling client {player_id}: {e}")
    finally:
        # Handle client disconnect
        print(f"Player {player_id} disconnected")
        client_socket.close()
        
        with lock:
            if client_socket in clients:
                clients.remove(client_socket)
            
            # Reset game if a player disconnects during game
            if game_started:
                game_started = False
                print("Game stopped due to player disconnect")
            
            # Remove player
            if player_id < len(players):
                players.pop(player_id)
                
            broadcast_lobby_state()

# Function to check if game can start
def check_game_start():
    global game_started, ball_pos, ball_vel
    
    with lock:
        if len(players) == 4 and not game_started:
            game_started = True
            print("Game starting with 4 players")
            # Reset ball
            ball_pos = [WIDTH // 2, HEIGHT // 2]
            ball_vel = [random.choice([-1, 1]) * BALL_SPEED, random.choice([-1, 1]) * BALL_SPEED]
            broadcast_game_start()

# Function to broadcast lobby state to all clients
def broadcast_lobby_state():
    lobby_info = {
        "type": "lobby",
        "count": len(players)
    }
    broadcast_message(lobby_info)

# Function to broadcast game start to all clients
def broadcast_game_start():
    start_message = {
        "type": "start"
    }
    broadcast_message(start_message)

# Function to broadcast a message to all clients
def broadcast_message(message):
    data = json.dumps(message).encode('utf-8')
    disconnected = []
    
    for client in clients:
        try:
            client.send(data)
        except:
            disconnected.append(client)
    
    # Remove disconnected clients
    for client in disconnected:
        if client in clients:
            clients.remove(client)

# Function to update game state
def update_game_state():
    global ball_pos, ball_vel
    
    if not game_started or len(players) < 4:
        return
        
    with lock:
        # Update player positions based on input
        for player in players:
            if player["keys"]["up"]:
                player["y"] = max(player["y"] - PLAYER_SPEED, PLAYER_RADIUS)
            if player["keys"]["down"]:
                player["y"] = min(player["y"] + PLAYER_SPEED, HEIGHT - PLAYER_RADIUS)
            if player["keys"]["left"]:
                player["x"] = max(player["x"] - PLAYER_SPEED, PLAYER_RADIUS)
            if player["keys"]["right"]:
                player["x"] = min(player["x"] + PLAYER_SPEED, WIDTH - PLAYER_RADIUS)
        
        # Update ball position
        ball_pos[0] += ball_vel[0]
        ball_pos[1] += ball_vel[1]
        
        # Ball collision with walls
        if ball_pos[0] - BALL_RADIUS <= 0 or ball_pos[0] + BALL_RADIUS >= WIDTH:
            ball_vel[0] = -ball_vel[0]
            
            # Check for goals (simplified)
            if ball_pos[1] > HEIGHT//3 and ball_pos[1] < 2*HEIGHT//3:
                # Reset ball
                ball_pos = [WIDTH // 2, HEIGHT // 2]
                ball_vel = [random.choice([-1, 1]) * BALL_SPEED, random.choice([-1, 1]) * BALL_SPEED]
        
        if ball_pos[1] - BALL_RADIUS <= 0 or ball_pos[1] + BALL_RADIUS >= HEIGHT:
            ball_vel[1] = -ball_vel[1]
            
        # Ball-player collision
        for player in players:
            dx = ball_pos[0] - player["x"]
            dy = ball_pos[1] - player["y"]
            distance = (dx**2 + dy**2)**0.5
            
            if distance < PLAYER_RADIUS + BALL_RADIUS:
                # Calculate reflection vector
                nx = dx / distance
                ny = dy / distance
                
                # Reflect ball velocity
                dot = ball_vel[0] * nx + ball_vel[1] * ny
                ball_vel[0] = ball_vel[0] - 2 * dot * nx
                ball_vel[1] = ball_vel[1] - 2 * dot * ny
                
                # Normalize and set speed
                vel_magnitude = (ball_vel[0]**2 + ball_vel[1]**2)**0.5
                if vel_magnitude > 0:
                    ball_vel[0] = ball_vel[0] / vel_magnitude * BALL_SPEED * 1.1
                    ball_vel[1] = ball_vel[1] / vel_magnitude * BALL_SPEED * 1.1
                
                # Move ball outside collision
                overlap = PLAYER_RADIUS + BALL_RADIUS - distance
                ball_pos[0] += nx * overlap
                ball_pos[1] += ny * overlap
        
        # Send updated game state to all clients
        game_state = {
            "type": "state",
            "players": players,
            "ball": ball_pos
        }
        broadcast_message(game_state)

# Function to accept new connections
def accept_connections():
    while True:
        try:
            client_socket, addr = server_socket.accept()
            print(f"New connection from {addr}")
            with lock:
                clients.append(client_socket)
                player_id = len(clients) - 1
            
            client_thread = threading.Thread(target=handle_client, args=(client_socket, player_id))
            client_thread.daemon = True
            client_thread.start()
        except Exception as e:
            print(f"Error accepting connection: {e}")
            break

# Start thread to accept connections
accept_thread = threading.Thread(target=accept_connections)
accept_thread.daemon = True
accept_thread.start()

# Main game loop
try:
    while True:
        update_game_state()
        time.sleep(1/60)  # ~60 FPS
except KeyboardInterrupt:
    print("Server shutting down...")
finally:
    server_socket.close()