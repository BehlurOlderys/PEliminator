from .data_processor import DataProcessor
from .guiding_data import GuidingData
import logging
log = logging.getLogger("guiding")


class ImageDisplay(DataProcessor):
    def __init__(self, canvas):
        super(ImageDisplay, self).__init__("ImageDisplay")
        self._canvas = canvas

    def _process_impl(self, data: GuidingData):
        self._canvas.update_with_np((256*data.image).astype("uint8"))
        return data
