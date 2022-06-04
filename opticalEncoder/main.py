import numpy as np
from scipy.ndimage import label, gaussian_filter
from PIL import Image
import os
from time import sleep
from serial import Serial

import matplotlib.patches as mpatches
from matplotlib import pyplot as plt

file1 = "C:/Users/Florek/Desktop/SharpCap Captures/2022-04-06/Capture/20_28_20/minimal/Capture_00011.png"
file2 = "C:/Users/Florek/Desktop/SharpCap Captures/2022-04-06/Capture/20_28_20/minimal/Capture_00012.png"
file3 = "C:/Users/Florek/Desktop/SharpCap Captures/2022-04-06/Capture/20_28_20/minimal/Capture_00013.png"
import tkinter as tk
from tkinter import filedialog

line_stripe_offset = 40
pixels_count_threshold_for_group = 1000
resolution_lpi = 200
counts_per_rotation = 1800
arcsec_full_circle = 1296000
arcsec_per_strip = arcsec_full_circle / counts_per_rotation
line_greaters = [False, False, True, True]


class RegionSingularX:
    def __init__(self, x):
        self._x = x

    def get_bounded_part_of_image(self, p, greater):
        mask = np.zeros_like(p)
        if greater:
            mask[:, int(self._x):] = 1
        else:
            mask[:, :int(self._x)] = 1
        return mask.astype(bool)


class RegionSingularY:
    def __init__(self, y):
        self._y = y

    def get_bounded_part_of_image(self, p, greater):
        mask = np.zeros_like(p)
        if greater:
            mask[:int(self._y), :] = 1
        else:
            mask[int(self._y):, :] = 1
        return mask.astype(bool)


class RegionRegularLine:
    def __init__(self, a, b):
        self._a = a
        self._b = b

    def get_bounded_part_of_image(self, p, greater):
        h, w = p.shape
        mask = np.zeros_like(p)
        for x in range(0, w):
            y = max(0, min(h - 1, int(self._a * x + self._b)))
            if greater:
                mask[y:, x] = 1
            else:
                mask[:y, x] = 1

        return mask.astype(bool)


def normalize(p):
    a = np.percentile(p, 5)
    b = np.percentile(p, 95)
    return (p - a) / (b-a)


def threshold_half(p):
    return 1*(p < np.median(p))  # less than median will be stripes, not spaces between


def get_mask_bounded_by_line(p, line, greater):
    a, b = line
    h, w = p.shape
    mask = np.zeros_like(p)
    for x in range(0, w):
        y = max(0, min(h-1, int(a*x + b)))
        if greater:
            mask[y:, x] = 1
        else:
            mask[:y, x] = 1

    return mask.astype(bool)


def get_line_two_points(p1, p2):
    x, y = p2 - p1
    a = y/x
    b = p1[1] - p1[0]*a
    return a, b


class MyRectangle:
    def __init__(self, anchor, width, height, angle_deg):
        self._point = anchor
        self._width = width
        self._height = height
        self._angle_deg = angle_deg

    def get_anchor_point(self):
        return self._point

    def get_dimensions(self):
        return self._width, self._height

    def get_angle_deg(self):
        return self._angle_deg

    def get_angle_rad(self):
        return np.deg2rad(self._angle_deg)


def get_lines_from_rect(rect: MyRectangle):
    pA = np.array(rect.get_anchor_point())
    fi = rect.get_angle_rad()
    w, h = rect.get_dimensions()
    pB = pA + (np.cos(fi) * w, np.sin(fi) * w)
    pC = pB + (-np.sin(fi) * h, np.cos(fi) * h)
    pD = pC + (-np.cos(fi) * w, -np.sin(fi) * w)
    print(f"pA = {pA}, pB = {pB}, pC = {pC}, pD = {pD}, ")

    line_AB = get_line_two_points(pA, pB)
    line_BC = get_line_two_points(pB, pC)
    line_CD = get_line_two_points(pC, pD)
    line_DA = get_line_two_points(pD, pA)
    return [line_AB, line_BC, line_CD, line_DA]


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
        # print(f"Preparing image no {self.__number}")
        prepared = threshold_half(gaussian_filter(normalize(raw_data), 3))
        return prepared


