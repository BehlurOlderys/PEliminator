from tkinter import scrolledtext, ttk
from functions.global_settings import possible_units
from functions.event_logger import EventLogger
from functions.coordinate_mover import CoordinateMover
from functions.serial_reader import SerialReader, get_available_com_ports
from functions.serial_handlers.all_handlers import encoder_data
from functions.online_analyzer import OnlineAnalyzer, get_correction_from_mount
from functions.server import get_web_server
from functions.dec_estimator import DecEstimator
from functions.dec_corrector import DecCorrector
from functions.recent_files_provider import RecentImagesProvider, is_file_fits
from functions.camera_encoder import CameraEncoder
from functions.image_tracker import ImageTrackerGUI


import time
from threading import Thread
import tkinter as tk


class ConnectionManager:
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
        connection_thread.start()


root = tk.Tk()
event_logger = EventLogger()
available_ports = get_available_com_ports()
com_port_choice = tk.StringVar(value=available_ports[0])

reader = SerialReader()
serial_thread = Thread(target=reader.loop)
connection_manager = ConnectionManager(event_logger, reader, serial_thread, com_port_choice)
root.title("PEliminator GUI")
mover = CoordinateMover(reader, event_logger)
de = DecEstimator()
dc = DecCorrector(de, reader)
dec_corrector = RecentImagesProvider(dc, is_file_fits)
dummy_effector_label = "Dummy output"
serial_effector_label = "Serial output"
available_effectors = [dummy_effector_label, serial_effector_label]

# web_server = get_web_server(mover)

root.geometry("800x480")
tabs = ttk.Notebook(root)
tabs.pack(expand=True)

mount_tab = tk.Frame(tabs)
mount_tab.pack(fill='both', expand=True)
tabs.add(mount_tab, text="Mount control")

correction_tab = tk.Frame(tabs)
correction_tab.pack(fill='both', expand=True)
tabs.add(correction_tab, text="Corrections")

tracking_tab = tk.Frame(tabs)
tracking_tab.pack(fill='both', expand=True)
tabs.add(tracking_tab, text="Tracking")

settings_tab = tk.Frame(tabs)
settings_tab.pack(fill='both', expand=True)
tabs.add(settings_tab, text="Settings")

log_tab = tk.Frame(tabs)
log_tab.pack(fill='both', expand=True)
tabs.add(log_tab, text="Command log")

connect_frame = tk.Frame(mount_tab, highlightbackground="black", highlightthickness=1)
connect_frame.pack(side=tk.TOP)

combobox = ttk.Combobox(connect_frame, textvariable=com_port_choice, values=available_ports)
combobox.pack(side=tk.RIGHT)

choose_port_button = tk.Button(connect_frame, text="Connect", command=connection_manager.connect_to_chosen_port)
choose_port_button.pack(side=tk.LEFT)

ttk.Separator(mount_tab, orient=tk.HORIZONTAL).pack(side=tk.TOP, ipady=10)

settings_frame = tk.Frame(settings_tab, highlightbackground="black", highlightthickness=1)
settings_frame.pack(side=tk.TOP)

optics_label = tk.Label(settings_frame, text='Image scale: f[mm]=', font=('calibre', 10, 'bold'))
optics_label.pack(side=tk.LEFT)
optics_f_spin = ttk.Spinbox(settings_frame, from_=0, to=10000, width=5, textvariable=mover.vars["optics_f"])
optics_f_spin.pack(side=tk.LEFT)
optics_pixel_label = tk.Label(settings_frame, text='px[um] =', font=('calibre', 10, 'bold'))
optics_pixel_label.pack(side=tk.LEFT)
optics_pixel_spin = ttk.Spinbox(settings_frame, from_=0, to=99, width=5,
                                textvariable=mover.vars["optics_pixel"], format='%.2f', increment=0.1)
optics_pixel_spin.pack(side=tk.LEFT)

ttk.Separator(mount_tab, orient=tk.HORIZONTAL).pack(side=tk.TOP, ipady=10)

