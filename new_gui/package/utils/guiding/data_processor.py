from .guiding_data import GuidingData
import time
import logging
log = logging.getLogger("guiding")


class DataProcessor:
    def __init__(self, name):
        self._name = name

    def process(self, data: GuidingData):
        if data is None:
            log.error(f"Processor {self._name} received None as data, returning...")
            return None
        if data.error:
            return data
        log.debug(f"Processor {self._name} starts processing...")
        return self._process_impl(data)

    def reset(self):
        self._reset_impl()

    def _reset_impl(self):
        pass

    def _process_impl(self, data):
        return data


class PreProcessor(DataProcessor):
    def __init__(self):
        super(PreProcessor, self).__init__("PreProcessor")

    def _process_impl(self, data: GuidingData):
        data.start = time.time()
        log.debug(f"Starting processing image {data.shortname}")
        return data


class PostProcessor(DataProcessor):
    def __init__(self):
        super(PostProcessor, self).__init__("PostProcessor")

    def _process_impl(self, data: GuidingData):
        elapsed = time.time() - data.start
        log.debug(f"Processing image {data.shortname} finished. It took {elapsed * 1000}ms")
        return data
