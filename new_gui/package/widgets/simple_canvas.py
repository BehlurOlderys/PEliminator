from .pe_base_widget import PeBaseWidget
import tkinter as tk
from PIL import ImageTk, Image
import time


window_max_width = 1024


class SimpleCanvas(PeBaseWidget):
    def __init__(self, initial_image_path, **kwargs):
        super(SimpleCanvas, self).__init__(**kwargs)
        if initial_image_path is not None:
            print(f"initial image path: {initial_image_path}")
            self._original_image = Image.open(initial_image_path)
        else:
            raise AssertionError("Missing mandatory argument or given null!")
        self._img = ImageTk.PhotoImage(self._original_image)
        self._frame.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(self._frame)
        self._canvas.configure(bg='black')
        self._image_container = self._canvas.create_image(0, 0, anchor="nw", image=self._img)
        self._canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self._display_ratio = 1

    def _resize_current(self):
        # getting actual canvas dimensions:
        cw = self._canvas.winfo_width()
        ch = self._canvas.winfo_height()  # not used for now...
        print(f"Canvas dimensions = {cw}x{ch}")

        # these are dimensions of unaltered image:
        iw, ih = self._original_image.size
        print(f"Original image dimensions = {iw}x{ih}")

        # now image is resized so new width = canvas width, and new height is proportional:
        self._display_ratio = cw/iw
        new_height = int(ih*self._display_ratio)
        self._displayed_image = self._original_image.resize(size=(cw, new_height))

        # transforming into TkImage which actually can be displayed on canvas
        self._img = ImageTk.PhotoImage(self._displayed_image)

        # putting all this into canvas by configuring image container content:
        self._canvas.itemconfig(self._image_container, image=self._img)
        print("... resizing done!")

    def update_with_pil_image(self, pilimage):
        print("Updating with new pil image")
        self._original_image = pilimage
        self._resize_current()
        print("... updating done!")

    def update_with_np(self, image, mode=None):
        print(f"Updating with image of shape: {image.shape}")
        start = time.time()
        h, w, *_ = image.shape
        image = Image.fromarray(image, mode)
        self.update_with_pil_image(image)
        print(f"Time elapsed on image update = {1000*(time.time() - start)}ms")


class SimpleCanvasRect(SimpleCanvas):
    def __init__(self, rectsize=70, **kwargs):
        super(SimpleCanvasRect, self).__init__(**kwargs)
        self._canvas.bind("<Button-1>", self._click_action)
        self._patch = None
        self._rectsize = rectsize
        self._real_image_rect = None
        self._enable = False

    def disable_rect_info(self):
        self._enable = False

    def enable_rect_info(self):
        self._enable = True

    def get_real_rect(self):
        if not self._enable:
            return None
        return self._real_image_rect

    def set_real_rect_middle(self, xy):
        dx, dy = xy
        if not self._enable:
            return
        h = self._rectsize * self._display_ratio
        # Coordinates on image:
        ix, iy = int(dx - self._rectsize / 2), int(dy - self._rectsize / 2)
        print(f"=======> New rect coords = ({ix}, {iy}")
        # Coordinates on canvas:
        cw = self._canvas.winfo_width()
        ch = self._canvas.winfo_height()

        cx = int(ix * self._display_ratio)
        cy = int(iy * self._display_ratio)

        # normalize cx, cy so it does not go below 0:
        cx = min(cw-h, max(0, cx))
        cy = min(ch-h, max(0, cy))

        # draw new or update old patch:
        if self._patch is not None:
            self._canvas.delete(self._patch)
        self._patch = self._canvas.create_rectangle(cx, cy, cx+h, cy+h)

        # Update on image rect coordinates:
        x, y, s = self._real_image_rect
        self._real_image_rect = ix, iy, s

    def _click_action(self, event):
        # patch size in canvas:
        h = self._rectsize * self._display_ratio

        # canvas coordinates of patch after centering on click site:
        cx, cy = event.x-h/2, event.y-h/2

        # normalize cx, cy so it does not go below 0 or above max:
        cw = self._canvas.winfo_width()
        ch = self._canvas.winfo_height()
        cx = min(cw-h, max(0, cx))
        cy = min(ch-h, max(0, cy))

        # real image coordinates of centered patch:
        rx = int(cx/self._display_ratio)
        ry = int(cy/self._display_ratio)
        self._real_image_rect = rx, ry, self._rectsize
        print(f"Real image rect left upper corner = ({rx}, {ry})")

        # draw new or update old patch:
        if self._patch is not None:
            self._canvas.delete(self._patch)
        self._patch = self._canvas.create_rectangle(cx, cy, cx+h, cy+h)
