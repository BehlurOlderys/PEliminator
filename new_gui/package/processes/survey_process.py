import time

from .child_process import ChildProcessGUI
from package.widgets.labeled_input import LabeledInput
from tkinter import ttk
import tkinter as tk


class SurveyProcessGUI(ChildProcessGUI):
    def __init__(self, serial_out_queue, serial_in_queue, *args, **kwargs):
        super(SurveyProcessGUI, self).__init__(title="Survey", *args, **kwargs)
        self._serial_out = serial_out_queue
        self._serial_in = serial_in_queue

        controls_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        controls_frame.pack(side=tk.TOP)

        self._interval_input = LabeledInput(frame=self._main_frame, desc="Interval [s]")\
            .add_on_right(ttk.Button, text="Start", command=self._start, style="B.TButton")\
            .pack(side=tk.LEFT)

    def _start(self):
        v = int(self._interval_input.get_value())
        print(f"Starting survey with interval={v}s")
        for i in range(0, 10):
            print(f"Sleeping for {v}s")
            time.sleep(v)
            print("Putting move ra command!")
            self._serial_out.put("move_ra")
            ack = self._serial_in.get()
            if ack != "move_done":
                print("Error, quiting interval!")
            else:
                print("Movement acked!")
