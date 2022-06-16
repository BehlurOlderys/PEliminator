import socket
from functions.global_settings import mount_server_port
from tkinter import  ttk
from functions.serial_reader import SerialReader, get_available_com_ports
from threading import Thread
import tkinter as tk
import time


class ConnectionManager:
    def __init__(self, r, st, c):
        self._message = None
        self._reader = r
        self._serial_thread = st
        self._com_port_choice = c

    def connect_to_chosen_port(self):
        chosen_port = self._com_port_choice.get()
        print(f"Connecting to port: {chosen_port}\n")
        try:
            welcome_message = reader.connect_to_port(chosen_port)
            print(f"{welcome_message}\n")
            self._serial_thread.start()
            return True

        except Exception as e:
            print(f"Encountered exception: {e} while connecting to port {chosen_port}")
            return False


class MountServer:
    def __init__(self, serial_reader):
        self._serial_reader = serial_reader
        self._socket = socket.socket()
        self._host = socket.gethostname()
        self._threads = []
        self._kill = False

    def kill(self):
        self._kill = True

    def start(self):
        self._socket.bind((self._host, mount_server_port))
        print("Server started!")
        self._socket.listen(5)
        while not self._kill:
            c, addr = self._socket.accept()
            print(f"Got connection from: {c}, {addr}")
            client_thread = Thread(target=self.on_new_client, args=(c, addr))
            client_thread.start()
            self._threads.append(client_thread)

        self._socket.close()

    def on_new_client(self, clientsocket, addr):
        while True:
            try:
                msg = clientsocket.recv(128).decode()
            except ConnectionResetError:
                print(f"Connection reset!")
                break
            if not msg:
                print(f"Client {clientsocket} disconnected!")
                break

            print(f"{addr}: {msg}")
        self._serial_reader.write_immediately(f"{msg}\n".encode())
        clientsocket.close()


root = tk.Tk()
available_ports = get_available_com_ports()
com_port_choice = tk.StringVar(value=available_ports[0])
reader = SerialReader()
serial_thread = Thread(target=reader.loop)
connection_manager = ConnectionManager(reader, serial_thread, com_port_choice)
root.title("PEliminator Serial server")


mount_tab = tk.Frame(root)
mount_tab.pack(fill='both', expand=True)

connect_frame = tk.Frame(mount_tab, highlightbackground="black", highlightthickness=1)
connect_frame.pack(side=tk.TOP)

combobox = ttk.Combobox(connect_frame, textvariable=com_port_choice, values=available_ports)
combobox.pack(side=tk.LEFT)


def connect_to_serial():
    print("Trying to connect")
    if connection_manager.connect_to_chosen_port() is True:
        start_server_button.configure(state='normal')


choose_port_button = tk.Button(connect_frame, text="Connect", command=connect_to_serial)
choose_port_button.pack(side=tk.LEFT)

mount_server = MountServer(reader)
mount_server_thread = None


def start_server():
    global mount_server_thread
    mount_server_thread = Thread(target=mount_server.start)
    mount_server_thread.start()


start_server_button = tk.Button(connect_frame, text="Start server", command=start_server, state='disabled')
start_server_button.pack(side=tk.LEFT)


root.mainloop()
print("End of main loop!")
reader.kill()
time.sleep(10)

if reader.is_connected():
    serial_thread.join()
