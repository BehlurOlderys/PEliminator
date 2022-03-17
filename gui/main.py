import serial_reader
from threading import Thread, Event
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk

# reader = serial_reader.SerialReader('COM8')
reader = serial_reader.SerialReader(None)

max_ra_as = 1296000
min_ra_as = 0
max_dec_as = 324000
min_dec_as = -324000
new_string = None
is_moving = False

root = tk.Tk()
ra_hours_var = tk.StringVar(value=23)
ra_minutes_var = tk.StringVar(value=59)
ra_seconds_var = tk.StringVar(value=59)
optics_f_var = tk.StringVar(value=650)
optics_pixel_var = tk.StringVar(value=2.9)
ra_precise_var = tk.StringVar(value=0)
dec_precise_var = tk.StringVar(value=0)
dec_degrees_var = tk.StringVar(value=-89)
dec_minutes_var = tk.StringVar(value=59)
dec_seconds_var = tk.StringVar(value=59)
dec_drift_var = tk.StringVar(value=0)

possible_units = ["steps", "arcsec", "pixels"]
ra_precise_units_var = tk.StringVar(value=possible_units[0])
dec_precise_units_var = tk.StringVar(value=possible_units[0])

# TODO: should be separate classes for that!
current_ra = None
current_dec = None
log_some_string = Event()
log_strings = []

killer_flag = False


def log_event(s):
    log_strings.append(s)
    log_some_string.set()


def halt():
    global is_moving
    log_event(f"Sending immediate HALT command!\n")
    reader.write("HALT")
    is_moving = False


def set_ra():
    global current_ra
    if is_moving:
        log_event(f"Cannot set new coordinates while moving!\n")
        return

    h = int(ra_hours_var.get())
    m = int(ra_minutes_var.get())
    s = int(ra_seconds_var.get())
    current_ra = h*3600*15+m*60*15+s*15
    log_event(f"Sending ra={h}:{m}:{s} which is {current_ra} arceseconds.\n")
    reader.write(f"SET_RA {current_ra}")


def calculate_as_from_dec(d, m, s):
    dec_as = (abs(d)*3600+m*60+s)
    return dec_as if d > 0 else -dec_as


def set_dec():
    global current_dec
    if is_moving:
        log_event(f"Cannot set new coordinates while moving!\n")
        return

    d = int(dec_degrees_var.get())
    m = int(dec_minutes_var.get())
    s = int(dec_seconds_var.get())
    current_dec = calculate_as_from_dec(d, m, s)
    log_event(f"Sending dec={d}:{m}:{s} which is {current_dec} arceseconds.\n")
    reader.write(f"SET_DEC {current_dec}")


def normalize_ra(value):
    if value >= max_ra_as:
        value -= max_ra_as
    return value


def on_ra_movement_end(quantity):
    global is_moving
    global current_ra
    log_event(f"RA Movement done!\n")
    is_moving = False
    current_ra += quantity
    normalize_ra(current_ra)


def move_ra_as(quantity):
    global is_moving
    global current_ra
    if is_moving:
        log_event(f"Not allowed to move when already moving!\n")
        return

    command = ""
    if quantity < 0:
        command = "MOVE_RA-"
    else:
        command = "MOVE_RA+"

    command = f"{command} {abs(quantity)}"
    is_moving = True
    serial_reader.move_done_callback = lambda: on_ra_movement_end(quantity)
    reader.write(command)
    log_event(f"Sending command to serial: {command}\n")


def on_dec_movement_end(quantity):
    global is_moving
    global current_dec
    log_event(f"DEC Movement done!\n")
    is_moving = False
    current_dec += quantity


def move_dec_as(quantity):
    global is_moving
    global current_dec
    if is_moving:
        log_event(f"Not allowed to move when already moving!\n")
        return
    command = ""
    if quantity < 0:
        command = "MOVE_DEC-"
    else:
        command = "MOVE_DEC+"

    command = f"{command} {abs(quantity)}"
    is_moving = True
    serial_reader.move_done_callback = lambda: on_dec_movement_end(quantity)
    reader.write(command)
    log_event(f"Sending command to serial: {command}\n")


