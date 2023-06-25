import math

from .child_process import ChildProcessGUI
from package.widgets.labeled_combo import LabeledCombo
from package.widgets.labeled_input import LabeledInput
from package.widgets.arrows_controls import ArrowsControls
from package.utils.guiding.directory_timed_image_provider import DirectoryTimedImageProvider
from package.utils.guiding.usb_camera_image_provider import USBCameraImageProvider
from package.utils.guiding.guiding_options import GuidingOptions
from package.utils.guiding.delta_calculator import DeltaXYCalculator
from package.utils.guiding.bw_transformations import NormalizedBWChanger
from package.utils.guiding.movement_watchdog import MovementWatchdog
from package.utils.guiding.time_watcher import TimeWatcher
from package.utils.guiding.data_printer import DataPrinter
from package.utils.guiding.image_saver import ImageSaver
from package.utils.guiding.guiding_data import GuidingData
from package.utils.guiding.data_processor import DataProcessor, PreProcessor, PostProcessor
from package.utils.guiding.star_center_calculator import StarCenterCalculator
from package.utils.guiding.image_display import ImageDisplay
from package.utils.guiding.fragment_extractor import FragmentExtractor
from package.utils.guiding.rectangle_mover import RectangleMover
from package.utils.serial_utils import get_available_com_ports, SerialWriter
from package.widgets.simple_canvas import SimpleCanvasRect
from tkinter import ttk
import numpy as np
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
usb_camera_serial_prevalue = "COM1"  # TODO very dummy
mount_mover_type_prevalue = "Dummy"

color_prevalue = "COLOR"
pattern_prevalue = "GBRG"
mover_history_size_prevalue = 5
ra_threshold_as = 2.0
dec_threshold_as = 2.0

orientations_normal = {
    "RA <-left, DEC up": 0,
    "RA up, DEC right->": 90,
    "RA right->, DEC down": 180,
    "RA down, DEC <-left": 270
}

orientations_flipped = {
    "RA <-left, DEC down": 0,
    "RA up, DEC <-left": 90,
    "RA right->, DEC up": 180,
    "RA down, DEC right->": 270
}


class OrientationMapper(DataProcessor):
    """
    using clockwise rotation = change signs in rotation matrix
    orientation = normal 0 deg:
    error x > 0 -> need to move RA-
    error x < 0 -> need to move RA+
    error y > 0 -> need to move DEC-
    error y < 0 -> need to move DEC+

    error = (ex, ey)
    matrix =  | -1  0 |
              |  0  -1 |

    movement = (-ra, -dec)

    orientation = normal 90 deg:
    error x > 0 -> need to move DEC+
    error x < 0 -> need to move DEC-
    error y < 0 -> need to move RA+
    error y > 0 -> need to move RA-

    error = (ex, ey)
    matrix = |  0  1 |
             | -1  0 |

             |  0  1 |     | ex |   | -ey |
             | -1  0 |  *  | ey | = | ex  |
    movement = (dec, -ra)
    """

    def __init__(self, degrees_getter, flip_getter=lambda: False):
        super(OrientationMapper, self).__init__(name="Orientation mapper")
        self._degrees_getter = degrees_getter
        self._flip_getter = flip_getter

    def _process_impl(self, data: GuidingData):
        if data.position_delta is None:
            return data

        theta = (self._degrees_getter() / 180.) * np.pi
        self._matrix = np.array([[-np.cos(theta), np.sin(theta)],
                                 [-np.sin(theta), -np.cos(theta)]])

        input = np.array(data.position_delta)

        log.debug(f"Input shape = {input.shape}")
        log.debug(f"Input = {input}")

        if self._flip_getter():
            input[1] = -input[1]

        movement = np.dot(self._matrix, input)
        log.debug(f"movement shape = {movement.shape}")
        log.debug(f"movement = {movement}")
        data.movement_px = movement
        return data


class MountMover(DataProcessor):
    def __init__(self, name):
        super(MountMover, self).__init__(name=name)
        self._enabled = True

    def disable(self):
        self._enabled = False

    def enable(self):
        self._enabled = True

    def _process_impl(self, data: GuidingData):
        if data.movement_as is None:
            return data

        if not self._enabled:
            log.warning("Mover is disabled!")
            return data

        arcseconds = data.movement_as
        log.debug(f"Got arcseconds: {data.movement_as}")

        if abs(arcseconds[0]) > ra_threshold_as:
            self._move_ra_impl(arcseconds[0])
        if abs(arcseconds[1]) > dec_threshold_as:
            self._move_dec_impl(arcseconds[1])
        return data

    def move(self, axis, amount_as):
        if axis == "RA":
            log.info(f"Moving RA by {amount_as}")
            self._move_ra_impl(amount_as)
        if axis == "DEC":
            log.info(f"Moving DEC by {amount_as}")
            self._move_dec_impl(amount_as)

    def _move_ra_impl(self, arcseconds):
        log.error("I hope not to see it...")

    def _move_dec_impl(self, arcseconds):
        log.error("I hope not to see it...")


