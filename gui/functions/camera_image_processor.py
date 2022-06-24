import os
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from datetime import datetime
from functions.global_settings import settings
import time
import math


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


class ImagePreparator:
    def __init__(self):
        self.__number = 0

    def prepare_one_image(self, raw_data):
        self.__number += 1
        prepared = threshold_half(gaussian_filter(normalize(raw_data), 3))
        return prepared


class Averager:
    def __init__(self, max_count=settings.get_averager_max()):
        self._max_count = max_count
        self._value = 0
        self._history = []

    def reset(self):
        self._history = []
        self._value = 0

    def is_empty(self):
        return len(self._history) == 0

    def is_full(self):
        return len(self._history) >= self._max_count

    def get_current_value(self):
        return self._value

    def update_value(self, v):
        if self.is_full():
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


class MyPID:
    def __init__(self, kp, ki, kd, isize, **_):
        self._kp_var = kp
        self._ki_var = ki
        self._kd_var = kd
        self._memory = [0]
        self._memory_size_var = isize
        print(f"Initializing PID with Kp={self._kp_var.get()},"
              f" Ki={self._ki_var.get()}, Kd={self._kd_var.get()} and size of {self._memory_size_var.get()}")

    def get_correction(self, error):
        diff_d = error-self._memory[-1]
        memory_size = int(self._memory_size_var.get())
        self._memory.append(error)
        while len(self._memory) >= memory_size:
            self._memory.pop(0)

        sum_i = sum(self._memory)
        try:
            return float(self._kp_var.get()) * error + \
                   float(self._ki_var.get()) * sum_i + \
                   float(self._kd_var.get()) * diff_d
        except ValueError:
            return 0


