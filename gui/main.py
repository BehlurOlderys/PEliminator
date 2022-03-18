import serial_reader
from threading import Thread
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from functions.global_settings import possible_units
from functions.event_logger import EventLogger
from functions.coordinate_mover import CoordinateMover


if __name__ == "__main__":
    event_logger = EventLogger()
    # reader = serial_reader.SerialReader('COM8')
    reader = serial_reader.SerialReader(None)
    root = tk.Tk()
    mover = CoordinateMover(reader, event_logger)

    root.geometry("640x480")
    [optics_row, separator1_row, precise_ra_row, separator2_row, ra_row,
     separator3_row, dec_row, separator4_row, dec_drift_row, log_row] = range(0, 10)
    max_columns = 11

    optics_label = tk.Label(root, text='Image scale: f[mm]=', font=('calibre', 10, 'bold'))
    optics_label.grid(row=optics_row, column=0)
    optics_f_spin = ttk.Spinbox(root, from_=0, to=10000, width=5, textvariable=mover.vars["optics_f"])
    optics_f_spin.grid(row=optics_row, column=1)
    optics_pixel_label = tk.Label(root, text='px[um] =', font=('calibre', 10, 'bold'))
    optics_pixel_label.grid(row=optics_row, column=2)
    optics_pixel_spin = ttk.Spinbox(root, from_=0, to=99, width=5,
                                    textvariable=mover.vars["optics_pixel"], format='%.2f', increment=0.1)
    optics_pixel_spin.grid(row=optics_row, column=3)

    ttk.Separator(root, orient=tk.HORIZONTAL).grid(column=0, row=separator1_row,
                                                   columnspan=max_columns, sticky=tk.EW, ipady=4)

    precise_ra_desc_label = tk.Label(root, text='Precise move: RA', font=('calibre', 10, 'bold'))
    precise_ra_desc_label.grid(row=precise_ra_row, column=0)
    precise_ra_ctrl_spin = ttk.Spinbox(root, from_=-9999, to=9999, width=5, textvariable=mover.vars["ra_precise"])
    precise_ra_ctrl_spin.grid(row=precise_ra_row, column=1)
    precise_ra_ctrl_units_label = tk.Label(root, text='Units:', font=('calibre', 10, 'bold'))
    precise_ra_ctrl_units_label.grid(row=precise_ra_row, column=2)
    precise_ra_ctrl_combo = ttk.Combobox(root, values=possible_units, width=7,
                                         textvariable=mover.vars["ra_precise_units"])
    precise_ra_ctrl_combo.grid(row=precise_ra_row, column=3)
    precise_ra_ctrl_button = tk.Button(root, text='<MOVE', command=mover.move_ra)
    precise_ra_ctrl_button.grid(row=precise_ra_row, column=4)

    ttk.Separator(root, orient=tk.VERTICAL).grid(row=precise_ra_row, column=5, sticky=tk.NS, ipadx=10)

    precise_dec_label = tk.Label(root, text='DEC', font=('calibre', 10, 'bold'))
    precise_dec_label.grid(row=precise_ra_row, column=6)
    precise_dec_spin = ttk.Spinbox(root, from_=-9999, to=9999, width=5, textvariable=mover.vars["dec_precise"])
    precise_dec_spin.grid(row=precise_ra_row, column=7)
    precise_dec_units_label = tk.Label(root, text='Units:', font=('calibre', 10, 'bold'))
    precise_dec_units_label.grid(row=precise_ra_row, column=8)
    precise_dec_combo = ttk.Combobox(root, values=possible_units, width=7, textvariable=mover.vars["dec_precise_units"])
    precise_dec_combo.grid(row=precise_ra_row, column=9)
    precise_dec_button = tk.Button(root, text='<MOVE', command=mover.move_dec)
    precise_dec_button.grid(row=precise_ra_row, column=10)

    ttk.Separator(root, orient=tk.HORIZONTAL).grid(column=0, row=separator2_row,
                                                   columnspan=max_columns, sticky=tk.EW, ipady=4)

    ra_hours_label = tk.Label(root, text='RA coordinates: H', font=('calibre', 10, 'bold'))
    ra_hours_label.grid(row=ra_row, column=0)
    ra_hours_spin = ttk.Spinbox(root, from_=0, to=23, width=3, textvariable=mover.vars["ra_hours"], wrap=True)
    ra_hours_spin.grid(row=ra_row, column=1)

    ra_minutes_label = tk.Label(root, text='M', font=('calibre', 10, 'bold'))
    ra_minutes_label.grid(row=ra_row, column=2)
    ra_minutes_spin = ttk.Spinbox(root, from_=0, to=59, width=3, textvariable=mover.vars["ra_minutes"], wrap=True)
    ra_minutes_spin.grid(row=ra_row, column=3)

    ra_seconds_label = tk.Label(root, text='S', font=('calibre', 10, 'bold'))
    ra_seconds_label.grid(row=ra_row, column=4)
    ra_seconds_spin = ttk.Spinbox(root, from_=0, to=59, width=3, textvariable=mover.vars["ra_seconds"], wrap=True)
    ra_seconds_spin.grid(row=ra_row, column=5)

    set_ra_button = tk.Button(root, text='SET', command=mover.set_ra)
    set_ra_button.grid(row=ra_row, column=6)

    goto_ra_button = tk.Button(root, text='GoTo', command=mover.goto_ra)
    goto_ra_button.grid(row=ra_row, column=7)

    halt_ra_button = tk.Button(root, text='HALT!', command=mover.halt)
    halt_ra_button.grid(row=ra_row, column=8)

    ttk.Separator(root, orient=tk.HORIZONTAL).grid(column=0, row=separator3_row, columnspan=max_columns,
                                                   sticky=tk.EW, ipady=4)

    dec_degrees_label = tk.Label(root, text='DEC coordinates: H', font=('calibre', 10, 'bold'))
    dec_degrees_label.grid(row=dec_row, column=0)
    dec_degrees_spin = ttk.Spinbox(root, from_=-89, to=89, width=3,
                                   textvariable=mover.vars["dec_degrees"], wrap=True)
    dec_degrees_spin.grid(row=dec_row, column=1)

    dec_minutes_label = tk.Label(root, text='M', font=('calibre', 10, 'bold'))
    dec_minutes_label.grid(row=dec_row, column=2)
    dec_minutes_spin = ttk.Spinbox(root, from_=0, to=59, width=3, textvariable=mover.vars["dec_minutes"], wrap=True)
    dec_minutes_spin.grid(row=dec_row, column=3)

    dec_seconds_label = tk.Label(root, text='S', font=('calibre', 10, 'bold'))
    dec_seconds_label.grid(row=dec_row, column=4)
    dec_seconds_spin = ttk.Spinbox(root, from_=0, to=59, width=3, textvariable=mover.vars["dec_seconds"], wrap=True)
    dec_seconds_spin.grid(row=dec_row, column=5)

    set_dec_button = tk.Button(root, text='SET', command=mover.set_dec)
    set_dec_button.grid(row=dec_row, column=6)

    goto_dec_button = tk.Button(root, text='GoTo', command=mover.goto_dec)
    goto_dec_button.grid(row=dec_row, column=7)

    halt_dec_button = tk.Button(root, text='HALT!', command=mover.halt)
    halt_dec_button.grid(row=dec_row, column=8)

    ttk.Separator(root, orient=tk.HORIZONTAL).grid(column=0, row=separator4_row, columnspan=max_columns, sticky=tk.EW,
                                                   ipady=4)

    dec_drift_label = tk.Label(root, text='DEC drift value: ', font=('calibre', 10, 'bold'))
    dec_drift_label.grid(row=dec_drift_row, column=0)

    dec_drift_spin = ttk.Spinbox(root, from_=-999, to=999, width=4, textvariable=mover.vars["dec_drift"], wrap=True)
    dec_drift_spin.grid(row=dec_drift_row, column=1)

    dec_drift_units_label = tk.Label(root, text='arcsek / 100s', font=('calibre', 10, 'bold'))
    dec_drift_units_label.grid(row=dec_drift_row, column=2)

    dec_drift_button_set = tk.Button(root, text='Set drift value', command=mover.set_dec_drift)
    dec_drift_button_set.grid(row=dec_drift_row, column=3)

    dec_drift_button_start = tk.Button(root, text='Compensate!', command=mover.start_dec_drift)
    dec_drift_button_start.grid(row=dec_drift_row, column=4)

    dec_drift_button_stop = tk.Button(root, text='STOP', command=mover.stop_dec_drift)
    dec_drift_button_stop.grid(row=dec_drift_row, column=5)

    serial_log = scrolledtext.ScrolledText(root,
                                           font=('calibre', 10, 'normal'),
                                           background='black',
                                           foreground="red")
    serial_log.grid(row=log_row, column=0, columnspan=max_columns)
    serial_log.configure(state='disabled')

    logger_thread = Thread(target=lambda: event_logger.run(serial_log))
    logger_thread.start()

    serial_thread = Thread(target=reader.loop)
    # serial_thread.start()

    root.mainloop()
    print("End of main loop!")
    event_logger.kill()
    reader.kill()
    logger_thread.join()
    serial_thread.join()
