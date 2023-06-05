import math

from .data_processor import DataProcessor
from .guiding_data import GuidingData
from package.widgets.simple_canvas import SimpleCanvasRect
import numpy as np
import logging
log = logging.getLogger("guiding")


class RectangleMover(DataProcessor):
    def __init__(self, canvas: SimpleCanvasRect, history_size=5):
        super(RectangleMover, self).__init__("RectangleMover")
        self._canvas = canvas
        self._history_size = history_size
        self._history = []

    def _reset_impl(self):
        self._history.clear()

    def _process_impl(self, data: GuidingData):
        if data.calculated_center is None:
            return data
        x, y = data.calculated_center
        if math.isnan(x) or math.isnan(y):
            return data

        self._history.append(data.calculated_center)
        if len(self._history) > self._history_size:
            self._history.pop(0)

        # Will calculate last few middles
        xs = np.array([h[0] for h in self._history])
        ys = np.array([h[1] for h in self._history])
        medx = int(np.median(xs))
        medy = int(np.median(ys))
        self._canvas.set_real_rect_middle((medx, medy))
        return data