class DummyMountMover(MountMover):
    def __init__(self):
        super(DummyMountMover, self).__init__(name="DummyMountMover")

    def _move_ra_impl(self, arcseconds):
        log.info(f"Moving RA by {arcseconds}")

    def _move_dec_impl(self, arcseconds):
        log.info(f"Moving DEC by {arcseconds}")


class MegaMountMover(MountMover):
    def __init__(self, serial=None):
        super(MegaMountMover, self).__init__(name="MegaMountSerialMover")
        self._serial = serial

    def set_serial(self, serial):
        self._serial = serial

    def _move_ra_impl(self, arcseconds):
        command = f"MOVE_RA_AS {int(arcseconds)}"
        log.debug(f"Issuing a command: {command}")
        self._serial.send_line(command)

    def _move_dec_impl(self, arcseconds):
        command = f"MOVE_DEC_AS {int(arcseconds)}"
        log.debug(f"Issuing a command: {command}")
        self._serial.send_line(command)


mount_movers_map = {
    "Dummy": DummyMountMover,
    "USB": MegaMountMover
}


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
    "Simulation": DirectoryTimedImageProvider,
    "USB Camera": USBCameraImageProvider
}


class MovementArcsecondsCalculator(DataProcessor):
    def __init__(self, focal_getter, pixel_getter, dec_getter):
        super(MovementArcsecondsCalculator, self).__init__(name="MovementArcsecondsCalculator")
        self._focal_getter = focal_getter
        self._pixel_getter = pixel_getter
        self._dec_getter = dec_getter

    def _process_impl(self, data):
        if data.movement_px is None:
            return data
        scale = 206.265 * self._pixel_getter() / self._focal_getter()
        arcseconds = scale * data.movement_px
        theta = (self._dec_getter() / 180.) * np.pi
        log.debug(f"Scale = {scale}. Input before scaling = ({data.movement_px}) with dec = {self._dec_getter()}")
        log.debug(f"Output after scaling = ({arcseconds})")
        arcseconds[0] = arcseconds[0] / np.cos(theta)
        log.debug(f"Output after dec correction = ({arcseconds})")
        data.movement_as = arcseconds
        return data


