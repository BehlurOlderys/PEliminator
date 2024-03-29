import tkinter as tk
from tkinter import ttk
import time


SUNKABLE_BUTTON = 'SunkableButton.TButton'


class BaseGuiApplication:
    def __init__(self, geometry="800x640", title="MyApp", *args, **kwargs):
        self._root = tk.Tk()
        self._root.title(title)
        self._root.geometry(geometry)

        self._style = ttk.Style()
        self._style.theme_use('alt')

        self._style.configure("SunkableButton.TButton",
                              relief=tk.SUNKEN,
                              font=('calibre', 10, 'bold'), background='#bb6644', foreground='#cccccc')
        self._style.map('SunkableButton.TButton',
                        relief=[('active', tk.SUNKEN)],
                        background=[('active', '#cc7755')],
                        foreground=[('active', 'white')])
        self._style.configure("B.TSeparator", background='#222222')
        self._style.configure('B.Horizontal.TScale', background="#222222")
        self._style.configure('TButton', font=('calibre', 10, 'bold'), background='#333333', foreground='#cccccc')
        self._style.map('TButton', background=[('active', '#444444')],
                                  foreground=[('active', 'white')])
        self._style.configure("B.TFrame", background="#222222")
        self._style.configure("B.TCheckbutton",
                              font=('calibre', 10, 'bold'),
                              background='#333333',
                              foreground='#999999')
        self._style.map('B.TCheckbutton',
              foreground=[('active', '#999999')],
              background=[('active', '#555555')])
        self._style.configure("D.TFrame", background="#222277")
        self._style.configure("E.TFrame", background="#227722")
        self._style.configure("B.TCombobox", font=('calibre', 10, 'bold'), background='#222222', foreground='white',
                              fieldbackground='#333333')
        self._style.configure("B.TSpinbox",
                              font=('calibre', 10, 'bold'), background='#333333', foreground='white',
                              fieldbackground='#333333')
        self._style.configure("B.TLabel", background="#222222", foreground="white", font=('calibre', 10, 'bold'))

    def maximize(self):
        self._root.state('zoomed')

    def run(self):
        self._root.mainloop()


class AfterQueueTask:
    def __init__(self, f, *args, **kwargs):
        if "timeout_ms" in kwargs:
            self._timeout_s = float(kwargs.pop("timeout_ms") / 1000)
        elif "timeout_s" in kwargs:
            self._timeout_s = kwargs.pop("timeout_s")
        else:
            raise RuntimeError("Did not provide timeout for task!")

        print(f"Using actual task timeout: {self._timeout_s}")
        self._f = f
        self._args = args
        self._kwargs = kwargs
        self._time = time.time

    def start(self):
        self._time = time.time()

    def try_to_run(self):
        end_time = time.time()
        interval = end_time - self._time
        if interval > self._timeout_s:
            self._time = end_time
            self._f(*self._args, **self._kwargs)


AFTER_QUEUE_MIN_CHECK_TIMEOUT_MS = 100


class SimpleGuiApplication(BaseGuiApplication):
    def __init__(self, *args, **kwargs):
        super(SimpleGuiApplication, self).__init__(*args, **kwargs)
        self._main_frame = ttk.Frame(self._root, style="B.TFrame")
        self._main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._after_queue = []

    def _add_task(self, f, *args, **kwargs):
        self._after_queue.append(AfterQueueTask(f, *args, **kwargs))

    def _call_after_queue(self):
        self._root.after(AFTER_QUEUE_MIN_CHECK_TIMEOUT_MS, self._call_after_queue)
        [t.try_to_run() for t in self._after_queue]

    def run(self):
        [t.start() for t in self._after_queue]
        self._root.after(AFTER_QUEUE_MIN_CHECK_TIMEOUT_MS, self._call_after_queue)
        super(SimpleGuiApplication, self).run()
