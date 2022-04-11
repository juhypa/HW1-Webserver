import socket
from utils import ResponseHeader

HOST = 'localhost'
PORT = 9999
ENCD = 'utf-8'

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()
print("Start Linstening")

while True:

    client_socket, addr = server_socket.accept()
    data = client_socket.recv(1024)
    if not data:
        print(f"Disconnect {addr[0]} - No Data")
        client_socket.close()
        break
    else:
        print(f"{addr[0]} connected")

    HTTP_requset = data.decode().split('\r\n')

    HTTP_method, HTTP_get, HTTP_version = HTTP_requset[0].split()
    HTTP_post = HTTP_requset[-1]

    with open('home.html', 'r', encoding=ENCD) as f:
        HTML_body = f.read()

    wrapped_HTML = ResponseHeader(version=HTTP_version, encoding=ENCD).wrap_html(HTML_body)
    encoded_HTML = wrapped_HTML.encode(ENCD)

    client_socket.sendall(encoded_HTML)

server_socket.close()