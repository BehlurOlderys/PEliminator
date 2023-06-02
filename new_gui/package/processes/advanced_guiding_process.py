import numpy as np

from .child_process import ChildProcessGUI
from package.utils.repeating_timer import RepeatingTimer
import logging
from tkinter import ttk
import tkinter as tk
import sys
import glob
import os
import colour_demosaicing
import time
from PIL import Image
from astropy.io import fits


initial_test_dir = "C:\\Users\\Florek\\Desktop\\SharpCap Captures\\test_files"
default_save_path = "C:\\Users\\Florek\\Desktop\\workspace\\PEliminator\\new_gui\\saved_images"


def get_mono_normalized_from_color_raw_gbrg(data):
    st = time.time()
    float01_data = data.astype(np.float32) / 65535
    result = colour_demosaicing.demosaicing_CFA_Bayer_bilinear(float01_data, pattern="GBRG")
    bw_result = rgb2gray(result)
    en = time.time()
    logger.debug(f"RAW transform took {1000*(en-st)}ms")
    return bw_result


raw_transforming_map = {
    "COLOR_RAW16_GBRG": get_mono_normalized_from_color_raw_gbrg
}


def rgb2gray(rgb):
    return np.dot(rgb[..., :3], [0.25, 0.5, 0.25])


def get_np_array_from_fits(filepath):
    hdul = fits.open(filepath)
    image_data = hdul[0].data
    return image_data


def get_np_array_from_png(filepath):
    im_frame = Image.open(filepath)
    return np.array(im_frame)


def add_log(name):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    main_handler = logging.FileHandler(name + ".log")
    formatter = logging.Formatter('%(levelname)s: %(asctime)s %(filename)s %(funcName)s(%(lineno)d) -- %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    main_handler.setFormatter(formatter)
    log.addHandler(main_handler)

    console_formatter = logging.Formatter(
        '%(levelname)s: %(asctime)s %(filename)s %(funcName)s(%(lineno)d) -- %(message)s',
        datefmt='%H:%M:%S')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    log.addHandler(console_handler)
    return log


logger = add_log("guiding")


class GuidingData:
    def __init__(self, im, t, shname):
        self.image = im
        self.timestamp = t
        self.shortname = shname
        self.start = None
        self.message = "OK"
        self.error = False

    def __repr__(self):
        return self.message


class DataProcessor:
    def __init__(self, name):
        self._name = name

    def process(self, data):
        if data is None:
            logger.error(f"Processor {self._name} received None as data, returning...")
            return None
        if data.error:
            return data
        logger.debug(f"Processor {self._name} starts processing...")
        return self._process_impl(data)

    def _process_impl(self, data):
        return data


class PreProcessor(DataProcessor):
    def __init__(self):
        super(PreProcessor, self).__init__("PreProcessor")

    def _process_impl(self, data: GuidingData):
        data.start = time.time()
        logger.debug(f"Starting processing image {data.shortname}")
        return data


class TimeWatcher(DataProcessor):
    def __init__(self):
        super(TimeWatcher, self).__init__("Time watcher")
        self._last = time.time()

    def _process_impl(self, data: GuidingData):
        right_now = time.time()
        diff = right_now - self._last
        self._last = right_now
        logger.debug(f"Time elapsed since last data feed = {diff}")
        return data


class PostProcessor(DataProcessor):
    def __init__(self):
        super(PostProcessor, self).__init__("PostProcessor")

    def _process_impl(self, data: GuidingData):
        elapsed = time.time() - data.start
        logger.debug(f"Processing image {data.shortname} finished. It took {elapsed*1000}ms")
        return data


class Guiding:
    def __init__(self, *processors):

        self._processors = processors

    def _reset_state(self):
        [p.reset() for p in self._processors]

    def reset(self):
        self._reset_state()

    def put_image(self, data: GuidingData):
        next_data = data
        for p in self._processors:
            next_data = p.process(next_data)

        logger.info(f"Guiding result: {next_data}")


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


class NormalizedBWChanger(DataProcessor):
    def __init__(self, color: str, imtype: str, pattern: str = ""):
        super(NormalizedBWChanger, self).__init__("NormalizedBWChanger")
        designation = '_'.join([color, imtype, pattern])
        self._opening_mode = raw_transforming_map[designation]

    def _process_impl(self, data):
        data.image = self._opening_mode(data.image)
        return data


class ImageSaver(DataProcessor):
    def __init__(self, prefix, save_path=default_save_path):
        super(ImageSaver, self).__init__("ImageSaver")
        self._prefix = prefix
        self._save_path = save_path
        if not os.path.isdir(self._save_path):
            try:
                os.mkdir(self._save_path)
            except Exception as e:
                logger.error(f"Could not create directory {self._save_path}: {repr(e)}")

    def _process_impl(self, data: GuidingData):
        im = Image.fromarray((256*data.image).astype('uint8'))
        no_ext = data.shortname.split(".")[0]
        image_new_path = os.path.join(self._save_path, self._prefix + "_" + no_ext + ".jpg")

        try:
            im.save(image_new_path)
        except Exception as e:
            logger.error(f"Could not save file {image_new_path}: {repr(e)}")
            return None
        logger.info(f"Saved image as {image_new_path}")
        return data


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
        logger.debug("Trying to put new image...")
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
        short_name = image_path.split('\\')[-1]

        self._sink.put_image(GuidingData(np_image, time.time(), short_name))

        logger.info(f"...image {short_name} put successfully")

    def _provide_next_image(self):
        yield from self._files

    def start(self):
        logger.debug("DirectoryTimedImageProvider starts")
        self._gen = self._provide_next_image()
        self._timer.start()

    def stop(self):
        self._timer.cancel()
        logger.debug("DirectoryTimedImageProvider stopped")


class AdvancedGuidingProcess(ChildProcessGUI):
    def __init__(self, *args, **kwargs):
        super(AdvancedGuidingProcess, self).__init__(title="Advanced guiding control", *args, **kwargs)
        self._guiding = Guiding(
            PreProcessor(),
            TimeWatcher(),
            NormalizedBWChanger("COLOR", "RAW16", "GBRG"),
            ImageSaver("test"),
            PostProcessor()
        )

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
