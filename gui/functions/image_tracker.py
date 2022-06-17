from functions.recent_files_provider import RecentImagesProvider, is_file_fits
from functions.offline_images_provider import OfflineImagesProvider
from functions.sharpcap_capture import get_latest_sharpcap_images_dir, get_latest_sharpcap_capture_dir
from functions.tracking_processor import TrackingProcessor
from functions.image_tracking_plot import ImageTrackingPlot
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

"""
suggested dir: [name] [choose this] [other dir...] [start/stop]
|                 |  |             |
|    image        |  |     plot    |
|                 |  |             |
"""


offline_tracking = "Offline"
online_tracking = "Online"
combo_values = [offline_tracking, online_tracking]


class ImageTrackerGUI:

    def __init__(self, frame):
        self._feedback_var = tk.StringVar(value=0)
        self._combo_choice = tk.StringVar(value=offline_tracking)
        try:
            self._suggested = tk.StringVar(value=get_latest_sharpcap_images_dir())
        except:
            self._suggested = tk.StringVar(value="")

        suggested_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        suggested_frame.pack(side=tk.TOP)

        control_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        control_frame.pack(side=tk.TOP)

        self._first_label = tk.Label(suggested_frame, text="Chosen image dir:", font=('calibre', 10, 'bold'))
        self._first_label.pack(side=tk.LEFT)
        self._suggested_label = tk.Label(suggested_frame, textvariable=self._suggested, font=('calibre', 10, 'bold'))
        self._suggested_label.pack(side=tk.LEFT)
        self._suggested_button = tk.Button(suggested_frame, text='Change...', command=self._change_dir)
        self._suggested_button.pack(side=tk.LEFT)

        self._feedback_label = tk.Label(control_frame, text="Current feedback value:", font=('calibre', 10, 'bold'))
        self._feedback_label.pack(side=tk.LEFT)
        self._feedback_display = tk.Entry(control_frame, textvariable=self._feedback_var)
        self._feedback_display.pack(side=tk.LEFT)
        self._send_button = tk.Button(control_frame, text='Send', command=self._send)
        self._send_button.pack(side=tk.LEFT)

        self._combobox = ttk.Combobox(control_frame, textvariable=self._combo_choice, values=combo_values)
        self._combobox.pack(side=tk.LEFT)
        self._start_button = tk.Button(control_frame, text='Start', command=self._start)
        self._start_button.pack(side=tk.LEFT)
        self._reset_button = tk.Button(control_frame, text='Reset', command=self.reset)
        self._reset_button.pack(side=tk.LEFT)

        self._plot = ImageTrackingPlot(frame=frame)
        self._processor = TrackingProcessor(self._plot, self._feedback_var)
        self._file_provider = None

    def _send(self):
        self._processor.send_feedback()

    def _start(self):
        tracking_type = self._combobox.get()
        self._file_provider = OfflineImagesProvider(self._processor, is_file_fits) \
            if tracking_type == offline_tracking \
            else RecentImagesProvider(self._processor, is_file_fits)
        self._file_provider.start(self._suggested.get())

    def reset(self):
        self._processor.reset()

    def _change_dir(self):
        new_dir = filedialog.askdirectory(title="Open dir with images for tracking",
                                          initialdir=get_latest_sharpcap_capture_dir())
        if not new_dir:
            print("No directory is chosen!")
            return
        print(f"Dir chosen = {new_dir}")
        self._suggested.set(new_dir)

    def kill(self):
        self._file_provider.kill()


if __name__ == "__main__":
    print(get_latest_sharpcap_images_dir())
