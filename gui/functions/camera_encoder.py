import math
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image
import os
from time import sleep
from functions.recent_files_provider import RecentImagesProvider, is_file_png
from functions.global_settings import settings
from functions.simple_1d_plotter import Simple1DPlotter
import tkinter as tk
from tkinter import ttk
from datetime import datetime

dummy_effector_label = "Dummy output"
serial_effector_label = "Serial output"
available_effectors = [dummy_effector_label, serial_effector_label]


def normalize(p):
    a = np.percentile(p, 5)
    b = np.percentile(p, 95)
    return (p - a) / (b-a)


def threshold_half(p):
    return 1*(p < np.median(p))  # less than median will be stripes, not spaces between


def get_np_data_from_image_file(file_path):
    im = Image.open(file_path)
    raw_data = np.array(im)
    return raw_data


class ImagePreparator:
    def __init__(self):
        self.__number = 0

    def prepare_one_image(self, raw_data):
        self.__number += 1
        prepared = threshold_half(gaussian_filter(normalize(raw_data), 3))
        return prepared


class Averager:

    max_count = settings.get_averager_max()

    def __init__(self):
        self._value = 0
        self._history = []

    def reset(self):
        self._history = []
        self._value = 0

    def get_current_value(self):
        return self._value

    def update_value(self, v):
        if len(self._history) >= Averager.max_count:
            self._history.pop(0)
        self._history.append(v)
        self._value = np.average(np.array(self._history))


class DifferenceCalculator:
    def __init__(self, p):
        self._h, _ = p.shape
        self._diff_lines = [np.diff(p[i, :]) for i in range(0, self._h)]

    def get_stripes_length(self):
        sum_length = 0
        for dline in self._diff_lines:
            falling_edges = dline < 0
            rising_edges = dline > 0
            f_edges_indices = np.where(falling_edges)
            r_edges_indices = np.where(rising_edges)
            # print(f"r = {r_edges_indices}, f = {f_edges_indices}")
            # for some reason f and r diffs are double (nested) arrays of shape [1][N] so I need to squeeze them
            f_lengths = np.squeeze(np.diff(f_edges_indices))
            r_lengths = np.squeeze(np.diff(r_edges_indices))
            sum_length += np.average(np.array(f_lengths[0], r_lengths[0]))
        return sum_length / self._h


def get_stripes_ends_positions(p):
    h, w = p.shape
    raw_ends = [
        np.where(
            np.diff(p[i, :]) < 0
        )[-1]
        for i in range(0, h)
    ]
    first_ends = [x[0] for x in raw_ends]
    return np.array(first_ends)


def get_stripes_starts_positions(p):
    """
    :param p: prepared image: binary with only full length stripes
    :return: array of positions of strip starts for each y coordinate of image
    """
    h, w = p.shape

    def get_edges(i):
        return np.where(np.diff(p[i, :]) > 0)

    raw_starts = [get_edges(i)[0] for i in range(0, h)]
    first_starts = [x[0] for x in raw_starts]
    return np.array(first_starts)


def get_starts_and_ends(p):
    s = get_stripes_starts_positions(p)
    e = get_stripes_ends_positions(p)
    return s, e


def get_mean_diff(s1, s2):
    r = []
    for (a, b) in zip(s1, s2):
        d = b - a
        if abs(d) < 10:
            r.append(d)

    return np.average(r)


def get_last_files(d):
    """
    returns list of pairs (file, timestamp)
    """
    files = [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith("png")]
    files = [(p, os.path.getctime(p)) for p in files]
    return sorted(files, key=lambda x: x[1])


class CorrectionEffector:
    def __init__(self, serial):
        self._serial = serial

    def effect(self, expected_value, measured_value):
        error = expected_value - measured_value
        print(f"Error = {error}")
        if abs(error) > settings.get_error_threshold():
            correction = int(min(settings.get_max_correction(), settings.get_error_gain() * abs(error)))
            if error > 0:
                self._serial.write_immediately(f"CORRECT {correction}\n".encode())
                print(f"Correcting by {correction}")
            else:
                self._serial.write_immediately(f"CORRECT {-correction}\n".encode())
                print(f"Correcting by {-correction}")


class DummyEffector:
    def effect(self, e, m):
        pass