precise_frame = tk.Frame(mount_tab, highlightbackground="black", highlightthickness=1)
precise_frame.pack(side=tk.TOP)

precise_ra_desc_label = tk.Label(precise_frame, text='Precise move: RA', font=('calibre', 10, 'bold'))
precise_ra_desc_label.pack(side=tk.LEFT)
precise_ra_ctrl_spin = ttk.Spinbox(precise_frame, from_=-9999, to=9999, width=5, textvariable=mover.vars["ra_precise"])
precise_ra_ctrl_spin.pack(side=tk.LEFT)
precise_ra_ctrl_units_label = tk.Label(precise_frame, text='Units:', font=('calibre', 10, 'bold'))
precise_ra_ctrl_units_label.pack(side=tk.LEFT)
precise_ra_ctrl_combo = ttk.Combobox(precise_frame, values=possible_units, width=7,
                                     textvariable=mover.vars["ra_precise_units"])
precise_ra_ctrl_combo.pack(side=tk.LEFT)
precise_ra_ctrl_button = tk.Button(precise_frame, text='<MOVE', command=mover.move_ra)
precise_ra_ctrl_button.pack(side=tk.LEFT)

precise_dec_label = tk.Label(precise_frame, text='     DEC', font=('calibre', 10, 'bold'))
precise_dec_label.pack(side=tk.LEFT)
precise_dec_spin = ttk.Spinbox(precise_frame, from_=-9999, to=9999, width=5, textvariable=mover.vars["dec_precise"])
precise_dec_spin.pack(side=tk.LEFT)
precise_dec_units_label = tk.Label(precise_frame, text='Units:', font=('calibre', 10, 'bold'))
precise_dec_units_label.pack(side=tk.LEFT)
precise_dec_combo = ttk.Combobox(precise_frame, values=possible_units, width=7,
                                 textvariable=mover.vars["dec_precise_units"])
precise_dec_combo.pack(side=tk.LEFT)
precise_dec_button = tk.Button(precise_frame, text='<MOVE', command=mover.move_dec)
precise_dec_button.pack(side=tk.LEFT)

ttk.Separator(mount_tab, orient=tk.HORIZONTAL).pack(side=tk.TOP, ipady=10)

set_coordinates_frame = tk.Frame(mount_tab, highlightbackground="black", highlightthickness=1)
set_coordinates_frame.pack(side=tk.TOP)

ra_hours_label = tk.Label(set_coordinates_frame, text='RA coordinates: H', font=('calibre', 10, 'bold'))
ra_hours_label.pack(side=tk.LEFT)
ra_hours_spin = ttk.Spinbox(set_coordinates_frame, from_=0, to=23, width=3,
                            textvariable=mover.vars["ra_hours"], wrap=True)
ra_hours_spin.pack(side=tk.LEFT)

ra_minutes_label = tk.Label(set_coordinates_frame, text='M', font=('calibre', 10, 'bold'))
ra_minutes_label.pack(side=tk.LEFT)
ra_minutes_spin = ttk.Spinbox(set_coordinates_frame, from_=0, to=59, width=3,
                              textvariable=mover.vars["ra_minutes"], wrap=True)
ra_minutes_spin.pack(side=tk.LEFT)

ra_seconds_label = tk.Label(set_coordinates_frame, text='S', font=('calibre', 10, 'bold'))
ra_seconds_label.pack(side=tk.LEFT)
ra_seconds_spin = ttk.Spinbox(set_coordinates_frame, from_=0, to=59, width=3,
                              textvariable=mover.vars["ra_seconds"], wrap=True)
ra_seconds_spin.pack(side=tk.LEFT)

set_ra_button = tk.Button(set_coordinates_frame, text='SET', command=mover.set_ra)
set_ra_button.pack(side=tk.LEFT)

goto_ra_button = tk.Button(set_coordinates_frame, text='GoTo', command=mover.goto_ra)
goto_ra_button.pack(side=tk.LEFT)

halt_ra_button = tk.Button(set_coordinates_frame, text='HALT!', command=mover.halt)
halt_ra_button.pack(side=tk.LEFT)

