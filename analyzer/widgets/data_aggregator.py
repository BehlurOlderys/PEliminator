from widgets.global_settings import settings
import pickle
import numpy as np


mocking = True


class DataAggregator:
    def __init__(self, fi, di, ei, button, axis, canvas, period_list):
        self._button = button
        self._button.configure(command=self.combine)
        self._files_ind = fi
        self._drift_ind = di
        self._encoder_ind = ei
        self._ax = axis
        self._canvas = canvas
        self._period_list = period_list

        self._files_with_dates = None
        self._drift_data = None
        self._encoder_data = None

    def push_files(self, file_list):
        self._files_with_dates = {f[0]: int(f[1]) for f in file_list}  # file_list = [(filename, datetime)]
        self._files_ind.set_light(True)
        print(list(self._files_with_dates.items())[:10])
        with open('files_with_dates.pickle', 'wb') as handle:
            pickle.dump(self._files_with_dates, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def push_encoder(self, encoder_data):
        self._encoder_data = encoder_data  # encoder_data = {datetime: (time, ticks)}
        self._encoder_ind.set_light(True)
        print(list(self._encoder_data.items())[:10])
        with open('encoder_data.pickle', 'wb') as handle:
            pickle.dump(self._encoder_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def push_drift(self, drift_data):
        px_scale = settings.get_image_scale()
        _, b = list(drift_data.items())[0]
        print(f"first item xy = {b}")
        self._drift_data = {name: ((v[0]-b[0])*px_scale, (v[1]-b[1])*px_scale) for name, v in drift_data.items()}  # drift_data = {name: (x, y) }
        print(list(self._drift_data.items())[:10])
        with open('drift_data.pickle', 'wb') as handle:
            pickle.dump(self._drift_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

        self._drift_ind.set_light(True)

    def combine(self):
        if mocking:
            with open('drift_data.pickle', 'rb') as handle:
                self._drift_data = pickle.load(handle)

            with open('encoder_data.pickle', 'rb') as handle:
                self._encoder_data = pickle.load(handle)

            with open('files_with_dates.pickle', 'rb') as handle:
                self._files_with_dates = pickle.load(handle)

        chosen_axis = 1
        print("Started combination! :) ")
        result = {}
        previous_ticks = 9999999
        previous_time = 0
        additional_time = 0
        current_period_time = 0
        for f, d in self._files_with_dates.items():
            int_dt = int(d)
            encoder_time, encoder_ticks = self._encoder_data[int_dt]

            if previous_time > encoder_time:
                print(f"Previous = {previous_time}, current = {encoder_time}")
                additional_time += 1

            previous_time = encoder_time
            encoder_time = encoder_time + 4294967 * additional_time

            if previous_ticks > encoder_ticks:
                current_period_time = encoder_time
                result[encoder_time] = []

            previous_ticks = encoder_ticks
            drift_value = self._drift_data[f][chosen_axis]
            result[current_period_time].append((encoder_ticks, drift_value, encoder_time))

        lines = {}

        interpolated_result = {}
        for k, v in result.items():
            [xs, ys, ts] = zip(*v)
            ts = np.subtract(ts, ts[0])
            t = np.linspace(0, ts[-1], num=settings.get_correction_bins() + 1)
            f = np.interp(t, ts, ys)
            interpolated_result[k] = (xs, f, t)

        for k, v in interpolated_result.items():
            [_, ys, ts] = v
            [line] = self._ax.plot(ts, ys)
            lines[k] = line
        self._canvas.draw()
        self._period_list.add_data((result, lines))
        print("Ended combination! :) ")
