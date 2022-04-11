import socket
import threading
from queue import Queue

class ResponseHeader:
    def __init__(self,  version:str="HTTP/1.1",
                        status:str="200",
                        status_text:str="OK",
                        server_name:str="lab",
                        content_type:str="text/html",
                        encoding:str='utf-8',
                        connection:str='keep-alive' ):

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

class ThreadedClientSocketHandler:
    def __init__(self):
        self.registerd_clients = []
        self.msgque = Queue()
        # self.msgcontext = ""
        with open("home.html", "r", encoding='utf-8') as f:
            self.html_body = f.read()

    def register_client_socket_and_init_recv_thread(self, client_socket:socket.socket, addr:any):
        client = self._ClientSocket(client_socket, addr)
        self.registerd_clients.append(client)
        recv_thread = threading.Thread(target=client.recieve, args=(self.msgque,))
        recv_thread.start()
        
    def start_sending_to_all_registered_clients_thread(self):
        send_thread = threading.Thread(target=self._sending_to_all_registerd_clients)
        send_thread.start()

    def _sending_to_all_registerd_clients(self):
        while True:
            if 0 < len(self.registerd_clients):
                msg = self.msgque.get()
                
                # self.msgcontext = '<br>'.join((self.msgcontext, msg))   
                
                msgcontext_idx = self.html_body.find('</textarea>')
                self.html_body = ''.join((self.html_body[:msgcontext_idx], msg, self.html_body[msgcontext_idx:]))
                
                for client in self.registerd_clients:
                    if self._check_socket_connected(client):
                        html_body = self.html_body.replace('black', client.color)
                        wrapped_html = ResponseHeader(client.rq_version).wrap_html(html_body)
                        client.sock.sendall(wrapped_html.encode())
                    else:
                        client.sock.close()
                        self.registerd_clients.remove(client)

    def _check_socket_connected(self, client_socket:socket.socket):
        try:
            client_socket.sendall(b'ping')
            return True
        except:
            return False
    
    class _ClientSocket:
        def __init__(self, client_socket:socket.socket, addr:any):
            self.sock = client_socket
            self.ip = addr[0]
            self.port = addr[1]
            self.color = 'black'
            self.rq_version = 'HTTP/1.1'

        def recieve(self, msgque:Queue):
            while True:
                try:
                    data = self.sock.recv(1024)
                    if not data:
                        msgque.put(f"Disconnect {self.ip} - No received data")
                        self.sock.close()
                        break
                    http_request = data.decode().split('\r\n')
                    rq_method, rq_get, self.rq_version = http_request[0].split()
                    rq_post = http_request[-1]

                    if rq_method is 'POST':
                        msg_idx = rq_post.find('msg=') + 4
                        msg = rq_post[msg_idx:]
                        msgque.put(f"{self.ip}:{msg}")
                    if rq_method is 'GET':
                        color_idx = rq_get.find('bgc=') + 4
                        if -1 < color_idx:
                            self.color = rq_get[color_idx:color_idx+5]

                except ConnectionError as e:
                    msgque.put(f"Disconnet {self.ip} - {e}")
                    self.sock.close()
                    break
