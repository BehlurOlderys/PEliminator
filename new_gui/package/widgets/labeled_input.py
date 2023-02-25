from .pe_base_widget import AppendablePeBaseWidget
from tkinter import ttk
import tkinter as tk


class LabeledInput(AppendablePeBaseWidget):
    def __init__(self, desc="Label: ", initial_value=0, from_=0, to=999, width=3, increment=1, callback=None, **kwargs):
        super(LabeledInput, self).__init__(**kwargs)
        self._value_var = tk.StringVar(value=min(to, max(from_, initial_value)))

        if callback is not None:
            self._value_var.trace("w", lambda name, index, mode, sv=self._value_var: callback(sv))

        gain_label = ttk.Label(self._frame, text=desc, style="B.TLabel")
        gain_label.pack(side=tk.LEFT)
        gain_spin = ttk.Spinbox(self._frame,
                                textvariable=self._value_var,
                                from_=from_,
                                to=to,
                                increment=increment,
                                width=width,
                                style="B.TSpinbox")
        gain_spin.pack(side=tk.LEFT)

    def set_value(self, v):
        self._value_var.set(v)

    def get_value(self):
        return self._value_var.get()
