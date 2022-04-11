import socket
from utils import *

HOST = 'localhost'
PORT = 9999
ENCD = 'utf-8'

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()
print("Start Linstening")

comm_manager = CommunicationManager()
comm_manager.get_html_body('home.html')

while True:
    try:
        client_socket, addr = server_socket.accept()

        comm_manager.start_communicating_thread(client_socket, addr)
    except:
        break

server_socket.close()
print("server closed")