import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches


class DecEstimator:
    def __init__(self):
        self._root = None
        self._ax = None
        self._canvas = None

    def _select_star(self, event):
        if not event.inaxes == self._ax:
            return
        ix, iy = event.xdata, event.ydata
        w = 70
        self._rect = (ix - w / 2, iy - w / 2)
        rect = mpatches.Rectangle(self._rect, w, w,
                                  fill=False,
                                  color="green",
                                  linewidth=2)

        self._ax.patches = []
        self._ax.add_patch(rect)
        self._canvas.draw()

    def _accept_selection(self):
        self._root.quit()
        print("A")
        del self._canvas

    def _discard_selection(self):
        self._rect = None
        self._root.destroy()

    def init(self, data):
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
        self._root.destroy()
        del self._root
        if self._rect is None:
            return False
        print("Chosen star!")
        return True

    def estimate(self, data):
        x0, y0 = self._rect
        w = 70  # settings.fragment size

        print(data.shape)

        fragment = data[int(y0-w/2):int(y0+w/2), int(x0-w/2):int(x0 + w/2)]

        without_hot = np.where(fragment < 65535, fragment, 0)
        mid_y, mid_x = np.unravel_index(without_hot.argmax(), without_hot.shape)
        px = int(mid_x + x0 - w/2)
        py = int(mid_y + y0 - w/2)
        print(f"Rect = {(x0, y0)}, mid = {(mid_x, mid_y)}, point = {(px, py)}")
        return px, py
