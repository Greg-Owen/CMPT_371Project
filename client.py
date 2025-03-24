import tkinter as tk
import socket
import threading

SERVER_IP = '127.0.0.1'
SERVER_PORT = 5005

class CheckBoxClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Checkbox Grid Client")

        # Local 10x10 board state
        self.board = [[False for _ in range(10)] for _ in range(10)]
        self.check_vars = [[tk.BooleanVar() for _ in range(10)] for _ in range(10)]

        for r in range(10):
            for c in range(10):
                cb = tk.Checkbutton(
                    root,
                    variable=self.check_vars[r][c],
                    command=lambda row=r, col=c: self.handle_click(row, col)
                )
                cb.grid(row=r, column=c)

        # Socket setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.sendto("register".encode(), (SERVER_IP, SERVER_PORT))

        # Listener thread
        self.listener = threading.Thread(target=self.listen_for_updates, daemon=True)
        self.listener.start()

    def handle_click(self, row, col):
        msg = f"click,{row},{col}"
        self.sock.sendto(msg.encode(), (SERVER_IP, SERVER_PORT))

    def listen_for_updates(self):
        while True:
            data, _ = self.sock.recvfrom(1024)
            msg = data.decode().split(',')
            if msg[0] == 'update':
                r, c, val = int(msg[1]), int(msg[2]), msg[3] == 'True'
                self.board[r][c] = val
                self.check_vars[r][c].set(val)

if __name__ == "__main__":
    root = tk.Tk()
    app = CheckBoxClient(root)
    root.mainloop()