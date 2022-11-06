from tkinter import ttk


class PeBaseWidget:
    def __init__(self, frame, **kwargs):
        self._frame = ttk.Frame(frame, style="B.TFrame")

    def pack(self, *args, **kwargs):
        self._frame.pack(*args, **kwargs)
        return self
