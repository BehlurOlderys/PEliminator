from package.widgets.pe_base_widget import PeBaseWidget
from tkinter import ttk
import tkinter as tk


PB_MAX_VALUE = 1000


class CaptureProgressBar(PeBaseWidget):
    def __init__(self, length=200, **kwargs):
        super(CaptureProgressBar, self).__init__(**kwargs)
        self._value = 0
        self._inc = 1
        self._style = ttk.Style()
        self._style.layout('text.Horizontal.TProgressbar',
                     [('Horizontal.Progressbar.trough',
                       {'children': [('Horizontal.Progressbar.pbar',
                                      {'side': 'left', 'sticky': 'ns'})],
                        'sticky': 'nswe'}),
                      ('Horizontal.Progressbar.label', {'sticky': ''})])
        self._style.configure('text.Horizontal.TProgressbar', text='0/0')

        self._progress_bar = ttk.Progressbar(self._frame,
                                             style='text.Horizontal.TProgressbar',
                                             length=length,
                                             maximum=PB_MAX_VALUE,
                                             value=self._value)

        self._progress_bar.pack(side=tk.TOP)

    def update(self, value):
        self._value = self._inc * value
        self._progress_bar.config(value=self._value)
        display_text = f"{int(self._value/self._inc)}/{int(PB_MAX_VALUE/self._inc)}"
        self._style.configure('text.Horizontal.TProgressbar', text=display_text)

    def finish(self):
        self.update(int(PB_MAX_VALUE/self._inc))

    def reset(self, max_no=PB_MAX_VALUE):
        self._inc = int(PB_MAX_VALUE/max_no)
        self._value = 0
        self._progress_bar.config(value=0)
        self._style.configure('text.Horizontal.TProgressbar', text="0/0")
