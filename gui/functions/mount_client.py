import socket
from functions.global_settings import mount_server_port


class MountClient:
    def __init__(self):
        self._host = socket.gethostname()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self._host, mount_server_port))

    def send(self, s):
        self._socket.sendall(s.encode())