class AdvancedGuidingProcess(ChildProcessGUI):
    def __init__(self, *args, **kwargs):
        super(AdvancedGuidingProcess, self).__init__(title="Advanced guiding control", *args, **kwargs)

        self._image_provider = None

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

        self._color_combo = LabeledCombo("Color/Mono:", ["COLOR", "MONO"], prevalue=color_prevalue,
                                         frame=self._input_frame)
        self._color_combo.pack(side=tk.TOP)

        self._pattern_combo = LabeledCombo("Bayer mask:", ["GBRG", "NONE"], prevalue=pattern_prevalue,
                                           frame=self._input_frame)
        self._pattern_combo.pack(side=tk.TOP)

        ttk.Separator(self._buttons_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)

        self._mount_frame = ttk.Frame(self._buttons_frame, style="B.TFrame")
        self._mount_frame.pack(side=tk.TOP)

        orient_values = list(orientations_normal.keys())
        self._orientation_combo = LabeledCombo("Orientation:", orient_values, prevalue=orient_values[0],
                                               frame=self._mount_frame)
        self._orientation_combo.pack(side=tk.TOP)

        self._mirror_combo = LabeledCombo("Mirror flip:", ["False", "True"],
                                          prevalue="False", event_handler=self._switch_orientation,
                                          frame=self._mount_frame)
        self._mirror_combo.pack(side=tk.TOP)

        self._focal_spin = LabeledInput("Focal length [mm]:", 200, 0, 9999, width=4,
                                        frame=self._mount_frame).pack(side=tk.TOP)
        self._pixel_spin = LabeledInput("Pixel size [um]:", 2.9, 1, 50, width=3, increment=0.1,
                                        frame=self._mount_frame).pack(side=tk.TOP)
        self._dec_spin = LabeledInput("Target DEC [deg]:", 30, -80, 80, width=3,
                                      frame=self._mount_frame).pack(side=tk.TOP)

        ttk.Separator(self._buttons_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)
        self._mover_frame = ttk.Frame(self._buttons_frame, style="B.TFrame")
        self._mover_frame.pack(side=tk.TOP)
        self._mover_combo = LabeledCombo("Mount type:", ["Dummy", "USB"], event_handler=self._change_mover,
                                         prevalue=mount_mover_type_prevalue, frame=self._mover_frame).pack(side=tk.TOP)
        self._mover_widgets = {}
        ttk.Separator(self._buttons_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)

        self._mover = mount_movers_map[mount_mover_type_prevalue]()
        self._arrows = ArrowsControls(descriptions={
            "UP": "DEC+", "DOWN": "DEC-", "LEFT": "RA+", "RIGHT": "RA-"
        }, event_handlers={
            "UP": lambda: self._mover.move("DEC", 100),
            "DOWN": lambda: self._mover.move("DEC", -100),
            "LEFT": lambda: self._mover.move("RA", 100),
            "RIGHT": lambda: self._mover.move("RA", -100),
        }, frame=self._buttons_frame).pack(side=tk.TOP)

        # RIGHT SIDE OF THE WINDOW:
        self._image_canvas = SimpleCanvasRect(frame=self._image_frame,
                                              initial_image_path="last.png")
        self._image_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def _change_serial(self, event):
        port = event.widget.get()
        if port == '<NONE>':
            return
        new_serial = SerialWriter(port)
        self._mover.set_serial(new_serial)

    def _change_mover(self, event):
        value = event.widget.get()
        if value == "USB":
            available_ports = get_available_com_ports()
            self._mover = MegaMountMover(SerialWriter(available_ports[0]))
            serial_chooser = LabeledCombo(frame=self._mover_frame, desc="Serial port: ",
                                          event_handler=self._change_serial,
                                          values=available_ports, prevalue=available_ports[0])
            serial_chooser.pack(side=tk.TOP)
            self._mover_widgets["serial_chooser"] = serial_chooser
        elif value == "Dummy":
            for w in self._mover_widgets.values():
                w.destroy()

    def _killme(self):
        self._stop_corrections()
        self._stop_calculations()
        self._stop_capturing()
        super(AdvancedGuidingProcess, self)._killme()

    def _get_orientation_angle(self):
        key = self._orientation_combo.get_value()
        angle_deg = orientations_normal[key]
        return angle_deg

    def _get_flip_value(self):
        str_value = self._mirror_combo.get_value()
        returned = True if str_value == "True" else False
        log.debug(f"Str value in mirror = {str_value}, returned = {returned}")
        return returned

    def _get_focal_length(self):
        return float(self._focal_spin.get_value())

    def _get_pixel(self):
        return float(self._pixel_spin.get_value())

    def _get_dec(self):
        return float(self._dec_spin.get_value())

    def _switch_orientation(self, event):
        if "True" == event.widget.get():
            new_list = list(orientations_flipped.keys())
        else:
            new_list = list(orientations_normal.keys())

        self._orientation_combo.set_list(new_list, new_list[0])

    def _start_capturing(self):
        self._capture_button.configure(text="Stop capturing",
                                       command=self._stop_capturing,
                                       style="SunkableButton.TButton")
        provider_factory = image_providers_map[self._guiding_options.get_guiding_type()]
        self._image_provider = provider_factory(Guiding(
            PreProcessor(),
            TimeWatcher(),
            NormalizedBWChanger(self._color_combo.get_value(),
                                self._guiding_options.get_image_type(),
                                self._pattern_combo.get_value()),
            ImageDisplay(self._image_canvas),
            FragmentExtractor(self._image_canvas),
            StarCenterCalculator(),
            DataPrinter("calculated_center"),
            DeltaXYCalculator("calculated_center", "position_delta"),
            DataPrinter("position_delta"),
            RectangleMover(self._image_canvas, history_size=mover_history_size_prevalue),
            OrientationMapper(self._get_orientation_angle, self._get_flip_value),
            MovementArcsecondsCalculator(self._get_focal_length, self._get_pixel, self._get_dec),
            MovementWatchdog(self._mover),
            self._mover,
            ImageSaver("fragment", "test", save_path=fragments_save_path),
            ImageSaver("image", "test", save_path=default_save_path),
            PostProcessor()
        ), self._guiding_options)
        self._image_provider.start()

    def _stop_capturing(self):
        self._capture_button.configure(text="Start capturing",
                                       command=self._start_capturing,
                                       style="B.TButton")
        if self._image_provider is not None:
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
        if self._image_provider is not None:
            self._image_provider.reset_calculation()

    def _start_corrections(self):
        self._corrections_button.configure(text="Stop corrections",
                                           command=self._stop_corrections,
                                           style="SunkableButton.TButton")

    def _stop_corrections(self):
        self._corrections_button.configure(text="Start corrections",
                                           command=self._start_corrections,
                                           style="B.TButton")
