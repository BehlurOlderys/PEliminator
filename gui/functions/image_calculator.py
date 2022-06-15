from astropy.io import fits
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import os
import numpy as np
import matplotlib.patches as mpatches
from scipy.ndimage import gaussian_filter, median_filter

from .global_settings import settings


def normalize(p):
    a = np.percentile(p, 5)
    b = np.percentile(p, 95)
    return (p - a) / (b-a)


def get_star_position_estimate(data, rect):
    x0, y0 = rect
    w = settings.get_fragment_size()

    print(data.shape)

    fragment = data[int(y0):int(y0 + w), int(x0):int(x0 + w)]
    fragment = gaussian_filter(median_filter(normalize(fragment), 5), 3)
    # plt.imshow(fragment)
    # plt.show()

    without_hot = np.where(fragment < 12535, fragment, 0)
    mid_y, mid_x = np.unravel_index(without_hot.argmax(), without_hot.shape)
    px = int(mid_x + x0)
    py = int(mid_y + y0)
    x0 = px - (w/2)
    y0 = py - (w/2)
    print(f"Rect = {(x0, y0)}, mid = {(mid_x, mid_y)}, point = {(px, py)}")
    return (x0, y0), (px, py)

# TODO!
# class StarChooser(tk.Toplevel):
#     def __init__(self, data, parent):
#         self._root = tk.Toplevel()
#         self._root.title("Choose star")
#         frame = tk.Frame(self._root)
#         frame.pack(fill=tk.BOTH, expand=True)
#         figure1 = plt.Figure(dpi=100)
#         self._ax = figure1.add_subplot(111)
#         self._canvas = FigureCanvasTkAgg(figure1, frame)
#         self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
#         self._canvas.mpl_connect('button_press_event', parent._select_star)
#         self._ax.imshow(np.log(data))
#         button_frame = tk.Frame(frame)
#         button_frame.pack(side=tk.BOTTOM)
#         ok_button = tk.Button(button_frame, text="Accept", command=parent._accept_selection)
#         ok_button.pack(side=tk.LEFT)
#         cancel_button = tk.Button(button_frame, text="Cancel", command=parent._discard_selection)
#         cancel_button.pack(side=tk.RIGHT)
#
#     def get_choice(self):


class ImageCalculator:
    def __init__(self, callback):
        self._callback = callback
        self._rect = None
        self._ax = None
        self._canvas = None

    def _select_star(self, event):
        if not event.inaxes == self._ax:
            return
        ix, iy = event.xdata, event.ydata
        w = settings.get_fragment_size()
        self._rect = (ix - w / 2, iy - w / 2)
        rect = mpatches.Rectangle(self._rect, w, w,
                                  fill=False,
                                  color="green",
                                  linewidth=2)

        self._ax.patches = []
        self._ax.add_patch(rect)
        self._canvas.draw()

    def _accept_selection(self):
        self._root.destroy()
        del self._canvas

    def _discard_selection(self):
        self._rect = None
        self._root.destroy()

    def _first_image(self, data):
        """
        popup window asking for rectangle:
         _______________________
        |  Choose star:         |
        |   ________            |
        |  | image  |   OK      |
        |   --------    Cancel  |
        ------------------------
        """
        self._root = tk.Tk()
        self._root.title("Choose star")
        frame = tk.Frame(self._root)
        frame.pack(fill=tk.BOTH, expand=True)
        figure1 = plt.Figure(dpi=100)
        self._ax = figure1.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(figure1, frame)
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._canvas.mpl_connect('button_press_event', self._select_star)
        self._ax.imshow(np.log(data))
        button_frame = tk.Frame(frame)
        button_frame.pack(side=tk.BOTTOM)

        ok_button = tk.Button(button_frame, text="Accept", command=self._accept_selection)
        ok_button.pack(side=tk.LEFT)
        cancel_button = tk.Button(button_frame, text="Cancel", command=self._discard_selection)
        cancel_button.pack(side=tk.RIGHT)
        self._root.mainloop()
        del self._root

        if self._rect is None:
            return

        return self._next_image(data)

    def _get_center(self, data):
        x0, y0 = self._rect
        w = settings.get_fragment_size()
        fragment = data[int(y0-w/2):int(y0+w/2), int(x0-w/2):int(x0 + w/2)]
        without_hot = np.where(fragment < 65535, fragment, 0)
        mid_y, mid_x = np.unravel_index(without_hot.argmax(), without_hot.shape)
        px = int(mid_x + x0 - w/2)
        py = int(mid_y + y0 - w/2)
        print(f"Rect = {(x0, y0)}, mid = {(mid_x, mid_y)}, point = {(px, py)}")
        return px, py

    def _next_image(self, data):
        p = self._get_center(data)
        self._rect = p
        return p

    def new_image(self, f):
        with fits.open(f) as hdul:
            current_data = hdul[0].data

        timestamp = os.path.getctime(f)
        if self._rect is None:
            p = self._first_image(current_data)
        else:
            p = self._next_image(current_data)

        if p is not None:
            self._callback((*p, timestamp))
