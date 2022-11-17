from .child_process import ChildProcessGUI
from package.widgets.dir_chooser import DirChooser
from package.widgets.labeled_input import LabeledInput
from package.utils.image_consumer import ImageConsumer
from package.utils.error_handler import ErrorHandler
from package.widgets.running_plot import RunningPlot2D
from package.utils.zwo_asi_camera_grabber import ASICamera
from tkinter import ttk
import tkinter as tk
from package.utils.image_provider import TimedFileImageProvider
import queue
import multiprocessing
from package.widgets.image_canvas import ImageCanvasWithRectangle
import numpy as np
from package.utils.star_position_calculator import StarPositionCalculator
from multiprocessing import Event, Process
from package.processes.camera_diagnostics import DiagnosticsGUI


CAMERA_TEMPERATURE_UPDATE_TIME_S = 10
RECTANGLE_SIZE = 60
NO_IMAGE_FILE = "data/no_image.png"
empty_camera_list_string = "<no zwo cameras here>"
initial_test_dir = "C:\\Users\\Florek\\Desktop\\workspace\\PEliminator\\new_gui\\test_data\\Capture_00497"


def diagnostics_gui(queue, ke):
    gui = DiagnosticsGUI(queue=queue, update_s=CAMERA_TEMPERATURE_UPDATE_TIME_S, kill_event=ke)
    gui.run()


def log_image(image):
    c = 255 / np.log(1 + np.max(image))
    li = c * (np.log(image + 1))
    return np.array(li, dtype=np.uint8)


