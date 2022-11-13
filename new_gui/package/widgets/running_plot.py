from .pe_base_widget import PeBaseWidget
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class RunningPlot(PeBaseWidget):
    def __init__(self, max_span=100, **kwargs):
        super(RunningPlot, self).__init__(**kwargs)
        data_figure = plt.Figure(dpi=72, facecolor="#222222")
        self._ax = data_figure.subplots(1, 1)
        data_figure.subplots_adjust(bottom=0.2)
        self._canvas = FigureCanvasTkAgg(data_figure, self._frame)
        self._canvas.get_tk_widget().pack(side=tk.RIGHT, expand=True)
        self._lines = self._ax.plot(0, 0, 'r', 0, 0, 'g', linewidth=2.0)
        self._xdata = [0]
        self._ydata = [0]
        self._tdata = [0]
        self._max_span_t = max_span
        self._max_t = max_span
        self._max_value = 1
        self._min_value = -1

        self._ax.set_xlim(0, self._max_span_t)
        self._ax.set_facecolor("#222222")
        self._canvas.draw()

    def clear(self):
        self._xdata = []
        self._ydata = []
        self._tdata = []

        self._lines[0].set_xdata(self._tdata)
        self._lines[0].set_ydata(self._xdata)
        self._lines[1].set_xdata(self._tdata)
        self._lines[1].set_ydata(self._ydata)

        self._canvas.draw()

    def add_point(self, p):
        t, x, y = p
        self._xdata.append(x)
        self._ydata.append(y)
        self._tdata.append(t)
        self._lines[0].set_xdata(self._tdata)
        self._lines[0].set_ydata(self._xdata)

        self._lines[1].set_xdata(self._tdata)
        self._lines[1].set_ydata(self._ydata)

        self._max_value = max(self._max_value, max(x+1, y+1))
        self._min_value = min(self._min_value, min(x-1, y-1))
        self._max_t = max(self._max_t, t)

        self._ax.set_ylim(self._min_value, self._max_value)
        self._ax.set_xlim(right=self._max_t, left=max(0, self._max_t-self._max_span_t))
        self._canvas.draw_idle()
