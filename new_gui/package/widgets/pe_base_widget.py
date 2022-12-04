from tkinter import ttk
import tkinter as tk


class PeBaseWidget:
    def __init__(self, frame, **kwargs):
        self._frame = ttk.Frame(frame, style="B.TFrame")

    def pack(self, *args, **kwargs):
        self._frame.pack(*args, **kwargs)
        return self


class AppendablePeBaseWidget(PeBaseWidget):
    def __init__(self, frame, **kwargs):
        super(AppendablePeBaseWidget, self).__init__(frame, **kwargs)
        self._addons = []

    def add_on_right(self, w, **kwargs):
        tmp = w(self._frame, **kwargs)
        tmp.pack(side=tk.LEFT)
        self._addons.append(tmp)
        return self

    def add_and_return(self, w, **kwargs):
        tmp = w(self._frame, **kwargs)
        self._addons.append(tmp)
        return self._addons[-1]