def move_dec():
    global new_string
    quantity = int(dec_precise_var.get())
    units = dec_precise_units_var.get()
    log_event(f"Moving in DEC by {quantity} {units}\n")

    if units == "arcsec":
        move_dec_as(quantity)


def move_ra():
    global new_string
    quantity = int(ra_precise_var.get())
    units = ra_precise_units_var.get()
    log_event(f"Moving in RA by {quantity} {units}\n")

    if units == "arcsec":
        move_ra_as(quantity)


def set_dec_drift():
    quantity = int(dec_drift_var.get())
    command = None
    if quantity < 0:
        command = f"SET_DC- {abs(quantity)}"
    else:
        command = f"SET_DC+ {quantity}"
    log_event(f"Sending command {command} to set dec drift to {quantity} arcsek/100s\n")
    reader.write(command)


def stop_dec_drift():
    command = "STOP_DC"
    log_event(f"Sending command to stop DEC drift compensation\n")
    reader.write(command)


def start_dec_drift():
    command = "START_DC"
    log_event(f"Sending command to start DEC drift compensation\n")
    reader.write(command)


def goto_ra():
    global new_string
    global current_ra
    if current_ra is None:
        log_event("Current RA is not set!\n")
        return
    h = int(ra_hours_var.get())
    m = int(ra_minutes_var.get())
    s = int(ra_seconds_var.get())
    ra_as = h*3600*15+m*60*15+s*15
    delta_ra = ra_as - current_ra
    delta_ra = normalize_ra(delta_ra)
    log_event(f"GoTo ra={h}:{m}:{s} which is moving by {delta_ra} arcseconds.\n")
    move_ra_as(delta_ra)


def goto_dec():
    global new_string
    global current_dec
    if current_dec is None:
        log_event("Current DEC is not set!\n")
        return
    d = int(dec_degrees_var.get())
    m = int(dec_minutes_var.get())
    s = int(dec_seconds_var.get())
    dec_as = calculate_as_from_dec(d, m, s)
    delta_dec = dec_as - current_dec
    # delta_dec = normalize_dec(delta_dec)
    log_event(f"GoTo dec={d}:{m}:{s} which is moving by {delta_dec} arcseconds.\n")
    move_dec_as(delta_dec)


