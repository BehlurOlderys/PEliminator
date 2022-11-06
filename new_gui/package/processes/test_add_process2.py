from package.widgets.application import SimpleGuiApplication
from package.widgets.labeled_input import LabeledInput
import tkinter as tk


class TestAddingGui2(SimpleGuiApplication):
    def __init__(self, in_queue, *args, **kwargs):
        super(TestAddingGui2, self).__init__(*args, **kwargs)
        self._in = in_queue

        self._li = LabeledInput(frame=self._main_frame, desc="Value", initial_value=0).pack(side=tk.LEFT)

    def _task(self):
        if not self._in.empty():
            data = self._in.get()
            if data == 'KILL_ME_NOW':
                self._root.destroy()
            self._li.set_value(data)
        self._root.after(1000, self._task)

    def run(self):
        self._root.after(1000, self._task)
        super(TestAddingGui2, self).run()
