from struct import unpack

from .correction_data_handler import CorrectionDataHandler
from .encoder_data_handler import EncoderDataHandler
from .welcome_message_handler import WelcomeMessageHandler
from .timing import deserialize_timing
from .common import general_log_index


UNSPECIFIED_TYPE_ID = 255
STEPPER_TYPE_ID = 2
ABS_ENCODER_TYPE_ID = 3
TIMING_CONTROL_TYPE_ID = 15
GET_CORRECTION_ID = 19
WELCOME_MESSAGE_ID = 21
SPECIAL_MOVE_DONE_ID = 17
special_messages = [SPECIAL_MOVE_DONE_ID]
special_message_desc = {SPECIAL_MOVE_DONE_ID: "MOVEMENT DONE"}


def is_special_message(ide):
    return ide in special_messages


class Callbacker:
    def __init__(self):
        self._move_done_callback = None

    def set_callback(self, c):
        self._move_done_callback = c

    def callback_once(self):
        self._move_done_callback()
        self._move_done_callback = None


callbacker = Callbacker()
encoder_data = EncoderDataHandler()
welcome_message_handler = WelcomeMessageHandler()
correction_data_provider = CorrectionDataHandler()


def deserialize_stepper(raw_payload, timestamp, logs):
    logger = logs[general_log_index]
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
    return info_dict


map_of_deserializers = {
  GET_CORRECTION_ID: correction_data_provider.deserialize_correction_data,
  STEPPER_TYPE_ID: deserialize_stepper,
  ABS_ENCODER_TYPE_ID: encoder_data.deserialize_abs_encoder,
  TIMING_CONTROL_TYPE_ID: deserialize_timing,
  WELCOME_MESSAGE_ID: welcome_message_handler.deserialize_welcome_message
}
special_message_handlers = {SPECIAL_MOVE_DONE_ID: callbacker.callback_once}


def handle_special_message(type_id, timestamp, logs):
    logger = logs[general_log_index]
    special_message_handlers[type_id]()
    logger.write(f"{timestamp}, {special_message_desc[type_id]}")


def unpack_type(type_id, timestamp, raw_payload, logs):
    deserializer = map_of_deserializers[type_id]
    return deserializer(raw_payload, timestamp, logs)


def handle_raw_payload(raw_payload, type_id, timestamp, logs):
    if is_special_message(type_id):
        handle_special_message(type_id, timestamp, logs)
    else:
        unpack_type(type_id, timestamp, raw_payload, logs)