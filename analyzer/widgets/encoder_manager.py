import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter.messagebox import showinfo
import tkinter as tk
import re
from tkinter import filedialog


# encoder_logs_path_mock = "C:/Users/Florek/Desktop/_STEROWANIE/PEliminator/result.txt"
# result is made from: "C:/Users/Florek/Desktop/_STEROWANIE/Feigenbaum/utils/logs/encoder_log_2022-02-25_23-33"
encoder_logs_path_mock = None


def read_encoder_ticks(line):
    inside_of_braces = re.search(r'{(.*?)}', line).group(1).split(',')
    values = list(map(lambda x: x.split(':')[1], inside_of_braces))
    return int(int(values[0]) / 1000), int(values[2])


class EncoderManager:
    def __init__(self, root, frame, progress, aggregator):
        self._root = root
        self._progress = progress
        data_figure = plt.Figure(dpi=100)
        self._ax = data_figure.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(data_figure, frame)
        self._canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._readings = {}
        self._step_size = 0
        self._counter = 0
        self._aggregator = aggregator

    def _read_datetime_from_encoder(self, line):
        dt = line.split('ABS')[0].split(',')[0]
        a = self._progress["value"]
        self._progress['value'] += self._step_size
        if self._counter > 100:
            self._root.update_idletasks()
            self._counter = 0
        self._counter += 1
        return int(float(dt))

    def get_encoder_data(self):
        encoder_logs_path = encoder_logs_path_mock
        if encoder_logs_path is None:
            encoder_logs_path = filedialog.askopenfilename(title='Open file with encoder logs', initialdir='.')
        print(f"Encoder logs path = {encoder_logs_path}")
        with open(encoder_logs_path, 'r') as f:
            lines = f.readlines()

        self._step_size = 100.0 / len(lines)
        for line in lines:
            self._readings[self._read_datetime_from_encoder(line)] = read_encoder_ticks(line)

        print(list(self._readings.items())[:10])
        self._ax.plot(self._readings.keys(), [v[1] for v in self._readings.values()], 'r')
        self._progress["value"] = 0.0
        showinfo(message='The progress completed!')
        self._aggregator.push_encoder(self._readings)
