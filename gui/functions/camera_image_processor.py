from functions.global_settings import settings
from functions.pid_controller import MyPID, filter_dict_for_prefix_to_pid
import numpy as np
from scipy.ndimage import gaussian_filter
from datetime import datetime
import time
import math
import matplotlib.pyplot as plt
import os


class OnceForAWhileDoer:
    def __init__(self, interval):
        self._interval = interval
        self._counter = 0

    def do_once_for_a_while(self, f):
        if self._counter >= self._interval:
            f()
            self._counter = 0
        self._counter += 1


def normalize(p):
    a = np.percentile(p, 5)
    b = np.percentile(p, 95)
    return (p - a) / (b-a)


def threshold_half(p):
    return 1*(p < np.median(p))  # less than median will be stripes, not spaces between


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
    def __init__(self, max_count):
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
        print(f"shape = {p.shape}")
        self._diff_lines = [np.diff(p[i, :]) for i in range(0, self._h)]

    def get_stripes_length(self):
        all_lengths = np.array([])
        for dline in self._diff_lines:
            falling_edges = dline < 0
            rising_edges = dline > 0
            f_edges_indices = np.where(falling_edges)
            r_edges_indices = np.where(rising_edges)
            print(f"indices_f = {f_edges_indices[0]} , indices_r = {r_edges_indices[0]})")
            lengths_r = np.diff(r_edges_indices[0])
            lengths_f = np.diff(f_edges_indices[0])
            all_lengths = np.concatenate((all_lengths, lengths_r, lengths_f))

        average_length = np.median(all_lengths)
        print(f"average_length = {average_length}")
        return average_length


