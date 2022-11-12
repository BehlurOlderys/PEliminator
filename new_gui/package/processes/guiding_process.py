from .child_process import ChildProcessGUI
from package.widgets.dir_chooser import DirChooser
from package.widgets.labeled_input import LabeledInput
from package.utils.image_consumer import ImageConsumer
from package.widgets.running_plot import RunningPlot
from package.utils.zwo_asi_camera_grabber import ASICamera
from tkinter import ttk
import tkinter as tk
from package.utils.image_provider import TimedFileImageProvider
from queue import Queue
from package.widgets.image_canvas import ImageCanvasWithRectangle
import numpy as np
from package.utils.star_position_calculator import StarPositionCalculator


RECTANGLE_SIZE = 60
NO_IMAGE_FILE = "data/no_image.png"
empty_camera_list_string = "<no zwo cameras here>"
initial_test_dir = "C:/Users/Florek/Desktop/workspace/PEliminator/gui/data/png_do_testow/Capture_00050"


def log_image(image):
    c = 255 / np.log(1 + np.max(image))
    log_image = c * (np.log(image + 1))
    return np.array(log_image, dtype=np.uint8)


class GuidingProcessGUI(ChildProcessGUI):
    def __init__(self, serial_out_queue, serial_in_queue, *args, **kwargs):
        super(GuidingProcessGUI, self).__init__(title="Guiding", *args, **kwargs)
        ASICamera.initialize_library()
        self._serial_out = serial_out_queue
        self._serial_in = serial_in_queue
        self._image_queue = Queue()
        self._sim_provider = None
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
                                            command=self._estimate, style="B.TButton")
        self._guiding_button.pack(side=tk.TOP)

        ttk.Separator(self._main_frame, orient=tk.HORIZONTAL, style="B.TSeparator").pack(side=tk.TOP, ipady=10)

        plot_frame = ttk.Frame(self._main_frame, style="B.TFrame")
        plot_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self._guiding_plot = RunningPlot(frame=plot_frame)
        self._guiding_plot.pack(side=tk.LEFT)

        self._lolvalue = 10
        self._lolbutton = ttk.Button(plot_frame, text="LOL", style="B.TButton", command=self._lol)
        self._lolbutton.pack(side=tk.TOP)

        self._star_position_calculator = StarPositionCalculator(display_callback=self._handle_new_rect,
                                                                movement_callback=self._handle_new_movement,
                                                                rect_size=RECTANGLE_SIZE)
        self._image_consumer = ImageConsumer(queue=self._image_queue,
                                             calculate_callback=self._star_position_calculator.calculate,
                                             display_callback=lambda x: self._image_canvas.update(log_image(x),
                                                                                                  cmap="gist_heat"))

    def _handle_new_rect(self, r):
        self._image_canvas.set_rectangle(r)

    def _handle_new_movement(self, p):
        self._guiding_plot.add_point(p)

    def _lol(self):
        self._guiding_plot.add_point((self._lolvalue, 4, -3))
        self._lolvalue += 10

    def _estimate(self):
        pass

    def _clear_selection(self):
        self._calculate_button.configure(state=tk.DISABLED)
        self._clear_selection_button.configure(state=tk.DISABLED)
        self._image_canvas.clear_rectangle()

    def _new_selection(self, rectangle):
        self._calculate_button.configure(state=tk.NORMAL)
        self._clear_selection_button.configure(state=tk.NORMAL)
        self._star_position_calculator.set_rect(rectangle)

    def _start_calculating(self):
        self._calculate_button.configure(text="Stop calculating", command=self._stop_calculating)
        self._star_position_calculator.start()

    def _stop_calculating(self):
        self._calculate_button.configure(text="Start calculating", command=self._start_calculating)
        self._star_position_calculator.stop()


    def _killme(self):
        self._stop_simulation()
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
