from .pe_base_widget import PeBaseWidget
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import numpy as np
from PIL import ImageTk, Image
import time
import matplotlib.patches as mpatches


window_max_width = 1024


class PhotoImage(PeBaseWidget):
    def __init__(self, initial_image=None, initial_image_path=None, **kwargs):
        super(PhotoImage, self).__init__(**kwargs)
        self._displayed_image = None
        self._original_image = None
        self._zoom = 1.0
        if initial_image is not None:
            print("initial image")
            self._original_image = initial_image
        elif initial_image_path is not None:
            print(f"initial image path: {initial_image_path}")
            self._original_image = Image.open(initial_image_path)
        else:
            raise AssertionError("Missing mandatory argument or given null!")
        self._displayed_image = self._original_image
        self._img = ImageTk.PhotoImage(self._displayed_image)

        self._frame.pack(fill=tk.BOTH, expand=True)

        w, h =self._original_image.size

        self._canvas = tk.Canvas(self._frame, width=window_max_width, height=768, scrollregion=(0, 0, w, h))
        self._canvas.configure(bg='cyan')

        hbar = tk.Scrollbar(self._frame, orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        hbar.config(command=self._canvas.xview)
        vbar = tk.Scrollbar(self._frame, orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        vbar.config(command=self._canvas.yview)
        self._canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self._image_container = self._canvas.create_image(0, 0, anchor="nw", image=self._img)
        self._canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    def _resize_current(self):
        print(f"Resizing current image with zoom = {self._zoom}...")
        w, h = self._original_image.size
        new_width = int(w * self._zoom)
        new_height = int(h * self._zoom)

        if new_width != w or new_height != h:
            print(f"Resizing: {w}x{h} -> {new_width}x{new_height}")
            self._displayed_image = self._original_image.resize(size=(new_width, new_height))
        else:
            self._displayed_image = self._original_image

        self._img = ImageTk.PhotoImage(self._displayed_image)

        canvas_width = min(w, window_max_width)
        print(f"Using canvas width = {canvas_width}")
        self._canvas.configure(scrollregion=(0, 0, new_width, new_height), width=canvas_width, height=h)
        self._canvas.itemconfig(self._image_container, image=self._img)
        print("... resizing done!")

    def zoom_in(self):
        self._zoom = round(self._zoom * 1.4, 2)
        self._resize_current()

    def zoom_out(self):
        self._zoom = round(self._zoom / 1.4, 2)
        self._resize_current()

    def _normalize_image(self, im):
        print("Photo image normalize")
        min_v = np.amin(im)
        max_v = np.amax(im)
        return (im - min_v) / (max_v - min_v)

    def log_image(self):
        print("Photo image log")
        w, h = self._original_image.size
        np_shape = [h, w]
        print("Calculating logarithm with np")
        np_image = np.array(self._original_image.getdata())
        normalized_before = np.add(self._normalize_image(np_image), 1.0)
        logarithmized = np.log(normalized_before)
        normalized_after = np.multiply(self._normalize_image(logarithmized), 255)
        log_image = Image.fromarray(normalized_after.reshape(np_shape).astype(np.uint8))
        self.update_with_pil_image(log_image)

    def update_with_pil_image(self, pilimage):
        print("Updating with new pil image")
        self._original_image = pilimage
        self._resize_current()
        print("... updating done!")

    def update_with_np(self, image, mode=None, **kwargs):
        print(f"Updating with image of shape: {image.shape}")
        start = time.time()
        h, w, *_ = image.shape
        image = Image.fromarray(image, mode)
        self.update_with_pil_image(image)
        print(f"Time elapsed on image update = {time.time()-start}s")


class PhotoImageWithRectangle(PhotoImage):
    def __init__(self, fragment_size=50, border_color="black", **kwargs):
        super(PhotoImageWithRectangle, self).__init__(**kwargs)
        self._original_fragment_size = fragment_size
        self._displayed_fragment_size = self._original_fragment_size
        self._border_color = border_color
        self._original_rect = None
        self._displayed_rect = None
        self._canvas.bind("<Button-1>", self._click_action)
        self._patch = None

    def _resize_current(self):
        super(PhotoImageWithRectangle, self)._resize_current()

        self._displayed_fragment_size = self._original_fragment_size * self._zoom

        x, y = self._original_rect
        x *= self._zoom
        y *= self._zoom
        self._displayed_rect = (x, y)

        self._update_patch()
        self._center_on_patch()

    def _center_on_patch(self):
        pass

    def set_rectangle(self, rect):
        self._original_rect = rect
        self._update_patch()

    def _update_patch(self):
        h = self._displayed_fragment_size
        x, y = self._displayed_rect
        if self._patch is not None:
            self._canvas.delete(self._patch)
        self._patch = self._canvas.create_rectangle(x, y, x+h, y+h)

    def _click_action(self, event):
        ix, iy = event.x, event.y
        _, _, srx, sry = tuple(map(int, self._canvas.cget("scrollregion").split(' ')))

        trans = lambda x, y: tuple([int(a*y) for a in x])
        region_x = trans(self._canvas.xview(), srx)
        region_y = trans(self._canvas.yview(), sry)

        print(f"Event data = {ix}, {iy}, region_x = {region_x}, sry={region_y}, canvas view= {self._canvas.xview()}, {self._canvas.yview()}")
        w = self._displayed_fragment_size
        self._original_rect = (region_x[0] + ix - w / 2, region_y[0] + iy - w / 2)
        self._displayed_rect = self._original_rect
        self._update_patch()


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
