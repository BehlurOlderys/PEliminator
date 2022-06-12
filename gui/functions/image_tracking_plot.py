import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ImageTrackingPlot:
    def __init__(self, frame):
        data_figure = plt.Figure(dpi=100)
        self._ax = data_figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(data_figure, frame)
        self._canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._data_x = []
        self._data_y = []
        self._data_t = []
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
        self._data_x = []
        self._data_y = []
        self._data_t = []
        self._ax.plot()

    def toggle_red(self):
        if self._red_on:
            if self._line_red is not None:
                self._line_red.remove()
                self._line_red = None

        else:
            self._line_red = self._ax.plot(self._data_t, self._data_x, 'r')[0]

        self._red_on = not self._red_on
        self._redraw()

    def toggle_green(self):
        if self._green_on:
            if self._line_green is not None:
                self._line_green.remove()
                self._line_green = None

        else:
            self._line_green = self._ax.plot(self._data_t, self._data_y, 'g')[0]

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

    def add_points(self, time_points):
        if not self._data_t:
            self._first_point = time_points[0]
            self._line_green, self._line_red = self._ax.plot(0, 0, 'g', 0, 0, 'r')
        t0, x0, y0 = self._first_point
        for p in time_points:
            t, x, y = p
            self._data_t.append(t - t0)
            self._data_x.append(x - x0)
            self._data_y.append(y - y0)

        self._line_red.set_ydata(self._data_x)
        self._line_red.set_xdata(self._data_t)
        self._line_green.set_ydata(self._data_y)
        self._line_green.set_xdata(self._data_t)
        self._redraw()
