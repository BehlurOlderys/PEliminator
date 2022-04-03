from queue import Queue, Empty
from struct import unpack

from .common import general_log_index


class CorrectionDataHandler:
    def __init__(self):
        self._last_data = None
        self._queue = Queue(maxsize=1)

    def get_data(self):
        try:
            return self._queue.get(timeout=10)
        except Empty:
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