import tkinter as tk
from tkinter import ttk
import time





class BaseGuiApplication:
    def __init__(self, geometry="800x640", title="MyApp", *args, **kwargs):
        self._root = tk.Tk()
        self._root.title(title)
        self._root.geometry(geometry)

        self._style = ttk.Style()
        self._style.theme_use('alt')
        self._style.configure("B.TSeparator", background='#222222')
        self._style.configure('TButton', font=('calibre', 10, 'bold'), background='#333333', foreground='white')
        self._style.map('TButton', background=[('active', '#444444')])
        self._style.configure("B.TFrame", background="#222222")
        self._style.configure("C.TFrame", background="#772222")
        self._style.configure("D.TFrame", background="#222277")
        self._style.configure("E.TFrame", background="#227722")
        self._style.configure("B.TCombobox", font=('calibre', 10, 'bold'), background='#222222', foreground='white',
                              fieldbackground='#333333')

        self._style.configure("B.TSpinbox",
                              font=('calibre', 10, 'bold'), background='#333333', foreground='white',
                              fieldbackground='#333333')
        self._style.configure("B.TLabel", background="#222222", foreground="white", font=('calibre', 10, 'bold'))

    def run(self):
        self._root.mainloop()


class AfterQueueTask:
    def __init__(self, timeout_s, f, *args, **kwargs):
        self._timeout_s = timeout_s
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


AFTER_QUEUE_MIN_CHECK_TIMEOUT_MS = 1000


class SimpleGuiApplication(BaseGuiApplication):
    def __init__(self, *args, **kwargs):
        super(SimpleGuiApplication, self).__init__(*args, **kwargs)
        self._main_frame = ttk.Frame(self._root, style="B.TFrame")
        self._main_frame.pack(expand=True, fill='both')
        self._after_queue = []

    def _add_task(self, timeout_s, f, *args, **kwargs):
        self._after_queue.append(AfterQueueTask(timeout_s, f, *args, **kwargs))

    def _call_after_queue(self):
        self._root.after(AFTER_QUEUE_MIN_CHECK_TIMEOUT_MS, self._call_after_queue)
        [t.try_to_run() for t in self._after_queue]

    def run(self):
        [t.start() for t in self._after_queue]
        self._root.after(AFTER_QUEUE_MIN_CHECK_TIMEOUT_MS, self._call_after_queue)
        super(SimpleGuiApplication, self).run()
