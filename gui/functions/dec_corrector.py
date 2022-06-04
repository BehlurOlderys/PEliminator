from astropy.io import fits
import numpy as np
from serial import Serial


image_scale = 2.9 * 206 / 650
orientation = "E"
#orientation = "S" #, "E", "W"


class SerialCommander:
    def __init__(self):
        self._ser = Serial()


def choose_dec(x, y):
    if orientation == "N":
        return y
    elif orientation == "E":
        return x
    elif orientation == "W":
        return -x
    elif orientation == "S":
        return -y


class DecCorrector:
    def __init__(self, dec_estimator, serial_commander):
        self._dec_estimator = dec_estimator
        self._commander = serial_commander
        self._last_timestamp = None
        self._last_dec = None

    def init(self, f, t):
        self._last_timestamp = t

        try:
            with fits.open(f) as hdul:
                current_data = np.array(hdul[0].data)
        except Exception as e:
            print(f"Exception while opening file {f}: {e}")
            return False

        if not self._dec_estimator.init(current_data):
            print("Dec estimator init failed!")
            return False
        try:
            print(f)
            with fits.open(f) as hdul:
                c_data = np.array(hdul[0].data)
            cx, cy = self._dec_estimator.estimate(c_data)
            self._last_dec = choose_dec(cx, cy)
        except Exception as e:
            print(f"Initial dec estimation failed: {e}")
            return False

        self._commander.write_string("START_DC")
        return True

    def process(self, f, t):
        try:
            print(f)
            with fits.open(f) as hdul:
                c_data = np.array(hdul[0].data)

            cx, cy = self._dec_estimator.estimate(c_data)

        except Exception as e:
            print(f"Image processing failed: {e}")
            return

        new_dec = choose_dec(cx, cy)
        delta_dec = new_dec - self._last_dec
        self._last_dec = new_dec
        delta_t = t - self._last_timestamp
        dec_speed_px = delta_dec / delta_t
        dec_speed_as = image_scale * dec_speed_px
        dec_speed_as_per_1000s = int(1000*dec_speed_as)
        print(f"Calculated dec speed = {dec_speed_px} px/s = {dec_speed_as_per_1000s} as/1000s")

        if dec_speed_as_per_1000s > 1:
            self._commander.write_string(f"SET_DC+ {dec_speed_as_per_1000s}")
        elif dec_speed_as_per_1000s < -1:
            self._commander.write_string(f"SET_DC- {-dec_speed_as_per_1000s}")
