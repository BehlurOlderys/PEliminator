from tkinter import ttk
from functions.event_logger import EventLogger
from functions.dec_estimator import DecEstimator
from functions.dec_corrector import DecCorrector
from functions.recent_files_provider import RecentImagesProvider, is_file_fits
from functions.image_tracker import ImageTrackerGUI

import tkinter as tk


root = tk.Tk()
event_logger = EventLogger()
root.title("PEliminator Star Tracking")


class DummyReader:
    def write_string(self, s):
        print(f"This should write >>{s}<< to serial!")


reader = DummyReader()
de = DecEstimator()
dc = DecCorrector(de, reader)
dec_corrector = RecentImagesProvider(dc, is_file_fits)

root.geometry("1080x480")
tabs = ttk.Notebook(root)
tabs.pack(expand=True)

tracking_tab = tk.Frame(tabs)
tracking_tab.pack(fill='both', expand=True)
tabs.add(tracking_tab, text="Tracking")

settings_tab = tk.Frame(tabs)
settings_tab.pack(fill='both', expand=True)
tabs.add(settings_tab, text="Settings")

log_tab = tk.Frame(tabs)
log_tab.pack(fill='both', expand=True)
tabs.add(log_tab, text="Command log")

optics_f_var = tk.StringVar(value=650)
optics_pixel_var = tk.StringVar(value=2.9)
settings_frame = tk.Frame(settings_tab, highlightbackground="black", highlightthickness=1)
settings_frame.pack(side=tk.TOP)

optics_label = tk.Label(settings_frame, text='Image scale: f[mm]=', font=('calibre', 10, 'bold'))
optics_label.pack(side=tk.LEFT)
optics_f_spin = ttk.Spinbox(settings_frame, from_=0, to=10000, width=5, textvariable=optics_f_var)
optics_f_spin.pack(side=tk.LEFT)
optics_pixel_label = tk.Label(settings_frame, text='px[um] =', font=('calibre', 10, 'bold'))
optics_pixel_label.pack(side=tk.LEFT)
optics_pixel_spin = ttk.Spinbox(settings_frame, from_=0, to=99, width=5,
                                textvariable=optics_pixel_var, format='%.2f', increment=0.1)
optics_pixel_spin.pack(side=tk.LEFT)


tracking_gui = ImageTrackerGUI(tracking_tab)

root.mainloop()
print("End of main loop!")

event_logger.kill()

reader.kill()
tracking_gui.kill()

