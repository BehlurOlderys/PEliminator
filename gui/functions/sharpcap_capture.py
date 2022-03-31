import os
from datetime import datetime
from functions.utils import is_acceptable_file


def get_latest_sharpcap_capture_dir():
    return "C:\\Users\\Florek\\Desktop\\SharpCap Captures"


def get_latest_sharpcap_images_dir():
    sharpcap_dir = get_latest_sharpcap_capture_dir()
    dirs_with_date = [(datetime.strptime(s, '%Y-%m-%d'), s) for s in os.listdir(sharpcap_dir) if s.startswith('20')]
    newest_dir = max(dirs_with_date, key=lambda x: x[0])
    capture_dir = os.path.join(sharpcap_dir, newest_dir[1], 'Capture')
    dirs_with_time = [(datetime.strptime(s, '%H_%M_%S'), s) for s in os.listdir(capture_dir)]
    latest_hour = max(dirs_with_time, key=lambda x: x[0])
    return os.path.join(capture_dir, latest_hour[1])


def get_latest_sharpcap_image():
    newest_images_dir = get_latest_sharpcap_images_dir()
    images = [(os.path.getctime(os.path.join(newest_images_dir, f)), f) for f in os.listdir(newest_images_dir) if is_acceptable_file(f)]
    latest_image = max(images, key=lambda x: x[0])
    newest_image_path = os.path.join(newest_images_dir, latest_image[1])
    return newest_image_path


def get_second_latest_sharpcap_image():
    newest_images_dir = get_latest_sharpcap_images_dir()
    images = [(os.path.getctime(os.path.join(newest_images_dir, f)), f) for f in os.listdir(newest_images_dir) if is_acceptable_file(f)]
    latest_image = max(images, key=lambda x: x[0])
    images.remove(latest_image)
    second_latest_image = max(images, key=lambda x: x[0])
    second_latest_image_path = os.path.join(newest_images_dir, second_latest_image[1])
    return second_latest_image_path
