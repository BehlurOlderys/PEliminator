import tkinter as tk
from tkinter import ttk


class SpinWithLabel:
    def __init__(self, frame, variable, name_str, **kwargs):
        self._label = tk.Label(frame, text=name_str, font=('calibre', 10, 'bold'))
        self._label.pack(side=tk.LEFT)

        self._spin = ttk.Spinbox(frame, textvariable=variable, **kwargs)
        self._spin.pack(side=tk.LEFT)
