import socket
import os

import ConnectionHandler

class Server:

    def main(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', 53333))
        server_socket.listen(5)
        print("Server is running...")

        while True:
            client_socket, addr = server_socket.accept()
            print("Client connected")

            data_out = client_socket.makefile('wb')
            file_path = "src/JSONFiles/serverData.json"
            file_in = open(file_path, 'rb')
            data_in = client_socket.makefile('rb')

            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            data_out.write(file_name.encode('utf-8') + b'\n')
            data_out.write(str(file_size).encode('utf-8') + b'\n')

            buffer = bytearray(4096)
            while True:
                bytes_read = file_in.readinto(buffer)
                if bytes_read == 0:
                    break
                data_out.write(buffer[:bytes_read])

            file_name = data_in.readline().decode('utf-8').strip()
            file_size = int(data_in.readline().decode('utf-8').strip())

            received_file = open(file_name, 'wb')
            try:
                remaining = file_size
                while remaining > 0:
                    bytes_read = data_in.readinto(buffer)
                    if bytes_read == 0:
                        break
                    received_file.write(buffer[:bytes_read])
                    remaining -= bytes_read
            finally:
                received_file.close()

            print("File received: " + file_name)

            handler = ConnectionHandler(received_file)
            handler.show_server_side()

            print("Finished processing Server")
            data_out.close()
            file_in.close()
            client_socket.close()

if __name__ == "__main__":
    server = Server()
    server.main()