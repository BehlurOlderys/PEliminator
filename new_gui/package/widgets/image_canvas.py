from .pe_base_widget import PeBaseWidget
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from PIL import Image
import numpy as np
import matplotlib.patches as mpatches


class ImageCanvas(PeBaseWidget):
    def __init__(self, initial_image_path=None, **kwargs):
        super(ImageCanvas, self).__init__(**kwargs)
        data_figure = plt.Figure(dpi=72, facecolor="#222222")
        self._ax = data_figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(data_figure, self._frame)
        self._canvas.get_tk_widget().pack(side=tk.RIGHT, expand=True)
        if initial_image_path is not None:
            print("Displaying initial image")
            im_frame = Image.open(initial_image_path)
            np_frame = np.array(im_frame)
            self._ax.imshow(np_frame)
        self._ax.set_frame_on(False)
        self._ax.axis("image")
        self._ax.axis("off")

    def update(self, image, **kwargs):
        self._ax.imshow(image, **kwargs)
        self._canvas.draw()


class ImageCanvasWithRectangle(ImageCanvas):
    def __init__(self, fragment_size=50, border_color="black", callback=None, **kwargs):
        super(ImageCanvasWithRectangle, self).__init__(**kwargs)
        self._fragment_size = fragment_size
        self._border_color = border_color
        self._rect = None
        self._callback = callback
        self._canvas.mpl_connect('button_press_event', self._click_action)

    def get_rectangle(self):
        return self._rect

    def clear_rectangle(self):
        self._rect = None
        [p.remove() for p in reversed(self._ax.patches)]
        self._canvas.draw()

    def _click_action(self, event):
        if not event.inaxes == self._ax:
            return
        ix, iy = event.xdata, event.ydata
        w = self._fragment_size
        self._rect = (ix - w / 2, iy - w / 2)
        rect = mpatches.Rectangle(self._rect, w, w,
                                  fill=False,
                                  color=self._border_color,
                                  linewidth=2)

        [p.remove() for p in reversed(self._ax.patches)]
        self._ax.add_patch(rect)
        self._canvas.draw()
        if self._callback is not None:
            self._callback()
