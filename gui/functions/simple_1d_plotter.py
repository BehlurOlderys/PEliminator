from functions.point_plot import PointPlot


class Simple1DPlotter(PointPlot):
    def __init__(self, frame):
        PointPlot.__init__(self, frame)
        self._data_y = []
        self._first_point = None
        self._line = None

    def clear_plot(self):
        self._first_point = None
        self._data_y = []
        super()._clear_plot()

    def add_points(self, time_points):
        if not super()._data_t:
            self._first_point = time_points[0]
            self._line = self._ax.plot(0, 0, 'b')
        t0, y0 = self._first_point
        for p in time_points:
            t, y = p
            super()._data_t.append(t - t0)
            self._data_y.append(y - y0)

        self._line.set_ydata(self._data_y)
        self._line.set_xdata(super()._data_t)
        super()._redraw()
