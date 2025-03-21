import pygame
import socket
import threading
import json
import sys
import os

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Soccer Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Player properties
PLAYER_RADIUS = 15
player_colors = [RED, RED, BLUE, BLUE]  # Team colors

# Game states
LOBBY = 0
GAME = 1
game_state = LOBBY

# Connect to server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    client_socket.connect(('localhost', 8765))
    print("Connected to server")
except Exception as e:
    print(f"Failed to connect: {e}")
    pygame.quit()
    sys.exit()

# Player ID (assigned by server)
player_id = None
players = []
ball_pos = [WIDTH // 2, HEIGHT // 2]
num_players = 0

# Load background image
try:
    bg_image = pygame.image.load(os.path.join('assets', 'soccer_field.jpg'))
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
except pygame.error as e:
    print(f"Unable to load background image: {e}")
    # Create a fallback field
    bg_image = pygame.Surface((WIDTH, HEIGHT))
    bg_image.fill(GREEN)
    # Draw field lines
    pygame.draw.rect(bg_image, WHITE, (0, 0, WIDTH, HEIGHT), 5)
    pygame.draw.circle(bg_image, WHITE, (WIDTH // 2, HEIGHT // 2), 70, 5)
    pygame.draw.line(bg_image, WHITE, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 5)

# Function to receive data from server
def receive_data():
    global player_id, players, ball_pos, num_players, game_state
    
    while True:
        try:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                print("Server connection closed")
                break
                
            message = json.loads(data)
            
            if message["type"] == "id":
                player_id = message["id"]
                print(f"Assigned player ID: {player_id}")
                
            elif message["type"] == "lobby":
                num_players = message["count"]
                print(f"Players in lobby: {num_players}/4")
                
            elif message["type"] == "start":
                game_state = GAME
                print("Game starting!")
                
            elif message["type"] == "state":
                players = message["players"]
                ball_pos = message["ball"]
                
        except Exception as e:
            print(f"Error receiving data: {e}")
            break
    
    print("Disconnected from server")
    client_socket.close()
    pygame.quit()
    sys.exit()

# Start receiving thread
receive_thread = threading.Thread(target=receive_data)
receive_thread.daemon = True
receive_thread.start()

# Game loop
running = True
clock = pygame.time.Clock()

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Clear screen
    screen.fill(BLACK)
    
    # Draw background
    screen.blit(bg_image, (0, 0))
    
    if game_state == LOBBY:
        # Draw lobby screen
        font = pygame.font.Font(None, 36)
        text = font.render(f"Waiting for players... {num_players}/4", True, WHITE)
        text_rect = text.get_rect(center=(WIDTH/2, HEIGHT/2))
        screen.blit(text, text_rect)
        
        # Draw instructions
        instructions = [
            "Game will start when 4 players connect.",
            "Use W, A, S, D keys to move.",
            "Red team vs Blue team"
        ]
        
        small_font = pygame.font.Font(None, 24)
        for i, line in enumerate(instructions):
            text = small_font.render(line, True, WHITE)
            screen.blit(text, (WIDTH/2 - text.get_width()/2, HEIGHT/2 + 40 + i*30))
    
    else:
        # Game is running
        # Draw players
        for i, player in enumerate(players):
            if i < len(player_colors):
                pygame.draw.circle(screen, player_colors[i], (player["x"], player["y"]), PLAYER_RADIUS)
                
                # Draw player number
                number_font = pygame.font.Font(None, 24)
                number_text = number_font.render(str(i+1), True, WHITE)
                number_rect = number_text.get_rect(center=(player["x"], player["y"]))
                screen.blit(number_text, number_rect)
        
        # Draw ball
        pygame.draw.circle(screen, YELLOW, (ball_pos[0], ball_pos[1]), 10)
        
        # Handle player movement (if we have a player_id)
        if player_id is not None and player_id < len(players):
            keys = pygame.key.get_pressed()
            movement = {
                "type": "input",
                "player_id": player_id,
                "keys": {
                    "up": keys[pygame.K_w],
                    "down": keys[pygame.K_s],
                    "left": keys[pygame.K_a],
                    "right": keys[pygame.K_d]
                }
            }
            try:
                client_socket.send(json.dumps(movement).encode('utf-8'))
            except:
                print("Failed to send movement data")
    
    # Update display
    pygame.display.flip()
    clock.tick(60)

# Cleanup
try:
    client_socket.close()
except:
    pass
pygame.quit()
sys.exit()
