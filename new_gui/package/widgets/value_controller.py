from .pe_base_widget import PeBaseWidget
from tkinter import ttk
import tkinter as tk
from math import log10


class ValueController(PeBaseWidget):
    def __init__(self, getter_fun, setter_fun, desc="Parameter: ", from_=0, to=999, increment=1, **kwargs):
        super(ValueController, self).__init__(**kwargs)
        self._getter = getter_fun
        self._setter = setter_fun
        self._width = int(1.0 + log10(to-from_))
        self._value_var = tk.StringVar()
        self._label = ttk.Label(self._frame, text=desc, style="B.TLabel")
        self._label.pack(side=tk.LEFT)
        self._spin = ttk.Spinbox(self._frame,
                                textvariable=self._value_var,
                                from_=from_,
                                to=to,
                                increment=increment,
                                width=self._width,
                                style="B.TSpinbox")
        self._spin.pack(side=tk.LEFT)

        self._set_button = ttk.Button(self._frame, text='SET', command=self._set_value)
        self._set_button.pack(side=tk.LEFT)
        self._get_button = ttk.Button(self._frame, text='GET', command=self._get_value)
        self._get_button.pack(side=tk.LEFT)
        self._addons = []

    def add_on_right(self, w, **kwargs):
        tmp = w(self._frame, **kwargs)
        tmp.pack(side=tk.LEFT)
        self._addons.append(tmp)
        return self

    def _set_value(self):
        self._setter(self._value_var.get())

    def _get_value(self):
        self._value_var.set(self._getter())

    def self_update(self):
        self._get_value()

    def update(self, v):
        self._value_var.set(v)
