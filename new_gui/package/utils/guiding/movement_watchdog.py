from .data_processor import DataProcessor
from .guiding_data import GuidingData
import math
import logging
log = logging.getLogger("guiding")


max_possible_max_counter = 20
max_ra_as_threshold = 15
max_dec_as_threshold = 25


class MovementWatchdog(DataProcessor):
    def __init__(self, mover):
        super(MovementWatchdog, self).__init__("MovementWatchdog")
        self._mover = mover
        self._max_counter = 0

    def _process_impl(self, data: GuidingData):
        arcseconds = data.movement_as
        log.debug(f"Watchdog got arcseconds: {data.movement_as}")

        if arcseconds is None:
            log.warning("Mover did not get arcseconds to move!")
            return data

        if math.isnan(arcseconds[0]):
            self._max_counter = max_possible_max_counter

        if math.isnan(arcseconds[1]):
            self._max_counter = max_possible_max_counter

        if self._max_counter >= max_possible_max_counter:
            log.error(" ======\n====== Too many errors, skipping movement! ======\n====== ")
            self._mover.disable()
            return None

        if abs(arcseconds[0]) > max_ra_as_threshold:
            self._max_counter += 1
        else:
            self._max_counter -= 1
        if abs(arcseconds[1]) > max_dec_as_threshold:
            self._max_counter += 1
        else:
            self._max_counter -= 1
        self._max_counter = max(self._max_counter, 0)
        log.debug(f"Max movements counter = {self._max_counter}")
        return data
