from .global_settings import possible_units
import tkinter as tk
from common.serial_reader import callbacker


max_ra_as = 1296000
min_ra_as = 0
max_dec_as = 324000
min_dec_as = -324000


def normalize_ra(value):
    if value >= max_ra_as:
        value -= max_ra_as
    return value


def calculate_as_from_dec(d, m, s):
    dec_as = (abs(d)*3600+m*60+s)
    return dec_as if d > 0 else -dec_as


class CoordinateMover:
    def __init__(self, r, logger):
        self._reader = r
        self._logger = logger
        self._is_moving = False
        self._current_ra = None
        self._current_dec = None
        self._dec_correction = 0
        self.vars = {
            "ra_hours": tk.StringVar(value=23),
            "ra_minutes": tk.StringVar(value=59),
            "ra_seconds": tk.StringVar(value=59),
            "optics_f": tk.StringVar(value=650),
            "optics_pixel": tk.StringVar(value=2.9),
            "ra_precise": tk.StringVar(value=0),
            "dec_precise": tk.StringVar(value=0),
            "dec_degrees": tk.StringVar(value=-89),
            "dec_minutes": tk.StringVar(value=59),
            "dec_seconds": tk.StringVar(value=59),
            "dec_drift": tk.StringVar(value=0),
            "ra_precise_units": tk.StringVar(value=possible_units[0]),
            "dec_precise_units": tk.StringVar(value=possible_units[0])
        }

    def halt(self):
        self._logger.log_event(f"Sending immediate HALT command!\n")
        self._reader.write_string("HALT")
        self._is_moving = False

    def set_ra(self):
        if self._is_moving:
            self._logger.log_event(f"Cannot set new coordinates while moving!\n")
            return

        h = int(self.vars["ra_hours"].get())
        m = int(self.vars["ra_minutes"].get())
        s = int(self.vars["ra_seconds"].get())
        self._current_ra = h*3600*15+m*60*15+s*15
        self._logger.log_event(f"Sending ra={h}:{m}:{s} which is {self._current_ra} arceseconds.\n")
        self._reader.write_string(f"SET_RA {self._current_ra}")

    def set_dec(self):
        if self._is_moving:
            self._logger.log_event(f"Cannot set new coordinates while moving!\n")
            return

        d = int(self.vars["dec_degrees"].get())
        m = int(self.vars["dec_minutes"].get())
        s = int(self.vars["dec_seconds"].get())
        self._current_dec = calculate_as_from_dec(d, m, s)
        self._logger.log_event(f"Sending dec={d}:{m}:{s} which is {self._current_dec} arceseconds.\n")
        self._reader.write_string(f"SET_DEC {self._current_dec}")

    def _on_ra_movement_end(self, quantity):
        self._logger.log_event(f"RA Movement done!\n")
        self._is_moving = False
        self._current_ra += quantity
        self._current_ra = normalize_ra(self._current_ra)

    def _move_ra_as(self, quantity):
        if self._is_moving:
            self._logger.log_event(f"Not allowed to move when already moving!\n")
            return

        if quantity < 0:
            command = "MOVE_RA-"
        else:
            command = "MOVE_RA+"

        command = f"{command} {abs(quantity)}"
        self._is_moving = True
        callbacker.set_callback(lambda: self._on_ra_movement_end(quantity))
        self._reader.write_string(command)
        self._logger.log_event(f"Sending command to serial: {command}\n")

    def _on_dec_movement_end(self, quantity):
        self._logger.log_event(f"DEC Movement done!\n")
        self._is_moving = False
        self._current_dec += quantity

    def _move_dec_as(self, quantity):
        if self._is_moving:
            self._logger.log_event(f"Not allowed to move when already moving!\n")
            return
        if quantity < 0:
            command = "MOVE_DEC-"
        else:
            command = "MOVE_DEC+"

        command = f"{command} {abs(quantity)}"
        self._is_moving = True
        callbacker.set_callback(lambda: self._on_dec_movement_end(quantity))
        self._reader.write_string(command)
        self._logger.log_event(f"Sending command to serial: {command}\n")

    def move_dec(self):
        quantity = int(self.vars["dec_precise"].get())
        units = self.vars["dec_precise_units"].get()
        self._logger.log_event(f"Moving in DEC by {quantity} {units}\n")

        if units == "arcsec":
            self._move_dec_as(quantity)

    def go_back_ra(self):
        self._move_ra_as(3*15*3600)

    def move_ra(self):
        quantity = int(self.vars["ra_precise"].get())
        units = self.vars["ra_precise_units"].get()
        self._logger.log_event(f"Moving in RA by {quantity} {units}\n")

        if units == "arcsec":
            self._move_ra_as(quantity)

    def set_dec_drift(self, value=None):
        if value is not None:
            quantity = value
        else:
            quantity = int(self.vars["dec_drift"].get())
        if quantity < 0:
            command = f"SET_DC- {abs(quantity)}"
        else:
            command = f"SET_DC+ {quantity}"

        self._dec_correction = quantity
        self._logger.log_event(f"Sending command {command} to set dec drift to {quantity} arcsek/100s\n")
        self._reader.write_string(command)

    def get_dec_correction(self):
        return self._dec_correction

    def stop_dec_drift(self):
        command = "STOP_DC"
        self._logger.log_event(f"Sending command to stop DEC drift compensation\n")
        self._reader.write_string(command)

    def start_dec_drift(self):
        command = "START_DC"
        self._logger.log_event(f"Sending command to start DEC drift compensation\n")
        self._reader.write_string(command)

    def goto_ra(self):
        if self._current_ra is None:
            self._logger.log_event("Current RA is not set!\n")
            return
        h = int(self.vars["ra_hours"].get())
        m = int(self.vars["ra_minutes"].get())
        s = int(self.vars["ra_seconds"].get())
        ra_as = h*3600*15+m*60*15+s*15
        delta_ra = ra_as - self._current_ra
        delta_ra = normalize_ra(delta_ra)
        self._logger.log_event(f"GoTo ra={h}:{m}:{s} which is moving by {delta_ra} arcseconds.\n")
        self._move_ra_as(delta_ra)

    def goto_dec(self):
        if self._current_dec is None:
            self._logger.log_event("Current DEC is not set!\n")
            return
        d = int(self.vars["dec_degrees"].get())
        m = int(self.vars["dec_minutes"].get())
        s = int(self.vars["dec_seconds"].get())
        dec_as = calculate_as_from_dec(d, m, s)
        delta_dec = dec_as - self._current_dec
        self._logger.log_event(f"GoTo dec={d}:{m}:{s} which is moving by {delta_dec} arcseconds.\n")
        self._move_dec_as(delta_dec)
