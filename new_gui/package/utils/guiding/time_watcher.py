from .data_processor import DataProcessor
from .guiding_data import GuidingData
import time
import logging
log = logging.getLogger("guiding")


class TimeWatcher(DataProcessor):
    def __init__(self):
        super(TimeWatcher, self).__init__("Time watcher")
        self._last = time.time()

    def _process_impl(self, data: GuidingData):
        right_now = time.time()
        diff = right_now - self._last
        self._last = right_now
        log.debug(f"Time elapsed since last data feed = {diff}")
        return data
