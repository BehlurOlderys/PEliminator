
from threading import Thread
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from functions.global_settings import possible_units
from functions.event_logger import EventLogger
from functions.coordinate_mover import CoordinateMover
from functions.serial_reader import SerialReader


if __name__ == "__main__":
    event_logger = EventLogger()
    reader = SerialReader('COM8')
    # reader = SerialReader(None)
    root = tk.Tk()
    root.title("PEliminator GUI")
    mover = CoordinateMover(reader, event_logger)

    root.geometry("800x480")

    settings_frame = tk.Frame(root, highlightbackground="black", highlightthickness=1)
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

    ttk.Separator(root, orient=tk.HORIZONTAL).pack(side=tk.TOP, ipady=10)

    precise_frame = tk.Frame(root, highlightbackground="black", highlightthickness=1)
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
    precise_dec_combo = ttk.Combobox(precise_frame, values=possible_units, width=7, textvariable=mover.vars["dec_precise_units"])
    precise_dec_combo.pack(side=tk.LEFT)
    precise_dec_button = tk.Button(precise_frame, text='<MOVE', command=mover.move_dec)
    precise_dec_button.pack(side=tk.LEFT)

    ttk.Separator(root, orient=tk.HORIZONTAL).pack(side=tk.TOP, ipady=10)

    set_coordinates_frame = tk.Frame(root, highlightbackground="black", highlightthickness=1)
    set_coordinates_frame.pack(side=tk.TOP)

    ra_hours_label = tk.Label(set_coordinates_frame, text='RA coordinates: H', font=('calibre', 10, 'bold'))
    ra_hours_label.pack(side=tk.LEFT)
    ra_hours_spin = ttk.Spinbox(set_coordinates_frame, from_=0, to=23, width=3, textvariable=mover.vars["ra_hours"], wrap=True)
    ra_hours_spin.pack(side=tk.LEFT)

    ra_minutes_label = tk.Label(set_coordinates_frame, text='M', font=('calibre', 10, 'bold'))
    ra_minutes_label.pack(side=tk.LEFT)
    ra_minutes_spin = ttk.Spinbox(set_coordinates_frame, from_=0, to=59, width=3, textvariable=mover.vars["ra_minutes"], wrap=True)
    ra_minutes_spin.pack(side=tk.LEFT)

    ra_seconds_label = tk.Label(set_coordinates_frame, text='S', font=('calibre', 10, 'bold'))
    ra_seconds_label.pack(side=tk.LEFT)
    ra_seconds_spin = ttk.Spinbox(set_coordinates_frame, from_=0, to=59, width=3, textvariable=mover.vars["ra_seconds"], wrap=True)
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
    dec_minutes_spin = ttk.Spinbox(set_coordinates_frame, from_=0, to=59, width=3, textvariable=mover.vars["dec_minutes"], wrap=True)
    dec_minutes_spin.pack(side=tk.LEFT)

    dec_seconds_label = tk.Label(set_coordinates_frame, text='S', font=('calibre', 10, 'bold'))
    dec_seconds_label.pack(side=tk.LEFT)
    dec_seconds_spin = ttk.Spinbox(set_coordinates_frame, from_=0, to=59, width=3, textvariable=mover.vars["dec_seconds"], wrap=True)
    dec_seconds_spin.pack(side=tk.LEFT)

    set_dec_button = tk.Button(set_coordinates_frame, text='SET', command=mover.set_dec)
    set_dec_button.pack(side=tk.LEFT)

    goto_dec_button = tk.Button(set_coordinates_frame, text='GoTo', command=mover.goto_dec)
    goto_dec_button.pack(side=tk.LEFT)

    halt_dec_button = tk.Button(set_coordinates_frame, text='HALT!', command=mover.halt)
    halt_dec_button.pack(side=tk.LEFT)

    ttk.Separator(root, orient=tk.HORIZONTAL).pack(side=tk.TOP, ipady=10)

    drift_frame = tk.Frame(root, highlightbackground="black", highlightthickness=1)
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

    ttk.Separator(root, orient=tk.HORIZONTAL).pack(side=tk.TOP, ipady=10)

    serial_log = scrolledtext.ScrolledText(root,
                                           font=('calibre', 10, 'normal'),
                                           background='black',
                                           foreground="red")
    serial_log.pack(side=tk.BOTTOM, expand=True)
    serial_log.configure(state='disabled')

    logger_thread = Thread(target=lambda: event_logger.run(serial_log))
    logger_thread.start()

    serial_thread = Thread(target=reader.loop)
    serial_thread.start()

    root.mainloop()
    print("End of main loop!")
    event_logger.kill()
    reader.kill()
    logger_thread.join()
    serial_thread.join()
