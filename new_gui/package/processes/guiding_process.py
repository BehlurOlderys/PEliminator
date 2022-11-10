from .child_process import ChildProcessGUI
from package.widgets.dir_chooser import DirChooser
from package.widgets.labeled_input import LabeledInput
from package.utils.zwo_asi_camera_grabber import ASICamera
from tkinter import ttk
import tkinter as tk
from package.utils.image_provider import TimedFileImageProvider
from queue import Queue
from threading import Thread
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


IMAGE_QUEUE_TIMEOUT_S = 5
empty_camera_list_string = "<no zwo cameras here>"
initial_test_dir = "C:/Users/Florek/Desktop/workspace/PEliminator/gui/data/png_do_testow/Capture_00050"


class GuidingProcessGUI(ChildProcessGUI):
    def __init__(self, serial_out_queue, serial_in_queue, *args, **kwargs):
        super(GuidingProcessGUI, self).__init__(title="Guiding", *args, **kwargs)
        ASICamera.initialize_library()
        self._serial_out = serial_out_queue
        self._serial_in = serial_in_queue
        self._image_queue = Queue()
        self._sim_thread = None
        self._sim_provider = None
        self._sim_kill = False
        self._camera = None
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

        ttk.Separator(self._main_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)

        sim_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        sim_frame.pack(side=tk.TOP)
        self._sim_dir_chooser = DirChooser(frame=sim_frame,
                                           initial_dir=initial_test_dir).pack(side=tk.LEFT)
        self._interval_chooser = LabeledInput(frame=sim_frame, desc="interval [s]", from_=1).pack(side=tk.LEFT)
        self._sim_button = ttk.Button(sim_frame, text="Start simulation",
                                      command=self._start_simulation, style="B.TButton")
        self._sim_button.pack(side=tk.LEFT)

        ttk.Separator(self._main_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)

        image_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        image_frame.pack(side=tk.TOP)

        data_figure = plt.Figure(dpi=100)
        self._ax = data_figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(data_figure, image_frame)
        self._canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def _killme(self):
        self._end_sim_thread()
        super(GuidingProcessGUI, self)._killme()

    def _handle_new_images(self):
        while not self._sim_kill:
            print("Waiting for new image...")
            image = self._image_queue.get(timeout=IMAGE_QUEUE_TIMEOUT_S)
            if image is None:
                print("Returning from handle images thread")
                return
            if self._sim_kill:
                return
            c = 255 / np.log(1 + np.max(image))
            log_image = c * (np.log(image + 1))
            log_image = np.array(log_image, dtype=np.uint8)

            self._ax.imshow(log_image, cmap='gist_heat')
            self._canvas.draw()

    def _start_simulation(self):
        self._sim_provider = TimedFileImageProvider(delay=int(self._interval_chooser.get_value()),
                                          directory=self._sim_dir_chooser.get_dir(),
                                          queue=self._image_queue)
        self._sim_provider.start()
        self._sim_kill = False
        self._sim_thread = Thread(target=self._handle_new_images)
        self._sim_thread.start()
        self._sim_button.configure(text="Stop simulation", command=self._stop_simulation)

    def _end_sim_thread(self):
        self._sim_provider.stop()
        if self._sim_thread is not None and self._sim_thread.is_alive():
            print("Sim thread still alive, killing it...")
            self._sim_kill = True
            self._image_queue.put(None)
            print("Waiting to join sim thread...")
            self._sim_thread.join()
            self._sim_thread = None
            print("Sim thread joined")
        print("Simulation ended successfully!")

    def _stop_simulation(self):
        self._end_sim_thread()
        self._sim_button.configure(text="Start simulation", command=self._start_simulation)

    def _connect(self):
        camera_string = self._camera_choice.get()
        if empty_camera_list_string == camera_string:
            print("Nothing to connect here...")
            return
        self._camera_id = self._available_cameras.index(camera_string)
        print(f"Starting camera {camera_string} which has index {self._camera_id}...")
        self._camera = ASICamera(self._camera_id)
        self._choose_camera_button.configure(state=tk.DISABLED)
