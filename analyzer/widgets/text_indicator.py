import tkinter as tk


class TextIndicator:
    def __init__(self, frame, s):
        self._holder = tk.Frame(frame)
        self._indicator_label = tk.Label(self._holder, text=s)
        self._indicator_label.pack(side=tk.LEFT)
        self._indicator_light = tk.Label(self._holder)
        self._indicator_light.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._holder.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.set_light(False)

    def set_light(self, value):
        if value is True:
            self._indicator_light.configure(text='YES', fg='white', bg='green')
        else:
            self._indicator_light.configure(text='NO', fg='yellow', bg='red')
