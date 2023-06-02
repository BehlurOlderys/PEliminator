from .child_process import ChildProcessGUI
from package.utils.repeating_timer import RepeatingTimer
import logging
from tkinter import ttk
import tkinter as tk
import sys
import glob
import os
import time
import numpy as np
from PIL import Image
from astropy.io import fits


initial_test_dir = "C:\\Users\\Florek\\Desktop\\SharpCap Captures\\test_files"


def get_np_array_from_fits(filepath):
    hdul = fits.open(filepath)
    return hdul[0].data


def get_np_array_from_png(filepath):
    im_frame = Image.open(filepath)
    return np.array(im_frame)


def add_log(name):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    mainHandler = logging.FileHandler(name+".log")
    formatter = logging.Formatter('%(levelname)s: %(asctime)s %(filename)s %(funcName)s(%(lineno)d) -- %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    mainHandler.setFormatter(formatter)
    log.addHandler(mainHandler)

    console_formatter = logging.Formatter('%(levelname)s: %(asctime)s %(filename)s %(funcName)s(%(lineno)d) -- %(message)s',
                                  datefmt='%H:%M:%S')
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(console_formatter)
    log.addHandler(consoleHandler)
    return log


logger = add_log("guiding")


class PreProcessor:
    def process(self, data):
        image, timestamp = data
        logger.info(f"Starting processing image with timestamp = {timestamp}")
        return data


class PostProcessor:
    def process(self, data):
        return "Processing Finished"


class Guiding:
    def __init__(self, *processors):

        self._processors = processors

    def _reset_state(self):
        [p.reset() for p in self._processors]

    def reset(self):
        self._reset_state()

    def put_image(self, image, timestamp):
        next = (image, timestamp)
        for p in self._processors:
            next = p.process(next)

        logger.info(repr(next))


class DummyImageProvider:
    def __init__(self, sink):
        self._sink = sink

    def start(self):
        logger.info("DummyImageProvider starts")
        self._sink.put_image(None, None)

    def stop(self):
        logger.info("DummyImageProvider stops")


image_openers_map = {
    "fits": get_np_array_from_fits,
    "png": get_np_array_from_png
}


class DirectoryTimedImageProvider:
    def __init__(self, sink, path, delay_s, extension="fits"):
        self._files = glob.glob(os.path.join(path, f"*.{extension}"))
        self._delay_s = delay_s
        self._directory = path
        self._sink = sink
        self._image_opener = image_openers_map.get(extension, None)
        self._files = glob.glob(os.path.join(self._directory, f"*.{extension}"))
        logger.info(f"Init TimedFileImageProvider with {len(self._files)} files in {self._directory}!")
        self._timer = RepeatingTimer(interval_s=self._delay_s, function=self._put_new)
        self._gen = None

    def _put_new(self):
        logger.info("Trying to put new image...")
        try:
            image_path = next(self._gen)
        except StopIteration:
            logger.info("End of images, stopping Provider")
            self._timer.cancel()
            return

        try:
            np_image = self._image_opener(image_path)
        except Exception as e:
            logger.warning(f"Opening file {image_path} failed: {repr(e)}")
            return

        self._sink.put_image(np_image, time.time())
        short_name = image_path.split('\\')[-1]
        logger.info(f"...image {short_name} put successfully")

    def _provide_next_image(self):
        yield from self._files

    def start(self):
        logger.info("DirectoryTimedImageProvider starts")
        self._gen = self._provide_next_image()
        self._timer.start()

    def stop(self):
        self._timer.cancel()
        logger.info("DirectoryTimedImageProvider stopped")


class AdvancedGuidingProcess(ChildProcessGUI):
    def __init__(self, *args, **kwargs):
        super(AdvancedGuidingProcess, self).__init__(title="Advanced guiding control", *args, **kwargs)
        self._guiding = Guiding(PreProcessor(), PostProcessor())

        self._image_provider = DirectoryTimedImageProvider(self._guiding, initial_test_dir, 2, "fits")

        self._guiding_button = ttk.Button(self._main_frame, text="Start guiding",
                                      command=self._start_guiding, style="B.TButton")
        self._guiding_button.pack(side=tk.LEFT)

    def _start_guiding(self):
        self._guiding_button.configure(text="Stop guiding",
                                       command=self._stop_guiding,
                                       style="SunkableButton.TButton")
        self._image_provider.start()

    def _stop_guiding(self):
        self._guiding_button.configure(text="Start guiding",
                                       command=self._start_guiding,
                                       style="B.TButton")
        self._image_provider.stop()

