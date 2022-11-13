from scipy.ndimage import gaussian_filter, median_filter, center_of_mass
import numpy as np


def normalize(p):
    a = np.percentile(p, 5)
    b = np.percentile(p, 95)
    return (p - a) / (b-a)


class StarPositionCalculator:
    def __init__(self, movement_callback, display_callback, rect_size):
        self._movement_callback = movement_callback
        self._display_callback = display_callback
        self._rect = None
        self._pause = True
        self._w = rect_size
        self._previous_time = None
        self._initial_xy = None

    def start(self):
        self._pause = False

    def stop(self):
        self._previous_time = None
        self._initial_xy = None
        self._pause = True

    def set_rect(self, rect):
        self._rect = rect

    def _get_fragment_data(self, image):
        x0, y0 = self._rect
        w = self._w
        print(image.shape)
        fragment = image[int(y0):int(y0 + w), int(x0):int(x0 + w)]
        return fragment

    def calculate(self, data):
        if self._pause:
            return
        image, time = data
        if self._previous_time is None:
            self._previous_time = time
            time = 0
        else:
            time = time - self._previous_time
        print(f"Acquired new image with time: {time}. Current rect ={self._rect}")
        fragment = self._get_fragment_data(image)
        fragment = gaussian_filter(median_filter(normalize(fragment), 5), 3)

        # Brightest pixel in coordinates of fragment:
        mid_y, mid_x = np.unravel_index(fragment.argmax(), fragment.shape)

        x0, y0 = self._rect
        w = self._w

        # Refine it with center of mass in smaller fragment around brightest pixel:
        narrowed_w = int(w // 3)
        narrow_x0 = int(x0+mid_x-(narrowed_w//2))
        narrow_y0 = int(y0+mid_y-(narrowed_w//2))
        narrowed_fragment = image[narrow_y0:narrow_y0+narrowed_w, narrow_x0:narrow_x0+narrowed_w]
        print(f"w = {w}, narrow_coords = ({narrow_x0},{narrow_y0}), Narrowed shape = {narrowed_fragment.shape}")

        # cm in coordinates of smaller fragment
        cmy, cmx = center_of_mass(narrowed_fragment)

        # Now we need to go back to global coordinates
        px = narrow_x0 + cmx
        py = narrow_y0 + cmy

        x0 = int(px - (w / 2))
        y0 = int(py - (w / 2))
        self._rect = x0, y0
        print(f"Rect = {(x0, y0)}, mid = {(mid_x, mid_y)}, point = {(px, py)}")

        if self._initial_xy is None:
            self._initial_xy = (px, py)
            dx, dy = (0, 0)

        else:
            [dx, dy] = np.subtract((px, py), self._initial_xy)

        print(f"dx, dy = ({dx}, {dy}), previous xy = {self._initial_xy}")
        self._display_callback((x0, y0))
        self._movement_callback((time, dx, dy))
