from .pe_base_widget import PeBaseWidget
from tkinter import ttk
import tkinter as tk


class LabeledInput(PeBaseWidget):
    def __init__(self, desc="Label: ", initial_value=0, from_=0, to=999, width=3, **kwargs):
        super(LabeledInput, self).__init__(**kwargs)
        self._value_var = tk.StringVar(value=initial_value)
        gain_label = ttk.Label(self._frame, text=desc, style="B.TLabel")
        gain_label.pack(side=tk.LEFT)
        gain_spin = ttk.Spinbox(self._frame, textvariable=self._value_var, from_=from_, to=to, width=width, style="B.TSpinbox")
        gain_spin.pack(side=tk.LEFT)
        self._addons = []

    def add_on_right(self, w, **kwargs):
        tmp = w(self._frame, **kwargs)
        tmp.pack(side=tk.LEFT)
        self._addons.append(tmp)
        return self

    def set_value(self, v):
        self._value_var.set(v)

    def get_value(self):
        return self._value_var.get()
