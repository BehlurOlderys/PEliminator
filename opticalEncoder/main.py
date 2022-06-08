import time
import math
import numpy as np
from scipy.ndimage import label, gaussian_filter
from PIL import Image
import os
from time import sleep
from serial import Serial, SerialException

from tkinter import filedialog

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

    max_count = 20

    def __init__(self):
        self._value = 0
        self._history = []

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


serial_port = "COM8"
ser = None


def connect_to_serial():
    try:
        ser = Serial(port=serial_port, baudrate=115200, timeout=3)
    except SerialException:
        print(f"Cannot connect to serial on {serial_port}!")
        exit(-1)


def calculate_error_and_correct(expected_value, measured_value):
    error = expected_value - measured_value
    if abs(error) > error_threshold:
        correction = int(min(max_correction, error_gain * abs(error)))
        if error > 0:
            ser.write(f"CORRECT {correction}\n".encode())
            print(f"Correcting by {correction}")
        else:
            ser.write(f"CORRECT {-correction}\n".encode())
            print(f"Correcting by {-correction}")


# connect_to_serial()
main_dir = filedialog.askdirectory(title="Open dir with images")
files = get_last_files(main_dir)
print(f"Opening {len(files)} files!")

pre = ImagePreparator()

first_file_name = files[-1][0]
print(f"First file = {first_file_name}")
first_prepared = pre.prepare_one_image(get_np_data_from_image_file(first_file_name))

previous_time = files[0][1]

previous_sp = get_stripes_starts_positions(first_prepared)
previous_ep = get_stripes_ends_positions(first_prepared)

log_file = open("result.log", 'w', buffering=1)
log_file.write("length\ttime\terror\texpected\tmean\n")

filenames = [os.path.basename(f[0]) for f in files]
print(f"Filenames in the beginning: \n{filenames}")


# ser = Serial(port="COM8", baudrate=115200, timeout=3)
length_averager = Averager()
total_t = 0
total_mean = 0
total_xs = 0
total_xe = 0
counter = 0
while True:
    latest_state = get_last_files(main_dir)
    latest_filenames = [os.path.basename(f) for f, t in latest_state]
    # print(f"latest_filenames in while: {latest_filenames}")
    # print(f"current filenames in while: {filenames}")
    new_files = [f for f in latest_state if os.path.basename(f[0]) not in filenames]
    new_filenames = [os.path.basename(f) for f, t in new_files]
    if not new_files:
        print("Waiting 0.25s for new files...")
        sleep(0.25)
        continue

    print(f"new filenames in while: {new_filenames}")
    print(f"Got {len(new_files)} new files!")
    for f, t in new_files:
        try:
            p = pre.prepare_one_image(get_np_data_from_image_file(f))
            sp, ep = get_starts_and_ends(p)
        except IndexError:
            continue
        except PermissionError:
            continue
        except Exception as ex:
            print(f"Strangest exception happened: {ex}")
            print("Sleeping for 1000s!")
            sleep(1000)
        delta_t = t - previous_time
        previous_time = t
        total_t += delta_t
        expected = total_t * magical_factor

        result_s = get_mean_diff(sp, previous_sp)
        result_e = get_mean_diff(ep, previous_ep)

        length_averager.get_current_value()
        mean_length = length_averager.get_current_value()

        scale = arcsec_per_strip / mean_length
        if math.isnan(result_s) or math.isnan(result_e):
            continue

        mean_result = (result_e + result_s) / 2
        total_mean += mean_result*scale

        error_s = expected - total_xs
        error_e = expected - total_xe
        error_m = expected - total_mean

        log_file.write(f"{mean_length}\t{total_t}\t{error_m}\t{expected}\t{total_mean}\n")
        print(f"result s = {result_s}, result e = {result_e}, mean = {mean_result}, err={error_m}, t={total_t}")

        # calculate_error_and_correct(expected_value=expected, measured_value=total_mean)

        previous_sp = sp
        previous_ep = ep

        if counter >= 20:
            counter = 0
        else:
            try:
                os.remove(f)
            except Exception as e:
                print(f"Exception on removing file: {e}")
        counter += 1

    filenames += new_filenames

log_file.close()
