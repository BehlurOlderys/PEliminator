import numpy as np
from common.global_settings import settings, us_in_1_second
from tkinter import filedialog
from datetime import date


ideal_speed_as_const = 1296000.0 / 86164.0


def get_data_from_correction_file(filepath):
    print(f"Loaded correction data from {filepath}")

    with open(filepath) as f:
        lines = [s.strip() for s in f.readlines()]

    all_text = ' '.join(lines)
    old_times_str, old_data_str, old_model_str = [r.strip() for r in all_text.split('};') if r]
    old_times = [int(s.strip()) for s in old_times_str.split(',')]
    old_data = np.array([int(''.join(filter(str.isnumeric, s))) for s in old_data_str.split(',')])
    print(f"Times = {old_times}")
    print(f"Data = {old_data}")
    return old_times, old_data


def get_new_correction_data(old_data, error_data):
    tics_per_s = np.divide(us_in_1_second * np.ones_like(old_data), old_data)
    speed_factor = settings.get_worm_speed_factor()
    worm_speed_as = speed_factor * tics_per_s
    ideal_speed_as = ideal_speed_as_const*np.ones_like(worm_speed_as)
    real_speed_as = np.add(ideal_speed_as, error_data)
    new_model = np.divide(worm_speed_as, real_speed_as)
    new_worm_speed = np.multiply(ideal_speed_as, new_model)
    new_ticks_pers_s = new_worm_speed / speed_factor
    new_data = np.divide(us_in_1_second * np.ones_like(new_ticks_pers_s), new_ticks_pers_s)
    return new_data


def write_correction_data(times, new_data):
    new_times_str = ', '.join(map(str, times)) + "};\n"
    new_data_str = 'UL, '.join(map(str, map(int, new_data))) + "};\n"

    d = date.today().strftime("%Y-%m-%d-%H-%M-%S")
    with open(d + '_correction_data.mdl', 'w') as f:
        f.write(new_times_str)
        f.write(new_data_str)


#correction_data_path_mock = "C:/Users/Florek/Desktop/_STEROWANIE/PEliminator/old_data.txt"
correction_data_path_mock = None


class TimesGenerator:
    def __init__(self):
        self._times = None
        self._data = None
        self._old = None
        self._old_path = correction_data_path_mock

    def push_errors(self, errors):
        self._times, self._data = errors

    def save(self):
        pass

    def load(self):
        direction = settings.get_correction_direction()
        if self._old_path is None:
            self._old_path = filedialog.askopenfilename(title="Select file with previous data:")

        if self._old_path is None:
            return

        old_times, old_data = get_data_from_correction_file(self._old_path)
        new_data, new_model = get_new_correction_data(old_data, self._data)
        write_correction_data(old_times, new_data)










