import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from astropy.io import fits
from common.global_settings import settings
import os
import numpy as np
import matplotlib.patches as mpatches


class ImageDisplayer:
    def __init__(self, frame, fragment_displayer, plotter):
        figure1 = plt.Figure(dpi=100)
        self._ax = figure1.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(figure1, frame)
        self._canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._canvas.mpl_connect('button_press_event', self.select_star)

        self._current_path = None
        self._current_data = None
        self._fragment_displayer = fragment_displayer
        self._current_rect = (0, 0)
        self._plotter = plotter
        self._current_datetime = None

    def get_current_path(self):
        return self._current_path

    def get_current_data(self):
        return self._current_data

    def _draw_any_image(self, image):
        self._ax.imshow(image, cmap='gray')
        self._canvas.draw()
        self._canvas.flush_events()

    def _draw_current_image(self):
        self._draw_any_image(self._current_data)
        self._update_fragment()

    def _open_and_draw_file(self, p, first=False):
        if p is not None:
            title_text = os.path.basename(p)
            with fits.open(p) as hdul:
                hdul.info()
                self._current_data = hdul[0].data

            self._ax.set_title(title_text)
            if settings.is_visualisation() or first:
                self._draw_current_image()

    def display(self, image_path):
        if image_path is not None:
            self._current_path = image_path
            self._open_and_draw_file(image_path)

    def enhance(self):
        enhanced_data = np.log(self._current_data)
        self._draw_any_image(enhanced_data)

    def _get_current_fragment(self):
        w = settings.get_fragment_size()
        x0, y0 = self._current_rect
        return self._current_data[int(y0):int(y0 + w), int(x0):int(x0 + w)]

    def _update_fragment(self):
        fragment_data = self._get_current_fragment()
        self._fragment_displayer.draw_data(fragment_data)

    def _reposition_fragment(self, ix, iy, vis=True):
        w = settings.get_fragment_size()
        self._current_rect = (ix - w / 2, iy - w / 2)
        rect = mpatches.Rectangle(self._current_rect, w, w,
                                  fill=False,
                                  color="purple",
                                  linewidth=2)

        self._ax.patches = []
        self._ax.add_patch(rect)
        if vis:
            self._canvas.draw()
        self._update_fragment()

    def select_star(self, event):
        if not event.inaxes == self._ax:
            return
        ix, iy = event.xdata, event.ydata
        self._reposition_fragment(ix, iy)
        print(f"Clicked on ({ix}, {iy})")

    def calculate_center(self, auto=False):
        data = self._get_current_fragment()
        # just for tests!
        w = settings.get_fragment_size()
        x0, y0 = self._current_rect

        # r = []
        # x0 = int(x0)
        # y0 = int(y0)
        # X = np.arange(0, w)
        # Y = np.arange(0, w)
        # for yy in range(y0-10, y0+10):
        #     for xx in range(x0-10, x0+10):
        #         data = self._current_data[yy:yy+w, xx:xx+w]
        #         weights = (data > np.average(data)).astype(int)
        #         weights = np.multiply(weights, weights)
        #         x2d, y2d = np.meshgrid(X, Y)
        #         mid_x = np.average(x2d, weights=weights)
        #         mid_y = np.average(y2d, weights=weights)
        #         r.append((mid_x+xx, mid_y+yy))
        #
        # np.savetxt("test_mid.csv", np.array(r), delimiter=",")

        without_hot = np.where(data < 65535, data, 0)
        mid_y, mid_x = np.unravel_index(without_hot.argmax(), without_hot.shape)
        px = mid_x + x0
        py = mid_y + y0
        print(f"Rect = {(x0, y0)}, mid = {(mid_x, mid_y)}, point = {(mid_x+x0, y0+mid_y)}")

        self._reposition_fragment(px, py, vis=settings.is_visualisation())
        if auto is False:
            self._plotter.add_point((px, py))
        #
        # weights = 1*(data > np.average(data))
        # weights = np.multiply(weights, weights)
        # x = np.arange(0, w)
        # y = np.arange(0, w)
        # x2d, y2d = np.meshgrid(x, y)
        # mid_x = np.average(x2d, weights=weights)
        # mid_y = np.average(y2d, weights=weights)
        # px = mid_x + x0
        # py = mid_y + y0
        # # print(f"Rect = {(x0, y0)}, mid = {(mid_x, mid_y)}, point = {(mid_x+x0, y0+mid_y)}")
        # self._reposition_fragment(px, py, vis=True)
        return px, py, self._current_path
