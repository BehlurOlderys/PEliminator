import socket
from threading import Thread
from functions.global_settings import mount_server_port


def on_new_client(clientsocket, addr):
    while True:
        msg = clientsocket.recv(1024)
        if not msg:
            break

        print(f"{addr}: {msg}")
    clientsocket.close()


s = socket.socket()
host = socket.gethostname()


print("Server started!")

s.bind((host, mount_server_port))  # Bind to the port
s.listen(5)  # Now wait for client connection.
threads = []
while True:
    c, addr = s.accept()  # Establish connection with client.
    print(f"Got connection from: {c}, {addr}")
    client_thread = Thread(target=on_new_client, args=(c, addr))
    client_thread.start()
    threads.append(client_thread)

s.close()