class GuidingProcessGUI(ChildProcessGUI):
    def __init__(self, serial_out_queue, serial_in_queue, *args, **kwargs):
        super(GuidingProcessGUI, self).__init__(title="Guiding", *args, **kwargs)
        ASICamera.initialize_library()
        self._serial_out = serial_out_queue
        self._serial_in = serial_in_queue
        self._image_queue = queue.Queue()
        self._sim_provider = None
        self._diagnostics_process = None
        self._diagnostics_kill_event = Event()
        self._diagnostics_queue = multiprocessing.Queue()
        self._camera = None
        self._camera_id = 0
        self._available_cameras = ASICamera.get_cameras_list()
        if not self._available_cameras:
            self._available_cameras = [empty_camera_list_string]

        self._camera_choice = tk.StringVar(value=self._available_cameras[0])

        connect_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        connect_frame.pack(side=tk.TOP)

        self._diagnostic_button = ttk.Button(connect_frame, text="Camera diagnostics...",
                                             state=tk.DISABLED,
                                             command=self._diagnostics, style="B.TButton")
        self._diagnostic_button.pack(side=tk.RIGHT)

        self._combobox = ttk.Combobox(connect_frame, textvariable=self._camera_choice,
                                      values=self._available_cameras, style="B.TCombobox")
        self._combobox.pack(side=tk.RIGHT)

        self._choose_camera_button = ttk.Button(connect_frame, text="Connect", command=self._connect, style="B.TButton")
        self._choose_camera_button.pack(side=tk.LEFT)

        ttk.Separator(self._main_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)

        params_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        params_frame.pack(side=tk.TOP)
        self._focal_spin = LabeledInput(frame=params_frame, desc="Focal length [mm]", from_=10, initial_value=650)
        self._focal_spin.pack(side=tk.LEFT)
        self._pixel_spin = LabeledInput(frame=params_frame,
                                        desc="Pixel size [um]",
                                        from_=0.1, to=20.0,
                                        increment=0.01,
                                        initial_value=2.9,
                                        width=6)
        self._pixel_spin.pack(side=tk.LEFT)
        self._ra_microsteps_spin = LabeledInput(frame=params_frame,
                                                desc="RA \" per step",
                                                from_=0.01, to=5.0,
                                                increment=0.01,
                                                initial_value=0.30,
                                                width=7)
        self._ra_microsteps_spin.pack(side=tk.LEFT)
        self._dec_microsteps_spin = LabeledInput(frame=params_frame,
                                                 desc="DEC \" per step",
                                                 from_=0.01, to=5.0,
                                                 increment=0.01,
                                                 initial_value=0.60,
                                                 width=7)
        self._dec_microsteps_spin.pack(side=tk.LEFT)

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
        image_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        self._image_canvas = ImageCanvasWithRectangle(frame=image_frame,
                                                      fragment_size=RECTANGLE_SIZE,
                                                      callback=self._new_selection,
                                                      initial_image_path=NO_IMAGE_FILE)
        self._image_canvas.pack(side=tk.LEFT, fill=tk.BOTH)

        self._calculate_button = ttk.Button(image_frame, text="Start calculating",
                                            state=tk.DISABLED,
                                            command=self._start_calculating, style="B.TButton")
        self._calculate_button.pack(side=tk.TOP)

        self._clear_selection_button = ttk.Button(image_frame, text="Clear selection",
                                                  state=tk.DISABLED,
                                                  command=self._clear_selection, style="B.TButton")
        self._clear_selection_button.pack(side=tk.TOP)
        self._guiding_button = ttk.Button(image_frame, text="Send guiding commands",
                                          state=tk.DISABLED,
                                          command=self._start_guide, style="B.TButton")
        self._guiding_button.pack(side=tk.TOP)
        self._camera_angle = LabeledInput(frame=image_frame, desc="Camera angle (deg)", from_=0, to=359)
        self._camera_angle.pack(side=tk.LEFT)

        self._guiding_button.pack(side=tk.TOP)

        ttk.Separator(self._main_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)

        plot_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        plot_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self._guiding_plot = RunningPlot2D(frame=plot_frame)
        self._guiding_plot.pack(side=tk.LEFT)

        self._star_position_calculator = StarPositionCalculator(display_callback=self._handle_new_rect,
                                                                movement_callback=self._handle_new_movement,
                                                                rect_size=RECTANGLE_SIZE)
        self._image_consumer = ImageConsumer(queue=self._image_queue,
                                             calculate_callback=self._star_position_calculator.calculate,
                                             display_callback=lambda x: self._image_canvas.update(log_image(x),
                                                                                                  cmap="gist_heat"))
        self._commander = ErrorHandler(read_queue=self._serial_in,
                                       write_queue=self._serial_out,
                                       scale_getter=self._read_micro_spins,
                                       angle_getter=lambda: float(self._camera_angle.get_value()))
        self._add_task(timeout_s=1, f=self._check_if_diagnostics_alive)
        self._add_task(timeout_s=CAMERA_TEMPERATURE_UPDATE_TIME_S, f=self._get_camera_temp)

    def _get_camera_temp(self):
        if self._diagnostics_queue is not None and self._camera is not None:
            self._diagnostics_queue.put(self._camera.get_camera_temperature())

    def _check_if_diagnostics_alive(self):
        if self._diagnostics_process is None:
            return
        if self._diagnostics_kill_event.is_set() or not self._diagnostics_process.is_alive():
            self._diagnostics_process.join()
            self._diagnostics_process = None
            self._diagnostics_kill_event.clear()
            print("Successfully joined diagnostics!")
            self._diagnostic_button.configure(state=tk.NORMAL)

    def _diagnostics(self):
        self._diagnostics_process = Process(target=diagnostics_gui,
                                            args=(self._diagnostics_queue, self._diagnostics_kill_event,))
        self._diagnostics_process.start()
        self._diagnostic_button.configure(state=tk.DISABLED)

    def _read_micro_spins(self):
        sx = float(self._ra_microsteps_spin.get_value())
        sy = float(self._dec_microsteps_spin.get_value())
        return sx, sy

    def _handle_new_rect(self, r):
        self._image_canvas.set_rectangle(r)

    def _handle_new_movement(self, p):
        scale = float(self._pixel_spin.get_value()) * 206.3 / float(self._focal_spin.get_value())
        t, x, y = p
        x = x*scale
        y = y*scale
        self._guiding_plot.add_point((t, x, y))
        self._commander.handle_error(x, y)

    def _start_guide(self):
        self._commander.start()
        self._guiding_button.configure(text="Stop sending commands")

    def _stop_guide(self):
        self._commander.stop()
        self._guiding_button.configure(text="Start sending commands")

    def _clear_selection(self):
        self._calculate_button.configure(state=tk.DISABLED)
        self._clear_selection_button.configure(state=tk.DISABLED)
        self._image_canvas.clear_rectangle()

    def _new_selection(self, rectangle):
        self._calculate_button.configure(state=tk.NORMAL)
        self._clear_selection_button.configure(state=tk.NORMAL)
        self._star_position_calculator.set_rect(rectangle)

    def _start_calculating(self):
        self._guiding_plot.clear()
        self._calculate_button.configure(text="Stop calculating", command=self._stop_calculating)
        self._guiding_button.configure(state=tk.NORMAL)
        self._star_position_calculator.start()

    def _stop_calculating(self):
        self._calculate_button.configure(text="Start calculating", command=self._start_calculating)
        self._star_position_calculator.stop()
        self._guiding_button.configure(state=tk.DISABLED)

    def _killme(self):
        self._stop_simulation()
        if self._diagnostics_process is not None:
            if self._diagnostics_process.is_alive():
                print("Send kill event to diagnostics!")
                self._diagnostics_kill_event.set()
            self._diagnostics_process.join()
            print("Successfully joined diagnostics!")

        super(GuidingProcessGUI, self)._killme()

    def _start_simulation(self):
        self._sim_provider = TimedFileImageProvider(delay=int(self._interval_chooser.get_value()),
                                                    directory=self._sim_dir_chooser.get_dir(),
                                                    queue=self._image_queue)
        self._sim_provider.start()
        self._image_consumer.start()
        self._sim_button.configure(text="Stop simulation", command=self._stop_simulation)

    def _stop_simulation(self):
        if self._sim_provider is not None:
            self._sim_provider.stop()
        self._image_consumer.stop()
        print("Simulation ended successfully!")
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
        self._diagnostic_button.configure(state=tk.NORMAL)
