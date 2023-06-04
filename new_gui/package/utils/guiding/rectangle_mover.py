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

    def _process_impl(self, data: GuidingData):
        # self._history.append(data.calculated_center)
        # if len(self._history) > self._history_size:
        #     self._history.pop(0)
        #
        # xs = np.array([h[0] for h in self._history])
        # ys = np.array([h[1] for h in self._history])
        # medx = np.median(xs)
        # medy = np.median(ys)
        # x, y, _ = self._canvas.get_real_rect()
        # diffx = int(medx-x)
        # diffy = int(medy-y)
        # TODO!!!!
        # self._canvas.move_real_rect((0, 0))
        return data

