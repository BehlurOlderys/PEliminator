from tkinter.messagebox import showinfo
import os


class Automat:
    def __init__(self, root, displayer, plotter, progress, file_list, aggregator):
        self._root = root
        self._displayer = displayer
        self._plotter = plotter
        self._progress = progress
        self._file_list = file_list
        self._data = {}
        self._aggregator = aggregator

    def go_auto(self):
        n = self._file_list.get_files_number()
        if n is None:  # TODO: maybe a pop-up?
            return
        counter = 1
        step_size = counter / n
        x, y, name = self._displayer.calculate_center()
        self._data[name] = (x, y)

        points = []
        while self._file_list.next() is not None:
            x, y, name = self._displayer.calculate_center(auto=True)
            points.append((x, y))
            self._data[name] = (x, y)

            counter += 1
            percent = 100 * counter / self._file_list.get_files_number()
            print(f"Percent = {percent}, file = {name}")
            self._progress.step(step_size)
            self._progress['value'] = percent
            self._root.update_idletasks()

        self._progress["value"] = 0.0
        self._plotter.add_points(points, self._file_list.get_files_relative_time())
        drift_data = {os.path.basename(f): v for f, v in self._data.items()}
        self._aggregator.push_drift(drift_data)
        showinfo(message='The progress completed!')
