from functions.point_plot import PointPlot


class ImageTrackingPlot(PointPlot):
    def __init__(self, frame):
        PointPlot.__init__(self, frame)
        self._data_x = []
        self._data_y = []
        self._red_on = True
        self._green_on = True
        self._line_green = None
        self._line_red = None
        self.first_point = None

    def clear_plot(self):
        self._line_green = None
        self._line_red = None
        self.first_point = None
        self._data_x = []
        self._data_y = []
        self._clear_plot()

    def toggle_red(self):
        if self._red_on:
            if self._line_red is not None:
                self._line_red.remove()
                self._line_red = None

        else:
            self._line_red = self._ax.plot(self.data_t, self._data_x, 'r', linewidth=1, drawstyle='steps-mid')[0]

        self._red_on = not self._red_on
        self.redraw()

    def toggle_green(self):
        if self._green_on:
            if self._line_green is not None:
                self._line_green.remove()
                self._line_green = None

        else:
            self._line_green = self.ax.plot(self.data_t, self._data_y, 'g', linewidth=4)[0]

        self._green_on = not self._green_on
        self.redraw()

    def get_green_state(self):
        return self._green_on

    def get_red_state(self):
        return self._red_on

    def add_points(self, time_points):
        if not self.data_t:
            self.first_point = time_points[0]
            self._line_green = self.ax.plot(0, 0, 'g', linewidth=4)[0]
            self._line_red = self.ax.plot(0, 0, 'r', linewidth=1, drawstyle='steps-mid')[0]
        t0, x0, y0 = self.first_point
        for p in time_points:
            t, x, y = p
            self.data_t.append(t - t0)
            self._data_x.append(x - x0)
            self._data_y.append(y - y0)

        self._line_red.set_ydata(self._data_x)
        self._line_red.set_xdata(self.data_t)
        self._line_green.set_ydata(self._data_y)
        self._line_green.set_xdata(self.data_t)
        self.redraw()
