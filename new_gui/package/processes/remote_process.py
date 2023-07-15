from .child_process import ChildProcessGUI
from package.widgets.value_controller import ValueController
from package.widgets.image_canvas import PhotoImageWithRectangle
from package.widgets.labeled_input import LabeledInput
from package.widgets.ip_address_input import IPAddressInput
from package.widgets.capture_progress_bar import CaptureProgressBar
from package.widgets.simple_plot import SimplePlot
from package.processes.camera_requester import CameraRequests, get_diff_ms
from package.utils.star_measurer import StarMeasurer
from tkinter import ttk
from datetime import datetime
import tkinter as tk
import requests
import numpy as np
import PIL
from threading import Thread


image_types_map = {
    "Y8": {"astype": np.uint8, "mode": "L"},
    "RAW8": {"astype": np.uint8, "mode": "L"},
    "RAW16": {"astype": np.uint16, "mode": "I;16"},
    "RGB24": {"astype": np.uint8, "mode": "RGB"},
}

max_threads = 4


def enqueue_task_if_possible(pool: list, pool_name: str, **kwargs):
    for i, t in enumerate(pool):
        if t is not None and not t.is_alive():
            print(f"Joining {pool_name} thread {i}...")
            t.join()
            pool[i] = None
    y = (i for i, v in enumerate(pool) if v is None)
    try:
        next_free = next(y)
    except StopIteration:
        print(f"== ERROR ==: No available {pool_name} threads!")
        return

    print(f"Next free {pool_name} thread = {next_free}")
    pool[next_free] = Thread(**kwargs)
    pool[next_free].start()


class ImagePercentileNormalizer:
    def __init__(self):
        self._equalize = False
        self._i16max = 65535
        self._max = self._i16max
        self._min = 0

    def set_clipping(self, bounds):
        pmin, pmax = bounds
        self._min = self._i16max * pmin / 100.0
        self._max = self._i16max * pmax / 100.0
        print(f"Min = {self._min}, Max = {self._max}")
        self._equalize = False

    def set_equalize(self):
        self._equalize = True

    def normalize(self, npimg):
        if16 = npimg.astype(np.float16)
        if self._equalize:
            a = np.percentile(if16, 5)
            b = np.percentile(if16, 95)
        else:
            a = self._min
            b = self._max

        epsilon = 0.1
        if b - a < epsilon:
            normalized_not_clipped = a * np.ones_like(if16)
        else:
            normalized_not_clipped = (if16 - a) / (b - a)

        min_clip = 0
        max_clip = 256

        return np.clip(max_clip * normalized_not_clipped, min_clip, max_clip-1).astype(np.uint8)


