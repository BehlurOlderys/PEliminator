import queue

import serial
from serial import SerialException
from struct import unpack
import logging
from datetime import datetime
import time
import sys
from queue import Queue


def get_available_com_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    else:
        return []

    result = []
    for p in ports:
        try:
            s = serial.Serial(p)
            s.close()
            result.append(p)
        except (OSError, serial.SerialException):
            pass
    return result


log = logging.getLogger(__name__)

general_log_index = 0
encoder_log_index = 1
timing_log_index = 2

UNSPECIFIED_TYPE_ID = 255
STEPPER_TYPE_ID = 2
ABS_ENCODER_TYPE_ID = 3
TIMING_CONTROL_TYPE_ID = 15
GET_CORRECTION_ID = 19
WELCOME_MESSAGE_ID = 21

WELCOME_MESSAGE_LENGTH = 20

# SPECIAL MESSAGES:
SPECIAL_MOVE_DONE_ID = 17

special_messages = [SPECIAL_MOVE_DONE_ID]
special_message_desc = {SPECIAL_MOVE_DONE_ID: "MOVEMENT DONE"}


class Callbacker:
    def __init__(self):
        self._move_done_callback = None

    def set_callback(self, c):
        self._move_done_callback = c

    def callback_once(self):
        self._move_done_callback()
        self._move_done_callback = None


callbacker = Callbacker()


def is_special_message(ide):
    return ide in special_messages


IS_TRACKING_RESPONSE_ID = 100


serial_mega_info = {
    STEPPER_TYPE_ID: {},
    ABS_ENCODER_TYPE_ID: {},
    IS_TRACKING_RESPONSE_ID: [],
    UNSPECIFIED_TYPE_ID: []
}

global_thread_killer = False


def get_is_tracking_response():
    begin_len = len(serial_mega_info[IS_TRACKING_RESPONSE_ID])
    for i in range(0, 10):
        current_len = len(serial_mega_info[IS_TRACKING_RESPONSE_ID])
        if current_len > begin_len:
            return serial_mega_info[IS_TRACKING_RESPONSE_ID][-1]

        log.debug(f"waiting for response 0.01s...")
        time.sleep(0.01)

    return False


def handle_move_done_special_message():
    callbacker.callback_once()


special_message_handlers = {SPECIAL_MOVE_DONE_ID: handle_move_done_special_message}


def handle_special_message(type_id, timestamp, logs):
    logger = logs[general_log_index]
    special_message_handlers[type_id]()
    logger.write(f"{timestamp}, {special_message_desc[type_id]}")


last_timestamp = None
last_micros = 0
last_millis = 0
last_real = 0
average_ratio = None
average_size = 0
last_datetime = None


class Averager:
    def __init__(self):
        self.average_ratio = 0
        self.average_size = 0
        self.ratios = []

    def update_average(self, added):
        self.average_ratio = (self.average_size * self.average_ratio + added) / (self.average_size + 1)
        self.average_size += 1
        self.ratios.append(added)
        if len(self.ratios) > 1000:
            removed = self.ratios.pop(0)
            self.average_ratio = (self.average_size * self.average_ratio - removed) / (self.average_size - 1)
            self.average_size -= 1

        return self.average_ratio, self.average_size


averager = Averager()


def deserialize_timing(raw_payload, timestamp, logs):
    # BELOW IS FOR CONTROLLING TRACKING INTERVAL:
    # global last_millis, last_real, last_micros
    # [raw_millis, real_millis] = [int(x) for x in unpack("II", raw_payload)]
    # interval = raw_millis - last_millis
    # interval_real = real_millis - last_real
    # pc_micros = round(time.time_ns() / 1000)
    # pc_interval = pc_micros - last_micros
    # difference = 399720 - pc_interval
    # mean_diff = 0
    # if last_millis > 0:
    #     a, _ = averager.update_average(difference)
    #     mean_diff = a
    # print(f"Raw = {raw_millis},"
    #       f" adjusted = {real_millis}, "
    #       f"interval = {interval}, "
    #       f"real interval = {interval_real},"
    #       f"pc_interval = {pc_interval},"
    #       f"mean_diff = {mean_diff}")
    # last_millis = raw_millis
    # last_real = real_millis
    # last_micros = pc_micros

    # BELOW VERSION FOR CONTROLLING TIME DRIFT:
    global last_timestamp, last_micros, last_datetime
    [prev_micros, current_millis] = [int(x) for x in unpack("II", raw_payload)]
    logger = logs[timing_log_index]
    pc_micros = round(time.time_ns() / 1000)
    logger.write(f"{timestamp}, {prev_micros}, {current_millis}, {pc_micros}\n")
    loop_constant = (timestamp - prev_micros) / 5000
    dt = datetime.now()
    if last_timestamp is not None:
        interval_on_arduino = timestamp - last_timestamp
        interval_pc_micros = pc_micros - last_micros
        ratio = interval_pc_micros / interval_on_arduino
        mean_ratio, ratios_size = averager.update_average(ratio)
        delta_dt = (dt - last_datetime)
        print(f"Arduino interval = {interval_on_arduino},"
              f" PC interval = {interval_pc_micros},"
              f" delta_dt = {delta_dt},"
              f" loop = {loop_constant},"
              f" ratio = {ratio},"
              f" mean ratio = {mean_ratio}, size={ratios_size}")

    last_timestamp = timestamp
    last_micros = pc_micros
    last_datetime = dt


