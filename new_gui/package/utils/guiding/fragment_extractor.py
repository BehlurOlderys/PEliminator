from .data_processor import DataProcessor
from .guiding_data import GuidingData
from package.widgets.simple_canvas import SimpleCanvasRect
import logging
log = logging.getLogger("guiding")


class FragmentExtractor(DataProcessor):
    def __init__(self, canvas: SimpleCanvasRect):
        super(FragmentExtractor, self).__init__("FragmentExtractor")
        self._canvas = canvas

    def _process_impl(self, data: GuidingData):
        r = self._canvas.get_real_rect()
        if r is None:
            log.warning("No fragment set on canvas")
            return data
        log.debug(f"Obtained rect from canvas: {r}")
        x, y, h = r
        data.fragment_rect = r
        data.fragment = data.image[y:y+h, x:x+h]

        return data
