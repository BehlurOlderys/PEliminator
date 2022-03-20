from astropy.io import fits
from common.global_settings import settings


class ImageCalculator:
    def __init__(self, callback):
        self._callback = callback
        self._rectangle = None

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

        self._next_image(data)

    def _get_center(self, data):
        # self._rect = (50, 50)
        y0, x0 = self._rect
        w = settings.get_fragment_size()
        fragment = data[int(y0-w/2):int(y0+w/2), int(x0-w/2):int(x0 + w/2)]
        # some calculations...
        center_x, center_y = (0, 0)
        return center_x, center_y

    def _next_image(self, data):
        p = self._get_center(data)
        self._rect = p
        self._callback(p)

    def new_image(self, f):
        with fits.open(f) as hdul:
            current_data = hdul[0].data

        if self._rect is None:
            self._first_image(current_data)
        else:
            self._next_image(current_data)