def deserialize_is_tracking(raw_payload, timestamp, logs):
    (value) = unpack("?", raw_payload)
    logger = logs[encoder_log_index]
    logger.write(f"{timestamp},VALUE={value}\n")
    serial_mega_info[IS_TRACKING_RESPONSE_ID].append(value)
    return value


class WelcomeMessageHandler:
    def __init__(self):
        self._queue = queue.Queue(maxsize=1)

    def deserialize_welcome_message(self, raw_payload, timestamp, logs):
        logger = logs[general_log_index]
        (message) = unpack(f"{WELCOME_MESSAGE_LENGTH}s", raw_payload)
        message = message[0].decode('UTF-8').strip(chr(0))
        logger.write(f"{timestamp} Acquired welcome message: {message}")
        self._queue.put(message)

    def get_welcome_message(self):
        try:
            return self._queue.get(timeout=10)
        except queue.Empty:
            print("Connection with mount failed!")
            return None


class EncoderData:
    def __init__(self):
        self._latest = []
        self._max = 10000 #settings.get_encoder_history_size()

    def add_readout(self, r):
        self._latest.append(r)
        if len(self._latest) > self._max:
            self._latest.pop(0)

    def find_readout_by_timestamp(self, ts):
        for t, r in reversed(self._latest):
            if int(t) == ts:
                return r

        return None


encoder_data = EncoderData()


def deserialize_abs_encoder(raw_payload, timestamp, logs):
    logger = logs[encoder_log_index]
    (position, raw_name) = unpack("H5s", raw_payload)
    name = raw_name.decode('UTF-8').strip()[:-1]

    info_dict = {
        "timestamp": timestamp,
        "name": name,
        "position": position,
    }

    t = time.time()
    logger.write(f"{t}, {timestamp} ABS_ENCODER: {info_dict}\n")
    encoder_data.add_readout((t, position))
    # print(f"{time.ctime()}, {timestamp} ABS_ENCODER: {info_dict}\n")
    if name not in serial_mega_info[ABS_ENCODER_TYPE_ID]:
        serial_mega_info[ABS_ENCODER_TYPE_ID][name] = []
    serial_mega_info[ABS_ENCODER_TYPE_ID][name].append(info_dict)
    return info_dict


class CorrectionDataDeserializer:
    def __init__(self):
        self._last_data = None
        self._queue = Queue(maxsize=1)

    def get_data(self):
        try:
            return self._queue.get(timeout=10)
        except queue.Empty:
            print("Getting correction data from mount timed out!")
            return None

    def deserialize_correction_data(self, raw_payload, timestamp, logs):
        logger = logs[general_log_index]
        print(f"Raw payload from correction data=\n{raw_payload}")
        data = unpack("129I", raw_payload)
        times = data[:64]
        intervals = data[64:128]
        length = data[-1]
        items_range = range(0, length)
        times_real = [times[i] for i in items_range]
        intervals_real = [intervals[i] for i in items_range]
        self._queue.put((timestamp, times_real, intervals_real))
        logger.write(f"{timestamp} GET CORR: {self._last_data}\n")


welcome_message_handler = WelcomeMessageHandler()
correction_data_provider = CorrectionDataDeserializer()


def deserialize_stepper(raw_payload, timestamp, logger):
    (delay, direction, position, desired, is_enabled, is_slewing, raw_name) = unpack("iiH???4s", raw_payload)
    name = raw_name.decode('UTF-8').strip()

    info_dict = {
        "timestamp": timestamp,
        "position": position,
        "direction": direction,
        "delay": delay,
        "desired": desired,
        "is_enabled": is_enabled,
        "is_slewing": is_slewing,
        "name": name
    }

    logger.write(f"{timestamp} STEPPER: {info_dict}\n")
    if name not in serial_mega_info[STEPPER_TYPE_ID]:
        serial_mega_info[STEPPER_TYPE_ID][name] = []
    serial_mega_info[STEPPER_TYPE_ID][name].append(info_dict)
    return info_dict


