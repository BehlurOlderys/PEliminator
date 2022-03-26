from common.global_settings import settings
from common.utils import moving_mean
import numpy as np


class Corrector:
    def __init__(self, encoder_data_provider, callback, data_file_name):
        self._file_path = data_file_name
        self._current_period = []
        self._periods = []
        self._encoder_data_provider = encoder_data_provider
        self._log = open("corrector_log.log", "w")
        self._speeds = []
        self._callback = callback

        self._min_points = settings.get_minimal_full_period_points()
        self._ticks = settings.get_encoder_ticks()
        self._threshold_low = 2*(self._ticks / self._min_points)
        self._threshold_high = self._ticks - self._threshold_low
        print(f"Thresholds are: LOW={self._threshold_low}, HIGH={self._threshold_high}")

    def __del__(self):
        self._log.close()

    def _add_new_speed(self, speed):
        self._speeds.append(speed)
        if len(self._speeds) < 3:
            return

        latest_speeds = np.array(self._speeds[-3:])
        average_speed = np.mean(latest_speeds, axis=0)
        print(f"Shape of average = {average_speed.shape}")
        self._callback(average_speed)

    def _calculate_current_period(self):
        start_reading = self._current_period[0][2]
        final_reading = self._current_period[-1][2]
        if start_reading > self._threshold_low or final_reading < self._threshold_high:
            print("Discarding period as not full for analysis <<<<<<<<<<<<<!")
            return  # not full period

        # t, y, e

        ts = [i[0] for i in self._current_period]
        ys = [i[1] for i in self._current_period]
        # es = [i[2] for i in self._current_period]

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
        df = np.diff(smoothed)
        dt = np.diff(t)
        f_speed = np.pad(np.divide(df, dt))
        self._add_new_speed(f_speed)

    def add_point(self, p):
        x, y, t = p
        e = self._encoder_data_provider.find_readout_by_timestamp(t)
        if e is None:
            print(f"Could not find right encoder reading for timestamp {t}")
            return
        print(f"Found encoder reading {e} for timestamp {t}")

        if len(self._current_period) > 0:
            previous_tick = self._current_period[-1][2]
            print(f"Previous tick = {previous_tick}")
            if previous_tick > e:
                print("Ended reading full period <<<<<<<<<<<<<<<!")
                self._log.write(f"Cokolwiek {self._current_period}\n")
                self._calculate_current_period()
                self._current_period = []

        self._current_period.append((t, y, e))  # TODO: should be x or y depending on orientation
        print(f"Added point {p} to current period of length: {len(self._current_period)}")
        # seek for t in reader encoder




