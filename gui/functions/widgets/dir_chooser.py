from tkinter import ttk
import tkinter as tk
from tkinter import filedialog


class PeBaseWidget:
    def __init__(self, frame, **kwargs):
        self._frame = ttk.Frame(frame, style="B.TFrame")

    def pack(self, *args, **kwargs):
        self._frame.pack(*args, **kwargs)
        return self


class LabeledInput(PeBaseWidget):
    def __init__(self, desc="Label: ", initial_value=0, from_=0, to=999, width=3, **kwargs):
        super(LabeledInput, self).__init__(**kwargs)
        self._value_var = tk.StringVar(value=initial_value)
        gain_label = ttk.Label(self._frame, text=desc, font=('calibre', 10, 'bold'), style="B.TLabel")
        gain_label.pack(side=tk.LEFT)
        gain_spin = ttk.Spinbox(self._frame, textvariable=self._value_var, from_=from_, to=to, width=width, style="B.TSpinbox")
        gain_spin.pack(side=tk.LEFT)

    def get_value(self):
        return self._value_var.get()


class DirChooser(PeBaseWidget):
    def __init__(self, dir_desc="Chosen image dir: ", initial_dir=".", dialog_text="Open directory", **kwargs):
        super(DirChooser, self).__init__(**kwargs)
        self._dialog_text = dialog_text
        self._dir_var = tk.StringVar(value=initial_dir)
        self._label = ttk.Label(self._frame, text=dir_desc, style="B.TLabel")
        self._label.pack(side=tk.LEFT)

        self._value = ttk.Label(self._frame, textvariable=self._dir_var, style="B.TLabel")
        self._value.pack(side=tk.LEFT)

        self._button = ttk.Button(self._frame, text='Change...', command=self._change_dir)
        self._button.pack(side=tk.LEFT)

    def get_dir(self):
        return self._dir_var.get()

    def _change_dir(self):
        new_dir = filedialog.askdirectory(title=self._dialog_text,
                                          initialdir=self._dir_var.get())
        if not new_dir:
            print("No directory is chosen!")
            return
        print(f"Dir chosen = {new_dir}")
        self._dir_var.set(new_dir)
