from .pe_base_widget import AppendablePeBaseWidget
from tkinter import ttk
import tkinter as tk


class ArrowsControls(AppendablePeBaseWidget):
    def __init__(self, descriptions, event_handlers, **kwargs):
        """
        :param descriptions: map of strings with keys: UP, DOWN, LEFT, RIGHT
        :param event_handlers: map of handlers same keys as descriptions
        :param kwargs:
        """
        super(ArrowsControls, self).__init__(**kwargs)
        self._up_frame = ttk.Frame(self._frame, style="B.TFrame")
        self._up_frame.pack(side=tk.TOP)
        self._middle_frame = ttk.Frame(self._frame, style="B.TFrame")
        self._middle_frame.pack(side=tk.TOP)
        self._bottom_frame = ttk.Frame(self._frame, style="B.TFrame")
        self._bottom_frame.pack(side=tk.TOP)

        self._up_button = ttk.Button(self._up_frame,
                                     text=descriptions["UP"],
                                     command=event_handlers["UP"]).pack(side=tk.TOP)
        self._left_button = ttk.Button(self._middle_frame,
                                     text=descriptions["LEFT"],
                                     command=event_handlers["LEFT"]).pack(side=tk.LEFT)
        self._right_button = ttk.Button(self._middle_frame,
                                     text=descriptions["RIGHT"],
                                     command=event_handlers["RIGHT"]).pack(side=tk.RIGHT)
        self._down_button = ttk.Button(self._bottom_frame,
                                     text=descriptions["DOWN"],
                                     command=event_handlers["DOWN"]).pack(side=tk.TOP)
