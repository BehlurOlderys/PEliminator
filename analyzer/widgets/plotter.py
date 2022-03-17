import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np


class Plotter:
    def __init__(self, frame):
        figure_plot = plt.Figure(figsize=(3, 3), dpi=100)
        self._ax = figure_plot.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(figure_plot, frame)
        self._canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self._data = []
        self._ax.plot()
        self._red_on = True
        self._green_on = True
        self._line_green = None
        self._line_red = None
        self._first_point = None

    def clear_plot(self):
        self._line_green = None
        self._line_red = None
        self._first_point = None
        self._data = []
        self._ax.plot()

    def toggle_red(self):
        if self._red_on:
            if self._line_red is not None:
                self._line_red.remove()
                self._line_red = None

        else:
            data1 = [d[1] for d in self._data]
            datax = np.arange(0, len(self._data))
            self._line_red = self._ax.plot(datax, data1, 'r')[0]

        self._red_on = not self._red_on
        self._redraw()

    def toggle_green(self):
        if self._green_on:
            if self._line_green is not None:
                self._line_green.remove()
                self._line_green = None

        else:
            data1 = [d[0] for d in self._data]
            datax = np.arange(0, len(self._data))
            self._line_green = self._ax.plot(datax, data1, 'g')[0]

        self._green_on = not self._green_on
        self._redraw()

    def _redraw(self):
        self._ax.relim()
        self._ax.autoscale_view()
        self._canvas.draw()

    def get_green_state(self):
        return self._green_on

    def get_red_state(self):
        return self._red_on

    def add_points(self, ps):
        if not self._data:
            self._first_point = ps[0]
            self._line_green, self._line_red = self._ax.plot(0, 0, 'g', 0, 0, 'r')
        x0, y0 = self._first_point
        for p in ps:
            x, y = p
            mp = (x - x0, y - y0)
            self._data.append(mp)

        data1 = [d[0] for d in self._data]
        data2 = [d[1] for d in self._data]
        datax = np.arange(0, len(self._data))

        self._line_green.set_ydata(data1)
        self._line_green.set_xdata(datax)
        self._line_red.set_ydata(data2)
        self._line_red.set_xdata(datax)
        self._redraw()

    def add_point(self, p):
        x, y = p
        if not self._data:
            self._first_point = p
            self._line_green, self._line_red = self._ax.plot(0, 0, 'g', 0, 0, 'r')

        x0, y0 = self._first_point
        mp = (x-x0, y-y0)
        self._data.append(mp)
        data1 = [d[0] for d in self._data]
        data2 = [d[1] for d in self._data]
        datax = np.arange(0, len(self._data))

        self._line_green.set_ydata(data1)
        self._line_green.set_xdata(datax)
        self._line_red.set_ydata(data2)
        self._line_red.set_xdata(datax)
        self._redraw()
