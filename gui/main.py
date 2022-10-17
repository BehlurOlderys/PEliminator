from tkinter import ttk
from functions.global_settings import possible_units
from functions.event_logger import EventLogger
from functions.coordinate_mover import CoordinateMover
from functions.serial_reader import SerialReader, get_available_com_ports
from functions.camera_encoder import CameraEncoderGUI
from functions.session_plan import SessionPlanGUI

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

# web_server = get_web_server(mover)

root.geometry("800x480")
tabs = ttk.Notebook(root)
tabs.pack(expand=True)

mount_tab = tk.Frame(tabs)
mount_tab.pack(fill='both', expand=True)
tabs.add(mount_tab, text="Mount control")

plan_tab = tk.Frame(tabs)
plan_gui = SessionPlanGUI(plan_tab, mover)
plan_tab.pack(fill='both', expand=True)
tabs.add(plan_tab, text="Session plan")

correction_tab = tk.Frame(tabs)
encoder_gui = CameraEncoderGUI(correction_tab, reader)
correction_tab.pack(fill='both', expand=True)
tabs.add(correction_tab, text="Corrections")

settings_tab = tk.Frame(tabs)
settings_tab.pack(fill='both', expand=True)
tabs.add(settings_tab, text="Settings")

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


root.mainloop()
print("End of main loop!")
event_logger.kill()
reader.kill()
encoder_gui.kill()
if reader.is_connected():
    serial_thread.join()
