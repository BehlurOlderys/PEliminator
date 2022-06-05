import os

from serial import Serial, SerialException
from struct import unpack
import logging
from datetime import datetime
import time
import sys

from .serial_handlers.all_handlers import handle_raw_payload, welcome_message_handler

log = logging.getLogger(__name__)


def get_available_com_ports():
    if sys.platform.startswith('win'):  # TODO: other platforms?
        ports = ['COM%s' % (i + 1) for i in range(256)]
    else:
        return ["<NONE>"]

    result = []
    for p in ports:
        try:
            s = Serial(p)
            s.close()
            result.append(p)
        except (OSError, SerialException):
            pass
    if not result:
        return ["<NONE>"]
    return result


class SerialReader:
    def __init__(self):
        self._ser = None
        self._log_file = None
        self._encoder_log_file = None
        self._timing_log_file = None
        self._logs = [self._log_file, self._encoder_log_file, self._timing_log_file]
        self._something_to_write = []
        self._current_position = 0
        self._current_time = 0
        self._previous_signals = None
        self._current_error = 0
        self._latest_encoder_readouts = []
        self._killme = False

    def is_connected(self):
        return self._ser is not None



        print(f"Opened serial on {port_name}")
        self._log_file = open("logs/log_entire_serial.txt", "w", buffering=1)
        self._encoder_log_file = open(datetime.now().strftime('logs/encoder_%Y-%m-%d_%H-%M.log'), "w", buffering=1)
        self._timing_log_file = open('logs/timing_log', "w", buffering=1)
        self._timing_log_file.write(f"Current [us], Previous [us], Arduino time [ms], PC Time [ms]\n")
        self._logs = [self._log_file, self._encoder_log_file, self._timing_log_file]

        print(f"Receiving welcome message...")
        self._receive_new_data_from_serial()  # should be welcome message
        message = welcome_message_handler.get_welcome_message()
        if message is None:
            self._log_file.write("Could not connect to mount!")
            return "Connection failed!"
        print(f"Received: {message}")
        return message

    def kill(self):
        self._killme = True

    def write_bytes(self, b):
        self._something_to_write.append(b)

    def write_string(self, something):
        print(f"SerialReader: writing {something}")
        self._something_to_write.append((something+"\n").encode())

    def __del__(self):
        if self._log_file is not None:
            self._log_file.close()
        if self._encoder_log_file is not None:
            self._encoder_log_file.close()

    def _receive_new_data_from_serial(self):
        message = self._ser.readline().decode('UTF-8').rstrip()
        if "BHS" == message:
            header_line = self._ser.read(12)
            try:
                (timestamp, type_id, data_size) = unpack("LLL", header_line)
            except ValueError as ve:
                log.error(f"Value error {ve} happened when reading header from {header_line}")
                return

            raw_payload = self._ser.read(data_size)
            handle_raw_payload(raw_payload, type_id, timestamp, self._logs)

    def _is_there_something_to_write(self):
        return len(self._something_to_write) > 0

    def _write_data_to_serial(self):
        element_to_write = self._something_to_write.pop(0)
        message = f"Written {element_to_write} to serial"
        if self._ser is not None:
            self._ser.write(element_to_write)
        else:
            message = "[PHONY] " + message
        print(message)

    def loop(self):
        print("Starting main loop")
        while not self._killme:
            if self._ser is None:
                time.sleep(1)
                continue
            try:
                if self._is_there_something_to_write():
                    self._write_data_to_serial()
                else:
                    self._receive_new_data_from_serial()

            except Exception as ex:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                log.error("SerialReader::loop Exception: " + message)
                continue
