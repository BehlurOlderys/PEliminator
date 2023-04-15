from .pe_base_widget import PeBaseWidget
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import numpy as np
from PIL import ImageTk, Image
import time
import matplotlib.patches as mpatches


class PhotoImage(PeBaseWidget):
    def __init__(self, initial_image=None, initial_image_path=None, **kwargs):
        super(PhotoImage, self).__init__(**kwargs)
        self._current_image = None
        if initial_image is not None:
            print("initial image")
            self._current_image = initial_image
            self._img = ImageTk.PhotoImage(initial_image)
        elif initial_image_path is not None:
            print(f"initial image path: {initial_image_path}")
            self._current_image = Image.open(initial_image_path)
            self._img = ImageTk.PhotoImage(self._current_image)
        else:
            raise AssertionError("Missing mandatory argument or given null!")

        self._frame.pack(fill=tk.BOTH, expand=True)
        self._canvas = tk.Canvas(self._frame, width=999, height=999)
        self._canvas.configure(bg='cyan')
        self._canvas.pack(fill=tk.BOTH, expand=True)
        print(f"Creating image...")
        self._image_container = self._canvas.create_image(0, 0, anchor="nw", image=self._img)

    def _normalize_image(self, im):
        print("Photo image normalize")
        min_v = np.amin(im)
        max_v = np.amax(im)
        return (im - min_v) / (max_v - min_v)

    def log_image(self):
        print("Photo image log")
        if self._current_image is not None:
            w, h = self._current_image.size
            np_shape = [h, w]
            print("Calculating logarithm with np")
            np_image = np.array(self._current_image.getdata())
            normalized_before = np.add(self._normalize_image(np_image), 1.0)
            logarithmized = np.log(normalized_before)
            normalized_after = np.multiply(self._normalize_image(logarithmized), 255)
            log_image = Image.fromarray(normalized_after.reshape(np_shape).astype(np.uint8))
            self.update_with_pil_image(log_image)
        else:
            print("There is no current image...")

    def update_with_pil_image(self, pilimage):
        print("Photo image update with pil")
        self._current_image = pilimage
        w, h = pilimage.size
        new_height = self._frame.winfo_height()
        print(f"New height = {new_height}")
        new_width = int(w * new_height / h)

        print(f"W={w}, H={h}, new = {new_width}x{new_height}")
        pilimage = pilimage.resize(size=(new_width, new_height))
        self._img = ImageTk.PhotoImage(pilimage)
        self._canvas.itemconfig(self._image_container, image=self._img)

    def update_with_np(self, image, mode=None, **kwargs):
        print(f"Updating with image of shape: {image.shape}")
        start = time.time()
        h, w, *_ = image.shape
        image = Image.fromarray(image, mode)
        self.update_with_pil_image(image)
        print(f"Time elapsed on image update = {time.time()-start}s")


class PhotoImageWithRectangle(PhotoImage):
    def __init__(self, fragment_size=50, border_color="black", callback=None, **kwargs):
        super(PhotoImageWithRectangle, self).__init__(**kwargs)
        self._fragment_size = fragment_size
        self._border_color = border_color
        self._rect = None
        self._callback = callback
        self._canvas.bind("<Button-1>", self._callback)
        self._patch = None

    def get_rectangle(self):
        return self._rect

    def clear_rectangle(self):
        self._rect = None
        [p.remove() for p in reversed(self._ax.patches)]
        self._canvas.draw_idle()

    def set_rectangle(self, rect):
        self._rect = rect
        self._update_patch()

    def _update_patch(self):
        w = self._fragment_size
        x, y = self._rect
        if self._patch is not None:
            self._canvas.delete(self._patch)
        self._patch = self._canvas.create_rectangle(x-25, y-25, x+25, y+25)
        # rect = mpatches.Rectangle(self._rect, w, w,
        #                           fill=False,
        #                           color=self._border_color,
        #                           linewidth=2)
        #
        # [p.remove() for p in reversed(self._ax.patches)]
        # self._ax.add_patch(rect)
        # self._canvas.draw_idle()

    def _click_action(self, event):
        if not event.inaxes == self._ax:
            return
        ix, iy = event.xdata, event.ydata
        w = self._fragment_size
        self._rect = (ix - w / 2, iy - w / 2)
        self._update_patch()
        if self._callback is not None:
            self._callback(self._rect)



class ImageCanvas(PeBaseWidget):
    def __init__(self, initial_image_path=None, dpi=None, **kwargs):
        super(ImageCanvas, self).__init__(**kwargs)
        data_figure = plt.Figure(dpi=dpi, facecolor="#222222")
        self._ax = data_figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(data_figure, self._frame)
        self._canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
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
        self._canvas.draw_idle()


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
        self._canvas.draw_idle()

    def set_rectangle(self, rect):
        self._rect = rect
        self._update_patch()

    def _update_patch(self):
        w = self._fragment_size
        rect = mpatches.Rectangle(self._rect, w, w,
                                  fill=False,
                                  color=self._border_color,
                                  linewidth=2)

        [p.remove() for p in reversed(self._ax.patches)]
        self._ax.add_patch(rect)
        self._canvas.draw_idle()

    def _click_action(self, event):
        if not event.inaxes == self._ax:
            return
        ix, iy = event.xdata, event.ydata
        w = self._fragment_size
        self._rect = (ix - w / 2, iy - w / 2)
        self._update_patch()
        if self._callback is not None:
            self._callback(self._rect)
