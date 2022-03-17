import tkinter as tk
import numpy as np
from widgets.global_settings import settings


def moving_mean(a, m):
    half = m // 2
    second_half = m - half

    a = np.pad(a, (half, second_half), mode='edge')
    print(f"Shape of a = {a.shape}")
    alist = a.tolist()
    start = np.array([a[m:]])

    for i in range(1, m):
        x = i
        y = m-i
        start = np.concatenate((start, np.array([alist[y:-x]])), axis=0)

    print(start[:20])
    print(f"Shape of start = {start.shape}")
    r = np.mean(start.T, axis=1).T
    print(r[:20])
    print(f"Shape of r = {r.shape}")
    return r


class PeriodsList:
    def __init__(self, frame, axis, canvas):
        self._listbox = tk.Listbox(frame)
        self._listbox.bind('<<ListboxSelect>>', self.on_select)
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self._listbox.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.BOTH)
        self._listbox.config(yscrollcommand=scrollbar.set)
        self._listbox.pack(side=tk.TOP)
        self._listbox.select_set(0)
        self._periods = None
        self._ax = axis
        self._canvas = canvas
        self._lines = None
        self._last_line_dt = None
        self._mean_time = None

    def _refresh_plot(self):
        self._ax.relim()
        self._ax.autoscale_view()
        self._canvas.draw()

    def _yield_dts(self):
        if self._lines is None:
            return

        dts = self._listbox.get(0, self._listbox.size())
        for dt in dts:
            if dt in self._lines:
                yield dt

    def _highlight_item(self, index):
        dt = self._listbox.get(index)
        if self._lines is not None:
            self._highlight_line(dt)
            if self._last_line_dt is not None:
                self._de_highlight_line(self._last_line_dt)

            self._refresh_plot()
            self._last_line_dt = dt

    def on_select(self, evt):
        w = evt.widget
        if w is not self._listbox:
            return
        cur_selection = self._listbox.curselection()
        if not cur_selection:
            return
        index = int(cur_selection[0])
        self._highlight_item(index)

    def _highlight_line(self, dt):
        if dt in self._lines.keys():
            self._lines[dt].set(linewidth=6, color='green')

    def _de_highlight_line(self, dt):
        if dt in self._lines.keys():
            self._lines[dt].set(linewidth=1, color='black')

    def _normalize_times(self):
        uniform_times = []
        for dt in self._yield_dts():
            (_, _, ts) = zip(*self._periods[dt])
            uniform_times.append(ts[-1] - ts[0])

        self._mean_time = np.linspace(0, np.mean(np.array(uniform_times)), num=settings.get_correction_bins())
        print(f"Mean time = {self._mean_time}")
        for dt in self._yield_dts():
            selected = self._lines[dt]
            selected.set(xdata=self._mean_time)

    def smooth(self):
        self._perform_function_on_lines(lambda x: moving_mean(x, 4))
        self._refresh_plot()

    def _perform_function_on_lines(self, f):
        for dt in self._yield_dts():
            selected = self._lines[dt]
            y_data = f(selected.get_ydata())
            selected.set(ydata=y_data)

    def calculate_speed(self):
        self._perform_function_on_lines(lambda x: np.diff(x))
        for dt in self._yield_dts():
            selected_line = self._lines[dt]
            drift_speed_as = selected_line.get_ydata()
            times = 0.001*selected_line.get_xdata()
            time_increments = np.diff(times)
            print(f"Shape of drifts = {drift_speed_as.shape}, shape of times={time_increments.shape}")
            print(time_increments)
            true_speed = np.pad(np.divide(drift_speed_as, time_increments), (0, 1), mode='edge')
            selected_line.set(ydata=true_speed)

        self._refresh_plot()

    def average_periods(self):
        self._normalize_times()

        results = []
        for dt in self._yield_dts():
            selected_line = self._lines[dt]
            drift_speed_as = selected_line.get_ydata()[:-1]
            results.append(np.array(drift_speed_as))

        results = np.mean(np.array(results), axis=0)
        self._ax.clear()
        self._lines = self._ax.plot(self._mean_time, results)
        self._refresh_plot()
        return self._mean_time, results

    def save_lines_to_file(self):
        data = np.array(self._lines[0].get_data()).T
        np.savetxt("periods.csv", data, delimiter=',')

    def remove(self):
        cur_selection = self._listbox.curselection()
        if not cur_selection:
            return
        index = int(cur_selection[0])
        dt = self._listbox.get(index)
        if self._lines is not None:
            if dt in self._lines.keys():
                self._lines.pop(dt).remove()
                self._periods.pop(dt)
                self._refresh_plot()

        self._listbox.delete(index)

        new_index = min(index, self._listbox.size())
        self._listbox.select_set(new_index)
        self._highlight_item(new_index)

    def add_data(self, data):
        self._periods, self._lines = data  # ({ datetime : (ticks, drift, t)}, {datetime: line})

        for k, v in self._periods.items():
            self._listbox.insert('end', k)
