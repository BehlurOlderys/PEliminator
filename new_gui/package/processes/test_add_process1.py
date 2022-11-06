from package.widgets.application import SimpleGuiApplication
from package.widgets.labeled_input import LabeledInput
from tkinter import ttk
import tkinter as tk


class TestAddingGui1(SimpleGuiApplication):
    def __init__(self, out_queue, *args, **kwargs):
        super(TestAddingGui1, self).__init__(*args, **kwargs)
        self._out = out_queue

        self._li = LabeledInput(frame=self._main_frame, desc="Value", initial_value=0)\
            .add_on_right(ttk.Button, text='Set', command=self._set_value).pack(side=tk.LEFT)

    def _set_value(self):
        self._out.put(self._li.get_value())