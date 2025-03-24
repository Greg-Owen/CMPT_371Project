import socket
import threading

HOST = '0.0.0.0'
PORT = 5005

# Shared 10x10 board (False = unchecked, True = checked)
board = [[False for _ in range(10)] for _ in range(10)]
board_lock = threading.Lock()
clients = set()

def handle_updates():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST, PORT))
        print("Server listening on port", PORT)
        while True:
            data, addr = sock.recvfrom(1024)
            msg = data.decode().split(',')
            if msg[0] == 'register':
                clients.add(addr)
                # Sync new client with entire board
                with board_lock:
                    # Flatten the board into a single list
                    board_state = [str(cell) for row in board for cell in row]
                # Send the "board" message with all cells
                sync_msg = "board," + ",".join(board_state)
                sock.sendto(sync_msg.encode(), addr)
            elif msg[0] == 'click':
                row, col = int(msg[1]), int(msg[2])
                with board_lock:
                    board[row][col] = not board[row][col]
                # Broadcast to all clients
                broadcast_msg = f"update,{row},{col},{board[row][col]}"
                for c in clients:
                    sock.sendto(broadcast_msg.encode(), c)

if __name__ == '__main__':
    t = threading.Thread(target=handle_updates, daemon=True)
    t.start()
    t.join()