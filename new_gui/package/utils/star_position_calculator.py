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
        self._previous_xy = None

    def start(self):
        self._pause = False

    def stop(self):
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

        # Brightest pixel:
        mid_y, mid_x = np.unravel_index(fragment.argmax(), fragment.shape)
        # Or center of mass?
        x0, y0 = self._rect
        w = self._w

        fragment_to_center = 1 * (fragment > np.median(fragment))
        mid_y, mid_x = center_of_mass(fragment_to_center)
        px = int(mid_x + x0)
        py = int(mid_y + y0)
        x0 = px - (w / 2)
        y0 = py - (w / 2)
        print(f"Rect = {(x0, y0)}, mid = {(mid_x, mid_y)}, point = {(px, py)}")
        self._rect = x0, y0

        if self._previous_xy is None:
            self._previous_xy = (px, py)
            px, py = (0, 0)

        else:
            [px, py] = np.subtract((px, py), self._previous_xy)

        self._display_callback((x0, y0))
        self._movement_callback((time, px, py))
