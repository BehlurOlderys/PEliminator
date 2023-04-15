from .child_process import ChildProcessGUI
from package.widgets.value_controller import ValueController
from package.widgets.image_canvas import PhotoImage
from package.widgets.labeled_input import LabeledInput
from package.widgets.ip_address_input import IPAddressInput
from package.widgets.capture_progress_bar import CaptureProgressBar
from package.processes.camera_requester import CameraRequests
from tkinter import ttk
import tkinter as tk
import requests
import numpy as np
import PIL


image_types_map = {
    "Y8": {"astype": np.uint8, "mode": "L"},
    "RAW8": {"astype": np.uint8, "mode": "L"},
    "RAW16": {"astype": np.uint16, "mode": "I;16"},
    "RGB24": {"astype": np.uint8, "mode": "RGB"},
}


class RemoteProcessGUI(ChildProcessGUI):
    def __init__(self, *args, **kwargs):
        super(RemoteProcessGUI, self).__init__(title="Remote control", *args, **kwargs)
        self.maximize()
        self._address_input = IPAddressInput(self._main_frame, self._connect, initial="192.168.0.59")

        ttk.Separator(self._main_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=5)
        self._requester = CameraRequests(camera_no=0)
        self._connected = False
        self._exposure_s = 1
        self._controls = {}
        self._current_shape = [768, 1024]  # [H, W]
        self._capturing = False
        self._add_task(1, self._check_capture_progress, timeout_ms=1000)
        self._temp_counter = 0
        self._cropped = tk.IntVar(value=0)

    def _connect(self, host_name, port_number):
        if self._connected is False:
            address = f"http://{host_name}:{port_number}"
            print(f"Connecting to {address}")
            try:
                self._requester.update_address(address)
                if self._requester.set_init():
                    self._current_shape = self._requester.get_imagesize()
                    self._add_controls()
                    self._connected = True
                else:
                    print("Init failed!")
            except requests.exceptions.ConnectionError:
                tk.messagebox.showerror('Connection error', f"Could not connect to {address}")

    def _add_controls(self):
        controls_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        controls_frame.pack(side=tk.TOP)

        image_params_frame = ttk.Frame(controls_frame, style="B.TFrame")
        image_params_frame.pack(side=tk.TOP)

        self._exp_ms_controller = LabeledInput(frame=image_params_frame,
                                               desc="Exp.[ms]", to=(10 * 1000 * 1000 - 1),
                                               width=8, callback=self._set_exposure_ms)
        self._exp_ms_controller.pack(side=tk.LEFT)
        self._exp_s_controller = LabeledInput(frame=image_params_frame,
                                              desc="Exp.[s]", to=(10 * 1000 - 1),
                                              width=6, callback=self._set_exposure_s)
        self._exp_s_controller.pack(side=tk.LEFT)
        self._exp_s_controller.set_value(self._exposure_s)

        self._temperature_label = ttk.Label(image_params_frame, style="B.TLabel")
        self._temperature_label.pack(side=tk.RIGHT)
        self._update_temp()

        image_types = self._requester.get_camera_readout_modes()
        self._type_combobox = ttk.Combobox(image_params_frame, values=image_types, style="B.TCombobox", )
        self._type_combobox.pack(side=tk.RIGHT)
        current_type = self._requester.get_current_readout_mode()
        print(f"Current type= {current_type}")
        self._type_combobox.current(newindex=current_type)
        self._type_combobox.bind("<<ComboboxSelected>>",
                                 lambda event: self._requester.set_readout_mode(event.widget.current()))

        self._controls["Gain"] = ValueController(frame=image_params_frame,
                                                 setter_fun=lambda x: self._requester.set_gain(x),
                                                 getter_fun=lambda: self._requester.get_gain(),
                                                 desc="Gain")
        self._controls["Gain"].pack(side=tk.LEFT)

        continuous_capturing_frame = ttk.Frame(controls_frame, style="B.TFrame")
        continuous_capturing_frame.pack(side=tk.TOP)

        self._capture_spin = LabeledInput(frame=continuous_capturing_frame, desc="Frames", from_=1)
        self._capture_spin.pack(side=tk.LEFT)

        self._start_capturing_button = ttk.Button(continuous_capturing_frame,
                                                  text="Start",
                                                  command=self._start_capturing,
                                                  style="B.TButton")
        self._start_capturing_button.pack(side=tk.LEFT)

        self._capture_pb = CaptureProgressBar(frame=continuous_capturing_frame)
        self._capture_pb.pack(side=tk.LEFT)

        ttk.Separator(continuous_capturing_frame, orient=tk.HORIZONTAL,
                      style="B.TSeparator").pack(side=tk.LEFT, ipadx=50)

        self._trigger_button = ttk.Button(continuous_capturing_frame,
                                       text="One shot",
                                       command=self._single,
                                       style="B.TButton")
        self._trigger_button.pack(side=tk.LEFT)

        image_frame = ttk.Frame(controls_frame, style="B.TFrame")
        image_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self._image_canvas = PhotoImage(frame=image_frame, initial_image_path="last.png")
        self._image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        image_controls_frame = ttk.Frame(image_frame, style="B.TFrame")
        image_controls_frame.pack(side=tk.LEFT)

        self._crop_button = ttk.Checkbutton(image_controls_frame,
                                       variable=self._cropped,
                                       text="Crop image",
                                       style="B.TCheckbutton")
        self._crop_button.pack(side=tk.TOP)

        self._log_button = ttk.Button(image_controls_frame,
                                          text="Logarithm image",
                                          command=self._log_image,
                                          style="B.TButton")
        self._log_button.pack(side=tk.TOP)

    def _update_temp(self):
        temp_string = f"T={self._requester.get_temperature()}°C"
        self._temperature_label.configure(text=temp_string)

    def _log_image(self):
        self._image_canvas.log_image()

    def _start_capturing(self):
        number = self._capture_spin.get_value()
        exposure = self._exposure_s
        self._requester.put_capture(exposure, number)
        self._capturing = True
        self._capture_pb.reset(max_no=int(number))

    def _update_image_when_capturing(self):
        self._image_canvas.update_with_pil_image(self._requester.get_last_image())

    def _check_capture_progress(self):
        if not self._capturing:
            self._temp_counter += 1
            if self._temp_counter < 10:
                return
            self._temp_counter = 0
            if self._connected:
                server_status = self._requester.is_alive()
                server_alive = "YES" if server_status else "NO"
                # print(f"Server alive?: {server_alive}")
                if not server_alive:
                    self._connected = False
                else: self._update_temp()

            return

        r = self._requester.get_camerastate()
        if r.status_code == 200:
            self._capture_pb.finish()
            self._update_image_when_capturing()
            self._capturing = False
            return

        try:
            c_state = r.json()["Status"]
            print(f"Camera state = {c_state}")
            if "/" in c_state:
                [progress, total] = c_state.split("/")
                self._capture_pb.update(int(progress))
                self._update_image_when_capturing()
        except KeyError as ke:
            print(f"Status not found in result json: {repr(ke)}")
        except Exception as e:
            print(f"Unknown exception happened on update for capturing: {repr(e)}")

    def _get_np_array_for_single(self, image_type):
        """
        Will return 8b or 16b np array of bytes send from camera
        :return:
        """
        type_info = image_types_map[image_type]
        imagebytes = self._requester.get_one_image(self._exposure_s, image_type, self._current_shape)
        shape = self._current_shape
        img_dtype = type_info["astype"]

        npimg = np.frombuffer(imagebytes, dtype=img_dtype)
        npimg = npimg.reshape(shape)
        return npimg

    def _single_save(self, npimg, typeinfo, filename="last.png"):
        image = PIL.Image.fromarray(npimg, mode=typeinfo["mode"])
        image.save(filename)

    def _single(self, save=False):
        epsilon = 0.1
        image_type = self._type_combobox.get()
        print(f"Image type = {image_type}")
        npimg = self._get_np_array_for_single(image_type)
        type_info = image_types_map[image_type]

        if save:
            self._single_save(npimg, type_info, "last.png")

        # CAREFUL! Below line make image downgraded into 8 bit from 16!
        # Just for sake of displaying it correcly:
        # if type_info["astype"] == np.uint16:

        if self._cropped.get() > 0:
            crop_xs = 100
            crop_xe = 356
            crop_ys = 100
            crop_ye = 356
            npimg = npimg[crop_xs:crop_xe, crop_ys:crop_ye]

        if16 = npimg.astype(np.float16)
        a = np.percentile(if16, 5)
        b = np.percentile(if16, 95)

        if b - a < epsilon:
            normalized_not_clipped = a*np.ones_like(if16)
        else:
            normalized_not_clipped = (if16 - a) / (b - a)

        img8b = np.clip(256*normalized_not_clipped, 0, 255).astype(np.uint8)
        print(f"a={a}, b={b}, span = {b - a}")
        print(f"img8b max={np.max(img8b)}, img8b min={np.min(img8b)}")
        npimg = img8b.astype(np.uint8)

        # else:
        #     pass
        image = PIL.Image.fromarray(npimg, mode="L")
        np_image = np.array(image.getdata())
        print(f"npmax={np.max(np_image)}, npmin={np.min(np_image)}")
        self._image_canvas.update_with_pil_image(image)

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