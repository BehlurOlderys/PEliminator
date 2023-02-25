from .child_process import ChildProcessGUI
from package.widgets.value_controller import ValueController
from package.widgets.image_canvas import PhotoImage
from package.widgets.labeled_input import LabeledInput
from package.widgets.ip_address_input import IPAddressInput
from package.processes.camera_requester import CameraRequests
from tkinter import ttk
import tkinter as tk
import time


class RemoteProcessGUI(ChildProcessGUI):
    def __init__(self, *args, **kwargs):
        super(RemoteProcessGUI, self).__init__(title="Remote control", *args, **kwargs)

        self._address_input = IPAddressInput(self._main_frame, self._connect, initial="192.168.0.129")

        ttk.Separator(self._main_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)
        self._requester = CameraRequests(camera_no=0)
        self._connected = False
        self._exposure_s = 1
        self._controls = {}
        self._current_shape = [768, 1024]  # [H, W]

    def _connect(self, host_name, port_number):
        if self._connected is False:
            address = f"http://{host_name}:{port_number}"
            print(f"Connecting to {address}")
            self._requester.update_address(address)
            self._current_shape = self._requester.get_imagesize()
            self._connected = True
            self._add_controls()

    def _add_controls(self):
        controls_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        controls_frame.pack(side=tk.TOP)

        self._capture_frame = ttk.Frame(controls_frame, style="B.TFrame")
        self._capture_frame.pack(side=tk.TOP)
        self._trigger_button = ttk.Button(self._capture_frame,
                                       text="Trigger single capture",
                                       command=self._single,
                                       style="B.TButton")
        self._trigger_button.pack(side=tk.LEFT)
        self._last_button = ttk.Button(self._capture_frame,
                                        text="Get last image",
                                        command=self._get_last,
                                        style="B.TButton")
        self._last_button.pack(side=tk.LEFT)
        self._capture_spin = LabeledInput(frame=self._capture_frame, desc="Frames number")
        self._capture_spin.pack(side=tk.LEFT)

        self._start_capturing_button = ttk.Button(self._capture_frame,
                                                  text="Start capturing",
                                                  # command=self._start_capturing,
                                                  style="B.TButton")
        self._start_capturing_button.pack(side=tk.LEFT)

        self._exp_ms_controller = LabeledInput(frame=self._capture_frame,
                                               desc="Exposure [ms]", to=(10 * 1000 * 1000 - 1),
                                               width=8, callback=self._set_exposure_ms)
        self._exp_ms_controller.pack(side=tk.TOP)
        self._exp_s_controller = LabeledInput(frame=self._capture_frame,
                                              desc="Exposure [s]", to=(10 * 1000 - 1),
                                              width=6, callback=self._set_exposure_s)
        self._exp_s_controller.pack(side=tk.TOP)
        self._exp_s_controller.set_value(self._exposure_s)

        image_types = self._requester.get_camera_readout_modes()
        self._type_combobox = ttk.Combobox(controls_frame, values=image_types, style="B.TCombobox", )
        self._type_combobox.pack(side=tk.TOP)
        current_type = self._requester.get_current_readout_mode()
        print(f"Current type= {current_type}")
        self._type_combobox.current(newindex=current_type)
        self._type_combobox.bind("<<ComboboxSelected>>",
                                 lambda event: self._requester.set_readout_mode(event.widget.current()))

        # self._controls["Gain"] = ValueController(frame=controls_frame,
        #                                          setter_fun=setter,
        #                                          getter_fun=getter,
        #                                          desc=desc)
        # self._controls["Gain"].pack(side=tk.TOP)


        # params = {
        #     "gain": ("Gain", lambda x: camera.set_gain(int(x)), camera.get_gain),
        #     "bandwidth": ("BandWidth", lambda x: camera.set_bandwidth(int(x)), camera.get_bandwidth),
        #     "highspeed": ("HighSpeedMode", lambda x: camera.set_high_speed_mode(int(x)), camera.get_high_speed_mode),
        # }
        #
        # self._controls = {
        #     "exposure_us": self._exp_us_controller,
        #     "exposure_ms": self._exp_ms_controller,
        # }
        # for key, param in params.items():
        #     desc, setter, getter = param
        #     self._controls[key] = ValueController(frame=controls_frame,
        #                                           setter_fun=setter,
        #                                           getter_fun=getter,
        #                                           desc=desc)
        #     self._controls[key].pack(side=tk.TOP)

        image_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        image_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        initial_image = self._requester.get_last_image()
        self._image_canvas = PhotoImage(frame=image_frame, initial_image=initial_image)
        self._image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _get_last(self):
        print("Downloading last available image")

    def _single(self):
        image_type = self._type_combobox.get()
        print(f"Image type = {image_type}")
        image_array = self._requester.get_one_image(self._exposure_s, image_type, self._current_shape)
        print(f"Image = {image_array}")
        self._image_canvas.update_with_np(image_array)
    #     img2 = ImageTk.PhotoImage(Image.fromarray(img_array))
    #     panel.configure(image=img2)
    #     panel.image = img2

    def _set_exposure_s(self, value):
        try:
            self._exposure_s = float(value.get())
        except ValueError:
            return
        self._exp_ms_controller.set_value(str(self._exposure_s*1000))

    def _set_exposure_ms(self, value):
        try:
            self._exposure_s = float(value.get())/1000
        except ValueError:
            return
        self._exp_s_controller.set_value(str(self._exposure_s))
