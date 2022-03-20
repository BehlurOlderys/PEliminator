from common.global_settings import settings
from common.utils import moving_mean
import numpy as np


class Corrector:
    def __init__(self, encoder_data_provider):
        self._current_period = []
        self._periods = []
        self._encoder_data_provider = encoder_data_provider
        self._log = open("corrector_log.log", "w")

    def __del__(self):
        self._log.close()

    def _calculate_current_period(self):
        if len(self._current_period) < settings.get_encoder_ticks():
            return  # not full period

        # t, y, e

        ts = [i[0] for i in self._current_period]
        ys = [i[1] for i in self._current_period]
        es = [i[2] for i in self._current_period]


        # Eliminate wrapped time:
        previous_time = 0
        additional_time = 0
        for i, t in enumerate(ts):
            if previous_time > t:
                additional_time += 1

            previous_time = t
            ts[i] += 4294967 * additional_time

        #interpolation:

        ts = np.subtract(ts, ts[0])
        t = np.linspace(0, ts[-1], num=settings.get_correction_bins() + 1)
        fs = np.interp(t, ts, ys)

        # smoothing
        smoothed = moving_mean(fs, 4)
        df = np.diff(fs)
        dt = np.diff(t)
        f_speed = np.pad(np.divide(df, dt), (0, 1), mode='edge')



    def add_point(self, p):
        print(f"Added point {p}")
        x, y, t = p
        e = self._encoder_data_provider.find_readout_by_timestamp(t)
        if e is None:
            print(f"Could not find right encoder reading for timestamp {t}")
            return
        print(f"Found encoder reading {e} for timestamp {t}")
        if len(self._current_period) > 0 and self._current_period[-1] > e:
            self._log.write(f"{self._current_period}\n")
            self._calculate_current_period()
            self._current_period = []

        self._current_period.append((t, y, e))  # TODO: should be x or y depending on orientation
        # seek for t in reader encoder