class RemoteProcessGUI(ChildProcessGUI):
    def __init__(self, *args, **kwargs):
        super(RemoteProcessGUI, self).__init__(title="Remote control", *args, **kwargs)
        self.maximize()
        self._measurer = StarMeasurer()
        self._address_input = IPAddressInput(self._main_frame, self._connect, initial="192.168.1.102")
        self._continuous_imaging = False
        ttk.Separator(self._main_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=5)
        self._requester = CameraRequests(camera_no=0)
        self._connected = False
        self._exposure_s = 1
        self._controls = {}
        self._current_shape = [768, 1024]  # [H, W]
        self._capturing = False
        self._add_task(self._check_capture_progress, timeout_ms=1000)
        self._add_task(self._check_continuous, timeout_ms=1000)
        self._temp_counter = 0
        self._current_raw_data = None
        self._last_good_image = datetime.now()
        self._normalizer = ImagePercentileNormalizer()
        self._min_scale_var = tk.DoubleVar(value=0)
        self._max_scale_var = tk.DoubleVar(value=100)
        self._continuous_threads = [None for _ in range(0, max_threads)]
        self._update_threads = [None for _ in range(0, max_threads)]

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
                                                  text="Start capturing",
                                                  command=self._start_capturing,
                                                  style="B.TButton")
        self._start_capturing_button.pack(side=tk.LEFT)

        self._capture_pb = CaptureProgressBar(frame=continuous_capturing_frame)
        self._capture_pb.pack(side=tk.LEFT)

        ttk.Separator(continuous_capturing_frame, orient=tk.HORIZONTAL,
                      style="B.TSeparator").pack(side=tk.LEFT, ipadx=50)

        self._trigger_button = ttk.Button(continuous_capturing_frame,
                                       text="One shot",
                                       command=self._get_one_shot_image,
                                       style="B.TButton")
        self._trigger_button.pack(side=tk.LEFT)
        self._instant_button = ttk.Button(continuous_capturing_frame,
                                       text="Instant image (max 5s)",
                                       command=self._get_instant_image,
                                       style="B.TButton")
        self._instant_button.pack(side=tk.LEFT)
        self._continuous_button = ttk.Button(continuous_capturing_frame,
                                       text="Start continuous",
                                       style="B.TButton")
        self._continuous_button.pack(side=tk.LEFT)
        self._continuous_button.configure(command=self._start_continuous_imaging)

        image_frame = ttk.Frame(controls_frame, style="B.TFrame")
        image_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        self._image_canvas = PhotoImageWithRectangle(frame=image_frame,
                                                     initial_image_path="last.png",
                                                     update_handler=self._new_image_handler)
        self._image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        image_controls_frame = ttk.Frame(image_frame, style="B.TFrame")
        image_controls_frame.pack(side=tk.LEFT)

        self._hist_plot = SimplePlot((0, 0), frame=image_controls_frame)
        self._hist_plot.pack(side=tk.TOP)

        self._scale_frame = ttk.Frame(image_controls_frame, style="B.TFrame")
        self._scale_frame.pack(side=tk.TOP)
        self._min_scale_label = ttk.Entry(self._scale_frame, width=3, textvariable=self._min_scale_var)
        self._min_scale_label.pack(side=tk.LEFT)
        self._min_scale = ttk.Scale(self._scale_frame, variable=self._min_scale_var,
                                    style="B.Horizontal.TScale", from_=0, to=100, orient=tk.HORIZONTAL)
        self._min_scale.pack(side=tk.LEFT)
        self._min_scale.bind("<ButtonRelease-1>", self._stretch)

        self._max_scale_label = ttk.Entry(self._scale_frame, width=3, textvariable=self._max_scale_var)
        self._max_scale_label.pack(side=tk.RIGHT)
        self._max_scale = ttk.Scale(self._scale_frame, variable=self._max_scale_var,
                                    style="B.Horizontal.TScale", from_=0, to=100, orient=tk.HORIZONTAL)
        self._max_scale.pack(side=tk.RIGHT)
        self._max_scale.bind("<ButtonRelease-1>", self._stretch)

        self._equalize_button = ttk.Button(image_controls_frame,
                                          text="Equalize",
                                          command=self._equalize,
                                          style="B.TButton")

        self._equalize_button.pack(side=tk.TOP)

        self._log_button = ttk.Button(image_controls_frame,
                                          text="Logarithm image",
                                          command=self._log_image,
                                          style="B.TButton")
        self._log_button.pack(side=tk.TOP)

        self._zoom_in_button = ttk.Button(image_controls_frame,
                                          text="Zoom image in (+)",
                                          command=self._image_canvas.zoom_in,
                                          style="B.TButton")
        self._zoom_in_button.pack(side=tk.TOP)

        self._zoom_out_button = ttk.Button(image_controls_frame,
                                          text="Zoom image out (-)",
                                          command=self._image_canvas.zoom_out,
                                          style="B.TButton")
        self._zoom_out_button.pack(side=tk.TOP)

        self._measure_button = ttk.Button(image_controls_frame,
                                          text="Measure stars",
                                          command=self._measure,
                                          style="B.TButton")
        self._measure_button.pack(side=tk.TOP)
        self._star_size_label = ttk.Label(image_controls_frame, style="B.TLabel", text="-1")
        self._star_size_label.pack(side=tk.RIGHT)

    def _measure(self):
        if self._current_raw_data is None:
            print("No current data for star measurement!")
            return
        value = self._measurer.measure_stars_on_np_array(self._current_raw_data)
        self._star_size_label.configure(text=value)

    def _stretch(self, event):
        smin = float(self._min_scale_var.get())
        smax = float(self._max_scale_var.get())
        print(f"Min = {smin}, Max = {smax}")
        self._normalizer.set_clipping((smin, smax))
        self._draw_image()

    def _equalize(self):
        self._normalizer.set_equalize()
        self._draw_image()

    def _new_image_handler(self):
        self._hist_image()

    def _hist_image(self):
        if self._current_raw_data is None:
            print("No current data!")
            return
        print("Obtaining image histogram")
        x, y = np.histogram(self._current_raw_data, bins=100)
        self._hist_plot.replot((x, y[1:]))

    def _update_temp(self):
        temp_string = f"T={self._requester.get_temperature()}°C"
        self._temperature_label.configure(text=temp_string)

    def _log_image(self):
        self._image_canvas.log_image()

    def _stop_capturing_internal(self):
        self._start_capturing_button.configure(text="Start capturing",
                                               state=tk.NORMAL,
                                               style="B.TButton")
        self._capturing = False

    def _start_capturing(self):
        self._start_capturing_button.configure(text="Capturing in progress",
                                               state=tk.DISABLED,
                                               style="SunkableButton.TButton")
        number = self._capture_spin.get_value()
        exposure = self._exposure_s
        self._requester.put_capture(exposure, number)
        self._capturing = True
        self._capture_pb.reset(max_no=int(number))

    def _start_continuous_imaging(self):
        exposure = self._exposure_s
        self._continuous_imaging = True
        self._continuous_button.configure(text="Stop continuous",
                                          command=self._stop_continuous_imaging,
                                          style="SunkableButton.TButton")
        r = self._requester.put_start_continuous_imaging(exposure)
        print(f"Request to start continuous imaging returned: {r}")

    def _stop_continuous_imaging(self):
        self._continuous_imaging = False
        self._continuous_button.configure(text="Start continuous",
                                          command=self._start_continuous_imaging,
                                          style="B.TButton")
        r = self._requester.put_stop_continuous_imaging()
        print(f"Request to stop continuous imaging returned: {r}")

    def _check_continuous_thread(self):
        print("Checking for continuous image available!")
        before = datetime.now()
        res = self._requester.get_continuous_image()
        after = datetime.now()
        ms = get_diff_ms(after, before)
        print(f"Getting continuous image response: {res}. Response took {ms}ms to finish.")
        if res.status_code == 418:
            print("Server is busy, waiting more...")
        elif res.status_code == 200:

            print(f"Got real image! Headers = {res.headers}")
            current_time = datetime.now()
            ms = get_diff_ms(current_time, self._last_good_image)
            print(f"Time passed from last image was: {ms}")
            self._last_good_image = current_time

            enqueue_task_if_possible(pool=self._continuous_threads,
                                     pool_name="continuous imaging",
                                     target=RemoteProcessGUI._single,
                                     args=(self, lambda: res.content))
            # self._single(getter=lambda: res.content)
        else:
            print(f"Got error: {res.status_code}")
        print("Continuous thread finished!")
        return

    def _check_continuous(self):
        if not self._continuous_imaging:
            return
        enqueue_task_if_possible(pool=self._continuous_threads,
                                 pool_name="continuous imaging",
                                 target=RemoteProcessGUI._check_continuous_thread,
                                 args=(self,))

    def _get_one_shot_image(self):
        return self._single(getter=lambda: self._requester.get_one_image(self._exposure_s, self._current_shape))

    def _get_instant_image(self):
        return self._single(getter=lambda: self._requester.put_instant_capture(self._exposure_s))

    def _update_image_when_capturing(self):
        npimg = self._requester.get_last_image()
        pil_image = self._convert_16b_np_image_into_pil(npimg)
        self._image_canvas.update_with_pil_image(pil_image)

    def _check_capture_progress(self):
        if not self._capturing:
            self._temp_counter += 1
            if self._temp_counter < 10:
                return
            self._temp_counter = 0
            # if self._connected:
            #     server_status = self._requester.is_alive()
            #     server_alive = "YES" if server_status else "NO"
            #     # print(f"Server alive?: {server_alive}")
            #     if not server_alive:
            #         self._connected = False
            #     else: self._update_temp()

            return

        if self._continuous_imaging:
            return

        r = self._requester.get_camerastate()
        if r.status_code == 200:
            self._capture_pb.finish()
            self._update_image_when_capturing()
            self._stop_capturing_internal()
            return

        try:
            c_state = r.json()["Status"]
            print(f"Camera state = {c_state}")
            if c_state == "ERROR":
                err_msg = r.json()["ErrorMessage"]
                print(f"Error from camera: {err_msg}, returning and stopping capture")
                self._capture_pb.reset()
                self._stop_capturing_internal()
                return

            if "/" in c_state:
                [progress, total] = c_state.split("/")
                self._capture_pb.update(int(progress))
                self._update_image_when_capturing()
        except KeyError as ke:
            print(f"Some key was not found in result json: {repr(ke)}")
            self._capture_pb.reset()
            self._stop_capturing_internal()
        except Exception as e:
            print(f"Unknown exception happened on update for capturing: {repr(e)}")
            self._capture_pb.reset()
            self._stop_capturing_internal()

    def _get_np_array_from_camera(self, image_type, getter):
        """
        Will return 8b or 16b np array of bytes send from camera
        :return:
        """
        type_info = image_types_map[image_type]
        imagebytes = getter()
        shape = self._current_shape
        img_dtype = type_info["astype"]

        npimg = np.frombuffer(imagebytes, dtype=img_dtype)
        npimg = npimg.reshape(shape)
        return npimg

    def _convert_16b_np_image_into_pil(self, npimg):

        # print(f"a={a}, b={b}, span = {b - a}")
        # print(f"img8b max={np.max(img8b)}, img8b min={np.min(img8b)}")
        npimg = self._normalizer.normalize(npimg)

        return PIL.Image.fromarray(npimg, mode="L")

    def _draw_image(self):
        if self._current_raw_data is None:
            return
        pil_image = self._convert_16b_np_image_into_pil(self._current_raw_data)
        self._image_canvas.update_with_pil_image(pil_image)

    def _single(self, getter):
        image_type = self._type_combobox.get()
        print(f"Image type = {image_type}")
        npimg = self._get_np_array_from_camera(image_type, getter=getter)
        type_info = image_types_map[image_type]
        self._current_raw_data = npimg

        # CAREFUL! Below line make image downgraded into 8 bit from 16!
        # Just for sake of displaying it correcly:
        # if type_info["astype"] == np.uint16:

        self._draw_image()

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
