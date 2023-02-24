import multiprocessing

from .child_process import ChildProcessGUI
from package.utils.zwo_asi_camera_grabber import ASICamera
from tkinter import ttk
import tkinter as tk
import time

from package.widgets.camera_chooser import CameraChooser
from package.widgets.value_controller import ValueController
from package.widgets.image_canvas import PhotoImage
from package.widgets.labeled_input import LabeledInput
from package.processes.capturing_process import capturing

NO_IMAGE_FILE = "data/no_image.png"


def return_kwargs(**kwargs):
    return kwargs


class AcquisitionProcessGUI(ChildProcessGUI):
    def __init__(self, *args, **kwargs):
        super(AcquisitionProcessGUI, self).__init__(title="Acquisition", *args, **kwargs)
        ASICamera.initialize_library()

        self._image_type_choice = tk.StringVar()

        self._camera_chooser = CameraChooser(frame=self._main_frame, on_connect=self._on_camera_select)
        self._camera_chooser.pack(side=tk.TOP)

        self._add_task(1, self._check_new_images, timeout_ms=100)
        self._image_queue = multiprocessing.Queue()
        self._kill_capture_event = multiprocessing.Event()
        self._capture_process = None
        self._last_time = time.time()

    def _check_new_images(self):

        if self._capture_process is not None and not self._capture_process.is_alive():
            self._stop_capturing()
            return
        if self._capture_process is not None and self._capture_process.is_alive():
            queue_size = self._image_queue.qsize()
            print(f"Image queue size = {queue_size}")

            if queue_size > 0:
                im = self._image_queue.get()
                self._image_canvas.update_with_np(im)

                current = time.time()
                elapsed = current - self._last_time
                print(f"Elapsed for checking = {elapsed}")
                self._last_time = current

    def _on_camera_select(self, camera: ASICamera, camera_id: int):
        self._add_controls(camera)
        self._update_controls()

    def _add_controls(self, camera: ASICamera):
        controls_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        controls_frame.pack(side=tk.TOP)

        self._capture_frame = ttk.Frame(controls_frame, style="B.TFrame")
        self._capture_frame.pack(side=tk.TOP)
        self._still_button = ttk.Button(self._capture_frame,
                                        text="Get still image",
                                        command=self._get_still,
                                        style="B.TButton")
        self._still_button.pack(side=tk.LEFT)
        self._capture_spin = LabeledInput(frame=self._capture_frame, desc="Frames number")
        self._capture_spin.pack(side=tk.LEFT)

        self._start_capturing_button = ttk.Button(self._capture_frame,
                                                  text="Start capturing",
                                                  command=self._start_capturing,
                                                  style="B.TButton")
        self._start_capturing_button.pack(side=tk.LEFT)

        self._exp_us_controller = ValueController(frame=controls_frame,
                                                  setter_fun=lambda x: self._set_exposure_us(camera, x),
                                                  getter_fun=lambda: self._get_exposure_us(camera),
                                                  desc="Exposure [us]", to=(1000 * 1000 * 1000 - 1))
        self._exp_us_controller.pack(side=tk.TOP)
        self._exp_ms_controller = ValueController(frame=controls_frame,
                                                  setter_fun=lambda x: self._set_exposure_ms(camera, x),
                                                  getter_fun=lambda: self._get_exposure_ms(camera),
                                                  desc="Exposure [ms]", to=(1000 * 1000 * 1000 - 1))
        self._exp_ms_controller.pack(side=tk.TOP)

        image_types = camera.get_supported_image_types()
        self._type_combobox = ttk.Combobox(controls_frame, textvariable=self._image_type_choice,
                                           values=image_types, style="B.TCombobox", )
        self._type_combobox.pack(side=tk.TOP)
        current_type = camera.get_image_type()
        current_type = camera.translate_image_type(current_type)
        print(f"Current type= {current_type}")
        self._type_combobox.set(current_type)
        self._type_combobox.bind("<<ComboboxSelected>>",
                                 lambda _: camera.set_image_type(self._image_type_choice.get()))

        params = {
            "gain": ("Gain", lambda x: camera.set_gain(int(x)), camera.get_gain),
            "bandwidth": ("BandWidth", lambda x: camera.set_bandwidth(int(x)), camera.get_bandwidth),
            "highspeed": ("HighSpeedMode", lambda x: camera.set_high_speed_mode(int(x)), camera.get_high_speed_mode),
        }

        self._controls = {
            "exposure_us": self._exp_us_controller,
            "exposure_ms": self._exp_ms_controller,
        }
        for key, param in params.items():
            desc, setter, getter = param
            self._controls[key] = ValueController(frame=controls_frame,
                                                  setter_fun=setter,
                                                  getter_fun=getter,
                                                  desc=desc)
            self._controls[key].pack(side=tk.TOP)

        image_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        image_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        self._image_canvas = PhotoImage(frame=image_frame, initial_image_path=NO_IMAGE_FILE)
        self._image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _update_controls(self):
        [v.self_update() for v in self._controls.values()]

    def _start_capturing(self):
        multiplicity = int(self._capture_spin.get_value())
        print(f"Starting capture of {multiplicity} frames")
        camera_id = self._camera_chooser.get_camera_id()
        self._image_queue = multiprocessing.Queue()
        process_kwargs = return_kwargs(interval_us=int(self._exp_us_controller.get_current()),
                                       bandwidth=int(self._controls["bandwidth"].get_current()),
                                       camera_id=camera_id,
                                       multiplicity=multiplicity,
                                       image_type=self._image_type_choice.get(),
                                       save_file=False)  # TODO: save file control!

        self._capture_process = multiprocessing.Process(target=capturing,
                                                        args=[self._image_queue,
                                                              self._kill_capture_event],
                                                        kwargs=process_kwargs)
        self._capture_process.start()
        self._start_capturing_button.configure(text="Stop capturing", command=self._stop_capturing)

    def _stop_capturing(self):
        if self._capture_process is not None and self._capture_process.is_alive():
            print("Sending kill event for capture!")
            self._kill_capture_event.set()
            self._image_queue.close()
            self._capture_process.join()
            self._kill_capture_event.clear()
        if self._camera_chooser.get_camera() is not None:
            self._start_capturing_button.configure(text="Start capturing", command=self._start_capturing)

    def _killme(self):
        self._stop_capturing()
        super(AcquisitionProcessGUI, self)._killme()

    def _get_still(self):
        if self._camera_chooser.get_camera() is not None:
            image = self._camera_chooser.get_camera().capture_image()
            if len(image.shape) == 3:
                image = image[:, :, ::-1]
            self._image_canvas.update_with_np(image=image)

    def _get_exposure_ms(self, camera: ASICamera):
        exposure_us = camera.get_exposure_us()
        print(f"Getting exposure equal to {exposure_us}ms")
        self._exp_us_controller.update(exposure_us)
        return float(exposure_us / 1000)

    def _get_exposure_us(self, camera):
        exposure_us = camera.get_exposure_us()
        print(f"Getting exposure equal to {exposure_us}us")
        self._exp_ms_controller.update(float(exposure_us / 1000))
        return exposure_us

    def _set_exposure_ms(self, camera, value):
        print(f"Setting exposure to {value}ms")
        exposure_us = int(float(value) * 1000)
        camera.set_exposure_us(exposure_us)
        self._exp_us_controller.update(exposure_us)

    def _set_exposure_us(self, camera, value):
        print(f"Setting exposure to {value}us")
        exposure_us = int(value)
        camera.set_exposure_us(exposure_us)
        self._exp_ms_controller.update(exposure_us / 1000)
