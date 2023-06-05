from .child_process import ChildProcessGUI
from package.widgets.labeled_combo import LabeledCombo
from package.utils.guiding.directory_timed_image_provider import DirectoryTimedImageProvider
from package.utils.guiding.guiding_options import GuidingOptions
from package.utils.guiding.delta_calculator import DeltaXYCalculator
from package.utils.guiding.bw_transformations import NormalizedBWChanger
from package.utils.guiding.time_watcher import TimeWatcher
from package.utils.guiding.data_printer import DataPrinter
from package.utils.guiding.image_saver import ImageSaver
from package.utils.guiding.guiding_data import GuidingData
from package.utils.guiding.data_processor import PreProcessor, PostProcessor
from package.utils.guiding.star_center_calculator import StarCenterCalculator
from package.utils.guiding.image_display import ImageDisplay
from package.utils.guiding.fragment_extractor import FragmentExtractor
from package.utils.guiding.rectangle_mover import RectangleMover
from package.widgets.simple_canvas import SimpleCanvasRect
from tkinter import ttk
import tkinter as tk
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
usb_camera_serial_prevalue = "COM1" # TODO very dummy

color_prevalue = "COLOR"
imtype_prevalue = "RAW16"
pattern_prevalue = "GBRG"
mover_history_size_prevalue = 5


class Guiding:
    def __init__(self, *processors):

        self._processors = processors

    def _reset_state(self):
        [p.reset() for p in self._processors]

    def reset(self):
        log.debug("Resetting all guiding calculators!")
        self._reset_state()

    def put_image(self, data: GuidingData):
        next_data = data
        for p in self._processors:
            next_data = p.process(next_data)

        log.info(f"Guiding result: {next_data}")


image_providers_map = {
    "Simulation": DirectoryTimedImageProvider
}


class AdvancedGuidingProcess(ChildProcessGUI):
    def __init__(self, *args, **kwargs):
        super(AdvancedGuidingProcess, self).__init__(title="Advanced guiding control", *args, **kwargs)

        self._buttons_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        self._buttons_frame.pack(side=tk.LEFT)

        self._image_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        self._image_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self._controls_frame = ttk.Frame(self._buttons_frame, style="B.TFrame")
        self._controls_frame.pack(side=tk.TOP)

        self._capture_button = ttk.Button(self._controls_frame, text="Start capturing",
                                          command=self._start_capturing, style="B.TButton")
        self._capture_button.pack(side=tk.LEFT)

        self._calculations_button = ttk.Button(self._controls_frame, text="Start calculations",
                                          command=self._start_calculations, style="B.TButton")
        self._calculations_button.pack(side=tk.LEFT)

        self._corrections_button = ttk.Button(self._controls_frame, text="Start corrections",
                                          command=self._start_calculations, style="B.TButton")
        self._corrections_button.pack(side=tk.LEFT)

        ttk.Separator(self._buttons_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)

        self._guiding_frame = ttk.Frame(self._buttons_frame, style="B.TFrame")
        self._guiding_frame.pack(side=tk.TOP)

        self._guiding_options = GuidingOptions(self._guiding_frame)

        ttk.Separator(self._buttons_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)

        self._input_frame = ttk.Frame(self._buttons_frame, style="B.TFrame")
        self._input_frame.pack(side=tk.TOP)

        self._color_combo = LabeledCombo("Color/Mono:", ["COLOR", "MONO"], prevalue=color_prevalue, frame=self._input_frame)
        self._color_combo.pack(side=tk.TOP)

        self._imtype_combo = LabeledCombo("Image type:", ["RAW16", "RAW8", "RGB24"], prevalue=imtype_prevalue, frame=self._input_frame)
        self._imtype_combo.pack(side=tk.TOP)

        self._pattern_combo = LabeledCombo("Bayer mask:", ["GBRG", "NONE"], prevalue=pattern_prevalue, frame=self._input_frame)
        self._pattern_combo.pack(side=tk.TOP)

        self._image_canvas = SimpleCanvasRect(frame=self._image_frame,
                                          initial_image_path="last.png")
        self._image_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # provider_factory = image_providers_map[self._guiding_options.get_guiding_type()]
        #
        # self._image_provider = provider_factory(Guiding(
        #     PreProcessor(),
        #     TimeWatcher(),
        #     NormalizedBWChanger(self._color_combo.get_value(),
        #                         self._imtype_combo.get_value(),
        #                         self._pattern_combo.get_value()),
        #     ImageDisplay(self._image_canvas),
        #     ImageSaver("image", "test", save_path=default_save_path),
        #     PostProcessor()
        # ), self._guiding_options)

    def _killme(self):
        self._stop_corrections()
        self._stop_calculations()
        self._stop_capturing()
        super(AdvancedGuidingProcess, self)._killme()

    def _start_capturing(self):
        self._capture_button.configure(text="Stop capturing",
                                           command=self._stop_capturing,
                                           style="SunkableButton.TButton")
        provider_factory = image_providers_map[self._guiding_options.get_guiding_type()]
        self._image_provider = provider_factory(Guiding(
            PreProcessor(),
            TimeWatcher(),
            NormalizedBWChanger(self._color_combo.get_value(),
                                self._imtype_combo.get_value(),
                                self._pattern_combo.get_value()),
            ImageDisplay(self._image_canvas),
            FragmentExtractor(self._image_canvas),
            StarCenterCalculator(),
            DataPrinter("calculated_center"),
            DeltaXYCalculator("calculated_center", "position_delta"),
            DataPrinter("position_delta"),
            RectangleMover(self._image_canvas, history_size=mover_history_size_prevalue),
            # TODO:
            # AbsoluteShiftCalculator
            # MountMover
            ImageSaver("fragment", "test", save_path=fragments_save_path),
            ImageSaver("image", "test", save_path=default_save_path),
            PostProcessor()
        ), self._guiding_options)
        self._image_provider.start()

    def _stop_capturing(self):
        self._capture_button.configure(text="Start capturing",
                                       command=self._start_capturing,
                                       style="B.TButton")
        self._image_provider.stop()

    def _start_calculations(self):
        self._calculations_button.configure(text="Stop calculations",
                                       command=self._stop_calculations,
                                       style="SunkableButton.TButton")
        self._image_canvas.enable_rect_info()

    def _stop_calculations(self):
        self._calculations_button.configure(text="Start calculations",
                                       command=self._start_calculations,
                                       style="B.TButton")
        self._image_canvas.disable_rect_info()
        self._image_provider.reset_calculation()

    def _start_corrections(self):
        self._corrections_button.configure(text="Stop corrections",
                                           command=self._stop_corrections,
                                           style="SunkableButton.TButton")

    def _stop_corrections(self):
        self._corrections_button.configure(text="Start corrections",
                                       command=self._start_corrections,
                                       style="B.TButton")



