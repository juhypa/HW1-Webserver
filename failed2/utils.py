import socket
import threading
from queue import Queue

ENCD = 'utf-8'

class ResponseHeader:
    def __init__(self,  version:str="HTTP/1.1",
                        status:str="200",
                        status_text:str="OK",
                        server_name:str="lab",
                        content_type:str="text/html",
                        encoding:str='utf-8',
                        connection:str='closed' ):

        self.version = version
        self.status = status
        self.status_text = status_text
        self.server = server_name
        self.content_type = content_type
        self.encoding = encoding
        self.connection = connection

    def wrap_html(self, html_body:str)->str:
        start_line = f"{self.version} {self.status} {self.status_text}"
        http_header_dict = {
            "Content-Type" : f"{self.content_type}; encoding={self.encoding}",
            "Content-Length" : len(html_body),
            "Connection" : self.connection
        }
        http_header_list = [f"{key}: {val}" for key, val in http_header_dict.items()]

        wrapped_html = '\r\n'.join([start_line, *http_header_list, "", html_body])
        return wrapped_html

class ClientsCommunicator:
    def __init__(self):
        self.registered_clients = []
        self.msgque = Queue()
        self.html_body = ""

    def start_send_thread(self):
        send_thread = threading.Thread(target=self._sending_to_all_registered_clients)
        send_thread.start()

    def _sending_to_all_registered_clients(self):
        while True:
            if not self.msgque.empty():
                msg_context = self._get_msg_context()
                self.html_body = self._put_msg_context_to_html_body(msg_context)

                for client in self.registered_clients:
                    html_body = self.html_body[:]
                    if client._sending(html_body)==-1:
                        self.registered_clients.remove(client)

    def _get_msg_context(self):
        msg_context = ""
        while not self.msgque.empty():
            msg = self.msgque.get()
            msg_context = '<br>'.join((msg_context, msg))
        return msg_context

    def _put_msg_context_to_html_body(self, msg_context:str):
        html_body = self.html_body
        msg_context_idx = html_body.find('</span>')
        html_body = ''.join((html_body[:msg_context_idx], msg_context, html_body[msg_context_idx:]))
        return html_body

    def register_client_and_start_recieve_thread(self, client_socket:socket.socket, addr:tuple):
        client = self._register_client(client_socket, addr)
        recv_thread = threading.Thread(target=client._recieving, args=(self.msgque,))
        recv_thread.start()

    def _register_client(self, client_socket:socket.socket, addr:tuple):
        ip = addr[0]
        port = addr[1]
        client = self._Client(client_socket, ip, port)
        self.registered_clients.append(client)
        return client

    def get_html_body(self, html_directory:str):
        with open(html_directory, 'r', encoding=ENCD) as f:
            self.html_body = f.read()

    class _Client:
        def __init__(self, client_socket:socket.socket, ip:str, port:str):
            self.sock = client_socket
            self.ip = ip
            self.port = port
            self.color = 'white'
            self.HTTP_version = 'HTTP/1.1'

        def _sending(self, html_body:str):
            client_socket = self.sock

            html_body = html_body.replace('white', self.color, 1)

            wrapped_HTML = ResponseHeader(version=self.HTTP_version, encoding=ENCD).wrap_html(html_body)
            encoded_HTML = wrapped_HTML.encode(ENCD)

            try:
                client_socket.sendall(encoded_HTML)
            except:
                print(f"Disconnect {self.ip}")
                client_socket.close()
                return -1

        def _recieving(self, msgque:Queue):
            while True:
                client_socket = self.sock
                data = client_socket.recv(1024)
                if not data:
                    print(f"Disconnect {self.ip} - No Data")
                    client_socket.close()
                    return -1
                
                HTTP_requset = data.decode().split('\r\n')

                HTTP_method, HTTP_get, self.HTTP_version = HTTP_requset[0].split()
                HTTP_post = HTTP_requset[-1]

                if HTTP_get.find('bgc=')!=-1:
                    self.color = self._get_color_from_HTTP_GET(HTTP_get)

                if HTTP_post.find('msg=')!=-1:
                    msg = self._get_msg_from_HTTP_GET(HTTP_post)
                    msg = f"{self.ip}: {msg}"
                    msgque.put(msg)
                    print(msg)

        def _get_color_from_HTTP_GET(self, HTTP_get:str):
            color_idx = HTTP_get.find('bgc=') + 4
            color = HTTP_get[color_idx:color_idx+5]
            return color

        def _get_msg_from_HTTP_GET(self, HTTP_post:str):
            msg_idx = HTTP_post.find('msg=') + 4
            msg = HTTP_post[msg_idx:msg_idx+5]
            return msg