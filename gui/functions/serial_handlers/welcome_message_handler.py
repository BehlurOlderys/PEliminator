from queue import Queue, Empty
from struct import unpack

from .common import general_log_index


WELCOME_MESSAGE_LENGTH = 20


class WelcomeMessageHandler:
    def __init__(self):
        self._queue = Queue(maxsize=1)

    def deserialize_welcome_message(self, raw_payload, timestamp, logs):
        logger = logs[general_log_index]
        (message) = unpack(f"{WELCOME_MESSAGE_LENGTH}s", raw_payload)
        message = message[0].decode('UTF-8').strip(chr(0))
        logger.write(f"{timestamp} Acquired welcome message: {message}")
        self._queue.put(message)

    def get_welcome_message(self):
        try:
            return self._queue.get(timeout=10)
        except Empty:
            print("Connection with mount failed!")
            return None
