import tkinter as tk
from tkinter import ttk


class IPAddressInput:
    def __init__(self, frame, on_connect):
        """

        :param frame:
        :param on_connect: Should be a function with two arguments: host and port
        """
        self._address = tk.StringVar(value="localhost")
        self._port = tk.StringVar(value="8080")

        address_frame = ttk.Frame(frame, style="B.TFrame")
        address_frame.pack(side=tk.TOP)

        address_label = ttk.Label(address_frame, text="Camera IP address", style="B.TLabel")
        address_label.pack(side=tk.LEFT)

        address_input = tk.Entry(address_frame, textvariable=self._address)
        address_input.pack(side=tk.LEFT)

        port_label = ttk.Label(address_frame, text="port", style="B.TLabel")
        port_label.pack(side=tk.LEFT)

        port_input = tk.Entry(address_frame, textvariable=self._port)
        port_input.pack(side=tk.LEFT)

        connect_button = ttk.Button(address_frame,
                                    text="Connect",
                                    command=lambda: on_connect(self.get_address(), self.get_port()),
                                    style="B.TButton")
        connect_button.pack(side=tk.LEFT)

    def get_address(self):
        return self._address.get()

    def get_port(self):
        return self._port.get()
