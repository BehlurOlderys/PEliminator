import numpy as np
from widgets.global_settings import settings, us_in_1_second
from tkinter import filedialog


correction_data_path_mock = "C:/Users/Florek/Desktop/_STEROWANIE/PEliminator/old_data.txt"


class TimesGenerator:
    def __init__(self):
        self._times = None
        self._data = None
        self._old = None
        self._old_path = correction_data_path_mock

    def push_error(self, errors):
        self._times, self._data = errors

    def save(self):
        pass

    def load(self):
        direction = settings.get_correction_direction()
        if self._old_path is None:
            self._old_path = filedialog.askopenfilename(title="Select file with previous data:")

        if self._old_path is None:
            return

        print(f"Loaded correction data from {self._old_path}")

        with open(self._old_path) as f:
            lines = [s.strip() for s in f.readlines()]

        all_text = ' '.join(lines)
        old_times_str, old_data_str, old_model_str = [r.strip() for r in all_text.split('};') if r]
        old_times = [int(s.strip()) for s in old_times_str.split(',')]
        old_data = np.array([int(''.join(filter(str.isnumeric, s))) for s in old_data_str.split(',')])
        old_model = [float(s.strip()) for s in old_model_str.split(',')]
        print(f"Times = {old_times}")
        print(f"Data = {old_data}")
        print(f"Model = {old_model}")

        tics_per_s = np.divide(us_in_1_second*np.ones_like(old_data), old_data)
        speed_factor = settings.get_worm_speed_factor()
        worm_speed_as = speed_factor*tics_per_s
        ideal_speed_as = np.divide(worm_speed_as, old_model)
        real_speed_as = np.add(ideal_speed_as, self._data)
        new_model = np.divide(worm_speed_as, real_speed_as)
        new_worm_speed = np.multiply(ideal_speed_as, new_model)
        new_ticks_pers_s = new_worm_speed / speed_factor
        new_data = np.divide(us_in_1_second*np.ones_like(new_ticks_pers_s), new_ticks_pers_s)

        new_times_str = ', '.join(map(str, old_times)) + "};\n"
        new_data_str = 'UL, '.join(map(str, map(int, new_data))) + "};\n"
        new_model_str = ', '.join(map(lambda x: "%.6f" % x, new_model)) + "};\n"

        with open('new_data.txt', 'w') as f:
            f.write(new_times_str)
            f.write(new_data_str)
            f.write(new_model_str)