def calculate_pixels_inside_rect(p, rect: MyRectangle):
    if rect.get_angle_deg() == 0.:
        w, h = rect.get_dimensions()
        x, y = rect.get_anchor_point()
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        fragment = p[y:y+h, x:x+w]
        return np.sum(fragment)
    lines = get_lines_from_rect(rect)
    mask = np.ones_like(p)
    sub_masks = [get_mask_bounded_by_line(p, line, greater=g) for line, g in zip(lines, line_greaters)]
    for s in sub_masks:
        mask = np.logical_and(mask, s)

    return np.sum(np.multiply(p, mask.astype(int)))


def get_lines_centered_on_stripes(binary_image):
    structure = np.ones((3, 3), dtype=np.uint8)
    labeled, ncomponents = label(binary_image, structure)
    print(f"Shape = {labeled.shape}, number = {ncomponents}")

    label_indices = list(range(1, ncomponents + 1))
    single_labels = [(labeled == index).astype(np.uint8) for index in label_indices]
    significant_labels = [i for i in single_labels if np.count_nonzero(i) > pixels_count_threshold_for_group]
    print(f"No of significant components = {len(significant_labels)}")

    coeffs = []
    for s in significant_labels:
        # plt.imshow(s)
        # plt.show()
        # one_label = np.multiply(np_frame, labels).astype(np.uint8)
        (x, y) = s.nonzero()
        coeffs.append(np.array(np.polyfit(y, x, 1)))

    coeffs.sort(key=lambda x: x[1])
    return coeffs



rectangle = MyRectangle((100, 240), width=1100, height=100, angle_deg=0)


# def mask_unfull_stripes(p):


def get_mean_slope(p):
    mid_lines = np.array(get_lines_centered_on_stripes(p))
    mean_slope = np.mean(mid_lines, axis=0)[0]
    return mean_slope


def get_full_stripes(p, mean_slope: float):
    only_full_stripes = None
    h, w = p.shape
    intercept_x_low = np.array(np.where(np.diff(p[:, 0]) > 0))[0]
    intercept_x_high = np.array(np.where(np.diff(p[:, -1]) < 0))[0]

    if mean_slope > 0:
        """
        stripes are "falling" on image.
        First full stripe will be first starting on low ys
        """
        line_low = intercept_x_low[0] - line_stripe_offset
        line_high = intercept_x_high[-1] + line_stripe_offset - w*mean_slope
        mask_low = get_mask_bounded_by_line(p, (mean_slope, line_low), greater=True)
        mask_high = get_mask_bounded_by_line(p, (mean_slope, line_high), greater=False)

        only_full_stripes = p*np.logical_and(mask_high, mask_low)

    return only_full_stripes


def get_function_for_average_width_of_stripe(p):
    """
    Should return average width of a stripe as a function of x coordinate
    :param p: image with only full stripes
    :return: real function of real argument
    """
    h, w = p.shape
    raw_lengths = [
        np.diff(
            np.array(
                np.where(
                    np.diff(p[:, i]) > 0
                )
            )[0]
        )
        for i in range(0, w)
    ]
    median_number_of_widths = np.median(np.array([len(x) for x in raw_lengths]))
    valid_lengths = np.array(
        [np.array([*x, c]) for c, x in enumerate(raw_lengths) if len(x) == median_number_of_widths]
    )
    x = valid_lengths[:, 3]
    y = np.mean(valid_lengths[:, :3], axis=1)
    g = np.polyfit(x, y, 2)

    def f(t):
        return g[0]*t*t + g[1]*t + g[2]

    return f


def get_pixel_scale_as_function_of_x(p):
    """
    This is function that can be used to convert difference in stripes position
    between two subsequent images into value of arcseconds of shift between them
    :param p: prepared image with only full stripes
    :return: array of floats with length equal to image width
    """
    f = get_function_for_average_width_of_stripe(p)
    widths_array = f(np.arange(0, p.shape[1]))
    print(widths_array.shape)
    return widths_array / arcsec_per_strip


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