class CameraImageProcessor:
    def __init__(self, effector, plotter, feedback, dec_feedback, vars_dict):
        self._effector = effector
        self._plotter = plotter
        self._feedback = feedback
        self._dec_feedback = dec_feedback
        self._image_length_var = vars_dict["image_length"]
        self._log_file = open("logs\\result" + datetime.now().strftime("%m%d%Y_%H-%M-%S") + ".log", 'w', buffering=1)
        self._log_file.write("scale\tlength\ttime\texpected\terror\tmean\n")
        self._preparator = ImagePreparator()
        self._length_averager = Averager()
        self._ticks_averager = Averager(10)
        self._pid = MyPID(**vars_dict)
        self._total_t = 0
        self._total_mean_as = 0
        self._counter = 0
        self._scale_amendment = settings.get_initial_scale_amendment()
        self._previous_time = None
        self._previous_sp = None
        self._previous_ep = None
        self._last_file_data = None
        self._pipe = None
        self._dec_pipe = None
        self._corrections_map = {}
        self._dec_corrections_map = {}
        self._cumulated_correction = 0
        self._finished_ra_correction = 0
        self._current_error_as = 0
        self._previous_mean_error_as = 0

    def _send_correction_to_mount(self, correction):
        print(f"PID correction = {correction}")
        step_as = settings.get_stepper_microstep_as()
        steps = int(correction / step_as)
        if abs(steps) > 0:
            steps = min(max(steps, -10), 10)
            command = f"CORRECT {steps}\n"
            self._effector.effect(command)
            print(command)

    def _get_image_length_s(self):
        return int(self._image_length_var.get())

    def reset(self):
        if self._last_file_data is None:
            return
        self._length_averager.reset()
        self._total_t = 0
        self._total_mean_as = 0
        self._counter = 0
        f, t = self._last_file_data
        _, sp, ep = self._preprocess_one_file(f)
        self._previous_time = t
        self._previous_sp = sp
        self._previous_ep = ep
        self._ticks_averager.reset()
        self._cumulated_correction = 0
        self._finished_ra_correction = 0
        self._current_error_as = 0

    def __del__(self):
        self._log_file.close()

    def init(self, filename, timestamp):
        p, sp, ep = self._preprocess_one_file(filename)
        self._length_averager.update_value(DifferenceCalculator(p).get_stripes_length())
        self._last_file_data = filename, timestamp
        self._previous_time = timestamp
        self._previous_sp = sp
        self._previous_ep = ep
        self._plotter.add_points([(timestamp, 0, 0)])
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
            time.sleep(1000)
            return None

    def get_scale_amendment(self):
        return self._scale_amendment

    def amend_scale(self, value):
        self._scale_amendment += value

    def _get_ra_correction_value(self):
        try:
            pipe_file = open(settings.get_star_tracking_pipe_name(), "r")
            pipe_lines = pipe_file.readlines()
            pipe_file.close()
        except:
            print(" !!!! Could not obtain ra correction from file !!!! ")
            return None

        if not pipe_lines:
            return None
        last_correction = pipe_lines[-1]
        split_by_colon = last_correction.split(":")
        value = float(split_by_colon[-1])
        ident = int(split_by_colon[0])
        if ident in self._corrections_map.keys():
            return None

        self._corrections_map[ident] = value
        print(f"Acquired RA correction: {value}")
        return value

    def _get_dec_correction_value(self):
        try:
            pipe_file = open(settings.get_star_tracking_pipe_name()+"_dec", "r")
            dec_pipe_lines = pipe_file.readlines()
            pipe_file.close()
        except:
            print(" !!!! Could not obtain dec correction from file !!!! ")
            return None

        if not dec_pipe_lines:
            return None

        last_correction = dec_pipe_lines[-1]
        split_by_colon = last_correction.split(":")
        value = float(split_by_colon[-1])
        ident = int(split_by_colon[0])
        if ident in self._dec_corrections_map.keys():
            return None

        self._dec_corrections_map[ident] = value
        print(f"Acquired DEC correction: {value}")
        return value

    def _implement_ra_correction(self, error_mean, error_instant):
        correction = self._pid.get_correction(error_instant)
        self._send_correction_to_mount(correction)

    def idle(self):
        # mean_error = self._ticks_averager.get_current_value()
        # mean_error -= self._finished_ra_correction
        # self._implement_ra_correction(mean_error, self._current_error_as)
        pass

    def process(self, filename, timestamp):
        start_t = time.time()
        preprocess = self._preprocess_one_file(filename)
        if preprocess is None:
            return
        p, sp, ep = preprocess
        delta_t = timestamp - self._previous_time
        self._previous_time = timestamp
        self._last_file_data = filename, timestamp
        self._total_t += delta_t
        expected_as = self._total_t * settings.sidereal_speed

        result_s = get_mean_diff(sp, self._previous_sp)
        result_e = get_mean_diff(ep, self._previous_ep)
        mean_result = (result_e + result_s) / 2

        mean_length = self._length_averager.get_current_value()

        if math.isnan(result_s) or \
                math.isnan(result_e) or\
                math.isnan(mean_length) or\
                mean_length == 0:
            print(f"NaN!: s={result_s}, e={result_e}, m={mean_length}")
            return

        scale = self._scale_amendment + (settings.get_arcsec_per_strip() / mean_length)
        print(f"Scale = {scale}")
        mean_result_as = mean_result*scale
        self._total_mean_as += mean_result_as

        error_as = expected_as - self._total_mean_as
        error_as = delta_t*settings.sidereal_speed - mean_result_as
        self._ticks_averager.update_value(error_as)
        mean_error_as = self._ticks_averager.get_current_value()
        self._current_error_as = mean_error_as

        self._plotter.add_points([(timestamp, error_as, mean_error_as)])
        self._log_file.write(f"{scale}\t{mean_length}\t{self._total_t}\t{expected_as}\t{error_as}\t{mean_error_as}\n")

        self._finished_ra_correction = 0
        diff_err = mean_error_as - self._previous_mean_error_as
        self._previous_mean_error_as = mean_error_as
        self._implement_ra_correction(mean_error_as, error_as)

        self._previous_sp = sp
        self._previous_ep = ep

        self._correct_longterm_ra()
        self._correct_longterm_dec()

        # if self._counter == 10 or self._counter == 20:
        #     ra_correction = self._get_ra_correction_value()
        #     if ra_correction is not None:
        #         self._feedback.set_feedback(ra_correction)
        #         sky_movement_as = self._get_image_length_s() * 15  #as/per_s
        #         image_measured_movement_as = sky_movement_as - ra_correction  # or +
        #         image_speed_ass = image_measured_movement_as / self._get_image_length_s()
        #         encoder_speed_ass = mean_result_as / delta_t
        #         speed_error_ass = image_speed_ass - encoder_speed_ass
        #         print(f"*** Image speed = {image_speed_ass},"
        #               f" Encoder speed = {encoder_speed_ass}, "
        #               f"speed error={speed_error_ass} ***")
        #
        #         gain = self._feedback.get_feedback_gain()
        #         print(f"Current gain = {gain}")
        #         delta_a = ra_correction * gain
        #         print(f"Correction to scale is: {delta_a}")
        #         self.amend_scale(-delta_a)
        #
        #     dec_correction = self._get_dec_correction_value()
        #     if dec_correction is not None:
        #         self._dec_feedback.set_feedback(dec_correction)
        #         feedback_as_per_100s = dec_correction * 100 / self._get_image_length_s()
        #         error_per_100s = feedback_as_per_100s - self._cumulated_correction
        #         gain = self._dec_feedback.get_feedback_gain()
        #         # correction = -gain * dec_correction
        #         # correction = gain * feedback_as_per_100s  # gain should be 1 initially
        #         correction = -0.25*gain*feedback_as_per_100s # -gain*error_per_100s #-
        #         print(f"==== DEC CORRECTION SETTING: {correction}")
        #         self._cumulated_correction += correction
        #         self._effector.effect(f"ADD_DC {correction}\n")

        try:
            os.remove(filename)
        except Exception as e:
            print(f"Exception on removing file: {e}")
        end_t = time.time()
        print(f"Time of execution = {end_t - start_t}s")

    def _correct_longterm_ra(self):
        pass

    def _correct_longterm_dec(self):
        pass
