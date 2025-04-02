import json
import os

class ConnectionHandler:
    def __init__(self, filename):
        self.set_filename(filename)

    def get_filename(self):
        return self.filename

    def set_filename(self, filename):
        self.filename = filename

    @staticmethod
    def read_json_file(file_path):
        with open(file_path, 'r') as reader:
            return reader.read()

    def show_client_side(self):
        if os.path.exists(self.filename):
            json_content = self.read_json_file(self.filename)
            json_array = json.loads(json_content)
            for item in json_array:
                game_state = item.get("gameState")
                print(f"Processed game state from file: {game_state}")
        else:
            print("Error: File not found")

    def update_client_side(self):
        game_state = "N/A"
        if os.path.exists(self.filename):
            json_content = self.read_json_file(self.filename)
            json_array = json.loads(json_content)
            for item in json_array:
                game_state = item.get("gameState")
            return game_state
        else:
            print("Error: File not found")
        return game_state

    def show_server_side(self):
        if os.path.exists(self.filename):
            json_content = self.read_json_file(self.filename)
            json_array = json.loads(json_content)
            for item in json_array:
                movement = item.get("movement")
                print(f"Processed movement from file: {movement}")
        else:
            print("Error: File not found")