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
        self._first_point = None

    def clear_plot(self):
        self._line_green = None
        self._line_red = None
        self._first_point = None
        self._data_x = []
        self._data_y = []
        super()._clear_plot()

    def toggle_red(self):
        if self._red_on:
            if self._line_red is not None:
                self._line_red.remove()
                self._line_red = None

        else:
            self._line_red = self._ax.plot(self._data_t, self._data_x, 'r')[0]

        self._red_on = not self._red_on
        super()._redraw()

    def toggle_green(self):
        if self._green_on:
            if self._line_green is not None:
                self._line_green.remove()
                self._line_green = None

        else:
            self._line_green = self._ax.plot(super()._data_t, self._data_y, 'g')[0]

        self._green_on = not self._green_on
        super()._redraw()

    def get_green_state(self):
        return self._green_on

    def get_red_state(self):
        return self._red_on

    def add_points(self, time_points):
        if not super()._data_t:
            self._first_point = time_points[0]
            self._line_green, self._line_red = self._ax.plot(0, 0, 'g', 0, 0, 'r')
        t0, x0, y0 = self._first_point
        for p in time_points:
            t, x, y = p
            super()._data_t.append(t - t0)
            self._data_x.append(x - x0)
            self._data_y.append(y - y0)

        self._line_red.set_ydata(self._data_x)
        self._line_red.set_xdata(super()._data_t)
        self._line_green.set_ydata(self._data_y)
        self._line_green.set_xdata(super()._data_t)
        super()._redraw()
