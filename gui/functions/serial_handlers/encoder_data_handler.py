import time
from struct import unpack

from .common import encoder_log_index


class EncoderDataHandler:
    def __init__(self):
        self._latest = []
        self._max = 10000  # TODO: settings.get_encoder_history_size()

    def _add_readout(self, r):
        self._latest.append(r)
        if len(self._latest) > self._max:
            self._latest.pop(0)

    def find_readout_by_timestamp(self, ts):
        for t, r in reversed(self._latest):
            if int(t) == ts:
                return r

        return None

    def deserialize_abs_encoder(self, raw_payload, timestamp, logs):
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
        self._add_readout((t, position))
        return info_dict
