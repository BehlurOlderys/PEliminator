from package.widgets.application import SimpleGuiApplication
from package.utils.zwo_asi_camera_grabber import ASICamera
from tkinter import ttk
import tkinter as tk

empty_camera_list_string = "<no zwo cameras here>"


class GuidingProcessGUI(SimpleGuiApplication):
    def __init__(self, serial_out_queue, serial_in_queue, kill_event, *args, **kwargs):
        super(GuidingProcessGUI, self).__init__(title="Guiding", *args, **kwargs)
        ASICamera.initialize_library()
        self._serial_out = serial_out_queue
        self._serial_in = serial_in_queue
        self._kill_event = kill_event
        self._root.protocol('WM_DELETE_WINDOW', self._killme)  # root is your root window

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

    def _killme(self):
        self._kill_event.set()
        self._root.destroy()

    def _connect(self):
        camera_string = self._camera_choice.get()
        if empty_camera_list_string == camera_string:
            print("Nothing to connect here...")
            return
        self._camera_id = self._available_cameras.index(camera_string)
        print(f"Starting camera {camera_string} which has index {self._camera_id}...")
        self._camera = ASICamera(self._camera_id)
        self._choose_camera_button.configure(state=tk.DISABLED)
