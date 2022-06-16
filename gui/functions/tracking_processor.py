from functions.star_selector import StarSelector
from astropy.io import fits
import numpy as np
from functions.image_calculator import get_star_position_estimate


def try_to_open_fits(f):
    try:
        with fits.open(f) as hdul:
            current_data = np.array(hdul[0].data)
    except Exception as e:
        print(f"Exception while opening file {f}: {e}")
        return None
    return current_data


class TrackingProcessor:
    def __init__(self, plotter):
        self._plotter = plotter
        self._rect = None
        self._star_position = None
        self._previous_t = None
        self._previous_p = None
        self._log = open("logs//tracking_processor.log", 'w', buffering=1)

    def __del__(self):
        self._log.close()

    def init(self, f, t):
        self._previous_t = t
        current_data = try_to_open_fits(f)
        self._rect = StarSelector(current_data).get_star_rect()
        print(f"Suspected star at {self._rect}")
        self._rect, self._previous_p = get_star_position_estimate(current_data, self._rect)
        x, y = self._previous_p
        print(f"Star position = {self._previous_p}")
        self._plotter.add_points([(t, x, y)])
        return True

    def process(self, f, t):
        print("Tracking processor = process!")
        if self._rect is None:
            print("No rect is set!")
            return

        delta_t = t - self._previous_t
        self._previous_t = t
        data = try_to_open_fits(f)
        if data is None:
            return
        self._rect, p = get_star_position_estimate(data, self._rect)
        x, y = p
        x0, y0 = self._previous_p
        delta_p = (x-x0, y-y0)
        self._previous_p = p
        self._plotter.add_points([(t, x, y)])
        print(f"New position = ({x}, {y}), delta p = {delta_p}, delta t = {delta_t}")
        self._log.write(f"{t}\t{x}\t{y}\n")