if __name__ == "__main__":

    serial_thread = Thread(target=reader.loop)
    serial_thread.start()

    root.geometry("640x480")
    [optics_row, separator1_row, precise_ra_row, separator2_row, ra_row,
     separator3_row, dec_row, separator4_row, dec_drift_row, log_row] = range(0, 10)
    max_columns = 11

    optics_label = tk.Label(root, text='Image scale: f[mm]=', font=('calibre', 10, 'bold'))
    optics_label.grid(row=optics_row, column=0)
    optics_f_spin = ttk.Spinbox(root, from_=0, to=10000, width=5, textvariable=optics_f_var)
    optics_f_spin.grid(row=optics_row, column=1)
    optics_pixel_label = tk.Label(root, text='px[um] =', font=('calibre', 10, 'bold'))
    optics_pixel_label.grid(row=optics_row, column=2)
    optics_pixel_spin = ttk.Spinbox(root, from_=0, to=99, width=5, textvariable=optics_pixel_var, format='%.2f', increment=0.1)
    optics_pixel_spin.grid(row=optics_row, column=3)

    ttk.Separator(root, orient=tk.HORIZONTAL).grid(column=0, row=separator1_row, columnspan=max_columns, sticky=tk.EW, ipady=4)

    precise_ra_desc_label = tk.Label(root, text='Precise move: RA', font=('calibre', 10, 'bold'))
    precise_ra_desc_label.grid(row=precise_ra_row, column=0)
    precise_ra_ctrl_spin = ttk.Spinbox(root, from_=-9999, to=9999, width=5, textvariable=ra_precise_var)
    precise_ra_ctrl_spin.grid(row=precise_ra_row, column=1)
    precise_ra_ctrl_units_label = tk.Label(root, text='Units:', font=('calibre', 10, 'bold'))
    precise_ra_ctrl_units_label.grid(row=precise_ra_row, column=2)
    precise_ra_ctrl_combo = ttk.Combobox(root, values=possible_units, width=7, textvariable=ra_precise_units_var)
    precise_ra_ctrl_combo.grid(row=precise_ra_row, column=3)
    precise_ra_ctrl_button = tk.Button(root, text='<MOVE', command=move_ra)
    precise_ra_ctrl_button.grid(row=precise_ra_row, column=4)

    ttk.Separator(root, orient=tk.VERTICAL).grid(row=precise_ra_row, column=5, sticky=tk.NS, ipadx=10)

    precise_dec_label = tk.Label(root, text='DEC', font=('calibre', 10, 'bold'))
    precise_dec_label.grid(row=precise_ra_row, column=6)
    precise_dec_spin = ttk.Spinbox(root, from_=-9999, to=9999, width=5, textvariable=dec_precise_var)
    precise_dec_spin.grid(row=precise_ra_row, column=7)
    precise_dec_units_label = tk.Label(root, text='Units:', font=('calibre', 10, 'bold'))
    precise_dec_units_label.grid(row=precise_ra_row, column=8)
    precise_dec_combo = ttk.Combobox(root, values=possible_units, width=7, textvariable=dec_precise_units_var)
    precise_dec_combo.grid(row=precise_ra_row, column=9)
    precise_dec_button = tk.Button(root, text='<MOVE', command=move_dec)
    precise_dec_button.grid(row=precise_ra_row, column=10)

    ttk.Separator(root, orient=tk.HORIZONTAL).grid(column=0, row=separator2_row, columnspan=max_columns, sticky=tk.EW, ipady=4)

    ra_hours_label = tk.Label(root, text='RA coordinates: H', font=('calibre', 10, 'bold'))
    ra_hours_label.grid(row=ra_row, column=0)
    ra_hours_spin = ttk.Spinbox(root, from_=0, to=23, width=3, textvariable=ra_hours_var, wrap=True)
    ra_hours_spin.grid(row=ra_row, column=1)

    ra_minutes_label = tk.Label(root, text='M', font=('calibre', 10, 'bold'))
    ra_minutes_label.grid(row=ra_row, column=2)
    ra_minutes_spin = ttk.Spinbox(root, from_=0, to=59, width=3, textvariable=ra_minutes_var, wrap=True)
    ra_minutes_spin.grid(row=ra_row, column=3)

    ra_seconds_label = tk.Label(root, text='S', font=('calibre', 10, 'bold'))
    ra_seconds_label.grid(row=ra_row, column=4)
    ra_seconds_spin = ttk.Spinbox(root, from_=0, to=59, width=3, textvariable=ra_seconds_var, wrap=True)
    ra_seconds_spin.grid(row=ra_row, column=5)

    set_ra_button = tk.Button(root, text='SET', command=set_ra)
    set_ra_button.grid(row=ra_row, column=6)

    goto_ra_button = tk.Button(root, text='GoTo', command=goto_ra)
    goto_ra_button.grid(row=ra_row, column=7)

    halt_ra_button = tk.Button(root, text='HALT!', command=halt)
    halt_ra_button.grid(row=ra_row, column=8)

    ttk.Separator(root, orient=tk.HORIZONTAL).grid(column=0, row=separator3_row, columnspan=max_columns, sticky=tk.EW, ipady=4)

    dec_degrees_label = tk.Label(root, text='DEC coordinates: H', font=('calibre', 10, 'bold'))
    dec_degrees_label.grid(row=dec_row, column=0)
    dec_degrees_spin = ttk.Spinbox(root, from_=-89, to=89, width=3, textvariable=dec_degrees_var, wrap=True)
    dec_degrees_spin.grid(row=dec_row, column=1)

    dec_minutes_label = tk.Label(root, text='M', font=('calibre', 10, 'bold'))
    dec_minutes_label.grid(row=dec_row, column=2)
    dec_minutes_spin = ttk.Spinbox(root, from_=0, to=59, width=3, textvariable=dec_minutes_var, wrap=True)
    dec_minutes_spin.grid(row=dec_row, column=3)

    dec_seconds_label = tk.Label(root, text='S', font=('calibre', 10, 'bold'))
    dec_seconds_label.grid(row=dec_row, column=4)
    dec_seconds_spin = ttk.Spinbox(root, from_=0, to=59, width=3, textvariable=dec_seconds_var, wrap=True)
    dec_seconds_spin.grid(row=dec_row, column=5)

    set_dec_button = tk.Button(root, text='SET', command=set_dec)
    set_dec_button.grid(row=dec_row, column=6)

    goto_dec_button = tk.Button(root, text='GoTo', command=goto_dec)
    goto_dec_button.grid(row=dec_row, column=7)

    halt_dec_button = tk.Button(root, text='HALT!', command=halt)
    halt_dec_button.grid(row=dec_row, column=8)

    ttk.Separator(root, orient=tk.HORIZONTAL).grid(column=0, row=separator4_row, columnspan=max_columns, sticky=tk.EW,
                                                   ipady=4)

    dec_drift_label = tk.Label(root, text='DEC drift value: ', font=('calibre', 10, 'bold'))
    dec_drift_label.grid(row=dec_drift_row, column=0)

    dec_drift_spin = ttk.Spinbox(root, from_=-999, to=999, width=4, textvariable=dec_drift_var, wrap=True)
    dec_drift_spin.grid(row=dec_drift_row, column=1)

    dec_drift_units_label = tk.Label(root, text='arcsek / 100s', font=('calibre', 10, 'bold'))
    dec_drift_units_label.grid(row=dec_drift_row, column=2)

    dec_drift_button_set = tk.Button(root, text='Set drift value', command=set_dec_drift)
    dec_drift_button_set.grid(row=dec_drift_row, column=3)

    dec_drift_button_start = tk.Button(root, text='Compensate!', command=start_dec_drift)
    dec_drift_button_start.grid(row=dec_drift_row, column=4)

    dec_drift_button_stop = tk.Button(root, text='STOP', command=stop_dec_drift)
    dec_drift_button_stop.grid(row=dec_drift_row, column=5)



    serial_log = scrolledtext.ScrolledText(root,
                                           font=('calibre', 10, 'normal'),
                                           background='black',
                                           foreground="red")
    serial_log.grid(row=log_row, column=0, columnspan=max_columns)
    serial_log.configure(state='disabled')

    #
    #
    # name_var = tk.StringVar()
    # passw_var = tk.StringVar()
    # serial_log_var = tk.StringVar()
    # name_label = tk.Label(root, text='Username', font=('calibre', 10, 'bold'))
    # name_entry = tk.Entry(root, textvariable=name_var, font=('calibre', 10, 'normal'))
    # passw_label = tk.Label(root, text='Password', font=('calibre', 10, 'bold'))
    # passw_entry = tk.Entry(root, textvariable=passw_var, font=('calibre', 10, 'normal'), show='*')
    # name_label.grid(row=0, column=0)
    # name_entry.grid(row=0, column=1)
    # passw_label.grid(row=1, column=0)
    # passw_entry.grid(row=1, column=1)
    # sub_btn = tk.Button(root, text='Submit', command=submit)
    #     #
    #     # sub_btn.grid(row=2, column=1)

    def insert():
        global new_string
        global killer_flag
        while not killer_flag:
            result = log_some_string.wait(1)
            if result:
                log_some_string.clear()
            else:
                continue
            serial_log.configure(state='normal')
            while log_strings:
                serial_log.insert(tk.INSERT, log_strings.pop(0))

            serial_log.configure(state='disabled')


    inserting_thread = Thread(target=insert)
    inserting_thread.start()

    root.mainloop()
    print("End of main loop!")
    killer_flag = True
    reader.kill()
    inserting_thread.join()
    serial_thread.join()
