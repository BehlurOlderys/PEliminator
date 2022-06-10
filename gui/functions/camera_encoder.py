import math
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image
import os
from time import sleep
from functions.recent_files_provider import RecentImagesProvider, is_file_png


sidereal_day_s = 86164
resolution_lpi = 200
counts_per_rotation = 1800
arcsec_full_circle = 1296000
magical_factor = arcsec_full_circle / sidereal_day_s
error_threshold = 0.3
error_gain = 5
max_correction = 10
arcsec_per_strip = arcsec_full_circle / counts_per_rotation


def normalize(p):
    a = np.percentile(p, 5)
    b = np.percentile(p, 95)
    return (p - a) / (b-a)


def threshold_half(p):
    return 1*(p < np.median(p))  # less than median will be stripes, not spaces between


def get_np_data_from_image_file(file_path):
    im = Image.open(file_path)
    raw_data = np.array(im)
    # print(raw_data.shape)
    return raw_data


class ImagePreparator:
    def __init__(self):
        self.__number = 0

    def prepare_one_image(self, raw_data):
        self.__number += 1
        prepared = threshold_half(gaussian_filter(normalize(raw_data), 3))
        return prepared


class Averager:

    max_count = 48

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
    raw_starts = [
            np.where(
                np.diff(p[i, :]) > 0
            )[0]
        for i in range(0, h)
    ]
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


# # connect_to_serial()
# main_dir = filedialog.askdirectory(title="Open dir with images")
# files = get_last_files(main_dir)
# print(f"Opening {len(files)} files!")
#
# pre = ImagePreparator()
#
# first_file_name = files[-1][0]
# print(f"First file = {first_file_name}")
# first_prepared = pre.prepare_one_image(get_np_data_from_image_file(first_file_name))
#
# previous_time = files[0][1]
#
# previous_sp = get_stripes_starts_positions(first_prepared)
# previous_ep = get_stripes_ends_positions(first_prepared)
#
# log_file = open("result.log", 'w', buffering=1)
# log_file.write("length\ttime\terror\texpected\tmean\n")
#
# filenames = [os.path.basename(f[0]) for f in files]
# print(f"Filenames in the beginning: \n{filenames}")
#
#
# # ser = Serial(port="COM8", baudrate=115200, timeout=3)
# length_averager = Averager()
# total_t = 0
# total_mean = 0
# total_xs = 0
# total_xe = 0
# counter = 0
# while True:
#     latest_state = get_last_files(main_dir)
#     latest_filenames = [os.path.basename(f) for f, t in latest_state]
#     # print(f"latest_filenames in while: {latest_filenames}")
#     # print(f"current filenames in while: {filenames}")
#     new_files = [f for f in latest_state if os.path.basename(f[0]) not in filenames]
#     new_filenames = [os.path.basename(f) for f, t in new_files]
#     if not new_files:
#         print("Waiting 0.25s for new files...")
#         sleep(0.25)
#         continue
#
#     print(f"new filenames in while: {new_filenames}")
#     print(f"Got {len(new_files)} new files!")
#     for f, t in new_files:
#         try:
#             p = pre.prepare_one_image(get_np_data_from_image_file(f))
#             sp, ep = get_starts_and_ends(p)
#         except IndexError:
#             continue
#         except PermissionError:
#             continue
#         except Exception as ex:
#             print(f"Strangest exception happened: {ex}")
#             print("Sleeping for 1000s!")
#             sleep(1000)
#         delta_t = t - previous_time
#         previous_time = t
#         total_t += delta_t
#         expected = total_t * magical_factor
#
#         result_s = get_mean_diff(sp, previous_sp)
#         result_e = get_mean_diff(ep, previous_ep)
#
#         length_averager.get_current_value()
#         mean_length = length_averager.get_current_value()
#
#         scale = arcsec_per_strip / mean_length
#         if math.isnan(result_s) or math.isnan(result_e):
#             continue
#
#         mean_result = (result_e + result_s) / 2
#         total_mean += mean_result*scale
#
#         error_s = expected - total_xs
#         error_e = expected - total_xe
#         error_m = expected - total_mean
#
#         log_file.write(f"{mean_length}\t{total_t}\t{error_m}\t{expected}\t{total_mean}\n")
#         print(f"result s = {result_s}, result e = {result_e}, mean = {mean_result}, err={error_m}, t={total_t}")
#
#         # calculate_error_and_correct(expected_value=expected, measured_value=total_mean)
#
#         previous_sp = sp
#         previous_ep = ep
#
#         if counter >= 20:
#             counter = 0
#         else:
#             try:
#                 os.remove(f)
#             except Exception as e:
#                 print(f"Exception on removing file: {e}")
#         counter += 1
#
#     filenames += new_filenames
#
# log_file.close()

class CorrectionEffector:
    def __init__(self, serial):
        self._serial = serial

    def effect(self, expected_value, measured_value):
        error = expected_value - measured_value
        if abs(error) > error_threshold:
            correction = int(min(max_correction, error_gain * abs(error)))
            if error > 0:
                self._serial.write(f"CORRECT {correction}\n".encode())
                print(f"Correcting by {correction}")
            else:
                self._serial.write(f"CORRECT {-correction}\n".encode())
                print(f"Correcting by {-correction}")


class DummyEffector:
    def effect(self, e, m):
        pass


class CameraImageProcessor:
    def __init__(self, effector):
        self._effector = effector
        self._log_file = open("result.log", 'w', buffering=1)
        self._log_file.write("length\ttime\terror\texpected\tmean\n")
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
        sp, ep = self._preprocess_one_file(f)
        self._previous_time = t
        self._previous_sp = sp
        self._previous_ep = ep

    def __del__(self):
        self._log_file.close()

    def init(self, filename, timestamp):
        sp, ep = self._preprocess_one_file(filename)
        self._last_file_data = filename, timestamp
        self._previous_time = timestamp
        self._previous_sp = sp
        self._previous_ep = ep
        return True

    def _preprocess_one_file(self, filename):
        try:
            p = self._preparator.prepare_one_image(get_np_data_from_image_file(filename))
            sp, ep = get_starts_and_ends(p)
            return sp, ep
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
        sp, ep = self._preprocess_one_file(filename)

        delta_t = timestamp - self._previous_time
        self._previous_time = timestamp

        self._last_file_data = filename, timestamp

        self._total_t += delta_t
        expected = self._total_t * magical_factor

        result_s = get_mean_diff(sp, self._previous_sp)
        result_e = get_mean_diff(ep, self._previous_ep)

        self._length_averager.get_current_value()
        mean_length = self._length_averager.get_current_value()

        scale = self._scale_amendment + (arcsec_per_strip / mean_length)
        if math.isnan(result_s) or math.isnan(result_e):
            print("NaN!")
            return

        mean_result = (result_e + result_s) / 2
        self._total_mean += mean_result*scale

        error_m = expected - self._total_mean

        self._log_file.write(f"{mean_length}\t{self._total_t}\t{error_m}\t{expected}\t{self._total_mean}\n")
        print(f"{mean_length}\t{self._total_t}\t{error_m}\t{expected}\t{self._total_mean}\n")

        self._effector(expected, self._total_mean)

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
    def __init__(self, serial_reader):
        self._serial = serial_reader
        self._effector = DummyEffector()
        self._processor = CameraImageProcessor(self._effector)
        self._provider = RecentImagesProvider(self._processor, is_file_png)

    def set_amend(self, value):
        self._processor.amend_scale(value)

    def reset(self):
        self._processor.reset()

    def start(self):
        self._provider.start()

    def kill(self):
        self._provider.kill()