dec_degrees_label = tk.Label(set_coordinates_frame, text='DEC coordinates: H', font=('calibre', 10, 'bold'))
dec_degrees_label.pack(side=tk.LEFT)
dec_degrees_spin = ttk.Spinbox(set_coordinates_frame, from_=-89, to=89, width=3,
                               textvariable=mover.vars["dec_degrees"], wrap=True)
dec_degrees_spin.pack(side=tk.LEFT)

dec_minutes_label = tk.Label(set_coordinates_frame, text='M', font=('calibre', 10, 'bold'))
dec_minutes_label.pack(side=tk.LEFT)
dec_minutes_spin = ttk.Spinbox(set_coordinates_frame, from_=0, to=59, width=3,
                               textvariable=mover.vars["dec_minutes"], wrap=True)
dec_minutes_spin.pack(side=tk.LEFT)

dec_seconds_label = tk.Label(set_coordinates_frame, text='S', font=('calibre', 10, 'bold'))
dec_seconds_label.pack(side=tk.LEFT)
dec_seconds_spin = ttk.Spinbox(set_coordinates_frame, from_=0, to=59, width=3,
                               textvariable=mover.vars["dec_seconds"], wrap=True)
dec_seconds_spin.pack(side=tk.LEFT)

set_dec_button = tk.Button(set_coordinates_frame, text='SET', command=mover.set_dec)
set_dec_button.pack(side=tk.LEFT)

goto_dec_button = tk.Button(set_coordinates_frame, text='GoTo', command=mover.goto_dec)
goto_dec_button.pack(side=tk.LEFT)

halt_dec_button = tk.Button(set_coordinates_frame, text='HALT!', command=mover.halt)
halt_dec_button.pack(side=tk.LEFT)

ttk.Separator(mount_tab, orient=tk.HORIZONTAL).pack(side=tk.TOP, ipady=10)

drift_frame = tk.Frame(mount_tab, highlightbackground="black", highlightthickness=1)
drift_frame.pack(side=tk.TOP)
dec_drift_label = tk.Label(drift_frame, text='DEC drift value: ', font=('calibre', 10, 'bold'))
dec_drift_label.pack(side=tk.LEFT)

dec_drift_spin = ttk.Spinbox(drift_frame, from_=-999, to=999, width=4, textvariable=mover.vars["dec_drift"], wrap=True)
dec_drift_spin.pack(side=tk.LEFT)

dec_drift_units_label = tk.Label(drift_frame, text='arcsek / 100s', font=('calibre', 10, 'bold'))
dec_drift_units_label.pack(side=tk.LEFT)

dec_drift_button_set = tk.Button(drift_frame, text='Set drift value', command=mover.set_dec_drift)
dec_drift_button_set.pack(side=tk.LEFT)

dec_drift_button_start = tk.Button(drift_frame, text='Compensate!', command=mover.start_dec_drift)
dec_drift_button_start.pack(side=tk.LEFT)

dec_drift_button_stop = tk.Button(drift_frame, text='STOP', command=mover.stop_dec_drift)
dec_drift_button_stop.pack(side=tk.LEFT)

ttk.Separator(mount_tab, orient=tk.HORIZONTAL).pack(side=tk.TOP, ipady=10)

online_frame = tk.Frame(correction_tab, highlightbackground="black", highlightthickness=1)
online_frame.pack(side=tk.TOP)

ttk.Separator(correction_tab, orient=tk.HORIZONTAL).pack(side=tk.TOP, ipady=10)

camera_encoder_frame = tk.Frame(correction_tab, highlightbackground="black", highlightthickness=1)
camera_encoder_frame.pack(side=tk.TOP)


def write_correction(correction):
    arrays_length, correction_bytes = correction
    if not reader.is_connected():
        event_logger.log_event("Mount is not connected!\n")
        return
    event_logger.log_event("Entering new correction for mount!\n")
    reader.write_bytes(f"ENTER_CORR {arrays_length}\n".encode() + correction_bytes)
    time.sleep(2)


