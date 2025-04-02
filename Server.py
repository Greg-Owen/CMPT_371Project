
import sys
import threading
import time
import random

HOST = '0.0.0.0'
PORT = 5005

board = [[None for _ in range(10)] for _ in range(10)]
board_lock = threading.Lock()

clients = {}
next_id = 1
colors = ["red", "blue", "green", "purple", "orange", "magenta", "cyan", "brown", "yellow", "pink"]

selecting_cells = {}
client_selecting = {}

adjacent_blocked_cells = {}
temp_blocked_during_selection = {}

def is_adjacent(row, col, other_row, other_col):
    """Check if two cells are adjacent (not diagonally)"""
    return (row == other_row and abs(col - other_col) == 1) or (col == other_col and abs(row - other_row) == 1)

def get_adjacent_cells(row, col):
    """Get adjacent cells (top, right, bottom, left - not diagonal)"""
    adjacent = []
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < 10 and 0 <= new_col < 10:
            adjacent.append((new_row, new_col))
            
    return adjacent

def clear_temp_blocks_for_selection(sock, row, col):
    """Clear temporary blocks associated with a selection"""
    global temp_blocked_during_selection
    
    cells_to_unblock = []
    for blocked_cell, info in temp_blocked_during_selection.items():
        if info["selection_cell"] == (row, col):
            cells_to_unblock.append(blocked_cell)
    
    for blocked_cell in cells_to_unblock:
        if blocked_cell in temp_blocked_during_selection:
            del temp_blocked_during_selection[blocked_cell]
            
            r, c = blocked_cell
            unblock_msg = f"unblock_adjacent,{r},{c}"
            for client_addr in clients:
                sock.sendto(unblock_msg.encode(), client_addr)

def selection_complete(sock, row, col, client_addr):
    """Called when selection timer completes"""
    with board_lock:
        if (row, col) in selecting_cells and selecting_cells[(row, col)]["addr"] == client_addr:
            client_id = clients[client_addr]["name"]
            color = clients[client_addr]["color"]
            board[row][col] = client_id
            
            del selecting_cells[(row, col)]
            
            if client_addr in client_selecting:
                del client_selecting[client_addr]
            
            update_msg = f"update,{row},{col},{client_id},{color}"
            for c in clients:
                sock.sendto(update_msg.encode(), c)
            
            clear_temp_blocks_for_selection(sock, row, col)
                
            adjacent_cells = get_adjacent_cells(row, col)
            block_duration = 3.0
            end_time = time.time() + block_duration
            
            for adj_r, adj_c in adjacent_cells:
                if board[adj_r][adj_c] is None:
                    adjacent_blocked_cells[(adj_r, adj_c)] = {
                        "owner": client_id,
                        "color": color,
                        "end_time": end_time
                    }
                    
                    block_msg = f"block_adjacent,{adj_r},{adj_c},{client_id},{color},{block_duration}"
                    for c in clients:
                        sock.sendto(block_msg.encode(), c)

def handle_adjacent_cells_timeout():
    """Check for timed out adjacent blocked cells"""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as notify_sock:
        while True:
            time.sleep(0.1)
            current_time = time.time()
            
            with board_lock:
                cells_to_remove = []
                
                for cell, info in adjacent_blocked_cells.items():
                    if current_time >= info["end_time"]:
                        cells_to_remove.append(cell)
                
                for cell in cells_to_remove:
                    if cell in adjacent_blocked_cells:
                        r, c = cell
                        unblock_msg = f"unblock_adjacent,{r},{c}"
                        for client_addr in clients:
                            notify_sock.sendto(unblock_msg.encode(), client_addr)
                        
                        del adjacent_blocked_cells[cell]

def handle_selection_timeout():
    """Check for timed out selections"""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as notify_sock:
        while True:
            time.sleep(0.1)
            current_time = time.time()
            
            with board_lock:
                cells_to_remove = []
                
                for (row, col), info in selecting_cells.items():
                    if current_time >= info["end_time"]:
                        cells_to_remove.append((row, col))
                        client_addr = info["addr"]
                        
                        if client_addr in client_selecting:
                            del client_selecting[client_addr]
                
                for cell in cells_to_remove:
                    if cell in selecting_cells:
                        r, c = cell
                        cancel_msg = f"selection_cancelled,{r},{c}"
                        for client_addr in clients:
                            notify_sock.sendto(cancel_msg.encode(), client_addr)
                        
                        clear_temp_blocks_for_selection(notify_sock, r, c)
                        
                        del selecting_cells[cell]

