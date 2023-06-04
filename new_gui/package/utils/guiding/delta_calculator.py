from .data_processor import DataProcessor
from .guiding_data import GuidingData
import logging
log = logging.getLogger("guiding")


class DeltaXYCalculator(DataProcessor):
    def __init__(self, input_name, output_name):
        super(DeltaXYCalculator, self).__init__("DeltaCalculator")
        self._input_name = input_name
        self._output_name = output_name
        self._start_value = None

    def _process_impl(self, data: GuidingData):
        new_value = getattr(data, self._input_name)
        if new_value is None:
            return data
        if self._start_value is None:
            delta = 0, 0
            self._start_value = new_value
        else:
            delta = (new_value[0] - self._start_value[0],
                     new_value[1] - self._start_value[1])

        log.debug(f"Delta = {delta}")
        setattr(data, self._output_name, delta)
        return data



