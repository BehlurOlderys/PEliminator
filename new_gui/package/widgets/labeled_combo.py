from .pe_base_widget import AppendablePeBaseWidget
from tkinter import ttk
import tkinter as tk


class LabeledCombo(AppendablePeBaseWidget):
    def __init__(self, desc, values, prevalue, event_handler=None, **kwargs):
        super(LabeledCombo, self).__init__(**kwargs)
        self._values = values
        if prevalue not in self._values:
            raise RuntimeError("Trying to use prevalue not present in values list!")
        self._value = tk.StringVar(value=prevalue)
        self._event_handler = event_handler

        self._label = ttk.Label(self._frame, text=desc, style="B.TLabel")
        self._label.pack(side=tk.LEFT)
        self._combobox = ttk.Combobox(self._frame, textvariable=self._value,
                                      values=self._values, style="B.TCombobox")
        self._combobox.pack(side=tk.RIGHT)
        self._combobox.bind('<<ComboboxSelected>>', self._event_handler)

    def set_list(self, values, prevalue):
        self._combobox.config(values=values)
        self._combobox.set(prevalue)

    def get_value(self):
        return self._value.get()
