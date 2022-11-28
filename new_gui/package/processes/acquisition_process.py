from .child_process import ChildProcessGUI
from package.utils.zwo_asi_camera_grabber import ASICamera
from tkinter import ttk
import tkinter as tk
import matplotlib.image as mpimg
from multiprocessing import Process
import numpy as np

from package.widgets.value_controller import ValueController
from package.widgets.image_canvas import PhotoImage

empty_camera_list_string = "<no zwo cameras here>"
NO_IMAGE_FILE = "data/no_image.png"


class AcquisitionProcessGUI(ChildProcessGUI):
    def __init__(self, *args, **kwargs):
        super(AcquisitionProcessGUI, self).__init__(title="Acquisition", *args, **kwargs)
        ASICamera.initialize_library()
        self._camera: ASICamera = None
        self._camera_id = 0
        self._available_cameras = ASICamera.get_cameras_list()
        if not self._available_cameras:
            self._available_cameras = [empty_camera_list_string]

        self._camera_choice = tk.StringVar(value=self._available_cameras[0])
        self._image_type_choice = tk.StringVar()

        connect_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        connect_frame.pack(side=tk.TOP)

        self._combobox = ttk.Combobox(connect_frame, textvariable=self._camera_choice,
                                      values=self._available_cameras, style="B.TCombobox")
        self._combobox.pack(side=tk.RIGHT)

        self._choose_camera_button = ttk.Button(connect_frame, text="Connect", command=self._connect, style="B.TButton")
        self._choose_camera_button.pack(side=tk.LEFT)

    def _add_controls(self, camera):
        controls_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        controls_frame.pack(side=tk.TOP)

        self._capture_frame = ttk.Frame(controls_frame, style="B.TFrame")
        self._capture_frame.pack(side=tk.TOP)
        self._still_button = ttk.Button(self._capture_frame,
                                        text="Get still image",
                                        command=self._get_still,
                                        style="B.TButton")
        self._still_button.pack(side=tk.LEFT)
        self._start_capturing_button = ttk.Button(self._capture_frame,
                                        text="Start capturing",
                                        command=self._start_capturing,
                                        style="B.TButton")
        self._start_capturing_button.pack(side=tk.LEFT)


        self._exp_us_controller = ValueController(frame=controls_frame,
                                                  setter_fun=lambda x: self._set_exposure_us(camera, x),
                                                  getter_fun=lambda: self._get_exposure_us(camera),
                                                  desc="Exposure [us]", to=(1000*1000*1000 - 1))
        self._exp_us_controller.pack(side=tk.TOP)
        self._exp_ms_controller = ValueController(frame=controls_frame,
                                                  setter_fun=lambda x: self._set_exposure_ms(camera, x),
                                                  getter_fun=lambda: self._get_exposure_ms(camera),
                                                  desc="Exposure [ms]", to=(1000*1000*1000 - 1))
        self._exp_ms_controller.pack(side=tk.TOP)

        image_types = self._camera.get_supported_image_types()
        self._type_combobox = ttk.Combobox(controls_frame, textvariable=self._image_type_choice,
                                      values=image_types, style="B.TCombobox", )
        self._type_combobox.pack(side=tk.TOP)
        current_type = self._camera.get_image_type()
        current_type = self._camera.translate_image_type(current_type)
        print(f"Current type= {current_type}")
        self._type_combobox.set(current_type)
        self._type_combobox.bind("<<ComboboxSelected>>",
                                 lambda _: self._camera.set_image_type(self._image_type_choice.get()))


        params = {
            "gain": ("Gain", lambda x: camera.set_gain(int(x)), camera.get_gain)
        }
        self._controls = {}
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

    def _start_capturing(self):
        print("Starting continuous capture!")

    def _get_still(self):
        if self._camera is not None:
            image = self._camera.capture_image()
            # print(f"Captured image with shape: {image.shape}")
            # if len(image.shape) == 3:
            #     image = image[:, :, ::-1]
            self._image_canvas.update(image=image)

    def _get_exposure_ms(self, camera: ASICamera):
        exposure_us = camera.get_exposure_us()
        print(f"Getting exposure equal to {exposure_us}ms")
        self._exp_us_controller.update(exposure_us)
        return float(exposure_us/1000)

    def _get_exposure_us(self, camera):
        exposure_us = camera.get_exposure_us()
        print(f"Getting exposure equal to {exposure_us}us")
        self._exp_ms_controller.update(float(exposure_us/1000))
        return exposure_us

    def _set_exposure_ms(self, camera, value):
        print(f"Setting exposure to {value}ms")
        exposure_us = int(float(value)*1000)
        camera.set_exposure_us(exposure_us)
        self._exp_us_controller.update(exposure_us)

    def _set_exposure_us(self, camera, value):
        print(f"Setting exposure to {value}us")
        exposure_us = int(value)
        camera.set_exposure_us(exposure_us)
        self._exp_ms_controller.update(exposure_us/1000)

    def _connect(self):
        camera_string = self._camera_choice.get()
        if empty_camera_list_string == camera_string:
            print("Nothing to connect here...")
            return
        self._camera_id = self._available_cameras.index(camera_string)
        print(f"Starting camera {camera_string} which has index {self._camera_id}...")
        self._camera = ASICamera(self._camera_id)
        self._choose_camera_button.configure(state=tk.DISABLED)
        self._add_controls(self._camera)


