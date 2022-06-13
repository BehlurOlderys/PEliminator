import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class PointPlot:
    def __init__(self, frame):
        self._figure = plt.Figure(dpi=100)
        self.ax = self._figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self._figure, frame)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.data_t = []
        self.ax.plot()
        self.first_point = None

    def _clear_plot(self):
        print("Clearing plot (base)!")
        self.data_t = []
        self.ax.cla()
        self.ax.plot()

    def redraw(self):
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()
