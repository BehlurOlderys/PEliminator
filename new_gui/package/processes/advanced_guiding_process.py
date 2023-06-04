import numpy as np

from .child_process import ChildProcessGUI
from package.utils.repeating_timer import RepeatingTimer
from package.widgets.labeled_combo import LabeledCombo
from package.widgets.dir_chooser import DirChooser
from package.utils.guiding.bw_transformations import NormalizedBWChanger
from package.utils.guiding.time_watcher import TimeWatcher
from package.utils.guiding.image_saver import ImageSaver
from package.utils.guiding.guiding_data import GuidingData
from package.utils.guiding.data_processor import PreProcessor, PostProcessor
from package.utils.guiding.image_display import ImageDisplay
from package.utils.guiding.fragment_extractor import FragmentExtractor
from package.widgets.simple_canvas import SimpleCanvasRect
from tkinter import ttk
import tkinter as tk
import glob
import os
import time
from PIL import Image
from astropy.io import fits
import logging
import sys


log = logging.getLogger("guiding")
log.setLevel(logging.DEBUG)
main_handler = logging.FileHandler("guiding.log")
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

initial_test_dir = "C:\\Users\\Florek\\Desktop\\SharpCap Captures\\test_files"
default_save_path = "C:\\Users\\Florek\\Desktop\\workspace\\PEliminator\\new_gui\\saved_images"
fragments_save_path = "C:\\Users\\Florek\\Desktop\\workspace\\PEliminator\\new_gui\\fragments"

guiding_type_prevalue = "Simulation"
simulation_file_type_prevalue = "fits"

color_prevalue = "COLOR"
imtype_prevalue = "RAW16"
pattern_prevalue = "GBRG"


def get_np_array_from_fits(filepath):
    hdul = fits.open(filepath)
    image_data = hdul[0].data
    return image_data


def get_np_array_from_png(filepath):
    im_frame = Image.open(filepath)
    return np.array(im_frame)



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

        log.info(f"Guiding result: {next_data}")


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
        log.info(f"Init TimedFileImageProvider with {len(self._files)} files in {self._directory}!")
        self._timer = RepeatingTimer(interval_s=self._delay_s, function=self._put_new)
        self._gen = None
        self._busy = False

    def _put_new(self):
        self._busy = True
        log.debug("Trying to put new image...")
        try:
            image_path = next(self._gen)
        except StopIteration:
            log.info("End of images, stopping Provider")
            self._timer.cancel()
            return

        try:
            np_image = self._image_opener(image_path)

        except Exception as e:
            log.warning(f"Opening file {image_path} failed: {repr(e)}")
            return
        short_name = image_path.split('\\')[-1]

        self._sink.put_image(GuidingData(np_image, time.time(), short_name))
        self._busy = False
        log.info(f"...image {short_name} put successfully")

    def _provide_next_image(self):
        yield from self._files

    def start(self):
        log.debug("DirectoryTimedImageProvider starts")
        self._gen = self._provide_next_image()
        self._timer.start()

    def stop(self):
        self._timer.cancel()
        for i in range(0, 10):
            if self._busy:
                time.sleep(0.2)
            else:
                break
        log.debug("DirectoryTimedImageProvider stopped")


image_providers_map = {
    "Simulation": DirectoryTimedImageProvider
}


def setup_simulation_options_frame(frame):
    guiding_combo = LabeledCombo("Guiding type",
                                 ["Simulation"],
                                 prevalue=guiding_type_prevalue,
                                 frame=frame)
    guiding_combo.pack(side=tk.TOP)
    file_type_combo = LabeledCombo("Input file type",
                                 ["fits", "png", "tiff"],
                                 prevalue=simulation_file_type_prevalue,
                                 frame=frame).pack(side=tk.TOP)
    path_chooser = DirChooser(frame=frame,
                              initial_dir=initial_test_dir).pack(side=tk.TOP)

    return guiding_combo, file_type_combo, path_chooser


class AdvancedGuidingProcess(ChildProcessGUI):
    def __init__(self, *args, **kwargs):
        super(AdvancedGuidingProcess, self).__init__(title="Advanced guiding control", *args, **kwargs)

        self._buttons_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        self._buttons_frame.pack(side=tk.LEFT)

        self._image_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        self._image_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self._controls_frame = ttk.Frame(self._buttons_frame, style="B.TFrame")
        self._controls_frame.pack(side=tk.TOP)
        self._guiding_button = ttk.Button(self._controls_frame, text="Start guiding",
                                          command=self._start_guiding, style="B.TButton")
        self._guiding_button.pack(side=tk.LEFT)

        ttk.Separator(self._main_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)

        self._guiding_frame = ttk.Frame(self._buttons_frame, style="B.TFrame")
        self._guiding_frame.pack(side=tk.TOP)

        self._simulation_options_widgets = setup_simulation_options_frame(self._guiding_frame)

        ttk.Separator(self._main_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)

        self._input_frame = ttk.Frame(self._buttons_frame, style="B.TFrame")
        self._input_frame.pack(side=tk.TOP)

        self._color_combo = LabeledCombo("Color/Mono:", ["COLOR", "MONO"], prevalue=color_prevalue, frame=self._input_frame)
        self._color_combo.pack(side=tk.TOP)

        self._imtype_combo = LabeledCombo("Image type:", ["RAW16", "RAW8", "RGB24"], prevalue=imtype_prevalue, frame=self._input_frame)
        self._imtype_combo.pack(side=tk.TOP)

        self._pattern_combo = LabeledCombo("Bayer mask:", ["GBRG"], prevalue=pattern_prevalue, frame=self._input_frame)
        self._pattern_combo.pack(side=tk.TOP)

        self._image_canvas = SimpleCanvasRect(frame=self._image_frame,
                                          initial_image_path="last.png")
        self._image_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)


        provider_factory = image_providers_map[guiding_type_prevalue]

        self._image_provider = provider_factory(Guiding(
            PreProcessor(),
            TimeWatcher(),
            NormalizedBWChanger(self._color_combo.get_value(),
                                self._imtype_combo.get_value(),
                                self._pattern_combo.get_value()),
            ImageDisplay(self._image_canvas),
            ImageSaver("image", "test", save_path=default_save_path),
            PostProcessor()
        ), initial_test_dir, 2, "fits")

    def _killme(self):
        self._stop_guiding()
        super(AdvancedGuidingProcess, self)._killme()

    def _start_guiding(self):
        self._guiding_button.configure(text="Stop guiding",
                                       command=self._stop_guiding,
                                       style="SunkableButton.TButton")

        provider_factory = image_providers_map[guiding_type_prevalue]
        self._image_provider = provider_factory(Guiding(
            PreProcessor(),
            TimeWatcher(),
            NormalizedBWChanger(self._color_combo.get_value(),
                                self._imtype_combo.get_value(),
                                self._pattern_combo.get_value()),
            ImageDisplay(self._image_canvas),
            FragmentExtractor(self._image_canvas),
            ImageSaver("fragment", "test", save_path=fragments_save_path),
            ImageSaver("image", "test", save_path=default_save_path),
            PostProcessor()
        ), initial_test_dir, 2, "fits")
        self._image_provider.start()

    def _stop_guiding(self):
        self._guiding_button.configure(text="Start guiding",
                                       command=self._start_guiding,
                                       style="B.TButton")
        self._image_provider.stop()
