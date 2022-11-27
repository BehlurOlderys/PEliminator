from .child_process import ChildProcessGUI
from package.utils.zwo_asi_camera_grabber import ASICamera
from tkinter import ttk
import tkinter as tk

from package.widgets.value_controller import ValueController

empty_camera_list_string = "<no zwo cameras here>"


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

        connect_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        connect_frame.pack(side=tk.TOP)

        self._combobox = ttk.Combobox(connect_frame, textvariable=self._camera_choice,
                                      values=self._available_cameras, style="B.TCombobox")
        self._combobox.pack(side=tk.RIGHT)

        self._choose_camera_button = ttk.Button(connect_frame, text="Connect", command=self._connect, style="B.TButton")
        self._choose_camera_button.pack(side=tk.LEFT)

        controls_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        controls_frame.pack(side=tk.TOP)
        self._exp_us_controller = ValueController(frame=controls_frame,
                                           setter_fun=self._set_exposure_us,
                                           getter_fun=self._get_exposure_us,
                                           desc="Exposure [us]", to=(1000*1000*1000 - 1))
        self._exp_us_controller.pack(side=tk.TOP)
        self._exp_ms_controller = ValueController(frame=controls_frame,
                                           setter_fun=self._set_exposure_ms,
                                           getter_fun=self._get_exposure_ms,
                                           desc="Exposure [ms]", to=(1000*1000*1000 - 1))
        self._exp_ms_controller.pack(side=tk.TOP)
        self._test_exp = 0

    def _get_exposure_ms(self):
        print(f"Getting exposure equal to {self._test_exp}ms")
        self._exp_us_controller.update(self._test_exp)
        return float(self._test_exp/1000)

    def _get_exposure_us(self):
        print(f"Getting exposure equal to {self._test_exp}us")
        self._exp_ms_controller.update(float(self._test_exp/1000))
        return self._test_exp

    def _set_exposure_ms(self, value):
        print(f"Setting exposure to {value}ms")
        self._test_exp = float(value)*1000
        self._exp_us_controller.update(self._test_exp)

    def _set_exposure_us(self, value):
        print(f"Setting exposure to {value}us")
        self._test_exp = float(value)
        self._exp_ms_controller.update(self._test_exp/1000)

    def _connect(self):
        camera_string = self._camera_choice.get()
        if empty_camera_list_string == camera_string:
            print("Nothing to connect here...")
            return
        self._camera_id = self._available_cameras.index(camera_string)
        print(f"Starting camera {camera_string} which has index {self._camera_id}...")
        self._camera = ASICamera(self._camera_id)
        self._choose_camera_button.configure(state=tk.DISABLED)
