from .pe_base_widget import AppendablePeBaseWidget
import tkinter as tk
from tkinter import ttk
from package.utils.zwo_asi_camera_grabber import ASICamera


empty_camera_list_string = "<no zwo cameras here>"


class CameraChooser(AppendablePeBaseWidget):
    def __init__(self, on_connect, **kwargs):
        super(CameraChooser, self).__init__(**kwargs)
        self._camera: ASICamera = None
        self._camera_id = 0
        self._available_cameras = ASICamera.get_cameras_list()
        if not self._available_cameras:
            self._available_cameras = [empty_camera_list_string]

        self._camera_choice = tk.StringVar(value=self._available_cameras[0])

        self._combobox = ttk.Combobox(self._frame, textvariable=self._camera_choice,
                                      values=self._available_cameras, style="B.TCombobox")
        self._combobox.pack(side=tk.RIGHT)

        self._choose_camera_button = ttk.Button(self._frame, text="Connect", command=self._connect, style="B.TButton")
        self._choose_camera_button.pack(side=tk.LEFT)

        self._refresh_camera_button = ttk.Button(self._frame, text="Refresh", command=self._refresh_cameras,
                                                 style="B.TButton")
        self._refresh_camera_button.pack(side=tk.RIGHT)

        self._on_connect = on_connect

    def _refresh_cameras(self):
        self._available_cameras = ASICamera.get_cameras_list()
        print(f"Available = {self._available_cameras}")
        if not self._available_cameras:
            self._available_cameras = [empty_camera_list_string]

        self._camera_choice = tk.StringVar(value=self._available_cameras[0])
        self._combobox.config(values=self._available_cameras)
        self._combobox.set(self._camera_choice.get())

    def get_camera(self):
        return self._camera

    def get_camera_id(self):
        return self._camera_id

    def _connect(self):
        camera_string = self._camera_choice.get()
        if empty_camera_list_string == camera_string:
            print("Nothing to connect here...")
            return
        self._camera_id = self._available_cameras.index(camera_string)
        print(f"Starting camera {camera_string} which has index {self._camera_id}...")
        self._camera = ASICamera(self._camera_id)
        self._camera.print_info()
        self._choose_camera_button.configure(state=tk.DISABLED)
        self._on_connect(self._camera, self._camera_id)