map_of_deserializers = {
  GET_CORRECTION_ID: correction_data_provider.deserialize_correction_data,
  STEPPER_TYPE_ID: deserialize_stepper,
  ABS_ENCODER_TYPE_ID: deserialize_abs_encoder,
  IS_TRACKING_RESPONSE_ID: deserialize_is_tracking,
  TIMING_CONTROL_TYPE_ID: deserialize_timing,
  WELCOME_MESSAGE_ID: welcome_message_handler.deserialize_welcome_message
}


def unpack_type(type_id, timestamp, raw_payload, logs):
    deserializer = map_of_deserializers[type_id]
    return deserializer(raw_payload, timestamp, logs)


class SerialReader:
    def __init__(self, com_port):
        self.ser = None
        self.log_file = None
        self.encoder_log_file = None
        self._something_to_write = []
        if com_port is not None:
            try:
                self.ser = serial.Serial(
                    port=com_port,
                    baudrate=115200,
                    timeout=1
                )
            except SerialException as se:
                print(f"Could not open serial port {com_port}, exiting...")
                exit(-1)

        if com_port is not None:
            self.log_file = open("logs/log_entire_serial.txt", "w", buffering=1)
            self.encoder_log_file = open(datetime.now().strftime('logs/encoder_%Y-%m-%d_%H-%M.log'), "w", buffering=1)
            self.timing_log_file = open('logs/timing_log', "w", buffering=1)
            self.timing_log_file.write(f"Current [us], Previous [us], Arduino time [ms], PC Time [ms]\n")
            self.logs = [self.log_file, self.encoder_log_file, self.timing_log_file]
        self.current_position = 0
        self.current_time = 0
        self.previous_signals = None
        self.current_error = 0
        self._latest_encoder_readouts = []

    def is_connected(self):
        return self.ser is not None

    def connect_to_port(self, port_name):
        self.ser = serial.Serial(
            port=port_name,
            baudrate=115200,
            timeout=3)

        print(f"Opened serial on {port_name}")
        self.log_file = open("logs/log_entire_serial.txt", "w", buffering=1)
        self.encoder_log_file = open(datetime.now().strftime('logs/encoder_%Y-%m-%d_%H-%M.log'), "w", buffering=1)
        self.timing_log_file = open('logs/timing_log', "w", buffering=1)
        self.timing_log_file.write(f"Current [us], Previous [us], Arduino time [ms], PC Time [ms]\n")
        self.logs = [self.log_file, self.encoder_log_file, self.timing_log_file]
        print(f"Receiving welcome message...")
        self._receive_new_data_from_serial()  # should be welcome message
        message = welcome_message_handler.get_welcome_message()
        if message is None:
            self.log_file.write("Could not connect to mount!")
            return "Connection failed!"
        print(f"Received: {message}")
        return message


    @staticmethod
    def kill():
        global global_thread_killer
        global_thread_killer = True

    def write_bytes(self, b):
        self._something_to_write.append(b)

    def write_string(self, something):
        print(f"SerialReader: writing {something}")
        self._something_to_write.append(something.encode())

    def __del__(self):
        if self.log_file is not None:
            self.log_file.close()
        if self.encoder_log_file is not None:
            self.encoder_log_file.close()

    def _receive_new_data_from_serial(self):
        message = self.ser.readline().decode('UTF-8').rstrip()
        if "BHS" == message:
            header_line = self.ser.read(12)
            try:
                (timestamp, type_id, data_size) = unpack("LLL", header_line)
            except ValueError as ve:
                log.error(f"Value error {ve} happened when reading header from {header_line}")
                return

            raw_payload = self.ser.read(data_size)
            if is_special_message(type_id):
                handle_special_message(type_id, timestamp, self.logs)
            else:
                unpack_type(type_id, timestamp, raw_payload, self.logs)

    def loop(self):
        print("Starting main loop")
        while not global_thread_killer:
            try:
                # print(f"Checking length= {something_to_write}")
                if len(self._something_to_write) > 0:
                    element_to_write = self._something_to_write.pop(0)
                    message = f"Written {element_to_write} to serial"
                    if self.ser is not None:
                        self.ser.write(element_to_write)
                    else:
                        message = "[PHONY] " + message
                    # log.info()
                    print(message)

                if self.ser is None:
                    time.sleep(1)
                    continue
                self._receive_new_data_from_serial()

            except Exception as ex:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                log.error("SerialReader::loop Exception: " + message)
                continue


if __name__ == "__main__":
    reader = SerialReader('COM8')
    reader.loop()