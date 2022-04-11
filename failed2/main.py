import socket
from utils import *
import threading

HOST = 'localhost'
PORT = 9999
ENCD = 'utf-8'

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()
print("Start Linstening")

clients_communicator = ClientsCommunicator()
clients_communicator.get_html_body('home.html')
clients_communicator.start_send_thread()

while True:

    client_socket, addr = server_socket.accept()

    clients_communicator.register_client_and_start_recieve_thread(client_socket, addr)

server_socket.close()
print("server closed")