onliner = OnlineAnalyzer(encoder_data, write_correction, reader)
online_button = tk.Button(online_frame, text="Start online...", command=onliner.start)
online_button.pack(side=tk.LEFT)

correct_dec_button = tk.Button(online_frame, text="START dec correction")


def start_dec_correction():
    dec_corrector.start()
    correct_dec_button.configure(text="STOP dec correction", command=stop_dec_correction)


def stop_dec_correction():
    dec_corrector.kill()
    correct_dec_button.configure(text="START dec correction", command=start_dec_correction)


correct_dec_button.configure(command=start_dec_correction)
correct_dec_button.pack(side=tk.LEFT)

onliner_historic = OnlineAnalyzer(None, write_correction)
online_history_button = tk.Button(online_frame, text="Start historical analysis...", command=onliner_historic.start)
online_history_button.pack(side=tk.LEFT)


class CameraEncoderGUI:
    def __init__(self, frame):
        self._camera_encoder = CameraEncoder(None)
        self._choice = tk.StringVar(value=available_effectors[0])
        self._reset_button = tk.Button(frame, text="Reset camera encoder",
                                       command=self._camera_encoder.reset())
        self._reset_button.pack(side=tk.RIGHT)
        self._amendment = tk.StringVar(value=0)
        self._amendment_spin = ttk.Spinbox(frame, from_=-999, to=999,
                                           width=5, textvariable=self._amendment)
        self._amendment_spin.pack(side=tk.RIGHT)
        self._amend_button = tk.Button(frame, text="Set encoder amendment",
                                       command=self._camera_encoder.set_amend(
                                                int(self._amendment.get()))
                                      )
        self._amend_button.pack(side=tk.RIGHT)

        self._button = tk.Button(frame,
                                 text="Start camera encoder", command=self._start_action)
        self._button.pack(side=tk.LEFT)

        self._combobox = ttk.Combobox(frame, textvariable=self._choice,
                                      values=available_effectors)
        self._combobox.pack(side=tk.RIGHT)

    def kill(self):
        self._camera_encoder.kill()

    def _start_action(self):
        effector = reader if self._choice.get() == serial_effector_label else None
        self._camera_encoder = CameraEncoder(effector)
        self._camera_encoder.start()
        self._button.configure(text="Stop camera encoder", command=self._stop_action)

    def _stop_action(self):
        self._camera_encoder.kill()
        self._camera_encoder = None
        self._button.configure(text="Start camera encoder", command=self._start_action)


encoder_gui = CameraEncoderGUI(camera_encoder_frame)


def get_and_log_correction():
    data = get_correction_from_mount(reader)
    if data is None:
        event_logger.log_event(f"Mount is not connected!\n")
    elif not data:
        event_logger.log_event(f"Getting correction data timed out!\n")
    else:
        event_logger.log_event(f"Obtained recent correction data from mount:\n{data}\n")


check_current_correction_button = tk. Button(online_frame, text="Get currect correction",
                                             command=get_and_log_correction)
check_current_correction_button.pack(side=tk.RIGHT)

ttk.Separator(mount_tab, orient=tk.HORIZONTAL).pack(side=tk.TOP, ipady=10)


tracking_gui = ImageTrackerGUI(tracking_tab)


serial_log = scrolledtext.ScrolledText(log_tab,
                                       font=('calibre', 10, 'normal'),
                                       background='black',
                                       foreground="red")
serial_log.pack(side=tk.BOTTOM, expand=True)
serial_log.configure(state='disabled')

logger_thread = Thread(target=lambda: event_logger.run(serial_log))
logger_thread.start()

# web_thread = Thread(target=web_server.serve_forever)
# web_thread.start()

root.mainloop()
print("End of main loop!")
# web_server.shutdown()
event_logger.kill()
onliner.kill()
onliner_historic.kill()
reader.kill()
encoder_gui.kill()
tracking_gui.kill()
logger_thread.join()
if reader.is_connected():
    serial_thread.join()
# web_thread.join()
# web_server.server_close()