class CameraImageProcessor:
    def __init__(self, effector, plotter):
        self._effector = effector
        self._plotter = plotter
        self._log_file = open("result" + datetime.now().strftime("%m%d%Y_%H-%M-%S") + ".log", 'w', buffering=1)
        self._log_file.write("scale\tlength\ttime\terror\texpected\tmean\n")
        self._preparator = ImagePreparator()
        self._length_averager = Averager()
        self._total_t = 0
        self._total_mean = 0
        self._counter = 0
        self._scale_amendment = 0
        self._previous_time = None
        self._previous_sp = None
        self._previous_ep = None
        self._last_file_data = None

    def reset(self):
        if self._last_file_data is None:
            return
        self._length_averager.reset()
        self._total_t = 0
        self._total_mean = 0
        self._counter = 0
        self._scale_amendment = 0
        f, t = self._last_file_data
        _, sp, ep = self._preprocess_one_file(f)
        self._previous_time = t
        self._previous_sp = sp
        self._previous_ep = ep

    def __del__(self):
        self._log_file.close()

    def init(self, filename, timestamp):
        _, sp, ep = self._preprocess_one_file(filename)
        self._last_file_data = filename, timestamp
        self._previous_time = timestamp
        self._previous_sp = sp
        self._previous_ep = ep
        self._plotter.add_points([(timestamp, 0)])
        return True

    def _preprocess_one_file(self, filename):
        try:
            p = self._preparator.prepare_one_image(get_np_data_from_image_file(filename))
            sp, ep = get_starts_and_ends(p)
            return p, sp, ep
        except IndexError:
            print("Index error ocurred!")
            return None
        except PermissionError:
            print("Permission error ocurred!")
            return None
        except Exception as ex:
            print(f"Strangest exception happened: {ex}")
            print("Sleeping for 1000s!")
            sleep(1000)
            return None

    def get_scale_amendment(self):
        return self._scale_amendment

    def amend_scale(self, value):
        self._scale_amendment = value

    def process(self, filename, timestamp):
        preprocess = self._preprocess_one_file(filename)
        if preprocess is None:
            return
        p, sp, ep = preprocess
        delta_t = timestamp - self._previous_time
        self._previous_time = timestamp

        self._last_file_data = filename, timestamp

        self._total_t += delta_t
        expected = self._total_t * settings.sidereal_speed

        result_s = get_mean_diff(sp, self._previous_sp)
        result_e = get_mean_diff(ep, self._previous_ep)

        self._length_averager.update_value(DifferenceCalculator(p).get_stripes_length())
        mean_length = self._length_averager.get_current_value()

        if math.isnan(result_s) or \
                math.isnan(result_e) or\
                math.isnan(mean_length) or\
                mean_length == 0:
            print(f"NaN!: s={result_s}, e={result_e}, m={mean_length}")
            return

        scale = self._scale_amendment + (settings.get_arcsec_per_strip() / mean_length)
        mean_result = (result_e + result_s) / 2
        self._total_mean += mean_result*scale

        error_m = expected - self._total_mean

        self._plotter.add_points([(timestamp, error_m)])

        self._log_file.write(f"{scale}\t{mean_length}\t{self._total_t}\t{error_m}\t{expected}\t{self._total_mean}\n")
        # print(f"{mean_length}\t{self._total_t}\t{error_m}\t{expected}\t{self._total_mean}\n")

        self._effector.effect(expected, self._total_mean)

        self._previous_sp = sp
        self._previous_ep = ep

        if self._counter >= 20:
            self._counter = 0
        else:
            try:
                os.remove(filename)
            except Exception as e:
                print(f"Exception on removing file: {e}")
        self._counter += 1


class CameraEncoder:
    def __init__(self, serial_reader, plotter):
        self._plotter = plotter
        self._effector = DummyEffector() if serial_reader is None else CorrectionEffector(serial_reader)
        if self._effector is None:
            print("Dummy effector chosen!")
        self._processor = CameraImageProcessor(self._effector, plotter)
        self._provider = RecentImagesProvider(self._processor, is_file_png)

    def set_amend(self, value):
        self._processor.amend_scale(value)

    def reset(self):
        self._plotter.clear_plot()
        self._processor.reset()

    def start(self):
        self._plotter.clear_plot()
        self._provider.start()

    def kill(self):
        self._provider.kill()


class CameraEncoderGUI:
    def __init__(self, frame, reader):
        self._encoder_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        self._encoder_frame.pack(side=tk.TOP)

        self._plotter = Simple1DPlotter(frame)
        self._reader = reader
        self._camera_encoder = CameraEncoder(None, self._plotter)
        self._choice = tk.StringVar(value=available_effectors[0])
        self._reset_button = tk.Button(self._encoder_frame, text="Reset camera encoder",
                                       command=self._camera_encoder.reset)
        self._reset_button.pack(side=tk.RIGHT)
        self._amendment = tk.StringVar(value=0)
        self._amendment_spin = ttk.Spinbox(self._encoder_frame, from_=-999, to=999,
                                           width=5, textvariable=self._amendment)
        self._amendment_spin.pack(side=tk.RIGHT)
        self._amend_button = tk.Button(self._encoder_frame, text="Set encoder amendment",
                                       command=self._camera_encoder.set_amend(
                                           int(self._amendment.get()))
                                       )
        self._amend_button.pack(side=tk.RIGHT)

        self._button = tk.Button(self._encoder_frame,
                                 text="Start camera encoder", command=self._start_action)
        self._button.pack(side=tk.LEFT)

        self._combobox = ttk.Combobox(self._encoder_frame, textvariable=self._choice,
                                      values=available_effectors)
        self._combobox.pack(side=tk.RIGHT)

    def kill(self):
        self._camera_encoder.kill()

    def _start_action(self):
        effector = self._reader if self._choice.get() == serial_effector_label else None
        self._camera_encoder = CameraEncoder(effector, self._plotter)
        self._camera_encoder.start()
        self._button.configure(text="Stop camera encoder", command=self._stop_action)

    def _stop_action(self):
        self._camera_encoder.kill()
        self._camera_encoder = None
        self._button.configure(text="Start camera encoder", command=self._start_action)
