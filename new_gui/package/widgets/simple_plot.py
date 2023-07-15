from .pe_base_widget import PeBaseWidget
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class SimplePlot(PeBaseWidget):
    def __init__(self, data, frame, height, **kwargs):
        super(SimplePlot, self).__init__(frame)
        self._kwargs = kwargs
        data_figure = plt.Figure(dpi=72, facecolor="#222222")
        self._ax = data_figure.subplots(1, 1)
        data_figure.subplots_adjust(bottom=0.2)
        self._canvas = FigureCanvasTkAgg(data_figure, self._frame)
        self._canvas.get_tk_widget().pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        self._canvas.get_tk_widget().config(height=height)
        x, y = data
        self._plot = self._ax.plot(y, x, **kwargs)
        self._ax.set_facecolor("#222222")
        self._canvas.draw_idle()

    def replot(self, data):
        self._ax.cla()
        x, y = data
        self._plot = self._ax.plot(y, x, **self._kwargs)
        self._canvas.draw_idle()
