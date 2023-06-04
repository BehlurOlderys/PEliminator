from .data_processor import DataProcessor
from .guiding_data import GuidingData
import logging
log = logging.getLogger("guiding")


class DataPrinter(DataProcessor):
    def __init__(self, attribute_name):
        super(DataPrinter, self).__init__("Data printer")
        self._attribute_name = attribute_name
        self._logfile = open(f"{self._attribute_name}.log", 'w', buffering=1)
        self._logfile.write(f"time\t{self._attribute_name}\n")
        self._last_time = None

    def __del__(self):
        self._logfile.close()

    def _process_impl(self, data: GuidingData):
        printed = getattr(data, self._attribute_name)
        if printed is None:
            printed = "<None>"
        if self._last_time is None:
            timeprinted = 0
            self._last_time = data.timestamp
        else:
            timeprinted = data.timestamp - self._last_time
        line_to_write = f"{timeprinted}\t{printed}\n"
        self._logfile.write(line_to_write)
        return data
