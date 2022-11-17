import time
from .child_process import ChildProcessGUI
from package.widgets.running_plot import RunningPlot1D
import tkinter as tk
from multiprocessing import Queue


class DiagnosticsGUI(ChildProcessGUI):

    def __init__(self, queue: Queue, update_s, *args, **kwargs):
        super(DiagnosticsGUI, self).__init__(title="Camera diagnostics", geometry="400x320", *args, **kwargs)
        self._queue = queue
        self._update_s = update_s

        self._temperature_plot = RunningPlot1D(frame=self._main_frame, max_span=1000)
        self._temperature_plot.pack(side=tk.LEFT)
        self._temperature_plot.clear()
        self._add_task(self._update_s, self._update)

    def _update(self):
        try:
            tem = self._queue.get(timeout=1.0)
            self._temperature_plot.add_point((time.time(), tem))
        except Exception:
            print("No new temperature info for diagnostics!")
