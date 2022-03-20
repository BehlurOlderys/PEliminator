import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from common.global_settings import settings


def force_aspect(ax, aspect=1):
    """https://stackoverflow.com/questions/7965743/how-can-i-set-the-aspect-ratio-in-matplotlib"""
    im = ax.get_images()
    extent = im[0].get_extent()
    ax.set_aspect(abs((extent[1]-extent[0])/(extent[3]-extent[2]))/aspect)


class FragmentDisplayer:
    def __init__(self, frame):
        figure_fragment = plt.Figure(figsize=(3, 3), dpi=100)
        self._ax = figure_fragment.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(figure_fragment, frame)
        self._canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH)
        self._data = None

    def get_data(self):
        return self._data

    def draw_data(self, data):
        self._data = data
        if settings.is_visualisation():
            self._ax.imshow(self._data, cmap='gray')
            force_aspect(self._ax, aspect=1)
            self._canvas.draw()
            plt.pause(0.01)

    def _redraw(self):
        self._canvas.draw()
        self._canvas.flush_events()
