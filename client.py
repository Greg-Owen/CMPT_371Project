import socket
import os

class Client:

    @staticmethod
    def main():
        gui = GUI()
        Client().run_client(gui)

    def run_client(self, gui):
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_socket.connect(("localhost", 53333))
        data_out = my_socket.makefile('wb')
        data_in = my_socket.makefile('rb')

        file_name = data_in.readline().decode().strip()
        file_size = int(data_in.readline().strip())

        received_file = open(file_name, 'wb')
        remaining = file_size

        while remaining > 0:
            buffer = data_in.read(min(4096, remaining))
            if not buffer:
                break
            received_file.write(buffer)
            remaining -= len(buffer)

        received_file.close()
        print("File received:", file_name)

        handler = ConnectionHandler(received_file)
        handler.show_client_side()

        # update GUI here
        gui.set_received_text(handler.update_client_side())

        # send client data back to server
        with open("src/JSONFiles/clientData.json", 'rb') as file_in:
            file = "src/JSONFiles/clientData.json"
            data_out.write(f"{os.path.basename(file)}\n".encode())
            data_out.write(f"{os.path.getsize(file)}\n".encode())

            buffer = file_in.read(4096)
            while buffer:
                data_out.write(buffer)
                buffer = file_in.read(4096)

        data_out.close()
        data_in.close()
        my_socket.close()