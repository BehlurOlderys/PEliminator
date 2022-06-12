import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class PointPlot:
    def __init__(self, frame):
        data_figure = plt.Figure(dpi=100)
        self._ax = data_figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(data_figure, frame)
        self._canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._data_t = []
        self._ax.plot()
        self._first_point = None

    def _clear_plot(self):
        self._data_t = []
        self._ax.plot()

    def _redraw(self):
        self._ax.relim()
        self._ax.autoscale_view()
        self._canvas.draw()
