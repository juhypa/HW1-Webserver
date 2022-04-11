from utils import *
import socket
HOST = "localhost"
PORT = 9999

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()
print("Start Linstening")

socket_handler = ThreadedClientSocketHandler()
socket_handler.start_sending_to_all_registered_clients_thread()

while True:
    try:
        print("Wait Listening")
        client_socket, addr = server_socket.accept()
        socket_handler.register_client_socket_and_init_recv_thread(client_socket, addr)
    except:
        break

server_socket.close()
print("Server Closed")