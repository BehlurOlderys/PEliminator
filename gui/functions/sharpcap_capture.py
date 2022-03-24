import os
from datetime import datetime
from common.utils import is_acceptable_file


def get_latest_sharpcap_capture_dir():
    return "C:\\Users\\Florek\\Desktop\\SharpCap Captures"


def get_latest_sharpcap_image():
    sharpcap_dir = get_latest_sharpcap_capture_dir()
    dirs_with_date = [(datetime.strptime(s, '%Y-%m-%d'), s) for s in os.listdir(sharpcap_dir) if s.startswith('20')]
    newest_dir = min(dirs_with_date, key=lambda x: x[0])
    capture_dir = os.path.join(sharpcap_dir, newest_dir[1], 'Capture')
    dirs_with_time = [(datetime.strptime(s, '%H_%M_%S'), s) for s in os.listdir(capture_dir)]
    latest_hour = min(dirs_with_time, key=lambda x: x[0])
    newest_images_dir = os.path.join(capture_dir, latest_hour[1])
    images = [(os.path.getctime(os.path.join(newest_images_dir, f)), f) for f in os.listdir(newest_images_dir) if is_acceptable_file(f)]
    newest_image = os.path.join(newest_images_dir, min(images, key=lambda x: x[0])[1])
    return newest_image
