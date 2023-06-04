from tkinter import ttk
import tkinter as tk
from tkinter import filedialog
from .pe_base_widget import PeBaseWidget
import os


class DirChooser(PeBaseWidget):
    def __init__(self, dir_desc="Chosen image dir: ", initial_dir=".", dialog_text="Open directory", **kwargs):
        super(DirChooser, self).__init__(**kwargs)
        self._dialog_text = dialog_text
        self._directory = initial_dir
        self._dir_var = tk.StringVar(value=os.path.basename(os.path.normpath(initial_dir)))
        self._label = ttk.Label(self._frame, text=dir_desc, style="B.TLabel")
        self._label.pack(side=tk.LEFT)

        self._value = ttk.Label(self._frame, textvariable=self._dir_var, style="B.TLabel")
        self._value.pack(side=tk.LEFT)

        self._button = ttk.Button(self._frame, text='Change...', command=self._change_dir)
        self._button.pack(side=tk.LEFT)

    def get_dir(self):
        return self._directory

    def get_value(self):
        return self._directory

    def _change_dir(self):
        new_dir = filedialog.askdirectory(title=self._dialog_text,
                                          initialdir=self._dir_var.get())
        if not new_dir:
            print("No directory is chosen!")
            return
        print(f"Dir chosen = {new_dir}")
        self._directory = new_dir
        self._dir_var.set(os.path.basename(os.path.normpath(new_dir)))
