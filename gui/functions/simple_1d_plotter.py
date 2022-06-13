from functions.point_plot import PointPlot


class Simple1DPlotter(PointPlot):
    def __init__(self, frame):
        PointPlot.__init__(self, frame)
        self._data_y = []
        self.first_point = None
        self._line = None

    def clear_plot(self):
        self.first_point = None
        self._data_y = []
        print("Clear plot (simple)")
        self._clear_plot()

    def add_points(self, time_points):
        if not self.data_t:
            self.first_point = time_points[0]
            print(self.first_point)
            self._line = self.ax.plot(0, 0, 'b')[0]
        t0, y0 = self.first_point
        for p in time_points:
            t, y = p
            self.data_t.append(t - t0)
            self._data_y.append(y - y0)

        self._line.set_ydata(self._data_y)
        self._line.set_xdata(self.data_t)
        super().redraw()
