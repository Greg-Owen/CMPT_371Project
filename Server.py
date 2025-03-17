import asyncio
import websockets
import json

# Game state
players = [{"x": 100, "y": 200, "keys": {"up": False, "left": False, "right": False}},
           {"x": 300, "y": 400, "keys": {"up": False, "left": False, "right": False}}]

async def handle_client(websocket, path):
    async for message in websocket:
        # Parse client input
        data = json.loads(message)
        if data["type"] == "input":
            player_id = data["player_id"]
            keys = data["keys"]
            players[player_id]["keys"] = keys

        # Update game state (e.g., move players based on input)
        for player in players:
            if player["keys"]["up"]:
                player["y"] -= 5
            if player["keys"]["left"]:
                player["x"] -= 5
            if player["keys"]["right"]:
                player["x"] += 5

        # Send updated game state to client
        await websocket.send(json.dumps({"type": "state", "players": players}))

# Start the server
start_server = websockets.serve(handle_client, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()