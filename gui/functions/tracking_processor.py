from functions.star_selector import StarSelector
from astropy.io import fits
import numpy as np
from functions.image_calculator import get_star_position_estimate
from functions.camera_image_processor import Averager
from functions.global_settings import settings


def try_to_open_fits(f):
    try:
        with fits.open(f) as hdul:
            current_data = np.array(hdul[0].data)
    except Exception as e:
        print(f"Exception while opening file {f}: {e}")
        return None
    return current_data


class TrackingProcessor:
    def __init__(self, plotter, feedback_var):
        self._plotter = plotter
        self._feedback_var = feedback_var
        self._averager = Averager(settings.get_star_tracking_average())
        self._rect = None
        self._star_position = None
        self._previous_t = None
        self._previous_p = None
        self._average_counter = 0
        self._log = open("logs//tracking_processor.log", 'w', buffering=1)
        self._pipe = open(settings.get_star_tracking_pipe_name(), 'w', buffering=1)
        self._counter = 0

    def __del__(self):
        self._log.close()

    def send_feedback(self):
        value = float(self._feedback_var.get())
        self._send_feedback(value)

    def _send_feedback(self, value):
        print(f"Sending feedback: {value}")
        self._pipe.write(f"{self._counter}: ra_correction: {value}\n")
        self._counter += 1

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

    def reset(self):
        self._average_counter = 0
        self._averager.reset()
        self._plotter.clear_plot()
        self._feedback_var.set(0)

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
        ra_in_x_axis_index = 0
        self._averager.update_value(delta_p[ra_in_x_axis_index])
        if self._average_counter >= 2:
            feedback_value = self._averager.get_current_value()
            self._send_feedback(feedback_value)
            self._feedback_var.set(feedback_value)
            self._average_counter = 0
        elif not self._averager.is_full():
            print("Averager is not full!")
        self._average_counter += 1

        print(f"New position = ({x}, {y}), delta p = {delta_p}, delta t = {delta_t}")
        self._log.write(f"{t}\t{x}\t{y}\n")