class CameraImageProcessor:
    def __init__(self, effector, plotter, ra_feedback, dec_feedback, vars_dict):
        self._effector = effector
        self._plotter = plotter
        self._ra_feedback = ra_feedback
        self._dec_feedback = dec_feedback
        self._image_length_var = vars_dict["image_length"]
        self._log_file = open("logs\\result" + datetime.now().strftime("%m%d%Y_%H-%M-%S") + ".log", 'w', buffering=1)
        self._log_file.write("scale\tlength\texpected\terror\tcorrection\n")
        self._preparator = ImagePreparator()
        self._length_averager = Averager(10)
        self._length_average_performer = OnceForAWhileDoer(100)
        self._main_pid = MyPID(**filter_dict_for_prefix_to_pid(vars_dict, "main_pid"))
        self._longterm_ra_pid = MyPID(verbose=True, **filter_dict_for_prefix_to_pid(vars_dict, "long_ra_pid"))
        self._longterm_dec_pid = MyPID(**filter_dict_for_prefix_to_pid(vars_dict, "long_dec_pid"))
        self._total_expected_as = 0
        self._total_mean_as = 0
        self._scale_amendment = settings.get_initial_scale_amendment()
        self._previous_time = None
        self._previous_sp = None
        self._previous_ep = None
        self._last_file_data = None
        self._corrections_map = {}
        self._dec_corrections_map = {}
        max_count_ra = self._get_max_count_ra()
        print(f"Max count for RA  ={max_count_ra}")
        self._longterm_ra_correction = 0
        self._longterm_dec_correction = 0
        self._start_t = time.time()
        self._leftover_correction = 0

    def _get_max_count_ra(self):
        return max(5, int(662/float(self._image_length_var.get())))

    def _send_correction_to_mount(self, correction):
        print(f"PID correction = {correction}")
        step_as = settings.get_stepper_microstep_as()
        steps = int(correction / step_as)
        if abs(steps) > 0:
            steps = min(max(steps, -settings.get_max_correction()), settings.get_max_correction())
            command = f"CORRECT {steps}\n"
            self._effector.effect(command)
            print(command)
            return steps
        return 0

    def _get_image_length_s(self):
        return int(self._image_length_var.get())

    def reset(self):
        if self._last_file_data is None:
            return
        self._length_averager.reset()
        self._total_expected_as = 0
        self._total_mean_as = 0
        f, t = self._last_file_data
        _, sp, ep = self._preprocess_one_file(f)
        self._previous_time = t
        self._previous_sp = sp
        self._previous_ep = ep
        max_count_ra = self._get_max_count_ra()
        self._longterm_ra_correction = 0
        self._longterm_dec_correction = 0
        self._leftover_correction = 0

    def _get_measured_speed(self):
        return settings.sidereal_speed + self._longterm_ra_correction

    def __del__(self):
        self._log_file.close()

    def init(self, data, timestamp):
        pipe_ra_name = settings.get_star_tracking_pipe_name()
        if os.path.exists(pipe_ra_name):
            os.remove(pipe_ra_name)
        dec_pipe_name = settings.get_star_tracking_pipe_name() + "_dec"
        if os.path.exists(dec_pipe_name):
            os.remove(dec_pipe_name)

        p, sp, ep = self._preprocess_one_file(data)
        print(f"p = {p} from init")
        self._length_averager.update_value(DifferenceCalculator(p).get_stripes_length())
        self._last_file_data = data, timestamp
        self._previous_time = timestamp
        self._previous_sp = sp
        self._previous_ep = ep
        self._plotter.add_points([(timestamp, 0, 0)])
        return True

    def _preprocess_one_file(self, data):
        try:
            p = self._preparator.prepare_one_image(data)
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
            print("Displaying last image and sleeping for 1000s!")
            plt.imshow(data)
            plt.show()
            time.sleep(1000)
            return None

    def get_scale_amendment(self):
        return self._scale_amendment

    def amend_scale(self, value):
        self._scale_amendment += value

    def _get_ra_correction_value(self):
        print("GET_RA_CORR: Started")
        try:
            pipe_file = open(settings.get_star_tracking_pipe_name(), "r")
            pipe_lines = pipe_file.readlines()
            pipe_file.close()
        except:
            print("GET_RA_CORR: !!!! Could not obtain ra correction from file !!!! ")
            return None

        if not pipe_lines:
            print("GET_RA_CORR: No lines found")
            return None
        last_correction = pipe_lines[-1]
        split_by_colon = last_correction.split(":")
        value = float(split_by_colon[-1])
        ident = int(split_by_colon[0])
        if ident in self._corrections_map.keys():
            print("GET_RA_CORR: No unique lines found")
            return None

        self._corrections_map[ident] = value
        print(f"GET_RA_CORR: Acquired RA correction: {value}")
        return value

    def add_ra_set_point_as(self, value_as):
        print(f"=== RA dither by {value_as}\"")
        self._total_expected_as += value_as

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

    def _implement_ra_correction(self, error_instant):
        correction = self._main_pid.get_correction(error_instant)
        return self._send_correction_to_mount(correction)

    def process(self, data, timestamp):
        preprocess = self._preprocess_one_file(data)
        if preprocess is None:
            return
        p, sp, ep = preprocess
        delta_t = timestamp - self._previous_time
        self._previous_time = timestamp
        self._last_file_data = data, timestamp
        self._total_expected_as += delta_t*self._get_measured_speed()

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

        self._length_average_performer.do_once_for_a_while(lambda:
            self._length_averager.update_value(
                DifferenceCalculator(p).get_stripes_length()
            )
        )
        scale = self._scale_amendment + (settings.get_arcsec_per_strip() / mean_length)
        print(f"Scale = {scale}")
        mean_result_as = mean_result*scale
        self._total_mean_as += mean_result_as

        total_error_as = self._total_expected_as - self._total_mean_as
        error_as = delta_t*self._get_measured_speed() - mean_result_as
        corr = self._implement_ra_correction(total_error_as)

        self._plotter.add_points([(timestamp, corr, total_error_as)])
        self._log_file.write(f"{scale}\t{mean_length}\t{self._total_expected_as}\t{error_as}\t{corr}\n")

        self._previous_sp = sp
        self._previous_ep = ep

        self._correct_longterm_ra()
        self._correct_longterm_dec()

        end_t = time.time()
        print(f"Time of execution = {end_t - self._start_t}s")
        self._start_t = time.time()

    def _correct_longterm_ra(self):
        ra_error = self._get_ra_correction_value()
        if ra_error is None:
            return
        frame_time = float(self._image_length_var.get())
        print(f"==================== LT RA ERROR aquired: {ra_error} as/s while frame is {frame_time}s")
        error_per_frame = ra_error*frame_time
        print(f"==================== LT RA ERROR = {error_per_frame} /frame")
        correction = self._longterm_ra_pid.get_correction(ra_error)
        self._ra_feedback.set_feedback(ra_error)
        print(f"==================== LT RA CORRECTION = {correction}")
        self._longterm_ra_correction += correction
        #
        # if abs(error_per_frame) < 1.5*settings.get_image_scale():
        #     print(f"==================== LT RA ERROR is smaller than scale {settings.get_image_scale()}")
        #     return
        # TODO LATER!

    def _correct_longterm_dec(self):
        dec_error = self._get_dec_correction_value()
        if dec_error is None:
            return

        """ probably minus sign... """
        dec_error = -dec_error
        frame_time = float(self._image_length_var.get())
        print(f"%%%%%%%%%%%%%%%% LT DEC ERROR acquired: {dec_error}\" per s while frame is {frame_time}s")

        error_per_100s = 100*dec_error
        print(f"%%%%%%%%%%%%%%%% LT DEC ERROR speed = {error_per_100s} \"/100s")
        correction = self._longterm_dec_pid.get_correction(error_per_100s)
        correction += self._leftover_correction
        self._dec_feedback.set_feedback(error_per_100s)
        print(f"%%%%%%%%%%%%%%%% LT DEC CORRECTION = {correction}")
        integer_correction = int(correction)
        self._leftover_correction = (correction - integer_correction)
        self._effector.effect(f"ADD_DC {int(correction)}\n")
