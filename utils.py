import socket
import threading

ENCD = 'utf-8'

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

class _Client:
    def __init__(self, client_socket:socket.socket, ip:str, port:str):
        self.sock = client_socket
        self.ip = ip
        self.port = port
        self.color = 'white'
        self.HTTP_version = 'HTTP/1.1'

    def _recieve(self, msglist:list):
        client_socket = self.sock
        try:
            data = client_socket.recv(4096)
            if not data:
                return -1
        except:
            return -1
        
        HTTP_requset = data.decode(ENCD).split('\r\n')

        HTTP_method, HTTP_get, self.HTTP_version = HTTP_requset[0].split()
        HTTP_post = HTTP_requset[-1]

        if HTTP_get.find('bgc=')!=-1:
            self.color = self._get_color_from_HTTP_GET(HTTP_get)

        if HTTP_post.find('msg=')!=-1:
            msg = self._get_msg_from_HTTP_POST(HTTP_post)
            msg = f"{self.ip}: {msg}"
            msglist.append(msg)

    def _send(self, html_body:str):
        client_socket = self.sock

        html_body = html_body.replace('white', self.color, 1)

        wrapped_HTML = ResponseHeader(version=self.HTTP_version, encoding=ENCD).wrap_html(html_body)
        encoded_HTML = wrapped_HTML.encode(ENCD)
        try:
            client_socket.sendall(encoded_HTML)
        except:
            return -1

    def _get_color_from_HTTP_GET(self, HTTP_get:str):
        color_idx = HTTP_get.find('bgc=') + 4
        color = HTTP_get[color_idx:color_idx+5]
        return color

    def _get_msg_from_HTTP_POST(self, HTTP_post:str):
        msg_idx = HTTP_post.find('msg=') + 4
        msg = HTTP_post[msg_idx:].replace("+", " ")
        return msg

class CommunicationManager:
    def __init__(self):
        self.msglist = []
        self.html_body_container = []

    def get_html_body(self, html_directory:str):
        with open(html_directory, 'r', encoding=ENCD) as f:
            self.html_body = f.read()

    def start_communicating_thread(self, client_socket:socket.socket, addr:tuple):
        client = _Client(client_socket, addr[0], addr[1])
        comm_thread = threading.Thread(target=self._communicating, args=(client,))
        comm_thread.start()

    def _communicating(self, client:_Client):
        while True:
            client._recieve(self.msglist)
            msg_context = self._get_msg_context(self.msglist)
            html_body = self._put_msg_context_to_html_body(self.html_body, msg_context)
            client._send(html_body)
    
    def _get_msg_context(self, msglist:list):
        msg_context = ""
        for msg in msglist:
            msg_context = '\n'.join((msg, msg_context))
        return msg_context

    def _put_msg_context_to_html_body(self, html_body:str, msg_context:str):
        msg_context_idx = html_body.find('</textarea>')
        html_body = ''.join((html_body[:msg_context_idx], msg_context, html_body[msg_context_idx:]))
        return html_body