def handle_updates():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST, PORT))
        print("Server listening on port", PORT)
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                msg = data.decode().split(',')
                
                if msg[0] == 'register':
                    global next_id
                    client_name = f"Player {next_id}"
                    next_id += 1
                    
                    used_colors = {client_data["color"] for client_data in clients.values()}
                    available_colors = [c for c in colors if c not in used_colors]
                    
                    if not available_colors:
                        color = random.choice(colors)
                    else:
                        color = random.choice(available_colors)
                    
                    clients[addr] = {"color": color, "name": client_name}
                    
                    identity_msg = f"identity,{client_name},{color}"
                    sock.sendto(identity_msg.encode(), addr)
                    
                    for client_addr, client_data in clients.items():
                        player_info = f"player_info,{client_data['name']},{client_data['color']}"
                        for c in clients:
                            sock.sendto(player_info.encode(), c)
                    
                    with board_lock:
                        board_state = []
                        for r in range(10):
                            for c in range(10):
                                cell = board[r][c]
                                if cell is None:
                                    board_state.append("None,None")
                                else:
                                    owner_id = cell
                                    owner_color = next((client_data["color"] for client_addr, client_data in clients.items() 
                                                       if client_data["name"] == owner_id), "gray")
                                    board_state.append(f"{owner_id},{owner_color}")
                    
                    sync_msg = "board," + ",".join(board_state)
                    sock.sendto(sync_msg.encode(), addr)
                    
                    for (r, c), selection_info in selecting_cells.items():
                        sel_addr = selection_info["addr"]
                        if sel_addr in clients:
                            sel_color = clients[sel_addr]["color"]
                            sel_name = clients[sel_addr]["name"]
                            remain_time = max(0, selection_info["end_time"] - time.time())
                            sel_msg = f"selecting,{r},{c},{sel_name},{sel_color},{remain_time:.1f}"
                            sock.sendto(sel_msg.encode(), addr)
                            
                            for (temp_r, temp_c), temp_info in temp_blocked_during_selection.items():
                                if temp_info["selection_cell"] == (r, c):
                                    block_msg = f"block_adjacent,{temp_r},{temp_c},{sel_name},{sel_color},{remain_time:.1f}"
                                    sock.sendto(block_msg.encode(), addr)
                    
                    for (r, c), block_info in adjacent_blocked_cells.items():
                        remain_time = max(0, block_info["end_time"] - time.time())
                        block_msg = f"block_adjacent,{r},{c},{block_info['owner']},{block_info['color']},{remain_time:.1f}"
                        sock.sendto(block_msg.encode(), addr)
                    
                    join_msg = f"player_joined,{client_name},{color}"
                    for c in clients:
                        if c != addr:
                            sock.sendto(join_msg.encode(), c)
                    
                elif msg[0] == 'click':
                    if addr not in clients:
                        continue
                        
                    if addr in client_selecting:
                        continue
                        
                    row, col = int(msg[1]), int(msg[2])
                    
                    with board_lock:
                        if (board[row][col] is not None or 
                            (row, col) in selecting_cells or 
                            (row, col) in adjacent_blocked_cells or
                            (row, col) in temp_blocked_during_selection):
                            continue
                        
                        adjacent_in_selection = False
                        for (sel_row, sel_col) in selecting_cells:
                            if is_adjacent(row, col, sel_row, sel_col):
                                adjacent_in_selection = True
                                break
                        
                        if adjacent_in_selection:
                            continue
                            
                        client_name = clients[addr]["name"]
                        client_color = clients[addr]["color"]
                        
                        selection_duration = 3.0
                        end_time = time.time() + selection_duration
                        
                        selecting_cells[(row, col)] = {
                            "addr": addr, 
                            "end_time": end_time
                        }
                        
                        client_selecting[addr] = (row, col)
                        
                        adjacent_cells = get_adjacent_cells(row, col)
                        for adj_r, adj_c in adjacent_cells:
                            if (board[adj_r][adj_c] is None and 
                                (adj_r, adj_c) not in selecting_cells and
                                (adj_r, adj_c) not in adjacent_blocked_cells):
                                
                                temp_blocked_during_selection[(adj_r, adj_c)] = {
                                    "selection_cell": (row, col)
                                }
                                
                                block_msg = f"block_adjacent,{adj_r},{adj_c},{client_name},{client_color},{selection_duration}"
                                for c in clients:
                                    sock.sendto(block_msg.encode(), c)
                        
                        timer = threading.Timer(
                            selection_duration, 
                            selection_complete,
                            args=(sock, row, col, addr)
                        )
                        timer.daemon = True
                        timer.start()
                        
                        selecting_msg = f"selecting,{row},{col},{client_name},{client_color},{selection_duration}"
                        for c in clients:
                            sock.sendto(selecting_msg.encode(), c)
                
                elif msg[0] == 'disconnect':
                    if addr in clients:
                        client_name = clients[addr]["name"]
                        
                        if addr in client_selecting:
                            cell = client_selecting[addr]
                            if cell in selecting_cells:
                                clear_temp_blocks_for_selection(sock, cell[0], cell[1])
                                del selecting_cells[cell]
                            del client_selecting[addr]
                        
                        del clients[addr]
                        
                        disconnect_msg = f"player_left,{client_name}"
                        for c in clients:
                            sock.sendto(disconnect_msg.encode(), c)
                            
            except Exception as e:
                print(f"Error: {e}")

if __name__ == '__main__':
    try:
        update_thread = threading.Thread(target=handle_updates, daemon=True)
        update_thread.start()
        
        timeout_thread = threading.Thread(target=handle_adjacent_cells_timeout, daemon=True)
        timeout_thread.start()
        
        selection_timeout_thread = threading.Thread(target=handle_selection_timeout, daemon=True)
        selection_timeout_thread.start()
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Server shutting down")
        sys.exit(0)