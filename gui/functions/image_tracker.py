import time
from functions.recent_files_provider import RecentImagesProvider, is_file_fits
from functions.sharpcap_capture import get_latest_sharpcap_images_dir, get_latest_sharpcap_capture_dir
from functions.tracking_processor import TrackingProcessor
import tkinter as tk
from tkinter import filedialog

"""
suggested dir: [name] [choose this] [other dir...] [start/stop]
|                 |  |             |
|    image        |  |     plot    |
|                 |  |             |
"""


class ImageTrackerGUI:
    def __init__(self, frame):
        suggested_frame = tk.Frame(frame, highlightbackground="black", highlightthickness=1)
        suggested_frame.pack(side=tk.TOP)
        self._suggested = tk.StringVar(value=get_latest_sharpcap_images_dir())
        self._first_label = tk.Label(suggested_frame, text="Chosen image dir:", font=('calibre', 10, 'bold'))
        self._first_label.pack(side=tk.LEFT)
        self._suggested_label = tk.Label(suggested_frame, textvariable=self._suggested, font=('calibre', 10, 'bold'))
        self._suggested_label.pack(side=tk.LEFT)
        self._suggested_button = tk.Button(suggested_frame, text='Change...', command=self._change_dir)
        self._suggested_button.pack(side=tk.LEFT)

        self._start_button = tk.Button(suggested_frame, text='Start', command=self._start)
        self._start_button.pack(side=tk.LEFT)
        self._processor = TrackingProcessor()
        self._file_provider = RecentImagesProvider(self._processor, is_file_fits)

    def _start(self):
        self._file_provider.start(self._suggested.get())

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