def get_mean_diff(s1, s2):
    initial = s2-s1
    # print(initial)
    m = np.average(initial)
    # print(f"First mean = {m}")
    counter = 0
    r = []
    for (a, b) in zip(s1, s2):
        d = b - a
        if abs(d) < 10:
            r.append(d)

    return np.average(r)



    # mask_1 = s1 > 0
    # mask_2 = s2 > 0
    # total_mask = 1.0*np.logical_and(mask_1, mask_2)
    # return total_mask*(s2-s1)
    return s2-s1


def measure_image_on_rect(f, rect: MyRectangle):
    print(f"Opening file: {f}")
    image_data = get_np_data_from_image_file(f)
    p = prepare_one_image(image_data)

    mean_slope = get_mean_slope(p)
    only_full_stripes = get_full_stripes(p, mean_slope)
    f = get_function_for_average_width_of_stripe(only_full_stripes)

    v = calculate_pixels_inside_rect(p, rect)
    print(v)
    plt.imshow(p)

    xy = rect.get_anchor_point()
    width, height = rect.get_dimensions()
    angle_deg = rect.get_angle_deg()
    rect_patch = mpatches.Rectangle(xy, width, height, angle=angle_deg, fill=False, color="purple", linewidth=2)
    plt.gca().add_patch(rect_patch)
    plt.show()

def get_last_files(d):
    """
    returns list of pairs (file, timestamp)
    """
    files = [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith("png")]
    files = [(p, os.path.getctime(p)) for p in files]
    return sorted(files, key=lambda x: x[1])


main_dir = filedialog.askdirectory(title="Open dir with images")
files = get_last_files(main_dir)
print(f"Opening {len(files)} files!")

pre = ImagePreparator()

first_file_name = files[0][0]
print(f"First file = {first_file_name}")
first_prepared = pre.prepare_one_image(get_np_data_from_image_file(first_file_name))
# mean_slope = get_mean_slope(first_prepared)
# print(f"Mean slope = {mean_slope}")
# only_full_stripes = get_full_stripes(first_prepared, mean_slope)
# print(f"Only full stripes = \n{only_full_stripes}")
# scale = get_pixel_scale_as_function_of_x(only_full_stripes)
# print(f"Scale = {scale}")
previous_time = files[0][1]
previous = get_stripes_starts_positions(first_prepared)

log_file = open("result.log", 'w', buffering=1)

filenames = [f[0] for f in files]

# ser = Serial(port="COM8", baudrate=115200, timeout=3)

while True:
    latest_state = get_last_files(main_dir)
    new_files = [f for f in latest_state if f not in filenames]
    if not new_files:
        print("Waiting 1s for new files...")
        sleep(1)
        continue

    print(f"Acquired new files: {new_files}")
    for f, t in new_files:
        p = pre.prepare_one_image(get_np_data_from_image_file(f))
        try:
            sp = get_stripes_starts_positions(p)
        except IndexError:
            continue
        except PermissionError:
            continue
        delta_t = t - previous_time
        previous_time = t
        # print(f"Positions = {sp}")
        # plt.imshow(p)
        # plt.show()
        result = get_mean_diff(sp, previous)
        print(f"dt = {delta_t}, dx = {result}")
        if abs(result) > 0:
            log_file.write(f"{delta_t}\t{result}\n")
        previous = sp
        try:
            os.remove(f)
        except e:
            print(f"Exception on removing file: {e}")
    files += new_files
    filenames = [f[0] for f in files]

log_file.close()
#
#
#
# def calculate_shift(a, b):
#     di = subtract_starts(a, b)
#     print(f"Shape of di = {di.shape}")
#     k = [np.mean(scale*di[:, i]) for i in range(0, di.shape[1])]
#     return np.array(k)
#
#
# d1 = calculate_shift(sp[0], sp[1])
# d2 = calculate_shift(sp[1], sp[2])
# d3 = calculate_shift(sp[0], sp[2])