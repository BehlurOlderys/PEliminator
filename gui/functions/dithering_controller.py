from functions.spin_with_label import SpinWithLabel
from random import randint
import tkinter as tk


class DitheringController:
    def __init__(self, effect_function, image_threshold_var, max_as_var):
        self._effect_function = effect_function
        self._image_threshold_var = image_threshold_var
        self._max_as_var = max_as_var
        self._counter = 0
        self._enable = False

    def enable(self):
        self._counter = 0
        self._enable = True

    def get_enable(self):
        return self._enable

    def disable(self):
        self._enable = False

    def manual_dither(self, value_as):
        if not self._enable:
            return
        self._effect_function(value_as)

    def step(self):
        if not self._enable:
            return
        threshold = int(self._image_threshold_var.get())
        max_as = int(self._max_as_var.get())
        self._counter += 1
        if self._counter >= max(0, threshold):
            self._counter = 0
            value_as = randint(-max_as, max_as)
            self._effect_function(value_as)


class DitheringControllerGUI:
    def __init__(self, frame, label, effect_function):
        self._interval_var = tk.StringVar(value=0)
        self._max_as_var = tk.StringVar(value=10)
        self._manual_var = tk.StringVar(value=0)

        self._label = tk.Label(frame, text=label, font=('calibre', 10, 'bold'))
        self._label.pack(side=tk.LEFT)

        self._enable_button = tk.Button(frame, text="Enable", command=self._enable_action)
        self._enable_button.pack(side=tk.LEFT)

        self._interval_spin = SpinWithLabel(
            frame, self._interval_var, "Interval [frames]:", format="%d", increment=1, width=4, from_=1, to=9999)
        self._max_as_spin = SpinWithLabel(
            frame, self._interval_var, "Maximum amount [\"]:", format="%d", increment=1, width=3, from_=1, to=999)

        self._dithering_controller = DitheringController(effect_function, self._interval_var, self._max_as_var)

        self._manual_as_spin = SpinWithLabel(
            frame, self._manual_var, "Manual dither[\"]:", format="%d", increment=1, width=3, from_=-999, to=999)

        self._manual_button = tk.Button(frame, text="Move", command=self._manual_dither, state=tk.DISABLED)
        self._manual_button.pack(side=tk.RIGHT)

    def _manual_dither(self):
        self._dithering_controller.manual_dither(int(self._manual_var.get()))

    def _enable_action(self):
        if not self._dithering_controller.get_enable():
            self._manual_button.configure(state=tk.NORMAL)
            self._enable_button.configure(text="Disable")
            self._enabled = True
            self._dithering_controller.enable()
        else:
            self._manual_button.configure(state=tk.DISABLED)
            self._enable_button.configure(text="Enable")
            self._enabled = False
            self._dithering_controller.disable()
