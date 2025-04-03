import tkinter as tk
import socket
import threading
import sys
import time

SERVER_IP = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
SERVER_PORT = 5005

class CheckBoxClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Checkbox Grid Client")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.player_name = None
        self.player_color = None
        
        self.player_colors = {}
        
        self.is_selecting = False
        
        self.board_owners = [[None for _ in range(10)] for _ in range(10)]
        self.board_colors = [[None for _ in range(10)] for _ in range(10)]
        
        self.selecting_cells = {}
        
        self.blocked_cells = {}
        self.blink_interval = 200
        
        self.blocked_by_selection = {}
        
        # Create waiting screen
        self.waiting_frame = tk.Frame(root, padx=20, pady=20)
        self.waiting_label = tk.Label(
            self.waiting_frame, 
            text="Waiting for players to join...",
            font=("Arial", 16)
        )
        self.waiting_label.pack(pady=20)
        
        self.players_count_label = tk.Label(
            self.waiting_frame,
            text="Players: 0/4",
            font=("Arial", 14)
        )
        self.players_count_label.pack(pady=10)
        
        # Show waiting frame initially
        self.waiting_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create game screen (initially hidden)
        self.grid_frame = tk.Frame(root)
        self.checkboxes = [[None for _ in range(10)] for _ in range(10)]
        for r in range(10):
            for c in range(10):
                cell_frame = tk.Frame(self.grid_frame, width=30, height=30, 
                                     borderwidth=1, relief="solid")
                cell_frame.grid(row=r, column=c)
                cell_frame.grid_propagate(False)
                
                cb = tk.Checkbutton(cell_frame, command=lambda row=r, col=c: self.handle_click(row, col))
                cb.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
                
                timer_label = tk.Label(cell_frame, text="", font=("Arial", 6))
                timer_label.place(relx=0.5, rely=0.8, anchor=tk.CENTER)
                
                self.checkboxes[r][c] = {
                    "checkbox": cb, 
                    "frame": cell_frame,
                    "timer_label": timer_label
                }
        
        self.info_frame = tk.Frame(root)
        
        self.player_label = tk.Label(self.info_frame, text="Connecting to server...")
        self.player_label.pack()
        
        self.status_label = tk.Label(self.info_frame, text="")
        self.status_label.pack()
        
        self.players_frame = tk.Frame(self.info_frame)
        self.players_frame.pack(pady=5)
        self.legend_label = tk.Label(self.players_frame, text="Players:")
        self.legend_label.pack()
        
        # Start the timers
        self.update_timers()
        self.update_blocked_cells_blink()
        
        # Connect to server
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.sendto("register".encode(), (SERVER_IP, SERVER_PORT))
        
        self.listener = threading.Thread(target=self.listen_for_updates, daemon=True)
        self.listener.start()
    
    def start_game(self):
        """Switch from waiting screen to game board"""
        self.waiting_frame.pack_forget()
        self.grid_frame.pack(padx=10, pady=10)
        self.info_frame.pack(pady=10)
        self.update_all_cells()
    
    def handle_click(self, row, col):
        if self.is_selecting:
            return
            
        if (self.board_owners[row][col] is not None or 
            (row, col) in self.selecting_cells or 
            (row, col) in self.blocked_cells):
            return
        
        msg = f"click,{row},{col}"
        self.sock.sendto(msg.encode(), (SERVER_IP, SERVER_PORT))
        
        self.is_selecting = True
        self.update_status("Selecting a cell...")
    
    def update_status(self, message):
        self.status_label.config(text=message)
    
    def update_timers(self):
        current_time = time.time()
        cells_to_remove = []
        
        for (row, col), info in self.selecting_cells.items():
            remaining = max(0, info["end_time"] - current_time)
            
            if remaining > 0:
                bg_color = info["color"]
                
                frame = self.checkboxes[row][col]["frame"]
                frame.config(background=bg_color)
                
                timer_label = self.checkboxes[row][col]["timer_label"]
                timer_label.config(text=f"{remaining:.1f}s")
                
                if info["player"] == self.player_name:
                    self.update_status(f"Selecting cell... {remaining:.1f}s")
            else:
                cells_to_remove.append((row, col))
                timer_label = self.checkboxes[row][col]["timer_label"]
                timer_label.config(text="")
                
                if info["player"] == self.player_name:
                    self.is_selecting = False
                    self.update_status("")
        
        for cell in cells_to_remove:
            if cell in self.selecting_cells:
                del self.selecting_cells[cell]
        
        self.root.after(100, self.update_timers)
    
    def update_blocked_cells_blink(self):
        cells_to_remove = []
        current_time = time.time()
        
        for (row, col), info in self.blocked_cells.items():
            info["blink_state"] = not info["blink_state"]
            
            if current_time > info["end_time"]:
                cells_to_remove.append((row, col))
                self.checkboxes[row][col]["frame"].config(background="white")
                
                if (row, col) in self.blocked_by_selection:
                    del self.blocked_by_selection[(row, col)]
                continue
                
            if info["blink_state"]:
                self.checkboxes[row][col]["frame"].config(background=info["color"])
            else:
                lighter_color = self.get_lighter_color(info["color"])
                self.checkboxes[row][col]["frame"].config(background=lighter_color)
        
        for cell in cells_to_remove:
            if cell in self.blocked_cells:
                del self.blocked_cells[cell]
                self.update_cell_appearance(cell[0], cell[1])
        
        self.root.after(self.blink_interval, self.update_blocked_cells_blink)
    
    def get_lighter_color(self, color):
        color_map = {
            "red": "#ffcccc", "blue": "#ccccff", "green": "#ccffcc",
            "purple": "#eeccff", "orange": "#ffddcc", "magenta": "#ffccff",
            "cyan": "#ccffff", "brown": "#ddccaa", "yellow": "#ffffcc",
            "pink": "#ffddee"
        }
        return color_map.get(color, "#f0f0f0")
    
    def update_player_legend(self):
        for widget in self.players_frame.winfo_children():
            if widget != self.legend_label:
                widget.destroy()
        
        for player, color in self.player_colors.items():
            player_frame = tk.Frame(self.players_frame)
            player_frame.pack(anchor=tk.W)
            
            color_indicator = tk.Frame(player_frame, width=15, height=15, bg=color)
            color_indicator.pack(side=tk.LEFT, padx=5)
            
            name_label = tk.Label(player_frame, text=player)
            name_label.pack(side=tk.LEFT)
    
    def update_cell_appearance(self, row, col):
        owner = self.board_owners[row][col]
        color = self.board_colors[row][col]
        
        if (row, col) in self.blocked_cells:
            self.checkboxes[row][col]["checkbox"].config(state=tk.DISABLED)
            return
            
        elif (row, col) in self.selecting_cells:
            sel_color = self.selecting_cells[(row, col)]["color"]
            self.checkboxes[row][col]["frame"].config(background=sel_color)
            self.checkboxes[row][col]["checkbox"].config(state=tk.DISABLED)
            return
            
        elif owner is not None:
            self.checkboxes[row][col]["frame"].config(background=color)
            self.checkboxes[row][col]["checkbox"].select()
            self.checkboxes[row][col]["checkbox"].config(state=tk.DISABLED)
            return
            
        else:
            self.checkboxes[row][col]["frame"].config(background="white")
            self.checkboxes[row][col]["checkbox"].deselect()
            
            if self.is_selecting:
                self.checkboxes[row][col]["checkbox"].config(state=tk.DISABLED)
            else:
                self.checkboxes[row][col]["checkbox"].config(state=tk.NORMAL)
    
    def update_all_cells(self):
        for r in range(10):
            for c in range(10):
                self.update_cell_appearance(r, c)
    
    def listen_for_updates(self):
        while True:
            try:
                data, _ = self.sock.recvfrom(1024)
                msg = data.decode().split(',')
                
                if msg[0] == 'waiting':
                    current_players = int(msg[1])
                    required_players = int(msg[2])
                    self.players_count_label.config(
                        text=f"Players: {current_players}/{required_players}"
                    )
                
                elif msg[0] == 'game_start':
                    self.start_game()
                
                elif msg[0] == 'identity':
                    self.player_name = msg[1]
                    self.player_color = msg[2]
                    
                    self.player_colors[self.player_name] = self.player_color
                    self.player_label.config(text=f"You are: {self.player_name}")
                    self.update_player_legend()
                
                elif msg[0] == 'player_info':
                    player_name = msg[1]
                    player_color = msg[2]
                    
                    self.player_colors[player_name] = player_color
                    self.update_player_legend()
                
                elif msg[0] == 'board':
                    board_data = msg[1:]
                    index = 0
                    for r in range(10):
                        for c in range(10):
                            owner = board_data[index]
                            color = board_data[index + 1]
                            
                            if owner == "None":
                                self.board_owners[r][c] = None
                                self.board_colors[r][c] = None
                            else:
                                self.board_owners[r][c] = owner
                                self.board_colors[r][c] = color
                                
                                if owner not in self.player_colors and color != "None":
                                    self.player_colors[owner] = color
                            
                            self.update_cell_appearance(r, c)
                            index += 2
                    
                    self.update_player_legend()
                
                elif msg[0] == 'update':
                    r, c = int(msg[1]), int(msg[2])
                    owner = msg[3]
                    color = msg[4]
                    
                    self.board_owners[r][c] = owner
                    self.board_colors[r][c] = color
                    
                    if (r, c) in self.selecting_cells:
                        if self.selecting_cells[(r, c)]["player"] == self.player_name:
                            self.is_selecting = False
                            self.update_status("Selection complete!")
                        
                        del self.selecting_cells[(r, c)]
                        self.checkboxes[r][c]["timer_label"].config(text="")
                    
                    self.update_all_cells()
                    
                    if owner not in self.player_colors:
                        self.player_colors[owner] = color
                        self.update_player_legend()
                
                elif msg[0] == 'selection_cancelled':
                    r, c = int(msg[1]), int(msg[2])
                    
                    if (r, c) in self.selecting_cells and self.selecting_cells[(r, c)]["player"] == self.player_name:
                        self.is_selecting = False
                        self.update_status("Selection cancelled")
                    
                    if (r, c) in self.selecting_cells:
                        del self.selecting_cells[(r, c)]
                        self.checkboxes[r][c]["timer_label"].config(text="")
                    
                    self.update_all_cells()
                
                elif msg[0] == 'selecting':
                    r, c = int(msg[1]), int(msg[2])
                    player = msg[3]
                    color = msg[4]
                    duration = float(msg[5])
                    
                    self.selecting_cells[(r, c)] = {
                        "player": player,
                        "color": color,
                        "end_time": time.time() + duration
                    }
                    
                    if player == self.player_name:
                        self.is_selecting = True
                        self.update_status(f"Selecting cell... {duration:.1f}s")
                    
                    self.update_all_cells()
                
                elif msg[0] == 'block_adjacent':
                    r, c = int(msg[1]), int(msg[2])
                    player = msg[3]
                    color = msg[4]
                    duration = float(msg[5])
                    
                    self.blocked_cells[(r, c)] = {
                        "player": player,
                        "color": color,
                        "end_time": time.time() + duration,
                        "blink_state": False
                    }
                    
                    for sel_r in range(10):
                        for sel_c in range(10):
                            if (sel_r, sel_c) in self.selecting_cells and self.selecting_cells[(sel_r, sel_c)]["player"] == player:
                                self.blocked_by_selection[(r, c)] = (sel_r, sel_c)
                                break
                    
                    self.update_cell_appearance(r, c)
                
                elif msg[0] == 'unblock_adjacent':
                    r, c = int(msg[1]), int(msg[2])
                    
                    if (r, c) in self.blocked_cells:
                        del self.blocked_cells[(r, c)]
                    
                    if (r, c) in self.blocked_by_selection:
                        del self.blocked_by_selection[(r, c)]
                    
                    self.update_cell_appearance(r, c)
                
                elif msg[0] == 'player_joined':
                    player = msg[1]
                    color = msg[2]
                    
                    self.player_colors[player] = color
                    self.update_player_legend()
                
                elif msg[0] == 'player_left':
                    player = msg[1]
                    
                    if player in self.player_colors:
                        del self.player_colors[player]
                        self.update_player_legend()
                
            except Exception as e:
                print(f"Error: {e}")
                break
    
    def on_closing(self):
        try:
            self.sock.sendto("disconnect".encode(), (SERVER_IP, SERVER_PORT))
        except:
            pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CheckBoxClient(root)
    root.mainloop()
