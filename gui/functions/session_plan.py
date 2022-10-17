import tkinter as tk
from tkinter import ttk
from .zwo_asi_camera_grabber import ASICamera
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import os
from datetime import date


MAX_FAILURES_TO_RECONNECT = 10
MAX_FAILURES_TO_QUIT = 20


"""

    def __init__(self, event_log, r, st, c):
        self._message = None
        self._logger = event_log
        self._reader = r
        self._serial_thread = st
        self._com_port_choice = c

    def _async_connection(self, chosen_port):
        welcome_message = reader.connect_to_port(chosen_port)
        self._logger.log_event(f"{welcome_message}\n")
        serial_thread.start()

    def connect_to_chosen_port(self):
        chosen_port = self._com_port_choice.get()
        self._logger.log_event(f"Connecting to port: {chosen_port}\n")
        connection_thread = Thread(target=self._async_connection, args=(chosen_port,))
        connection_thread.start()"""

empty_camera_list_string = "<no zwo cameras here>"
formats = [".jpg", ".tiff", ".fits"]


class SessionPlanGUI:
    def __init__(self, frame, mover):
        ASICamera.initialize_library()

        self._mover = mover

        self._move_time_s = 1
        self._camera = None

        self._camera_id = 0
        self._available_cameras = ASICamera.get_cameras_list()
        if not self._available_cameras:
            self._available_cameras = [empty_camera_list_string]

        self._exposure_var = tk.StringVar(value=1)
        self._multiplicity_var = tk.StringVar(value=1)
        self._gain_var = tk.StringVar(value=50)
        self._camera_choice = tk.StringVar(value=self._available_cameras[0])

        connect_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        connect_frame.pack(side=tk.TOP)

        self._combobox = ttk.Combobox(connect_frame, textvariable=self._camera_choice, values=self._available_cameras)
        self._combobox.pack(side=tk.RIGHT)

        choose_camera_button = tk.Button(connect_frame, text="Connect", command=self._connect)
        choose_camera_button.pack(side=tk.LEFT)

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(side=tk.TOP, ipady=10)
        controls_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        controls_frame.pack(side=tk.TOP)

        exposure_label = tk.Label(controls_frame, text='Exposure [s] =', font=('calibre', 10, 'bold'))
        exposure_label.pack(side=tk.LEFT)
        exposure_spin = ttk.Spinbox(controls_frame, from_=0, to=9999, width=4, textvariable=self._exposure_var)
        exposure_spin.pack(side=tk.LEFT)

        multiplicity_label = tk.Label(controls_frame, text='Number of frames =', font=('calibre', 10, 'bold'))
        multiplicity_label.pack(side=tk.LEFT)
        multiplicity_spin = ttk.Spinbox(controls_frame, from_=0, to=9999, width=4, textvariable=self._multiplicity_var)
        multiplicity_spin.pack(side=tk.LEFT)

        gain_label = tk.Label(controls_frame, text='Gain =', font=('calibre', 10, 'bold'))
        gain_label.pack(side=tk.LEFT)
        gain_spin = ttk.Spinbox(controls_frame, from_=0, to=999, width=3, textvariable=self._gain_var)
        gain_spin.pack(side=tk.LEFT)

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(side=tk.TOP, ipady=10)

        start_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        start_frame.pack(side=tk.TOP)

        start_button = tk.Button(start_frame, text="Start", command=self._start)
        start_button.pack(side=tk.LEFT)

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(side=tk.TOP, ipady=10)

        figure1 = plt.Figure(dpi=100)
        self._ax = figure1.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(figure1, frame)
        self._canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # im = Image.open("2022-10-12//capture_0000.tiff")
        # imarray = np.array(im)
        # self._ax.imshow(np.log(imarray))

    def _start(self):
        if self._camera is None:
            print("Nothing to start right now!")
            return

        exposure_s = int(self._exposure_var.get())
        multiplicity = int(self._multiplicity_var.get())
        gain = int(self._gain_var.get())

        print(f"Exposure = {exposure_s*1000}ms")
        print(f"Multiplicity = {multiplicity}")
        print(f"Gain = {gain}")

        interval_ms = exposure_s * 1000
        increment_s = exposure_s + self._move_time_s
        increment_as = 15*increment_s
        self._camera.connect_and_prepare_camera(exposure_ms=interval_ms, gain=gain, roi=None)
        failure_counter = 0

        dir_name = date.today()
        if not os.path.isdir(dir_name):
            os.mkdir(dir_name)

        for i in range(0, multiplicity):
            filename = os.path.join(f"{dir_name}", "capture_{i:04d}.tiff")
            print(f"Capturing to file {filename}...")
            st = time.time()
            if not self._camera.capture_file(filename):
                failure_counter += 1
                print(f"Failure count = {failure_counter}")
                if failure_counter > MAX_FAILURES_TO_QUIT:
                    print("Too many failures, quiting!")
                    return
                elif failure_counter == MAX_FAILURES_TO_RECONNECT:
                    print("Too many failures: Trying to reconnect the camera...")
                    self._camera.close()
                    self._camera = ASICamera(self._camera_id)
                else:
                    print(f"Continuing despite of failures ({failure_counter}\\{MAX_FAILURES_TO_QUIT})")
            else:
                failure_counter = 0

            print("... done!")
            et = time.time()
            diff_time = int(et-st)
            print(et-st)
            diff_time = max(0, min(diff_time, exposure_s))

            while diff_time < exposure_s:
                time.sleep(1)
                diff_time += 1

            self._mover.move_ra_as_pub(increment_as)
            im = Image.open(filename)
            imarray = np.array(im)
            self._ax.imshow(np.log(imarray))
            self._canvas.draw()
            time.sleep(self._move_time_s)

    def _connect(self):
        camera_string = self._camera_choice.get()
        if empty_camera_list_string == camera_string:
            print("Nothing to connect here...")
            return
        self._camera_id = self._available_cameras.index(camera_string)
        print(f"Starting camera {camera_string} which has index {self._camera_id}...")
        self._camera = ASICamera(self._camera_id)
        print(self._camera.get_controls())


